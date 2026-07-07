"""hand_mouth_distance_px가 telemetry 스키마에 포함되는지 확인 (mediapipe 불필요)."""
from camca.telemetry.pipeline import TELEMETRY_KEYS, TelemetrySample


def test_hand_mouth_distance_in_keys():
    assert "hand_mouth_distance_px" in TELEMETRY_KEYS


def test_telemetry_sample_has_hand_mouth_field():
    s = TelemetrySample(
        timestamp_ms=0, audio_energy_db=36.0, lip_distance_px=20.0,
        head_pitch_deg=0.0, index_finger_acceleration=0.0,
        wrist_zero_crossing_rate=0, chest_expansion_ratio=1.0,
        hand_mouth_distance_px=300.0,
    )
    assert s.to_dict()["hand_mouth_distance_px"] == 300.0
