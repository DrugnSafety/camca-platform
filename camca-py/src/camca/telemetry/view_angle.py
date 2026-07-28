"""View angle classification (v0.3.0 — L6 fix).

Classifies camera angle from MediaPipe FaceMesh + Pose landmarks to:
  - "frontal":      head facing camera (±15° yaw)
  - "oblique":      30-60° rotation
  - "lateral":      side view (>60° rotation)
  - "back_or_unknown": cannot detect face

Downstream effects:
  - Lateral views → reduce telemetry confidence + favor VLM evaluation
  - Frontal views → telemetry can be primary anchor
  - device-id agent can warn user if angle is suboptimal for evaluation
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass
class ViewAngleClassification:
    primary_view: str             # frontal | oblique | lateral | back_or_unknown
    confidence: float             # 0.0-1.0
    yaw_estimate_deg: float | None
    face_detection_rate: float    # fraction of frames where face was detected
    recommendation: str           # what to do based on this angle


def estimate_yaw_from_face_landmarks(face_landmark_obj) -> float | None:
    """Estimate face yaw (left-right rotation) in degrees from MediaPipe FaceMesh.

    Uses left eye outer corner (33) vs right eye outer corner (263) horizontal symmetry.
    """
    try:
        lm = face_landmark_obj.landmark
        left_eye = lm[33]
        right_eye = lm[263]
        nose = lm[1]
        # Distance from nose to each eye (in image x-coords)
        left_dist = abs(nose.x - left_eye.x)
        right_dist = abs(nose.x - right_eye.x)
        if left_dist + right_dist == 0:
            return None
        # If symmetric (1.0 ratio): 0° yaw (frontal); if one side dominates: high yaw
        asymmetry = (right_dist - left_dist) / (right_dist + left_dist)
        # Empirical mapping: |asymmetry| < 0.15 → ±15°, 0.5 → 60°
        yaw_deg = asymmetry * 120.0  # rough linear scaling
        return float(round(yaw_deg, 1))
    except Exception:
        return None


def classify_view_angle(telemetry_stream: list[dict],
                         face_detection_rate_threshold: float = 0.5) -> ViewAngleClassification:
    """Classify camera view angle from telemetry stream.

    Args:
        telemetry_stream: List of telemetry samples (each with face/pose data implied)
        face_detection_rate_threshold: Below this rate of face detection = back/unknown

    Returns:
        ViewAngleClassification with view, confidence, recommendation.

    Heuristics:
      - face_detection_rate < 0.5  → back_or_unknown
      - face_detection_rate ≥ 0.9 AND lip_distance variance low → frontal
      - face_detection_rate ≥ 0.5 AND face data noisy/missing intermittent → oblique
      - face_detection_rate moderate AND lip_distance often 0 → lateral
    """
    if not telemetry_stream:
        return ViewAngleClassification(
            primary_view="back_or_unknown",
            confidence=0.0,
            yaw_estimate_deg=None,
            face_detection_rate=0.0,
            recommendation="No telemetry samples — cannot classify",
        )

    # Use lip_distance_px > 0 as proxy for "face detected"
    face_detected = sum(1 for s in telemetry_stream if s.get("lip_distance_px", 0) > 0)
    detection_rate = face_detected / len(telemetry_stream)

    # Use lip_distance variance + non-zero rate to differentiate frontal vs lateral
    lip_distances = [s.get("lip_distance_px", 0) for s in telemetry_stream
                     if s.get("lip_distance_px", 0) > 0]
    lip_mean = sum(lip_distances) / len(lip_distances) if lip_distances else 0

    if detection_rate < face_detection_rate_threshold:
        return ViewAngleClassification(
            primary_view="back_or_unknown",
            confidence=0.7,
            yaw_estimate_deg=None,
            face_detection_rate=round(detection_rate, 2),
            recommendation=(
                f"Face detected in only {detection_rate:.0%} of frames. Camera likely showing "
                f"side or back view. Recommend re-recording with frontal angle for reliable "
                f"telemetry. VLM-only evaluation suggested (reduced confidence)."
            ),
        )

    if detection_rate >= 0.9 and lip_mean > 0:
        return ViewAngleClassification(
            primary_view="frontal",
            confidence=0.9,
            yaw_estimate_deg=0.0,  # approximate; refine with eye-distance asymmetry if available
            face_detection_rate=round(detection_rate, 2),
            recommendation=(
                "Frontal view with consistent face detection. Telemetry can serve as primary "
                "evaluation anchor. Ideal acquisition geometry."
            ),
        )

    if detection_rate >= 0.7:
        return ViewAngleClassification(
            primary_view="oblique",
            confidence=0.75,
            yaw_estimate_deg=30.0,
            face_detection_rate=round(detection_rate, 2),
            recommendation=(
                "Oblique view — face detected most of the time but intermittent. "
                "Telemetry can be used but VLM should also evaluate."
            ),
        )

    return ViewAngleClassification(
        primary_view="lateral",
        confidence=0.7,
        yaw_estimate_deg=60.0,
        face_detection_rate=round(detection_rate, 2),
        recommendation=(
            f"Lateral view — face detected in {detection_rate:.0%} of frames only. "
            f"Some telemetry (lip seal, head pitch) unreliable. VLM evaluation preferred."
        ),
    )


def adjust_telemetry_confidence_for_angle(
    base_confidence: float,
    view_angle: str,
) -> float:
    """Adjust telemetry confidence based on view angle.

    Returns a multiplier-adjusted confidence.
    """
    multipliers = {
        "frontal": 1.0,           # No reduction
        "oblique": 0.85,          # 15% reduction
        "lateral": 0.50,          # 50% reduction (vision unreliable)
        "back_or_unknown": 0.20,  # 80% reduction
    }
    multiplier = multipliers.get(view_angle, 0.5)
    return round(min(1.0, base_confidence * multiplier), 2)
