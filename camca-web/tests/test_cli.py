"""`camca-web create-staff` — 스태프 계정 시드 CLI.

회원가입 없는 설계(spec)에서 유일한 계정 생성 경로. DB에 저장된 계정은
로그인 시 in-memory 주입 계정의 fallback으로 조회된다.
"""
import pytest

from camca_web.auth import verify_password
from camca_web.cli import main
from camca_web.config import Settings
from camca_web.db import (AuditLog, Staff, make_engine, make_session_factory,
                          init_db)


@pytest.fixture
def db_url(tmp_path):
    return f"sqlite:///{tmp_path}/cli.db"


def _rows(db_url):
    engine = make_engine(db_url)
    init_db(engine)
    with make_session_factory(engine)() as s:
        return {r.username: r.password_hash for r in s.query(Staff).all()}


def test_create_staff_inserts_account(db_url):
    rc = main(["create-staff", "--username", "dr-kang",
               "--password", "s3cret!", "--db-url", db_url])
    assert rc == 0
    rows = _rows(db_url)
    assert set(rows) == {"dr-kang"}
    assert verify_password("s3cret!", rows["dr-kang"])
    assert rows["dr-kang"].startswith("pbkdf2_sha256$")   # 평문 저장 금지


def test_create_staff_upserts_existing(db_url):
    main(["create-staff", "--username", "dr-kang",
          "--password", "old", "--db-url", db_url])
    rc = main(["create-staff", "--username", "dr-kang",
               "--password", "new", "--db-url", db_url])
    assert rc == 0
    rows = _rows(db_url)
    assert len(rows) == 1
    assert verify_password("new", rows["dr-kang"])
    assert not verify_password("old", rows["dr-kang"])


def test_create_staff_writes_audit(db_url):
    main(["create-staff", "--username", "dr-kang",
          "--password", "pw", "--db-url", db_url])
    engine = make_engine(db_url)
    with make_session_factory(engine)() as s:
        events = [a.event for a in s.query(AuditLog).all()]
    assert "staff_account_seeded" in events


def test_create_staff_prompts_when_password_omitted(db_url, monkeypatch):
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "prompted-pw")
    rc = main(["create-staff", "--username", "dr-kim", "--db-url", db_url])
    assert rc == 0
    assert verify_password("prompted-pw", _rows(db_url)["dr-kim"])


def test_create_staff_rejects_empty_password(db_url):
    rc = main(["create-staff", "--username", "dr-kang",
               "--password", "", "--db-url", db_url])
    assert rc != 0
    assert _rows(db_url) == {}


def test_login_falls_back_to_db_account(tmp_path, db_url):
    """CLI로 시드한 계정으로 실제 로그인 가능 (in-memory dict에 없어도)."""
    from fastapi.testclient import TestClient
    from camca_web.app import create_app

    main(["create-staff", "--username", "dr-kang",
          "--password", "pw", "--db-url", db_url])
    settings = Settings(db_url=db_url, storage_root=tmp_path / "st",
                        secret_key="t")
    client = TestClient(create_app(settings))
    r = client.post("/login", data={"username": "dr-kang", "password": "pw"},
                    follow_redirects=False)
    assert r.status_code == 303
    assert "camca_session" in r.cookies


def test_login_db_fallback_rejects_wrong_password(tmp_path, db_url):
    from fastapi.testclient import TestClient
    from camca_web.app import create_app

    main(["create-staff", "--username", "dr-kang",
          "--password", "pw", "--db-url", db_url])
    settings = Settings(db_url=db_url, storage_root=tmp_path / "st",
                        secret_key="t")
    client = TestClient(create_app(settings))
    r = client.post("/login", data={"username": "dr-kang", "password": "nope"},
                    follow_redirects=False)
    assert r.status_code == 401
