"""DB-backed 잡 큐 — 실행/실패 기록/재시도 상한/원클릭 재실행."""
import time

import pytest
from camca_web.db import (make_engine, make_session_factory, init_db,
                          Participant, Case, Job)
from camca_web.state import FAILED
from camca_web.jobs import run_pending_once, start_worker


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
        assert s.get(Case, "case-j").status == FAILED


def test_failed_job_not_retried_automatically(sf):
    def boom(case_id):
        raise RuntimeError("x")
    run_pending_once(sf, processor=boom)
    assert run_pending_once(sf, processor=boom) == 0   # failed는 자동 재시도 안 함


def test_claim_is_atomic_rowcount_guard(sf):
    """WHERE 절 가드 — attempts가 이미 max_attempts에 도달한 잡은 claim되지 않는다.

    (동시성 경쟁으로 잡이 이미 claim된 상황을 rowcount==0 분기로 시뮬레이션.)
    """
    with sf() as s:
        job = s.get(Job, "job-1")
        job.attempts = 3
        s.commit()
    seen = []
    n = run_pending_once(sf, processor=seen.append, max_attempts=3)
    assert n == 0
    assert seen == []
    with sf() as s:
        assert s.get(Job, "job-1").status == "pending"


def test_start_worker_processes_pending_job_and_is_daemon(sf):
    seen = []
    thread = start_worker(sf, processor=seen.append, interval_sec=0.05)
    try:
        deadline = time.monotonic() + 5.0   # 전체 스위트 부하에서도 여유 (flake 방지)
        while time.monotonic() < deadline:
            with sf() as s:
                job = s.get(Job, "job-1")
                if job.status == "done":
                    break
            time.sleep(0.02)
        with sf() as s:
            assert s.get(Job, "job-1").status == "done"
        assert seen == ["case-j"]
        assert thread.daemon is True
        assert thread.is_alive()
    finally:
        # daemon thread — 프로세스 종료 시 자동 정리. 테스트에서 명시적으로
        # join하지 않는다 (loop()가 무한 루프이므로).
        pass


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
        job = s.get(Job, "job-r")
        assert job.status == "pending"
        assert job.attempts == 0
        assert s.get(Case, "case-r").status == "ANALYZING"


def test_rerun_rejected_when_not_failed(client, settings):
    from camca_web.auth import hash_password
    client.app.state.staff_accounts = {"staff": hash_password("pw")}
    cookies = client.post("/login", data={"username": "staff", "password": "pw"},
                          follow_redirects=False).cookies
    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-NR", dob="1980-01-01")
        s.add(p); s.flush()
        s.add(Case(id="case-nr", participant_id=p.id, video_path="v.mp4",
                   device_type="pMDI", source="clinic", status="REPORT_ISSUED"))
        s.add(Job(id="job-nr", case_id="case-nr", status="done"))
        s.commit()
    r = client.post("/cases/case-nr/rerun", cookies=cookies)
    assert r.status_code == 409
    with client.app.state.session_factory() as s:
        job = s.get(Job, "job-nr")
        assert job.status == "done"
        assert s.get(Case, "case-nr").status == "REPORT_ISSUED"


def test_rerun_rejected_when_quality_check(client, settings):
    from camca_web.auth import hash_password
    client.app.state.staff_accounts = {"staff": hash_password("pw")}
    cookies = client.post("/login", data={"username": "staff", "password": "pw"},
                          follow_redirects=False).cookies
    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-QC", dob="1980-01-01")
        s.add(p); s.flush()
        s.add(Case(id="case-qc", participant_id=p.id, video_path="v.mp4",
                   device_type="pMDI", source="clinic", status="QUALITY_CHECK"))
        s.add(Job(id="job-qc", case_id="case-qc", status="pending"))
        s.commit()
    r = client.post("/cases/case-qc/rerun", cookies=cookies)
    assert r.status_code == 409
    with client.app.state.session_factory() as s:
        job = s.get(Job, "job-qc")
        assert job.status == "pending"
        assert job.attempts == 0
        assert s.get(Case, "case-qc").status == "QUALITY_CHECK"
