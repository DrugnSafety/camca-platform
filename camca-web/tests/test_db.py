"""spec §3 데이터 모델 — 테이블 생성과 관계, audit 기록."""
import pytest
from camca_web.db import (
    make_engine, make_session_factory, init_db, write_audit,
    Participant, Case, Segmentation, SegmentsCorrected, Evaluation, Score, Report, Job, AuditLog,
)


@pytest.fixture
def session():
    engine = make_engine("sqlite://")
    init_db(engine)
    return make_session_factory(engine)()


def test_participant_case_relationship(session):
    p = Participant(research_code="RC-001", dob="1980-01-01")
    session.add(p)
    session.flush()
    c = Case(participant_id=p.id, video_path="v.mp4", device_type="pMDI",
             source="clinic", status="UPLOADED")
    session.add(c)
    session.commit()
    assert c.id is not None
    assert session.get(Participant, p.id).cases[0].id == c.id


def test_case_children(session):
    p = Participant(research_code="RC-002", dob="1990-02-02")
    session.add(p); session.flush()
    c = Case(participant_id=p.id, video_path="v.mp4", device_type="pMDI",
             source="clinic", status="SCORED")
    session.add(c); session.flush()
    session.add_all([
        Segmentation(case_id=c.id, segments=[{"step_id": "S1"}], events=[], engine="telemetry-anchored-v1"),
        Evaluation(case_id=c.id, evaluator="A", raw={"per_step": []}),
        Score(case_id=c.id, final_score={"final_verdict": "PASS"}, kappa={"linear_weighted": 0.8}, verdict="PASS"),
        Report(case_id=c.id, kind="patient_ko", pdf_path="r.pdf", revision=1),
        Job(case_id=c.id, status="pending"),
    ])
    session.commit()
    assert session.query(Segmentation).filter_by(case_id=c.id).count() == 1
    # Assert JSON round-trip: re-query and check segments value
    seg_row = session.query(Segmentation).filter_by(case_id=c.id).one()
    assert seg_row.segments == [{"step_id": "S1"}]


def test_segments_corrected(session):
    """Test SegmentsCorrected model with JSON field round-trip integrity."""
    p = Participant(research_code="RC-004", dob="1975-03-15")
    session.add(p); session.flush()
    c = Case(participant_id=p.id, video_path="v.mp4", device_type="pMDI",
             source="clinic", status="SCORED")
    session.add(c); session.flush()

    # Create a SegmentsCorrected record with complex JSON fields
    segments_data = [{"step_id": "S1", "duration_ms": 1000}, {"step_id": "S2", "duration_ms": 1200}]
    diff_data = [
        {"step_id": "S1", "field": "duration_ms", "before": 950, "after": 1000},
        {"step_id": "S5", "field": "t_start_ms", "before": 6000, "after": 6200}
    ]

    sc = SegmentsCorrected(
        case_id=c.id,
        corrected_by="clinician_A",
        segments=segments_data,
        diff=diff_data
    )
    session.add(sc)
    session.commit()

    # Re-query and verify JSON round-trip
    queried_sc = session.query(SegmentsCorrected).filter_by(case_id=c.id).one()
    assert queried_sc.case_id == c.id
    assert queried_sc.corrected_by == "clinician_A"
    assert queried_sc.segments == segments_data
    assert queried_sc.diff == diff_data
    # Verify specific diff entry
    assert {"step_id": "S5", "field": "t_start_ms", "before": 6000, "after": 6200} in queried_sc.diff


def test_write_audit(session):
    # Create a Participant and Case to use for case_id
    p = Participant(research_code="RC-003", dob="1985-05-05")
    session.add(p); session.flush()
    c = Case(participant_id=p.id, video_path="v.mp4", device_type="pMDI",
             source="clinic", status="UPLOADED")
    session.add(c); session.flush()

    write_audit(session, "cloud_upload", case_id=c.id, detail={"frames": 12})
    session.commit()
    row = session.query(AuditLog).one()
    assert row.event == "cloud_upload"
    assert row.case_id == c.id
    assert row.detail["frames"] == 12
