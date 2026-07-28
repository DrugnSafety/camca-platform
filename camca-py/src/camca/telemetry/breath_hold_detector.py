"""Audio-based breath-hold detection — implements the Gemini-CDSS key insight.

Reference clinical principle:
    "Chest expansion plateaus during the late inhalation phase. To accurately
    detect the transition from 'Inhalation' to 'Breath Hold', you MUST look at
    audio_energy_db. The exact moment audio_energy_db drops abruptly back to
    baseline marks the true acoustic cessation of inhalation."

This module turns that principle into a deterministic detector usable by
either the VLM evaluators (as a clinical anchor) or the scoring engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .thresholds import (
    AUDIO_BASELINE_DB,
    AUDIO_BREATH_HOLD_THRESHOLD_DB,
    AUDIO_DB_DROP_FOR_HOLD,
    AUDIO_INHALATION_MIN_DB,
    BREATH_HOLD_MIN_DURATION_MS,
    BREATH_HOLD_ADEQUATE_DURATION_MS,
)


@dataclass
class BreathHoldEvent:
    """Detected breath-hold event."""
    onset_ms: int
    offset_ms: int | None
    duration_ms: int
    peak_db_before: float
    min_db_during: float
    drop_db: float
    is_adequate: bool          # ≥10 sec
    is_attempted: bool         # ≥3 sec
    confidence: float          # 0.0-1.0

    def to_dict(self) -> dict:
        return {
            "onset_ms": self.onset_ms,
            "offset_ms": self.offset_ms,
            "duration_ms": self.duration_ms,
            "peak_db_before": round(self.peak_db_before, 1),
            "min_db_during": round(self.min_db_during, 1),
            "drop_db": round(self.drop_db, 1),
            "is_adequate": self.is_adequate,
            "is_attempted": self.is_attempted,
            "confidence": round(self.confidence, 2),
        }


def detect_breath_hold(
    telemetry: list[dict],
    min_drop_db: float = AUDIO_DB_DROP_FOR_HOLD,
    silence_threshold_db: float = AUDIO_BREATH_HOLD_THRESHOLD_DB,
    min_hold_duration_ms: int = BREATH_HOLD_MIN_DURATION_MS,
    min_peak_db_for_detection: float = 55.0,
) -> BreathHoldEvent | None:
    """Detect the main breath-hold event from a telemetry stream.

    Algorithm:
      1. Find audio peak (inhalation peak).
      2. **v0.2.1 fix**: if peak is below min_peak_db_for_detection, no real inhalation
         was detected → return None (avoid false-positive on quiet AIM-simulator audio).
      3. After peak, find the first sustained drop to silence_threshold_db.
      4. Track how long the silence persists.

    Args:
        telemetry: Output of extract_telemetry()
        min_drop_db: Minimum dB drop from peak to register as transition
        silence_threshold_db: dB level below which is considered silence
        min_hold_duration_ms: Minimum duration to count as a breath-hold event
        min_peak_db_for_detection: Inhalation peak must exceed this; below = no real inhalation detected
                                   (use camca.telemetry.thresholds.get_audio_profile to tune per device)

    Returns:
        BreathHoldEvent or None if no breath-hold detected
    """
    if not telemetry:
        return None

    # Find peak before searching for drop
    peak_idx = max(range(len(telemetry)), key=lambda i: telemetry[i]["audio_energy_db"])
    peak_db = telemetry[peak_idx]["audio_energy_db"]
    peak_ts = telemetry[peak_idx]["timestamp_ms"]

    # v0.2.1 guard: prevent false-positive on quiet sources (e.g., AIM simulator)
    if peak_db < min_peak_db_for_detection:
        return None

    # Find first sustained drop after peak
    onset_ts = None
    min_db = peak_db
    for i in range(peak_idx + 1, len(telemetry)):
        s = telemetry[i]
        if s["audio_energy_db"] <= silence_threshold_db:
            # Check sustained (need to stay low for at least 1 sec / 10 samples at 100ms)
            sustain_count = 0
            for j in range(i, min(len(telemetry), i + 10)):
                if telemetry[j]["audio_energy_db"] <= silence_threshold_db + 5:
                    sustain_count += 1
                else:
                    break
            if sustain_count >= 5:  # 500ms sustained
                onset_ts = s["timestamp_ms"]
                break

    if onset_ts is None:
        return None

    # Find offset (when audio rises back above threshold)
    offset_ts = None
    onset_idx = next(i for i, s in enumerate(telemetry) if s["timestamp_ms"] == onset_ts)
    for i in range(onset_idx + 1, len(telemetry)):
        s = telemetry[i]
        if s["audio_energy_db"] > AUDIO_INHALATION_MIN_DB:
            offset_ts = s["timestamp_ms"]
            break
        min_db = min(min_db, s["audio_energy_db"])

    # Use last frame timestamp if hold continues to end of video
    final_offset_ts = offset_ts or telemetry[-1]["timestamp_ms"]
    duration = final_offset_ts - onset_ts
    drop = peak_db - min_db

    # Confidence calculation
    confidence = 0.0
    if drop >= min_drop_db:
        confidence += 0.5
    if duration >= min_hold_duration_ms:
        confidence += 0.3
    if peak_db >= AUDIO_INHALATION_MIN_DB:
        confidence += 0.2
    confidence = min(confidence, 1.0)

    return BreathHoldEvent(
        onset_ms=onset_ts,
        offset_ms=offset_ts,
        duration_ms=duration,
        peak_db_before=peak_db,
        min_db_during=min_db,
        drop_db=drop,
        is_adequate=duration >= BREATH_HOLD_ADEQUATE_DURATION_MS,
        is_attempted=duration >= min_hold_duration_ms,
        confidence=confidence,
    )


def detect_inhalation_onset(
    telemetry: list[dict],
    onset_threshold_db: float = AUDIO_INHALATION_MIN_DB,
) -> int | None:
    """Detect the first inhalation onset (audio rises above threshold).

    Returns the timestamp_ms of onset, or None if no inhalation detected.
    """
    for s in telemetry:
        if s["audio_energy_db"] >= onset_threshold_db:
            return s["timestamp_ms"]
    return None


def compute_telemetry_summary(telemetry: list[dict]) -> dict:
    """Aggregate telemetry into clinically interpretable summary metrics.

    This summary is what we inject into VLM prompts — it provides deterministic
    measurements as anchors for VLM reasoning.
    """
    if not telemetry:
        return {"empty": True}

    audio_dbs = [s["audio_energy_db"] for s in telemetry]
    chest = [s["chest_expansion_ratio"] for s in telemetry]
    lip = [s["lip_distance_px"] for s in telemetry]
    pitch = [s["head_pitch_deg"] for s in telemetry]
    accel = [s["index_finger_acceleration"] for s in telemetry]
    zcr = [s["wrist_zero_crossing_rate"] for s in telemetry]

    bh = detect_breath_hold(telemetry)
    inhalation_onset = detect_inhalation_onset(telemetry)

    # Find actuation moments (acceleration spikes)
    actuation_events = []
    for i, s in enumerate(telemetry):
        if abs(s["index_finger_acceleration"]) >= 8.0:
            actuation_events.append(s["timestamp_ms"])

    # v0.3.0: also include view_angle classification (L6 fix)
    try:
        from .view_angle import classify_view_angle
        view_classification = classify_view_angle(telemetry)
        view_info = {
            "primary_view": view_classification.primary_view,
            "confidence": view_classification.confidence,
            "face_detection_rate": view_classification.face_detection_rate,
            "recommendation": view_classification.recommendation,
        }
    except Exception:
        view_info = None

    return {
        "duration_ms": telemetry[-1]["timestamp_ms"] - telemetry[0]["timestamp_ms"],
        "sample_count": len(telemetry),
        "view_angle": view_info,
        "audio": {
            "peak_db": max(audio_dbs),
            "min_db": min(audio_dbs),
            "mean_db": round(sum(audio_dbs) / len(audio_dbs), 1),
            "inhalation_onset_ms": inhalation_onset,
        },
        "chest": {
            "max_ratio": max(chest),
            "baseline_ratio": min(chest),
            "expansion_pct": round((max(chest) - min(chest)) * 100, 1),
        },
        "lip_seal": {
            "min_distance_px": min(lip) if lip else None,
            "max_distance_px": max(lip) if lip else None,
            "seal_present": (min(lip) < 5.0) if lip else False,
        },
        "head_pitch": {
            "max_deg": max(pitch),
            "min_deg": min(pitch),
            "mean_deg": round(sum(pitch) / len(pitch), 1) if pitch else 0,
        },
        "actuation": {
            "detected_count": len(actuation_events),
            "first_event_ms": actuation_events[0] if actuation_events else None,
            "all_events_ms": actuation_events,
        },
        "shaking": {
            "max_zcr_per_window": max(zcr) if zcr else 0,
            "total_zero_crossings": sum(zcr),
            "shake_attempted": sum(zcr) >= 5,
        },
        "breath_hold": bh.to_dict() if bh else None,
        "clinical_anchors": {
            "S5_coordination_check": {
                "actuation_ms": actuation_events[0] if actuation_events else None,
                "inhalation_onset_ms": inhalation_onset,
                "gap_ms": (
                    (inhalation_onset - actuation_events[0])
                    if (actuation_events and inhalation_onset is not None)
                    else None
                ),
                "interpretation": _interpret_coordination(
                    actuation_events[0] if actuation_events else None,
                    inhalation_onset,
                ),
            },
            "S7_breath_hold_check": {
                "detected": bh is not None,
                "duration_ms": bh.duration_ms if bh else 0,
                "is_adequate_per_GINA": bh.is_adequate if bh else False,
                "interpretation": (
                    f"Breath-hold {bh.duration_ms/1000:.1f}s "
                    f"({'adequate' if bh.is_adequate else 'attempted' if bh.is_attempted else 'inadequate'})"
                    if bh else "No breath-hold detected"
                ),
            },
        },
    }


def _interpret_coordination(actuation_ms: int | None, inhalation_ms: int | None) -> str:
    """Clinical interpretation of S5 coordination from timing alone."""
    if actuation_ms is None or inhalation_ms is None:
        return "Cannot determine — actuation or inhalation onset missing from telemetry"
    gap = inhalation_ms - actuation_ms
    if -300 <= gap <= 300:
        return "OPTIMAL — actuation and inhalation within 300ms (ideal coordination)"
    elif gap > 300:
        return f"EARLY actuation — pressed canister {gap}ms BEFORE inhaling (CRIT-pMDI-04 risk)"
    elif gap < -1000:
        return f"LATE actuation — pressed canister {abs(gap)}ms AFTER inhalation began (CRIT-pMDI-05 risk)"
    else:
        return f"BORDERLINE — gap of {gap}ms; clinical impact likely minor"
