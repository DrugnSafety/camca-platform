"""Stage 2 — VLM이 후보 경계 ±window의 dense 프레임만 보고 라벨 확정/보정.

역할 분리:
  - telemetry 경계가 있으면 VLM은 '확인자' — 일치 시 confidence 상승(source=both),
    큰 불일치 시 conflict_flagged (기존 reconciliation 정책과 동일 사상).
  - telemetry-blind step(needs_vlm)은 VLM이 '검출자' — sparse 전체 스캔으로 채움.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

BOUNDARY_WINDOW_MS = 1000
BOUNDARY_DENSE_FPS = 6
VLM_AGREEMENT_TOLERANCE_MS = 500
VLM_CONFLICT_THRESHOLD_MS = 2000


def extract_boundary_frames(
    video_path: Path | str,
    center_ms: int,
    output_dir: Path,
    window_ms: int = BOUNDARY_WINDOW_MS,
    fps: int = BOUNDARY_DENSE_FPS,
) -> list[Path]:
    """경계 center_ms ± window_ms 구간을 dense fps로 추출 (L7 해결의 핵심)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    start_sec = max(0.0, (center_ms - window_ms) / 1000.0)
    duration_sec = 2 * window_ms / 1000.0
    pattern = str(output_dir / f"b{center_ms}_%03d.png")
    subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{start_sec:.3f}", "-i", str(video_path),
         "-t", f"{duration_sec:.3f}", "-vf", f"fps={fps}", pattern],
        capture_output=True, check=True,
    )
    return sorted(output_dir.glob(f"b{center_ms}_*.png"))


def build_refiner_prompt(segment: dict[str, Any], window_ms: int = BOUNDARY_WINDOW_MS) -> str:
    """단일 세그먼트 경계 확인용 프롬프트 (JSON 출력 강제)."""
    return (
        f"You are verifying one step of an inhaler-technique video.\n"
        f"Step: {segment['step_id']} — {segment['label']}\n"
        f"Telemetry-proposed window: {segment['t_start_ms']}ms to {segment['t_end_ms']}ms "
        f"(frames cover ±{window_ms}ms around this window).\n"
        f"Confirm whether this step actually occurs here, adjust boundaries if the frames "
        f"show otherwise, and describe what you see.\n"
        f"Respond ONLY with JSON: {{\"step_id\": \"{segment['step_id']}\", "
        f"\"observed\": bool, \"t_start_ms\": int, \"t_end_ms\": int, "
        f"\"visual_summary\": str, \"confidence\": float}}"
    )


def build_blind_scan_prompt(unobserved: list[dict[str, Any]], device_type: str) -> str:
    """telemetry-blind step들(S2/S3 등)을 sparse 전체 프레임에서 찾는 프롬프트."""
    steps_desc = "\n".join(f"- {s['step_id']}: {s['label']}" for s in unobserved)
    return (
        f"You are scanning an inhaler-technique video ({device_type}) for steps that "
        f"body-landmark telemetry cannot detect:\n{steps_desc}\n"
        f"For EACH step above, report whether it is visible anywhere in these frames.\n"
        f"NEVER fabricate timestamps — if not visible, set observed=false.\n"
        f'Respond ONLY with JSON: {{"segments": [{{"step_id": str, "observed": bool, '
        f'"t_start_ms": int|null, "t_end_ms": int|null, "visual_summary": str, '
        f'"confidence": float}}]}}'
    )


def _clamp_no_overlap(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """observable 세그먼트를 리스트(템플릿) 순서로 훑어 겹침을 제거 —
    Stage 3의 구조 불변조건(경계 겹침 0건)을 VLM 경계 채택 후에도 보장."""
    prev_end: int | None = None
    for seg in segments:
        if not seg.get("observable") or seg.get("t_start_ms") is None:
            continue
        if prev_end is not None and seg["t_start_ms"] < prev_end:
            seg["t_start_ms"] = prev_end
        if seg.get("t_end_ms") is not None and seg["t_end_ms"] < seg["t_start_ms"]:
            seg["t_end_ms"] = seg["t_start_ms"]
        prev_end = seg.get("t_end_ms", seg["t_start_ms"])
    return segments


def apply_vlm_refinement(
    segments: list[dict[str, Any]],
    vlm_result: dict[str, Any],
    vlm_weight_up: bool = False,
) -> list[dict[str, Any]]:
    """VLM 응답을 draft 세그먼트에 병합 (순수 함수 — I/O 없음).

    규칙 (기본 모드):
      - needs_vlm step + VLM observed → observable=True, source=vlm
      - telemetry step + VLM 일치(±500ms) → source=both, confidence +0.1 (cap 1.0)
      - telemetry step + VLM 불일치(>2000ms) → conflict_flagged, confidence×0.6,
        경계는 telemetry 유지 (ms 정밀도 우위 원칙)

    vlm_weight_up=True (spec §5.3-2 — quality gate가 telemetry 열화를 보고한 영상):
      - 일치(±500ms) 규칙은 동일
      - 불일치(>500ms)면 VLM 경계를 채택 (source=vlm, telemetry 제안은
        telemetry_proposed_t_start_ms로 보존). conflict 구간(≥2000ms)의
        conflict_flagged는 유지 — NEEDS_ATTENTION 배지 경로 불변.
      - 채택 후 no-overlap 클램프 적용 (구조 불변조건 유지)
    """
    vlm_by_id = {s["step_id"]: s for s in vlm_result.get("segments", [])}
    refined = []
    adopted_any = False
    for seg in segments:
        seg = dict(seg)  # copy
        v = vlm_by_id.get(seg["step_id"])
        if v is None:
            refined.append(seg)
            continue
        if seg.get("needs_vlm") and v.get("observed"):
            seg.update(
                observable=True, needs_vlm=False,
                t_start_ms=v["t_start_ms"], t_end_ms=v["t_end_ms"],
                boundary_source="vlm",
                boundary_confidence=round(min(v.get("confidence", 0.5), 0.85), 2),
                visual_summary=v.get("visual_summary"),
            )
        elif seg.get("observable") and v.get("observed"):
            gap = abs(v["t_start_ms"] - seg["t_start_ms"])
            if gap <= VLM_AGREEMENT_TOLERANCE_MS:
                seg.update(
                    boundary_source="both",
                    boundary_confidence=round(min(1.0, seg["boundary_confidence"] + 0.1), 2),
                    visual_summary=v.get("visual_summary"),
                )
            elif vlm_weight_up:
                # telemetry 열화 모드: VLM 경계 채택 (검출자 cap 0.85와 동일)
                seg.update(
                    t_start_ms=v["t_start_ms"], t_end_ms=v["t_end_ms"],
                    boundary_source="vlm",
                    boundary_confidence=round(min(v.get("confidence", 0.5), 0.85), 2),
                    visual_summary=v.get("visual_summary"),
                    telemetry_proposed_t_start_ms=seg["t_start_ms"],
                )
                if gap >= VLM_CONFLICT_THRESHOLD_MS:
                    seg["conflict_flagged"] = True
                adopted_any = True
            elif gap >= VLM_CONFLICT_THRESHOLD_MS:
                seg.update(
                    conflict_flagged=True,
                    boundary_confidence=round(seg["boundary_confidence"] * 0.6, 2),
                    visual_summary=v.get("visual_summary"),
                    vlm_proposed_t_start_ms=v["t_start_ms"],
                )
            else:
                seg["visual_summary"] = v.get("visual_summary")
        refined.append(seg)
    if adopted_any:
        refined = _clamp_no_overlap(refined)
    return refined
