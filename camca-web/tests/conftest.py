"""공용 fixture — in-memory 설정 + TestClient."""
import pytest
from fastapi.testclient import TestClient

from camca_web.config import Settings
from camca_web.app import create_app


@pytest.fixture
def settings(tmp_path):
    return Settings(
        db_url="sqlite://",              # in-memory
        storage_root=tmp_path / "storage",
        secret_key="test-secret",
    )


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))
