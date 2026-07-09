"""대시보드 목록/배지 + 타임라인 경계 수정 → segments_corrected + diff."""
import pytest

from camca_web.auth import hash_password
from camca_web.db import (AuditLog, Case, Participant, Segmentation,
                          SegmentsCorrected)


@pytest.fixture
def staff(client):
    client.app.state.staff_accounts = {"staff": hash_password("pw")}
    return client.post("/login", data={"username": "staff", "password": "pw"},
                       follow_redirects=False).cookies


@pytest.fixture
def seeded(client):
    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-D", dob="1980-01-01")
        s.add(p); s.flush()
        s.add(Case(id="case-ok", participant_id=p.id, video_path="v.mp4",
                   device_type="pMDI", source="clinic", status="REPORT_ISSUED"))
        s.add(Case(id="case-warn", participant_id=p.id, video_path="v.mp4",
                   device_type="pMDI", source="clinic", status="REPORT_ISSUED",
                   needs_attention=True, attention_reasons=["critical_error"]))
        s.add(Segmentation(case_id="case-warn", engine="telemetry-anchored-v1",
                           events=[],
                           segments=[{"step_id": "S5", "observable": True,
                                      "t_start_ms": 6000, "t_end_ms": 9000}]))
        s.commit()


def test_dashboard_requires_login(client, seeded):
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code in (302, 303)


def test_dashboard_lists_cases_with_badge(client, staff, seeded):
    r = client.get("/dashboard", cookies=staff)
    assert r.status_code == 200
    assert "case-ok" in r.text and "case-warn" in r.text
    assert "NEEDS_ATTENTION" in r.text


def test_case_detail_renders_timeline(client, staff, seeded):
    r = client.get("/cases/case-warn", cookies=staff)
    assert r.status_code == 200
    assert "S5" in r.text
    assert "timeline" in r.text        # 타임라인 컨테이너 존재


def test_segment_correction_saved_with_diff(client, staff, seeded):
    r = client.post("/cases/case-warn/segments", cookies=staff, json={
        "segments": [{"step_id": "S5", "observable": True,
                      "t_start_ms": 6200, "t_end_ms": 9000}],
    })
    assert r.status_code == 200
    with client.app.state.session_factory() as s:
        row = s.query(SegmentsCorrected).one()
        assert row.case_id == "case-warn"
        assert row.diff == [{"step_id": "S5", "field": "t_start_ms",
                             "before": 6000, "after": 6200}]
        events = [a.event for a in s.query(AuditLog).all()]
        assert "segments_corrected" in events
