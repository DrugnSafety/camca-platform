"""스태프 계정(간단) + 환자 연구코드/서명링크/생년월일 (spec 결정표)."""
import os
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


def test_password_hash_self_describing():
    """Assert stored hash starts with 'pbkdf2_sha256$' and has 4 $-separated fields."""
    h = hash_password("s3cret")
    assert h.startswith("pbkdf2_sha256$")
    parts = h.split("$")
    assert len(parts) == 4, f"Expected 4 fields, got {len(parts)}: {parts}"
    scheme, iter_str, salt_hex, dk_hex = parts
    assert scheme == "pbkdf2_sha256"
    assert iter_str.isdigit()
    assert len(salt_hex) == 32  # 16 bytes hex
    assert len(dk_hex) == 64    # 32 bytes hex


def test_verify_password_honors_stored_iterations():
    """Build a hash with lower iterations manually; verify_password should still verify it."""
    import hashlib
    pw = "s3cret"
    old_iterations = 1000
    salt = os.urandom(16)
    salt_hex = salt.hex()
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, old_iterations)
    dk_hex = dk.hex()
    # Manually construct hash string with old iteration count
    old_hash = f"pbkdf2_sha256${old_iterations}${salt_hex}${dk_hex}"
    # verify_password should read the iteration count from the hash, not the module constant
    assert verify_password(pw, old_hash), "Should verify hash with lower iterations"
    assert not verify_password("wrong", old_hash)


def test_verify_password_malformed_inputs():
    """Malformed inputs must return False, not raise."""
    pw = "s3cret"
    # Empty string
    assert not verify_password(pw, "")
    # Nonsense
    assert not verify_password(pw, "nonsense")
    # Non-int iterations
    assert not verify_password(pw, "pbkdf2_sha256$abc$00$00")
    # Unknown scheme
    assert not verify_password(pw, "unknown$1000$00$00")
    # Wrong field count (too few)
    assert not verify_password(pw, "pbkdf2_sha256$1000$00")
    # Invalid hex for salt
    assert not verify_password(pw, "pbkdf2_sha256$1000$zzz$00")
