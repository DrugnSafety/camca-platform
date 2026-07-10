"""케이스 원본 영상 서빙 — 스태프 전용, 타임라인 리뷰의 실제 재생 소스.

원본은 로컬 스토리지에만 있고(PIPA 경계는 클라우드 전송에 적용),
스태프 인증을 거친 로컬 재생은 경계 수정 워크플로우의 전제 조건이다.
"""
import pytest

from camca_web.auth import hash_password
from camca_web.db import Case, Participant


@pytest.fixture
def staff(client):
    client.app.state.staff_accounts = {"staff": hash_password("pw")}
    return client.post("/login", data={"username": "staff", "password": "pw"},
                       follow_redirects=False).cookies


@pytest.fixture
def seeded_video(client, settings):
    video = settings.storage_root / "cases" / "case-v" / "original.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"fake-mp4-bytes")
    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-V", dob="1980-01-01")
        s.add(p); s.flush()
        s.add(Case(id="case-v", participant_id=p.id, video_path=str(video),
                   device_type="pMDI", source="clinic", status="REPORT_ISSUED"))
        s.commit()
    return "case-v"


def test_video_requires_login(client, seeded_video):
    r = client.get(f"/cases/{seeded_video}/video", follow_redirects=False)
    assert r.status_code in (302, 303)


def test_video_served_for_staff(client, staff, seeded_video):
    r = client.get(f"/cases/{seeded_video}/video", cookies=staff)
    assert r.status_code == 200
    assert r.headers["content-type"] == "video/mp4"
    assert r.content == b"fake-mp4-bytes"


def test_video_unknown_case_404(client, staff):
    r = client.get("/cases/no-such-case/video", cookies=staff)
    assert r.status_code == 404


def test_video_missing_file_404(client, staff, seeded_video, settings):
    (settings.storage_root / "cases" / "case-v" / "original.mp4").unlink()
    r = client.get(f"/cases/{seeded_video}/video", cookies=staff)
    assert r.status_code == 404


def test_case_detail_player_points_to_video_route(client, staff, seeded_video):
    r = client.get(f"/cases/{seeded_video}", cookies=staff)
    assert r.status_code == 200
    assert f"/cases/{seeded_video}/video" in r.text
    assert "placeholder.mp4" not in r.text
