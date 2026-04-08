from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_settings
from app.main import app
from app.transcripts.router import get_db


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    # Clear before: prevent a cached real-key instance from bleeding into this test.
    # Clear after: prevent the test key from contaminating subsequent tests.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def mock_db():
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
