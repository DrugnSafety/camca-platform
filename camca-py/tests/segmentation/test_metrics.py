"""Spec §5.4 검증 게이트 지표 — human 라벨 대비 mean absolute boundary error."""
from camca.segmentation.metrics import mean_absolute_boundary_error_sec, overlap_violations


def test_boundary_error_perfect_match():
    pred = [{"step_id": "S1", "observable": True, "t_start_ms": 500, "t_end_ms": 2400}]
    gold = [{"step_id": "S1", "observable": True, "t_start_ms": 500, "t_end_ms": 2400}]
    assert mean_absolute_boundary_error_sec(pred, gold) == 0.0


def test_boundary_error_averages_start_and_end():
    pred = [{"step_id": "S1", "observable": True, "t_start_ms": 1000, "t_end_ms": 3000}]
    gold = [{"step_id": "S1", "observable": True, "t_start_ms": 500, "t_end_ms": 2400}]
    # |1000-500| + |3000-2400| = 1100ms / 2경계 = 550ms = 0.55s
    assert abs(mean_absolute_boundary_error_sec(pred, gold) - 0.55) < 1e-9


def test_boundary_error_skips_unobservable():
    pred = [{"step_id": "S2", "observable": False, "t_start_ms": None, "t_end_ms": None}]
    gold = [{"step_id": "S2", "observable": False, "t_start_ms": None, "t_end_ms": None}]
    assert mean_absolute_boundary_error_sec(pred, gold) is None  # 비교 대상 없음


def test_overlap_violations_counts():
    segs = [
        {"step_id": "S4", "observable": True, "t_start_ms": 0, "t_end_ms": 1500},
        {"step_id": "S5", "observable": True, "t_start_ms": 500, "t_end_ms": 3000},
    ]
    assert overlap_violations(segs) == 1
