"""End-to-end CAMCA pipeline orchestrating multiple VLM backends."""
from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .backends import VLMBackend, BackendError
from .prompts import (
    DEVICE_ID_PROMPT,
    build_segmentation_prompt,
    build_evaluator_prompt,
)
from .scoring import compute_stats, compute_final_score


@dataclass
class PersonaConfig:
    """Identifies a specific evaluator persona invocation."""

    name: str  # e.g., "evaluator-a"
    persona_label: str  # e.g., "GINA-strict"
    backend: VLMBackend

    def model_id(self) -> str:
        return self.backend.model_id()


@dataclass
class PipelineResult:
    case_id: str
    case_dir: Path
    device_id: dict[str, Any] = field(default_factory=dict)
    segments: dict[str, Any] = field(default_factory=dict)
    evaluator_a: dict[str, Any] = field(default_factory=dict)
    evaluator_b: dict[str, Any] = field(default_factory=dict)
    tie_breaker: dict[str, Any] | None = None
    kappa_stats: dict[str, Any] = field(default_factory=dict)
    final_score: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def extract_frames(video_path: Path, output_dir: Path, fps: float = 2.0) -> list[Path]:
    """Extract frames from video using ffmpeg. Returns sorted list of frame paths.

    v0.3.0 change (L7 fix): default fps raised 1.0 → 2.0 to better capture
    sub-second events like pMDI actuation. For critical-event analysis,
    callers can pass fps=4 for even denser sampling.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pattern = output_dir / "frame_%03d.jpg"
    result = subprocess.run([
        "ffmpeg", "-i", str(video_path), "-vf", f"fps={fps}",
        str(pattern), "-y",
    ], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[:500]}")
    frames = sorted(output_dir.glob("frame_*.jpg"))
    if not frames:
        raise RuntimeError(f"No frames extracted from {video_path}")
    return frames


def extract_frames_step_aware(
    video_path: Path,
    output_dir: Path,
    base_fps: float = 2.0,
    critical_steps_fps: float = 4.0,
    critical_step_segments: list[dict] | None = None,
) -> list[Path]:
    """v0.3.0 (L7 fix): step-aware frame sampling.

    Extracts at base_fps throughout video, but uses critical_steps_fps for
    segments listed in critical_step_segments (typically S5 coordination,
    S7 breath-hold).

    Args:
        video_path: input .mp4
        output_dir: where to save frames
        base_fps: default sampling rate for general video (default 2.0)
        critical_steps_fps: dense sampling for critical events (default 4.0)
        critical_step_segments: list of {"start_ts": float_sec, "end_ts": float_sec}
                                If None, falls back to uniform base_fps extraction.

    Returns:
        Sorted list of all frame paths.
    """
    if not critical_step_segments:
        return extract_frames(video_path, output_dir, fps=base_fps)

    # Extract base frames
    output_dir = Path(output_dir)
    base_frames = extract_frames(video_path, output_dir / "base", fps=base_fps)

    # Extract dense frames in critical segments
    dense_dir = output_dir / "dense"
    dense_dir.mkdir(parents=True, exist_ok=True)
    for i, seg in enumerate(critical_step_segments):
        seg_pattern = dense_dir / f"seg{i:02d}_dense_%03d.jpg"
        subprocess.run([
            "ffmpeg", "-i", str(video_path),
            "-ss", str(seg["start_ts"]), "-to", str(seg["end_ts"]),
            "-vf", f"fps={critical_steps_fps}",
            str(seg_pattern), "-y",
        ], capture_output=True, text=True)

    all_frames = sorted(base_frames + list(dense_dir.glob("seg*_dense_*.jpg")))
    return all_frames


class MultiModelPipeline:
    """End-to-end CAMCA pipeline.

    Args:
        enable_telemetry: If True, extract MediaPipe + audio telemetry (P1) and
                         inject summary into evaluator prompts (P2). Requires
                         `pip install camca[telemetry]`. Defaults to True if
                         dependencies available.
        use_pydantic_schema: If True (default), enforce VLM output via Pydantic
                            schema (P4) — Gemini response_schema, Claude tool_use.
    """

    def __init__(
        self,
        device_id_backend: VLMBackend,
        segmenter_backend: VLMBackend,
        evaluator_a: PersonaConfig,
        evaluator_b: PersonaConfig,
        tie_breaker: PersonaConfig | None = None,
        case_dir: Path | None = None,
        enable_telemetry: bool = True,
        use_pydantic_schema: bool = True,
        use_phase_engine: bool = False,
    ):
        self.device_id_backend = device_id_backend
        self.segmenter_backend = segmenter_backend
        self.evaluator_a = evaluator_a
        self.evaluator_b = evaluator_b
        self.tie_breaker = tie_breaker
        self.case_dir = Path(case_dir) if case_dir else None
        self.enable_telemetry = enable_telemetry
        self.use_pydantic_schema = use_pydantic_schema
        self.use_phase_engine = use_phase_engine
        self.phase_vlm_weight_up = False
        self._telemetry_summary: dict | None = None
        self._telemetry_stream: list[dict] | None = None
        self._video_path: Path | None = None
        self._stage_records: list[dict[str, Any]] = []

    def inject_telemetry(self, stream: list[dict]) -> None:
        """외부에서 추출한 telemetry(예: 익명화 전 원본 영상)를 주입 — 내부 재추출을 건너뛴다."""
        self._telemetry_stream = stream
        try:
            from .telemetry.breath_hold_detector import compute_telemetry_summary
            self._telemetry_summary = compute_telemetry_summary(stream)
        except ImportError:
            self._telemetry_summary = None

    def set_phase_vlm_weight_up(self, value: bool = True) -> None:
        """quality gate가 telemetry 열화(낮은 얼굴 검출률·측면 촬영)를 보고한
        영상에서 Stage 2 VLM 가중을 상향한다 (spec §5.3-2, L6 완화)."""
        self.phase_vlm_weight_up = bool(value)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _record(self, name: str, model: str, started: str, duration_ms: int,
                status: str = "success", error: str | None = None) -> None:
        self._stage_records.append({
            "stage_name": name, "model_used": model,
            "started_at": started, "completed_at": self._now_iso(),
            "duration_ms": duration_ms, "status": status, "error_message": error,
        })

    def _write_json(self, filename: str, data: Any) -> Path | None:
        if not self.case_dir:
            return None
        self.case_dir.mkdir(parents=True, exist_ok=True)
        path = self.case_dir / filename
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return path

    def _stage_device_id(self, frames: list[Path]) -> dict[str, Any]:
        start = self._now_iso()
        t0 = time.perf_counter()
        try:
            result = self.device_id_backend.analyze_frames(
                DEVICE_ID_PROMPT, frames[:5], expect_json=True,
            )
        except BackendError as e:
            self._record("device-id", self.device_id_backend.model_id(), start,
                         int((time.perf_counter() - t0) * 1000),
                         status="error", error=str(e))
            raise
        self._record("device-id", self.device_id_backend.model_id(), start,
                     int((time.perf_counter() - t0) * 1000))
        self._write_json("02_device_id.json", result)
        return result

    def _stage_segment(self, frames: list[Path], device_type: str,
                       video_path: Path | None = None,
                       telemetry: list[dict] | None = None,
                       case_id: str | None = None) -> dict[str, Any]:
        # v0.4.0: telemetry-anchored phase engine (opt-in)
        if self.use_phase_engine and telemetry:
            from .segmentation import PhaseRecognitionEngine
            start = self._now_iso()
            t0 = time.perf_counter()
            engine = PhaseRecognitionEngine(
                vlm_backend=self.segmenter_backend,
                vlm_weight_up=self.phase_vlm_weight_up,
            )
            result = engine.segment_from_telemetry(
                telemetry, device_type, case_id=case_id or "unknown",
                video_path=video_path,
            )
            self._record("phase-engine", self.segmenter_backend.model_id(),
                         start, int((time.perf_counter() - t0) * 1000))
            self._write_json("03_segments.json", result)
            return result
        # 기존 VLM-프롬프트 경로 (변경 없음)
        start = self._now_iso()
        t0 = time.perf_counter()
        prompt = build_segmentation_prompt(device_type)
        try:
            result = self.segmenter_backend.analyze_frames(
                prompt, frames, expect_json=True,
            )
        except BackendError as e:
            self._record("video-segmenter", self.segmenter_backend.model_id(),
                         start, int((time.perf_counter() - t0) * 1000),
                         status="error", error=str(e))
            raise
        self._record("video-segmenter", self.segmenter_backend.model_id(),
                     start, int((time.perf_counter() - t0) * 1000))
        self._write_json("03_segments.json", result)
        return result

    def _stage_telemetry(self, video_path: Path) -> dict | None:
        """Extract quantitative telemetry (P1) — runs once before evaluators."""
        if not self.enable_telemetry:
            return None
        start = self._now_iso()
        t0 = time.perf_counter()
        try:
            from .telemetry import extract_telemetry
            from .telemetry.breath_hold_detector import compute_telemetry_summary
            stream = extract_telemetry(video_path)
            self._telemetry_stream = stream  # raw 10Hz stream — phase engine 입력
            summary = compute_telemetry_summary(stream)
            self._record("telemetry", "MediaPipe+librosa",
                         start, int((time.perf_counter() - t0) * 1000))
            self._write_json("01b_telemetry_stream.json", {"samples": stream[:200]})
            self._write_json("01c_telemetry_summary.json", summary)
            return summary
        except ImportError as e:
            self._record("telemetry", "MediaPipe+librosa",
                         start, int((time.perf_counter() - t0) * 1000),
                         status="skipped",
                         error=f"telemetry deps not installed: {e}")
            print(f"  Telemetry skipped: {e}")
            return None
        except Exception as e:
            self._record("telemetry", "MediaPipe+librosa",
                         start, int((time.perf_counter() - t0) * 1000),
                         status="error", error=str(e))
            print(f"  Telemetry failed: {e} — continuing without telemetry")
            return None

    def _stage_evaluate(
        self, persona: PersonaConfig, frames: list[Path],
        segments: dict, device_type: str, case_id: str, output_filename: str,
    ) -> dict[str, Any]:
        start = self._now_iso()
        t0 = time.perf_counter()
        prompt = build_evaluator_prompt(
            persona_label=persona.persona_label,
            device_type=device_type,
            case_id=case_id,
            model_id=persona.model_id(),
            segments=segments,
            telemetry_summary=self._telemetry_summary,
        )

        # Schema enforcement (P4)
        schema = None
        if self.use_pydantic_schema:
            try:
                from .schemas import VLMClinicalReport, can_enforce_schema
                if can_enforce_schema():
                    schema = VLMClinicalReport
            except ImportError:
                pass

        try:
            result = persona.backend.analyze_frames(
                prompt, frames, expect_json=True, max_tokens=6000,
                response_schema=schema,
            )
        except BackendError as e:
            self._record(persona.name, persona.model_id(),
                         start, int((time.perf_counter() - t0) * 1000),
                         status="error", error=str(e))
            raise
        self._record(persona.name, persona.model_id(),
                     start, int((time.perf_counter() - t0) * 1000))
        self._write_json(output_filename, result)
        return result

    def _stage_kappa(self) -> dict[str, Any]:
        start = self._now_iso()
        t0 = time.perf_counter()
        stats = compute_stats(self.evaluator_a_result, self.evaluator_b_result)
        self._record("kappa-calculator", "deterministic-python", start,
                     int((time.perf_counter() - t0) * 1000))
        self._write_json("06b_kappa_stats.json", stats)
        return stats

    def _stage_final_score(
        self, per_step_levels: dict[str, int], critical_errors: list[str],
        device_type: str, case_id: str,
    ) -> dict[str, Any]:
        start = self._now_iso()
        t0 = time.perf_counter()
        final = compute_final_score(per_step_levels, critical_errors, device_type, case_id)
        self._record("scoring-engine", "deterministic-python", start,
                     int((time.perf_counter() - t0) * 1000))
        self._write_json("07_final_score.json", final)
        return final

    # ----- Public runners -----

    def run(
        self,
        frames: list[Path],
        case_id: str,
        invoke_tie_breaker_threshold: float = 0.6,
        verbose: bool = True,
    ) -> PipelineResult:
        """Run the full pipeline given pre-extracted frames."""
        pipeline_start = self._now_iso()
        pipeline_t0 = time.perf_counter()
        result = PipelineResult(case_id=case_id, case_dir=self.case_dir or Path("."))

        if verbose:
            print(f"[1/5] Device ID via {self.device_id_backend.model_id()}...")
        result.device_id = self._stage_device_id(frames)
        device_type = result.device_id.get("device_type", "unknown")
        if verbose:
            print(f"      → {device_type} (confidence {result.device_id.get('confidence')})")

        if verbose:
            print(f"[2/5] Segmenting via {self.segmenter_backend.model_id()}...")
        result.segments = self._stage_segment(
            frames, device_type,
            video_path=self._video_path, telemetry=self._telemetry_stream,
            case_id=case_id,
        )

        if verbose:
            print(f"[3a/5] Evaluator A ({self.evaluator_a.persona_label}) via {self.evaluator_a.model_id()}...")
        result.evaluator_a = self._stage_evaluate(
            self.evaluator_a, frames, result.segments, device_type, case_id,
            "04_evaluator_a.json",
        )
        self.evaluator_a_result = result.evaluator_a

        if verbose:
            print(f"[3b/5] Evaluator B ({self.evaluator_b.persona_label}) via {self.evaluator_b.model_id()}...")
        result.evaluator_b = self._stage_evaluate(
            self.evaluator_b, frames, result.segments, device_type, case_id,
            "05_evaluator_b.json",
        )
        self.evaluator_b_result = result.evaluator_b

        if verbose:
            print("[4/5] Kappa + adjudication...")
        result.kappa_stats = self._stage_kappa()
        kappa_lin = result.kappa_stats["kappa"]["linear_weighted"]
        if verbose:
            print(f"      → κ_linear = {kappa_lin}")

        # Optional tie-breaker
        if self.tie_breaker and kappa_lin < invoke_tie_breaker_threshold:
            if verbose:
                print(f"[4b/5] Tie-breaker via {self.tie_breaker.model_id()}...")
            result.tie_breaker = self._stage_evaluate(
                self.tie_breaker, frames, result.segments, device_type, case_id,
                "06c_tie_breaker.json",
            )

        # Final scoring (consensus from A + B, with TB tiebreak if present)
        if verbose:
            print("[5/5] Final scoring...")
        consensus_levels = _build_consensus_levels(
            result.evaluator_a, result.evaluator_b, result.tie_breaker,
        )
        consensus_critical = result.kappa_stats["critical_error_consensus"]["both_flagged"]
        result.final_score = self._stage_final_score(
            consensus_levels, consensus_critical, device_type, case_id,
        )

        # Metadata
        result.metadata = {
            "case_id": case_id,
            "pipeline_version": "0.1.0 (camca-py)",
            "started_at": pipeline_start,
            "completed_at": self._now_iso(),
            "total_duration_ms": int((time.perf_counter() - pipeline_t0) * 1000),
            "stages": self._stage_records,
            "config": {
                "device_id_backend": self.device_id_backend.model_id(),
                "segmenter_backend": self.segmenter_backend.model_id(),
                "evaluator_a": f"{self.evaluator_a.persona_label} / {self.evaluator_a.model_id()}",
                "evaluator_b": f"{self.evaluator_b.persona_label} / {self.evaluator_b.model_id()}",
                "tie_breaker": (
                    f"{self.tie_breaker.persona_label} / {self.tie_breaker.model_id()}"
                    if self.tie_breaker else None
                ),
            },
        }
        self._write_json("00_pipeline_metadata.json", result.metadata)

        if verbose:
            print(f"Done — {result.metadata['total_duration_ms']/1000:.1f}s total")
        return result

    def run_from_video(
        self,
        video_path: Path | str,
        case_id: str,
        fps: float = 1.0,
        invoke_tie_breaker_threshold: float = 0.6,
        verbose: bool = True,
    ) -> PipelineResult:
        """Extract frames + telemetry from a video file and run the full pipeline."""
        video_path = Path(video_path)
        self._video_path = video_path
        frames_dir = (self.case_dir or Path(".")) / "frames"
        if verbose:
            print(f"[0a/5] Extracting frames from {video_path.name} at {fps} fps...")
        frames = extract_frames(video_path, frames_dir, fps=fps)
        if verbose:
            print(f"       → {len(frames)} frames")

        # P1: Extract quantitative telemetry BEFORE evaluator stages
        # (skip if already injected via inject_telemetry() — e.g. extracted from
        # the pre-anonymization original video, since the anonymized video has
        # no audio and would yield degraded telemetry).
        if self._telemetry_stream is not None:
            if verbose:
                print("[0b/5] Using injected telemetry (skipping re-extraction)...")
        elif self.enable_telemetry:
            if verbose:
                print(f"[0b/5] Extracting telemetry (MediaPipe + librosa)...")
            self._telemetry_summary = self._stage_telemetry(video_path)
            if verbose and self._telemetry_summary and not self._telemetry_summary.get("empty"):
                bh = self._telemetry_summary.get("breath_hold")
                if bh:
                    print(f"       Breath-hold: {bh['duration_ms']/1000:.1f}s (adequate={bh['is_adequate']})")
                ca = self._telemetry_summary.get("clinical_anchors", {})
                s5 = ca.get("S5_coordination_check", {})
                if s5.get("interpretation"):
                    print(f"       Coordination: {s5['interpretation'][:80]}")

        return self.run(frames, case_id=case_id,
                        invoke_tie_breaker_threshold=invoke_tie_breaker_threshold,
                        verbose=verbose)


def _build_consensus_levels(
    eval_a: dict, eval_b: dict, tie_breaker: dict | None = None,
) -> dict[str, int]:
    """Build consensus per-step levels from A, B (and optionally TB).

    Without TB: rounded average.
    With TB on disputed steps: 2/3 majority on disputed; agree-only on others.
    """
    levels_a = {s["step_id"]: s["level"] for s in eval_a.get("per_step_evaluation", [])
                if s.get("level") is not None}
    levels_b = {s["step_id"]: s["level"] for s in eval_b.get("per_step_evaluation", [])
                if s.get("level") is not None}

    tb_levels: dict[str, int] = {}
    if tie_breaker:
        for s in tie_breaker.get("disputed_step_evaluations", []) or tie_breaker.get("per_step_evaluation", []):
            if s.get("level") is not None or s.get("tie_breaker_level") is not None:
                tb_levels[s["step_id"]] = s.get("tie_breaker_level") or s.get("level")

    consensus = {}
    for step_id in levels_a:
        if step_id not in levels_b:
            continue
        a, b = levels_a[step_id], levels_b[step_id]
        if a == b:
            consensus[step_id] = a
        elif step_id in tb_levels:
            # Majority vote 2/3
            votes = sorted([a, b, tb_levels[step_id]])
            consensus[step_id] = votes[1]  # median
        else:
            consensus[step_id] = round((a + b) / 2)
    return consensus
