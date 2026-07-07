"""Clinical thresholds for telemetry interpretation.

These thresholds turn raw measurements into clinical decisions. They are
calibrated to GINA 2024 + CRITIKAL recommendations and adjusted for
real-world video noise.

All thresholds are tunable — if pilot data suggests adjustment, modify
here and the entire pipeline updates consistently.
"""
from __future__ import annotations

# ---- Audio thresholds ----

AUDIO_BASELINE_DB = 35.0
"""Typical ambient room noise floor (dB). Below this = silence."""

AUDIO_INHALATION_MIN_DB = 50.0
"""Minimum audio energy considered an active inhalation sound (default for real pMDI)."""

# v0.2.1 NEW: device-specific audio profiles
DEVICE_AUDIO_PROFILES = {
    "pMDI": {
        "baseline_db": 35.0,
        "inhalation_min_db": 50.0,
        "breath_hold_threshold_db": 40.0,
        "min_peak_db_for_detection": 55.0,  # avoid false-positive detection on quiet sources
    },
    "pMDI-AIM-simulator": {
        # AIM training device produces ~5-10dB less audio than real pMDI
        # Calibrated from CAMCA-PARK-001 (peak 56.3dB) and CAMCA-KIM-001 (peak 43.9dB)
        "baseline_db": 35.0,
        "inhalation_min_db": 42.0,
        "breath_hold_threshold_db": 38.0,
        "min_peak_db_for_detection": 45.0,
    },
    "pMDI-spacer": {
        "baseline_db": 35.0,
        "inhalation_min_db": 48.0,  # spacer muffles slightly
        "breath_hold_threshold_db": 40.0,
        "min_peak_db_for_detection": 53.0,
    },
    "DPI-turbuhaler": {
        # DPI inhalation is forceful, higher audio energy expected
        "baseline_db": 35.0,
        "inhalation_min_db": 55.0,
        "breath_hold_threshold_db": 40.0,
        "min_peak_db_for_detection": 60.0,
    },
}

def get_audio_profile(device_type: str) -> dict:
    """Return device-specific audio thresholds; default to pMDI if unknown."""
    return DEVICE_AUDIO_PROFILES.get(device_type, DEVICE_AUDIO_PROFILES["pMDI"])

AUDIO_INHALATION_PEAK_DB = 70.0
"""Typical peak during active inhalation through inhaler."""

AUDIO_BREATH_HOLD_THRESHOLD_DB = AUDIO_BASELINE_DB + 5.0
"""When dB drops below this after an inhalation peak, breath-hold has started."""

AUDIO_DB_DROP_FOR_HOLD = 25.0
"""Minimum dB drop (from peak) to register as transition to breath-hold."""

# ---- Visual landmark thresholds ----

LIP_SEAL_MAX_DISTANCE_PX = 5.0
"""Lip distance below this px = adequate mouth seal around mouthpiece."""

LIP_SEAL_LOOSE_DISTANCE_PX = 15.0
"""Above this = visible air gap, poor seal."""

HEAD_PITCH_OPTIMAL_DEG = (10.0, 20.0)
"""Optimal forward pitch range during inhalation (degrees). Out of range = airway suboptimal."""

INDEX_FINGER_ACTUATION_ACCEL_THRESHOLD = 100.0
"""Y-axis acceleration spike (px/s²) suggesting canister press. Above this = actuation event.

v0.2.1 fix: raised from 8.0 → 100.0 px/s². Original threshold caused 99% false positive
rate on KIM-001 case (181/183 samples flagged). New threshold targets >5x baseline motion.
"""

INDEX_FINGER_ACTUATION_MIN_DURATION_MS = 50
"""Minimum sustained spike duration to count as actuation (filters single-frame noise)."""

INDEX_FINGER_SMOOTHING_WINDOW = 3
"""Moving average window (samples) for finger acceleration before threshold check."""

WRIST_SHAKE_ZCR_MIN = 3
"""Minimum zero-crossings per 500ms window to qualify as shaking (vs translation)."""

CHEST_EXPANSION_INHALATION_RATIO = 1.10
"""Chest width must exceed 1.10× baseline to confirm deep inhalation."""

CHEST_EXPANSION_PLATEAU_TOLERANCE = 0.02
"""Chest ratio variation ≤2% over 5+ sec → plateau = sustained breath-hold."""

# ---- Temporal thresholds ----

SAMPLE_INTERVAL_MS = 100
"""Default telemetry sampling rate. 100ms = 10 Hz."""

COORDINATION_TOLERANCE_MS = 300
"""S5 (pMDI coordination): actuation-to-inhalation onset gap > this = CRIT-pMDI-04."""

BREATH_HOLD_MIN_DURATION_MS = 3000
"""Minimum breath-hold duration to count as 'attempted' (3 sec)."""

BREATH_HOLD_ADEQUATE_DURATION_MS = 10_000
"""GINA-recommended 10 sec breath-hold."""

INHALATION_MIN_DURATION_MS = 2000
"""Minimum 2 sec of audible inhalation = Level 1+; below = Level 0."""

INHALATION_OPTIMAL_DURATION_MS = 3000
"""3-5 sec sustained inhalation = Level 3."""

# ---- Phase recognition (segmentation) thresholds — v0.4.0 ----

HAND_MOUTH_NEAR_PX = 80.0
"""검지-입 거리가 이 값 미만이면 '기기가 입 근처'로 판정."""

HAND_MOUTH_FAR_PX = 160.0
"""이 값 초과로 복귀하면 '기기 제거'로 판정 (히스테리시스 밴드)."""

EVENT_MIN_SUSTAIN_SAMPLES = 5
"""이벤트 성립 최소 지속 샘플 수 (10Hz에서 500ms) — 단발 노이즈 배제."""

STILLNESS_CHEST_STD_MAX = 0.02
"""숨참기(정지) 판정: 창 내 chest_expansion_ratio 표준편차 상한."""
