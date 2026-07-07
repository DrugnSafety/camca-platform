"""인증 — 스태프: 서명 세션 쿠키. 환자: 만료되는 서명 링크 + 생년월일 확인.

회원가입 없음(spec). 외부 의존은 itsdangerous 하나로 최소화.
"""
from __future__ import annotations

import hashlib
import hmac
import os

from itsdangerous import BadSignature, URLSafeTimedSerializer

_PBKDF2_ITER = 600_000


def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, _PBKDF2_ITER)
    return f"pbkdf2_sha256${_PBKDF2_ITER}${salt.hex()}${dk.hex()}"


def verify_password(pw: str, hashed: str) -> bool:
    try:
        parts = hashed.split("$")
        if len(parts) != 4:
            return False
        scheme, iter_str, salt_hex, dk_hex = parts
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iter_str)
    except (ValueError, IndexError):
        return False
    try:
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt_hex), iterations)
    except ValueError:
        return False
    return hmac.compare_digest(dk.hex(), dk_hex)


def _serializer(secret: str, salt: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret, salt=salt)


def make_session_cookie(username: str, secret: str) -> str:
    return _serializer(secret, "staff-session").dumps(username)


def read_session_cookie(value: str, secret: str,
                        max_age_sec: int = 12 * 3600) -> str | None:
    try:
        return _serializer(secret, "staff-session").loads(value, max_age=max_age_sec)
    except BadSignature:
        return None


def make_patient_token(case_id: str, secret: str) -> str:
    return _serializer(secret, "patient-link").dumps(case_id)


def read_patient_token(token: str, secret: str, max_age_sec: int) -> str | None:
    try:
        return _serializer(secret, "patient-link").loads(token, max_age=max_age_sec)
    except BadSignature:
        return None


def dob_matches(input_dob: str, stored_dob: str) -> bool:
    """입력 유연화: 숫자만 남겨 비교 (1980-01-01 == 19800101)."""
    digits = lambda s: "".join(ch for ch in s if ch.isdigit())
    return digits(input_dob) == digits(stored_dob) and len(digits(input_dob)) == 8
