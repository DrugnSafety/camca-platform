"""MultiModelPipeline이 use_phase_engine 플래그로 신규 엔진을 쓰는지 (mock, 영상 없음)."""
from camca.pipeline import MultiModelPipeline


class DummyBackend:
    def model_id(self):
        return "dummy:v0"

    def analyze_frames(self, prompt, frames, **kwargs):
        return {}


def _make_pipeline(**kwargs):
    from camca.pipeline import PersonaConfig
    return MultiModelPipeline(
        device_id_backend=DummyBackend(),
        segmenter_backend=DummyBackend(),
        evaluator_a=PersonaConfig("A", "strict", DummyBackend()),
        evaluator_b=PersonaConfig("B", "pragmatic", DummyBackend()),
        case_dir=None,
        **kwargs,
    )


def test_flag_defaults_false_for_backward_compat():
    p = _make_pipeline()
    assert p.use_phase_engine is False


def test_flag_accepted():
    p = _make_pipeline(use_phase_engine=True)
    assert p.use_phase_engine is True


def test_stage_segment_routes_to_phase_engine_with_telemetry():
    """telemetry가 주어지면 phase engine 경로로 분기하고 engine 결과를 반환한다."""
    p = _make_pipeline(use_phase_engine=True)
    telemetry = [{
        "timestamp_ms": ts, "audio_energy_db": 36.0, "lip_distance_px": 20.0,
        "head_pitch_deg": 0.0, "index_finger_acceleration": 0.0,
        "wrist_zero_crossing_rate": 0, "chest_expansion_ratio": 1.0,
        "hand_mouth_distance_px": 300.0,
    } for ts in range(0, 5000, 100)]
    result = p._stage_segment(
        frames=[], device_type="pMDI", telemetry=telemetry, case_id="X-001",
    )
    assert result["engine"] == "telemetry-anchored-v1"
    assert result["case_id"] == "X-001"


def test_inject_telemetry_sets_stream_and_summary():
    """inject_telemetry()로 주입한 telemetry는 내부 재추출 없이 그대로 보관된다."""
    p = _make_pipeline(use_phase_engine=True)
    telemetry = [{
        "timestamp_ms": ts, "audio_energy_db": 36.0, "lip_distance_px": 20.0,
        "head_pitch_deg": 0.0, "index_finger_acceleration": 0.0,
        "wrist_zero_crossing_rate": 0, "chest_expansion_ratio": 1.0,
        "hand_mouth_distance_px": 300.0,
    } for ts in range(0, 5000, 100)]

    p.inject_telemetry(telemetry)

    assert p._telemetry_stream is telemetry
    assert p._telemetry_summary is not None
    assert p._telemetry_summary.get("empty") is not True
