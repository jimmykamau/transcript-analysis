import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_settings
from app.main import app


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
