"""Quantitative telemetry extraction for CAMCA pipeline.

This module performs Layer-0 analysis: it extracts ground-truth physical
measurements from inhaler-use videos BEFORE the VLM evaluators see them.
The telemetry stream is then fed to the VLM along with the raw frames,
turning the VLM from a "guesser" into an "interpreter of measurements".

Six core metrics (0.1s sampling, per Gemini-CDSS-style design):
  - audio_energy_db          → breath-hold onset detection (dB drop)
  - lip_distance_px          → mouth seal
  - head_pitch_deg           → airway position
  - index_finger_acceleration → exact actuation moment
  - wrist_zero_crossing_rate → true shaking vs translation
  - chest_expansion_ratio    → inhalation depth + breath-hold proxy

All extractors are optional dependencies:
    pip install camca[telemetry]
installs mediapipe + librosa.

Usage:
    from camca.telemetry import extract_telemetry

    stream = extract_telemetry("patient.mp4", sample_interval_ms=100)
    # → list of dict with all 6 metrics per 0.1s

    from camca.telemetry import detect_breath_hold
    onset_ms, offset_ms = detect_breath_hold(stream)
"""
from __future__ import annotations

from .pipeline import extract_telemetry, TelemetrySample, TELEMETRY_KEYS, compact_telemetry_for_prompt
from .breath_hold_detector import (
    detect_breath_hold,
    detect_inhalation_onset,
    compute_telemetry_summary,
    BreathHoldEvent,
)
from .reconciliation import (
    reconcile_step_score,
    ReconciliationOutcome,
    ReconciliationResult,
    breath_hold_to_level,
    lip_seal_to_level,
    chest_expansion_to_level,
    coordination_to_level,
)
from .thresholds import (
    get_audio_profile,
    DEVICE_AUDIO_PROFILES,
)
from .view_angle import (
    classify_view_angle,
    adjust_telemetry_confidence_for_angle,
    ViewAngleClassification,
)

__all__ = [
    "extract_telemetry",
    "compact_telemetry_for_prompt",
    "TelemetrySample",
    "TELEMETRY_KEYS",
    "detect_breath_hold",
    "detect_inhalation_onset",
    "compute_telemetry_summary",
    "BreathHoldEvent",
    # v0.2.1: reconciliation
    "reconcile_step_score",
    "ReconciliationOutcome",
    "ReconciliationResult",
    "breath_hold_to_level",
    "lip_seal_to_level",
    "chest_expansion_to_level",
    "coordination_to_level",
    # v0.2.1: device profiles
    "get_audio_profile",
    "DEVICE_AUDIO_PROFILES",
    # v0.3.0: view angle classification (L6)
    "classify_view_angle",
    "adjust_telemetry_confidence_for_angle",
    "ViewAngleClassification",
]
