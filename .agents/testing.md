# Testing

```bash
uv run pytest                              # run all tests
uv run pytest tests/transcripts/           # run one domain
uv run pytest tests/test_foo.py::test_bar  # single test
uv run pytest -n auto                      # parallel (pytest-xdist)
```

## Async pattern

Tests use `pytest-anyio` with `@pytest.mark.anyio`. The shared `client` fixture in `tests/conftest.py` provides an `httpx.AsyncClient` backed by the FastAPI app via ASGI transport:

```python
@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

Use `@pytest.mark.anyio` on every async test (not `@pytest.mark.asyncio`).

## Mocking the Claude API

Patch `app.transcripts.services.anthropic.AsyncAnthropic` — target the module where it is used, not where it is defined:

```python
from unittest.mock import AsyncMock, MagicMock, patch

mock_instance = AsyncMock()
mock_instance.messages.create = AsyncMock(return_value=mock_response)

with patch("app.transcripts.services.anthropic.AsyncAnthropic", return_value=mock_instance):
    response = await client.post("/transcripts/analyze", json={...})
```

No real API calls are made in tests.
