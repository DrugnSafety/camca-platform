"""Phase Recognition Engine — Stage 1(events) → Stage 2(VLM refine) → Stage 3(align).

VLM 백엔드가 None이면 Stage 2를 건너뛴다 (telemetry-only 모드 — CI/테스트/저비용 스크리닝).
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from .events import detect_events
from .alignment import align_events_to_steps
from .templates import get_template
from .vlm_refiner import (
    apply_vlm_refinement,
    build_blind_scan_prompt,
    build_refiner_prompt,
    extract_boundary_frames,
)


class PhaseRecognitionEngine:
    """telemetry-anchored 하이브리드 세그멘테이션 엔진.

    Usage:
        engine = PhaseRecognitionEngine(vlm_backend=create_backend("claude:sonnet"))
        result = engine.segment(video_path, device_type="pMDI", case_id="X")
        # 또는 telemetry를 이미 갖고 있으면:
        result = engine.segment_from_telemetry(telemetry, "pMDI", "X")
    """

    def __init__(self, vlm_backend: Any | None = None):
        self.vlm_backend = vlm_backend

    def segment_from_telemetry(
        self,
        telemetry: list[dict],
        device_type: str,
        case_id: str,
        video_path: Path | str | None = None,
    ) -> dict[str, Any]:
        duration_ms = telemetry[-1]["timestamp_ms"] if telemetry else 0
        template = get_template(device_type)

        # Stage 1
        events = detect_events(telemetry, device_type)

        # Stage 3 (draft — Stage 2 전에 draft 경계가 필요)
        segments = align_events_to_steps(events, template, duration_ms)

        # Stage 2 (VLM 있고 영상 접근 가능할 때만)
        vlm_model = None
        if self.vlm_backend is not None and video_path is not None:
            segments = self._refine_with_vlm(segments, Path(video_path), device_type)
            vlm_model = self.vlm_backend.model_id()

        return {
            "engine": "telemetry-anchored-v1",
            "case_id": case_id,
            "device_type": device_type,
            "total_duration_ms": duration_ms,
            "vlm_model": vlm_model,
            "events": [e.to_dict() for e in events],
            "segments": segments,
        }

    def segment(
        self,
        video_path: Path | str,
        device_type: str,
        case_id: str,
    ) -> dict[str, Any]:
        """영상에서 telemetry 추출부터 실행하는 편의 진입점 (mediapipe 필요)."""
        from ..telemetry.pipeline import extract_telemetry
        telemetry = extract_telemetry(video_path)
        return self.segment_from_telemetry(telemetry, device_type, case_id, video_path)

    # ---- internal ----

    def _refine_with_vlm(
        self, segments: list[dict], video_path: Path, device_type: str
    ) -> list[dict]:
        import json

        with tempfile.TemporaryDirectory(prefix="camca_refine_") as tmp:
            tmp_dir = Path(tmp)
            merged = segments

            # (a) telemetry 경계 확인 — observable step마다 경계 dense 프레임
            for seg in [s for s in merged if s.get("observable")]:
                frames = extract_boundary_frames(video_path, seg["t_start_ms"], tmp_dir)
                if not frames:
                    continue
                raw = self.vlm_backend.analyze_frames(build_refiner_prompt(seg), frames)
                parsed = raw if isinstance(raw, dict) else json.loads(raw)
                merged = apply_vlm_refinement(merged, {"segments": [parsed]})

            # (b) telemetry-blind step — sparse 전체 스캔 1회
            blind = [s for s in merged if s.get("needs_vlm")]
            if blind:
                sparse = extract_boundary_frames(
                    video_path, center_ms=0, output_dir=tmp_dir,
                    window_ms=10 ** 9, fps=1,   # 전체 구간 1fps
                )
                raw = self.vlm_backend.analyze_frames(
                    build_blind_scan_prompt(blind, device_type), sparse,
                )
                parsed = raw if isinstance(raw, dict) else json.loads(raw)
                merged = apply_vlm_refinement(merged, parsed)

        return merged
