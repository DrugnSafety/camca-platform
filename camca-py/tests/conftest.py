"""Shared fixtures — synthetic telemetry builder (no mediapipe required)."""
import pytest


BASELINE_SAMPLE = {
    "audio_energy_db": 36.0,
    "lip_distance_px": 20.0,
    "head_pitch_deg": 0.0,
    "index_finger_acceleration": 0.0,
    "wrist_zero_crossing_rate": 0,
    "chest_expansion_ratio": 1.0,
    "hand_mouth_distance_px": 300.0,
}


def make_telemetry(duration_ms: int, overrides: list[tuple[int, int, dict]] = ()) -> list[dict]:
    """Build a 10Hz synthetic telemetry stream.

    Args:
        duration_ms: total length
        overrides: list of (t_start_ms, t_end_ms, {field: value}) applied to
                   samples whose timestamp falls in [t_start_ms, t_end_ms).
    """
    samples = []
    for ts in range(0, duration_ms, 100):
        s = {"timestamp_ms": ts, **BASELINE_SAMPLE}
        for t0, t1, fields in overrides:
            if t0 <= ts < t1:
                s.update(fields)
        samples.append(s)
    return samples


@pytest.fixture
def telemetry_builder():
    return make_telemetry


@pytest.fixture
def full_technique_telemetry():
    """정석적인 pMDI 시연 20초: 흔들기→손이 입으로→입술 밀폐→흡입+actuation→숨참기→제거."""
    return make_telemetry(20_000, [
        (500, 2500, {"wrist_zero_crossing_rate": 4}),                       # E1 shake
        (3000, 4500, {"hand_mouth_distance_px": 150.0}),                    # E2 접근 중
        (4500, 15_000, {"hand_mouth_distance_px": 40.0}),                   # 입 근처 유지
        (5000, 12_000, {"lip_distance_px": 3.0}),                           # E3 lip seal
        (6000, 9000, {"audio_energy_db": 62.0,                              # E4 흡입음
                      "chest_expansion_ratio": 1.15}),
        (6000, 6200, {"index_finger_acceleration": 150.0}),                 # E5 actuation
        (9000, 15_000, {"audio_energy_db": 36.0,                            # E6 숨참기(무음+정지)
                        "chest_expansion_ratio": 1.14}),
        (15_000, 20_000, {"hand_mouth_distance_px": 280.0}),                # E7 제거
    ])
