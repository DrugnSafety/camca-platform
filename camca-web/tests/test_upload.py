"""업로드 → 케이스 생성 + 잡 등록 + 원본이 로컬 스토리지에만 저장."""
import io
from camca_web.db import Participant, Case, Job
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
