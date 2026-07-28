"""Pydantic schemas for structured VLM output (P4 — Gemini-style schema enforcement).

These schemas can be passed to:
  - Gemini's `response_schema` (response_mime_type="application/json")
  - Claude's tool_use (function calling with strict JSON output)
  - Ollama's `format` (limited support)

Falls back gracefully if pydantic is not installed (telemetry layer's only
strict dependency is pydantic v2, included in core dependencies).
"""
from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Stub class so type hints don't break
    class BaseModel:  # type: ignore
        pass
    def Field(*args, **kwargs):  # type: ignore
        return None


if PYDANTIC_AVAILABLE:

    class StepEvaluation(BaseModel):
        """Per-step evaluation entry."""
        step_id: str = Field(description="Step identifier (S1-S9 or T1-T9)")
        step_name: str = Field(description="Human-readable step name")
        level: int | None = Field(
            default=None,
            description="Proficiency level 0-3, or null if unobservable"
        )
        status: str = Field(
            default="observed",
            description="observed | unobservable | ambiguous"
        )
        rationale: str = Field(
            description="Evaluation reasoning with frame/timestamp evidence"
        )
        evidence_frames: list[int] = Field(
            default_factory=list,
            description="Frame indices supporting the rationale"
        )
        is_critical_error: bool = Field(default=False)
        matched_critical_error_id: str | None = Field(default=None)
        telemetry_anchors: dict[str, Any] = Field(
            default_factory=dict,
            description="Specific telemetry timestamps/values used as evidence"
        )


    class CriticalErrorDetection(BaseModel):
        critical_error_id: str = Field(description="e.g., CRIT-pMDI-04")
        description: str = Field(description="What the error is")
        evidence: str = Field(description="Specific frames/timestamps proving it")


    class EvaluationSummary(BaseModel):
        observable_steps: int
        observable_max: int
        observable_total_score: int
        observable_percent: float
        unobservable_steps: list[str] = Field(default_factory=list)
        critical_error_count: int
        overall_verdict_provisional: str = Field(
            description="PROFICIENT | ADEQUATE_WITH_EDUCATION | NEEDS_INTENSIVE_TRAINING | FAIL"
        )


    class VLMClinicalReport(BaseModel):
        """The complete evaluator output schema.

        Designed to be drop-in compatible with both:
          - The CAMCA plugin's evaluator-{a,b}.md schema
          - Gemini's response_schema enforcement
        """
        evaluator: str = Field(description="A | B | Tie-Breaker")
        evaluator_persona: str = Field(description="GINA-strict | real-world-pragmatic | clinical-pharmacy-educator")
        model: str = Field(description="Model identifier (e.g., claude-opus-4-7)")
        case_id: str
        device_type: str
        evaluated_at: str = Field(description="ISO 8601 UTC timestamp")
        per_step_evaluation: list[StepEvaluation]
        critical_errors_detected: list[CriticalErrorDetection] = Field(default_factory=list)
        summary: EvaluationSummary
        telemetry_used: bool = Field(
            default=False,
            description="Whether quantitative telemetry was provided as evaluation anchor"
        )


    class DeviceIdReport(BaseModel):
        """Output of device-id stage."""
        device_type: str = Field(description="pMDI | pMDI-spacer | DPI-turbuhaler | unknown")
        confidence: float = Field(ge=0.0, le=1.0)
        rationale: str
        frame_indices_used: list[int] = Field(default_factory=list)


    class VideoSegment(BaseModel):
        step_id: str
        step_name: str
        status: str  # observed | unobservable | ambiguous
        start_ts: str | None = None
        end_ts: str | None = None
        frame_indices_representative: list[int] = Field(default_factory=list)
        visual_summary: str
        audio_summary: str | None = None
        ambiguity_notes: str | None = None


    class SegmentationReport(BaseModel):
        device_type: str
        total_duration_sec: float
        video_segments: list[VideoSegment]


else:
    # No-op classes when pydantic unavailable (keeps imports working)
    class StepEvaluation: pass
    class CriticalErrorDetection: pass
    class EvaluationSummary: pass
    class VLMClinicalReport: pass
    class DeviceIdReport: pass
    class VideoSegment: pass
    class SegmentationReport: pass


# Module-level helper to check capability

def can_enforce_schema() -> bool:
    """Return True if pydantic is available for schema enforcement."""
    return PYDANTIC_AVAILABLE
