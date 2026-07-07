"""플랫폼 설정 — 환경변수 우선, 테스트에서는 Settings 직접 생성."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    db_url: str = field(default_factory=lambda: os.environ.get(
        "CAMCA_DB_URL", "sqlite:///./camca_web.db"))
    storage_root: Path = field(default_factory=lambda: Path(os.environ.get(
        "CAMCA_STORAGE_ROOT", "./storage")))
    secret_key: str = field(default_factory=lambda: os.environ.get(
        "CAMCA_SECRET_KEY", "dev-only-change-me"))
    patient_link_max_age_sec: int = 7 * 24 * 3600  # 서명 링크 만료 7일
