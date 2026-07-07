"""Stage 3 — 이벤트→겹침 없는 canonical 세그먼트 정렬."""
from camca.segmentation.events import PhaseEvent
from camca.segmentation.alignment import align_events_to_steps
from camca.segmentation.templates import PMDI_TEMPLATE


def _ev(type, t0, t1=None, conf=0.9):
    return PhaseEvent(type=type, t_start_ms=t0, t_end_ms=t1 or t0, confidence=conf)


FULL_EVENTS = [
    _ev("shake", 500, 2400),
    _ev("hand_to_mouth", 4500),
    _ev("lip_seal", 5000, 11_900),
    _ev("inhalation_onset", 6000),
    _ev("actuation", 6000, 6100),
    _ev("breath_hold", 9000, 14_900),
    _ev("mouth_removal", 15_000),
]


def test_all_canonical_steps_present():
    segs = align_events_to_steps(FULL_EVENTS, PMDI_TEMPLATE, video_duration_ms=20_000)
    assert [s["step_id"] for s in segs] == ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]


def test_no_overlapping_boundaries():
    segs = align_events_to_steps(FULL_EVENTS, PMDI_TEMPLATE, video_duration_ms=20_000)
    observed = [s for s in segs if s["observable"]]
    for a, b in zip(observed, observed[1:]):
        assert a["t_end_ms"] <= b["t_start_ms"], f"{a['step_id']} overlaps {b['step_id']}"


def test_event_anchored_steps_observable():
    segs = align_events_to_steps(FULL_EVENTS, PMDI_TEMPLATE, video_duration_ms=20_000)
    by_id = {s["step_id"]: s for s in segs}
    assert by_id["S1"]["observable"] is True          # shake
    assert by_id["S4"]["observable"] is True          # hand_to_mouth + lip_seal
    assert by_id["S5"]["observable"] is True          # inhalation + actuation
    assert by_id["S7"]["observable"] is True          # breath_hold + removal
    assert by_id["S2"]["observable"] is False         # telemetry-blind (cap)
    assert by_id["S3"]["observable"] is False         # telemetry-blind (exhale away)
    assert by_id["S2"]["needs_vlm"] is True           # Stage 2가 채울 대상


def test_boundary_source_and_confidence_recorded():
    segs = align_events_to_steps(FULL_EVENTS, PMDI_TEMPLATE, video_duration_ms=20_000)
    s5 = next(s for s in segs if s["step_id"] == "S5")
    assert s5["boundary_source"] == "telemetry"
    assert 0.0 < s5["boundary_confidence"] <= 1.0
    assert any(e["type"] == "actuation" for e in s5["events"])


def test_out_of_order_events_still_canonical_order():
    """환자가 순서를 바꿔도 (예: 흔들기를 입에 문 후에) canonical 순서로 출력."""
    events = [
        _ev("hand_to_mouth", 1000),
        _ev("shake", 3000, 4000),          # 순서 위반
        _ev("inhalation_onset", 6000),
        _ev("breath_hold", 9000, 12_000),
    ]
    segs = align_events_to_steps(events, PMDI_TEMPLATE, video_duration_ms=15_000)
    assert [s["step_id"] for s in segs] == ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]
    s1 = next(s for s in segs if s["step_id"] == "S1")
    assert s1["observable"] is True
    assert s1.get("order_violation") is True          # 위반 사실은 기록


def test_missing_events_marked_unobservable():
    segs = align_events_to_steps([], PMDI_TEMPLATE, video_duration_ms=10_000)
    assert all(s["observable"] is False for s in segs)
