"""업로드 → 케이스 생성 + 잡 등록 + 원본이 로컬 스토리지에만 저장."""
import io
from unittest.mock import patch
import pytest
from camca_web.db import Participant, Case, Job, AuditLog
from camca_web.auth import hash_password


def _login(client, settings):
    # 테스트용 스태프 계정을 앱 상태에 시드
    client.app.state.staff_accounts = {"staff": hash_password("pw")}
    r = client.post("/login", data={"username": "staff", "password": "pw"},
                    follow_redirects=False)
    assert r.status_code in (302, 303)
    return r.cookies


def test_upload_requires_login(client):
    r = client.post("/upload", files={"video": ("v.mp4", b"xx", "video/mp4")},
                    data={"research_code": "RC-1", "dob": "1980-01-01"},
                    follow_redirects=False)
    assert r.status_code in (302, 303, 401)


def test_upload_creates_case_and_job(client, settings):
    cookies = _login(client, settings)
    r = client.post(
        "/upload",
        files={"video": ("v.mp4", io.BytesIO(b"fake-mp4-bytes"), "video/mp4")},
        data={"research_code": "RC-1", "dob": "1980-01-01",
              "device_type": "pMDI", "source": "clinic"},
        cookies=cookies,
    )
    assert r.status_code == 200
    with client.app.state.session_factory() as s:
        case = s.query(Case).one()
        assert case.status == "UPLOADED"
        job = s.query(Job).filter_by(case_id=case.id).one()
        assert job.status == "pending"
        p = s.query(Participant).filter_by(research_code="RC-1").one()
        assert case.participant_id == p.id
        
        # Assert AuditLog row exists with event == "case_uploaded" and case_id == case.id
        audit = s.query(AuditLog).filter_by(event="case_uploaded", case_id=case.id).one()
        assert audit.detail["by"] == "staff"
        assert audit.detail["source"] == "clinic"
    
    saved = settings.storage_root / "cases" / case.id / "original.mp4"
    assert saved.read_bytes() == b"fake-mp4-bytes"


def test_upload_reuses_existing_participant(client, settings):
    cookies = _login(client, settings)
    for _ in range(2):
        client.post(
            "/upload",
            files={"video": ("v.mp4", io.BytesIO(b"x"), "video/mp4")},
            data={"research_code": "RC-9", "dob": "1990-09-09"},
            cookies=cookies,
        )
    with client.app.state.session_factory() as s:
        assert s.query(Participant).filter_by(research_code="RC-9").count() == 1
        assert s.query(Case).count() == 2


def test_upload_commit_failure_removes_file(client, settings):
    """On commit failure, orphan video file and empty case dir are cleaned up."""
    cookies = _login(client, settings)
    
    # Patch Session.commit to raise RuntimeError
    with patch("sqlalchemy.orm.Session.commit", side_effect=RuntimeError("db error")):
        # Expect the exception to be raised due to commit failure
        with pytest.raises(RuntimeError, match="db error"):
            client.post(
                "/upload",
                files={"video": ("v.mp4", io.BytesIO(b"fake-video"), "video/mp4")},
                data={"research_code": "RC-2", "dob": "1985-05-05"},
                cookies=cookies,
            )
    
    # No Case row should be persisted (commit failed and was rolled back)
    with client.app.state.session_factory() as s:
        assert s.query(Case).count() == 0
    
    # No video file should remain (orphan file cleanup happened)
    cases_dir = settings.storage_root / "cases"
    if cases_dir.exists():
        # Check that no original.mp4 files exist in any case subdirectories
        for case_dir in cases_dir.iterdir():
            video_file = case_dir / "original.mp4"
            assert not video_file.exists(), f"Orphan video file should be removed: {video_file}"
