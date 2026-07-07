"""Stage 1 이벤트 검출기 테스트 — 전부 합성 telemetry, mediapipe 불필요."""
from tests.conftest import make_telemetry
from camca.segmentation.events import PhaseEvent
from camca.segmentation.events import (
    detect_shake, detect_hand_to_mouth, detect_lip_seal,
    detect_inhalation_onset_event, detect_actuation,
    detect_breath_hold_event, detect_events,
)


def test_phase_event_to_dict():
    e = PhaseEvent(type="shake", t_start_ms=500, t_end_ms=2400,
                   confidence=0.9, source="telemetry", detail={"max_zcr": 4})
    d = e.to_dict()
    assert d["type"] == "shake"
    assert d["t_start_ms"] == 500
    assert d["source"] == "telemetry"


def test_detect_shake_finds_sustained_zcr():
    t = make_telemetry(5000, [(500, 2500, {"wrist_zero_crossing_rate": 4})])
    events = detect_shake(t)
    assert len(events) == 1
    assert events[0].type == "shake"
    assert events[0].t_start_ms == 500
    assert 2300 <= events[0].t_end_ms <= 2500


def test_detect_shake_ignores_single_spike():
    t = make_telemetry(5000, [(500, 700, {"wrist_zero_crossing_rate": 4})])  # 200ms < 500ms
    assert detect_shake(t) == []


def test_detect_hand_to_mouth_approach_and_removal():
    t = make_telemetry(20_000, [
        (4500, 15_000, {"hand_mouth_distance_px": 40.0}),
        (15_000, 20_000, {"hand_mouth_distance_px": 280.0}),
    ])
    events = detect_hand_to_mouth(t)
    types = [e.type for e in events]
    assert "hand_to_mouth" in types
    assert "mouth_removal" in types
    approach = next(e for e in events if e.type == "hand_to_mouth")
    removal = next(e for e in events if e.type == "mouth_removal")
    assert approach.t_start_ms == 4500
    assert removal.t_start_ms == 15_000


def test_detect_hand_to_mouth_ignores_zero_unknown():
    """0.0은 미검출(unknown)이므로 '가까움'으로 판정하면 안 된다."""
    t = make_telemetry(5000, [(0, 5000, {"hand_mouth_distance_px": 0.0})])
    assert detect_hand_to_mouth(t) == []


def test_detect_lip_seal():
    t = make_telemetry(15_000, [(5000, 12_000, {"lip_distance_px": 3.0})])
    events = detect_lip_seal(t)
    assert len(events) == 1
    assert events[0].type == "lip_seal"
    assert events[0].t_start_ms == 5000


def test_inhalation_onset_from_audio():
    t = make_telemetry(15_000, [(6000, 9000, {"audio_energy_db": 62.0})])
    events = detect_inhalation_onset_event(t, device_type="pMDI")
    assert len(events) == 1
    assert events[0].t_start_ms == 6000
    assert events[0].detail["signal"] == "audio"


def test_inhalation_onset_chest_fallback_when_audio_quiet():
    """L8 완화: AIM 시뮬레이터처럼 audio가 조용하면 chest expansion으로 fallback."""
    t = make_telemetry(15_000, [(6000, 9000, {"chest_expansion_ratio": 1.15})])
    events = detect_inhalation_onset_event(t, device_type="pMDI-AIM-simulator")
    assert len(events) == 1
    assert events[0].detail["signal"] == "chest"
    assert events[0].confidence < 0.8  # fallback은 confidence 낮게


def test_detect_actuation_spike():
    t = make_telemetry(10_000, [(6000, 6200, {"index_finger_acceleration": 150.0})])
    events = detect_actuation(t)
    assert len(events) == 1
    assert events[0].type == "actuation"
    assert events[0].t_start_ms == 6000


def test_detect_actuation_below_threshold_ignored():
    t = make_telemetry(10_000, [(6000, 6200, {"index_finger_acceleration": 50.0})])
    assert detect_actuation(t) == []


def test_detect_breath_hold_stillness_fallback():
    """audio peak가 없어도 (chest plateau + 무음) 정지 구간을 breath_hold로 검출."""
    t = make_telemetry(20_000, [
        (6000, 9000, {"audio_energy_db": 43.0, "chest_expansion_ratio": 1.12}),   # AIM 수준 흡입 (< 45dB min_peak)
        (9000, 15_000, {"chest_expansion_ratio": 1.11}),                         # 정지+무음
    ])
    events = detect_breath_hold_event(t, device_type="pMDI-AIM-simulator")
    assert len(events) == 1
    assert events[0].type == "breath_hold"
    assert 8500 <= events[0].t_start_ms <= 9500


def test_breath_hold_not_fabricated_without_inhalation():
    """흡입 이벤트가 전혀 없으면 정지 구간이 있어도 breath_hold를 만들지 않는다 (임상적 불가능)."""
    t = make_telemetry(12_000, [
        # chest 1.09: stillness 하한(1.08) 이상이지만 흡입 onset 기준(1.10) 미달, 오디오 조용
        (0, 12_000, {"chest_expansion_ratio": 1.09}),
    ])
    assert detect_breath_hold_event(t, device_type="pMDI-AIM-simulator") == []


def test_detect_events_full_technique(full_technique_telemetry):
    events = detect_events(full_technique_telemetry, device_type="pMDI")
    types = {e.type for e in events}
    assert {"shake", "hand_to_mouth", "lip_seal", "inhalation_onset",
            "actuation", "breath_hold", "mouth_removal"} <= types
    # 시간순 정렬 보장
    starts = [e.t_start_ms for e in events]
    assert starts == sorted(starts)
