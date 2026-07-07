"""업로드 직후 사전검사 — camca-py view_angle 분류를 재사용해 L6를 촬영 시점에 차단.

정책:
  - face_detection_rate < 0.3 또는 back_or_unknown → 재촬영 (passed=False)
  - 0.3 ≤ rate < 0.8 (oblique/lateral) → 통과하되 vlm_weight_up=True (spec §5.3-2)
  - 그 외 → 통과
"""
from __future__ import annotations

from dataclasses import dataclass, field

from camca.telemetry.view_angle import classify_view_angle

FACE_RATE_FAIL_BELOW = 0.3
FACE_RATE_VLM_WEIGHT_BELOW = 0.8


@dataclass
class QualityResult:
    passed: bool
    view: str
    face_detection_rate: float
    vlm_weight_up: bool = False
    reasons: list[str] = field(default_factory=list)


def evaluate_quality(telemetry_stream: list[dict]) -> QualityResult:
    if not telemetry_stream:
        return QualityResult(passed=False, view="unknown", face_detection_rate=0.0,
                             reasons=["no_telemetry"])
    cls = classify_view_angle(telemetry_stream)
    reasons: list[str] = []
    if cls.face_detection_rate < FACE_RATE_FAIL_BELOW or \
            cls.primary_view == "back_or_unknown":
        reasons.append("face_not_detected")
        return QualityResult(passed=False, view=cls.primary_view,
                             face_detection_rate=cls.face_detection_rate,
                             reasons=reasons)
    weight_up = cls.face_detection_rate < FACE_RATE_VLM_WEIGHT_BELOW
    return QualityResult(passed=True, view=cls.primary_view,
                         face_detection_rate=cls.face_detection_rate,
                         vlm_weight_up=weight_up, reasons=reasons)
