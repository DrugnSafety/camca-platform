"""spec §4 상태 머신 + NEEDS_ATTENTION 4조건 (순수 함수)."""
from camca_web.state import (
    UPLOADED, QUALITY_CHECK, RETAKE_REQUESTED, ANALYZING, SCORED,
    REPORT_ISSUED, FAILED, can_transition, needs_attention_reasons,
)

OK_SCORE = {"critical_error_override": {"critical_errors": []}}
OK_KAPPA = {"kappa": {"linear_weighted": 0.8}}
OK_SEGS = [{"step_id": f"S{i}", "observable": i in (1, 4, 5, 6, 7)} for i in range(1, 10)]


def test_happy_path_transitions():
    for a, b in [(UPLOADED, QUALITY_CHECK), (QUALITY_CHECK, ANALYZING),
                 (ANALYZING, SCORED), (SCORED, REPORT_ISSUED)]:
        assert can_transition(a, b)


def test_branch_transitions():
    assert can_transition(QUALITY_CHECK, RETAKE_REQUESTED)
    assert can_transition(ANALYZING, FAILED)
    assert can_transition(FAILED, ANALYZING)          # 원클릭 재실행
    assert not can_transition(UPLOADED, SCORED)       # 단계 건너뛰기 금지
    assert not can_transition(REPORT_ISSUED, UPLOADED)


def test_no_attention_when_all_ok():
    assert needs_attention_reasons(OK_SCORE, OK_KAPPA, OK_SEGS) == []


def test_attention_critical_error():
    score = {"critical_error_override": {"critical_errors": ["no_breath_hold"]}}
    assert "critical_error" in needs_attention_reasons(score, OK_KAPPA, OK_SEGS)


def test_attention_conflict_flag():
    segs = OK_SEGS[:4] + [dict(OK_SEGS[4], conflict_flagged=True)] + OK_SEGS[5:]
    assert "conflict_flagged" in needs_attention_reasons(OK_SCORE, OK_KAPPA, segs)


def test_attention_partial_data():
    segs = [{"step_id": f"S{i}", "observable": i == 5} for i in range(1, 10)]  # 8/9 미관측
    assert "partial_data" in needs_attention_reasons(OK_SCORE, OK_KAPPA, segs)


def test_attention_low_kappa():
    kappa = {"kappa": {"linear_weighted": 0.45}}
    assert "low_kappa" in needs_attention_reasons(OK_SCORE, kappa, OK_SEGS)
