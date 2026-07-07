"""DB-backed 잡 큐 — 실행/실패 기록/재시도 상한/원클릭 재실행."""
import pytest
from camca_web.db import (make_engine, make_session_factory, init_db,
                          Participant, Case, Job)
from camca_web.jobs import run_pending_once


@pytest.fixture
def sf():
    engine = make_engine("sqlite://")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        p = Participant(research_code="RC-J", dob="1980-01-01")
        s.add(p); s.flush()
        c = Case(id="case-j", participant_id=p.id, video_path="v.mp4",
                 device_type="pMDI", source="clinic", status="UPLOADED")
        s.add(c)
        s.add(Job(id="job-1", case_id="case-j", status="pending"))
        s.commit()
    return factory


def test_run_pending_calls_processor_and_marks_done(sf):
    seen = []
    n = run_pending_once(sf, processor=seen.append)
    assert n == 1
    assert seen == ["case-j"]
    with sf() as s:
        assert s.get(Job, "job-1").status == "done"


def test_processor_error_marks_failed_and_records_error(sf):
    def boom(case_id):
        raise RuntimeError("pipeline exploded")
    run_pending_once(sf, processor=boom)
    with sf() as s:
        job = s.get(Job, "job-1")
        assert job.status == "failed"
        assert "pipeline exploded" in job.error
        assert job.attempts == 1


def test_failed_job_not_retried_automatically(sf):
    def boom(case_id):
        raise RuntimeError("x")
    run_pending_once(sf, processor=boom)
    assert run_pending_once(sf, processor=boom) == 0   # failed는 자동 재시도 안 함


def test_rerun_endpoint_requeues(client, settings):
    from camca_web.auth import hash_password
    client.app.state.staff_accounts = {"staff": hash_password("pw")}
    cookies = client.post("/login", data={"username": "staff", "password": "pw"},
                          follow_redirects=False).cookies
    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-R", dob="1980-01-01")
        s.add(p); s.flush()
        s.add(Case(id="case-r", participant_id=p.id, video_path="v.mp4",
                   device_type="pMDI", source="clinic", status="FAILED"))
        s.add(Job(id="job-r", case_id="case-r", status="failed", attempts=1, error="x"))
        s.commit()
    r = client.post("/cases/case-r/rerun", cookies=cookies)
    assert r.status_code == 200
    with client.app.state.session_factory() as s:
        assert s.get(Job, "job-r").status == "pending"
        assert s.get(Case, "case-r").status == "ANALYZING"
