"""스태프 계정(간단) + 환자 연구코드/서명링크/생년월일 (spec 결정표)."""
import time
import pytest
from camca_web.auth import (
    hash_password, verify_password, make_session_cookie, read_session_cookie,
    make_patient_token, read_patient_token, dob_matches,
)

SECRET = "test-secret"


def test_password_roundtrip():
    h = hash_password("s3cret")
    assert h != "s3cret"
    assert verify_password("s3cret", h)
    assert not verify_password("wrong", h)


def test_session_cookie_roundtrip_and_tamper():
    c = make_session_cookie("dr.kang", SECRET)
    assert read_session_cookie(c, SECRET) == "dr.kang"
    assert read_session_cookie(c + "x", SECRET) is None
    assert read_session_cookie(c, "other-secret") is None


def test_patient_token_roundtrip():
    t = make_patient_token("case-abc", SECRET)
    assert read_patient_token(t, SECRET, max_age_sec=60) == "case-abc"


def test_patient_token_expiry():
    t = make_patient_token("case-abc", SECRET)
    time.sleep(2.2)
    assert read_patient_token(t, SECRET, max_age_sec=1) is None


def test_dob_matches_formats():
    assert dob_matches("1980-01-01", "1980-01-01")
    assert dob_matches("19800101", "1980-01-01")   # 숫자만 입력해도 허용
    assert not dob_matches("1980-01-02", "1980-01-01")
