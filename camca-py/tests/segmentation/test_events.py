"""Stage 1 이벤트 검출기 테스트 — 전부 합성 telemetry, mediapipe 불필요."""
from tests.conftest import make_telemetry
from camca.segmentation.events import PhaseEvent


def test_phase_event_to_dict():
    e = PhaseEvent(type="shake", t_start_ms=500, t_end_ms=2400,
                   confidence=0.9, source="telemetry", detail={"max_zcr": 4})
    d = e.to_dict()
    assert d["type"] == "shake"
    assert d["t_start_ms"] == 500
    assert d["source"] == "telemetry"
