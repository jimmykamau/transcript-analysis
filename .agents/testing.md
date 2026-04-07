# Testing

```bash
uv run pytest                              # run all tests
uv run pytest tests/transcripts/           # run one domain
uv run pytest tests/test_foo.py::test_bar  # single test
uv run pytest -n auto                      # parallel (pytest-xdist)
```

## Async pattern

Tests use `anyio` with `@pytest.mark.anyio`. The shared `client` fixture in `tests/conftest.py` provides an `httpx.AsyncClient` backed by the FastAPI app via ASGI transport:

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

## Mocking MongoDB

The `mock_db` fixture in `tests/conftest.py` overrides the `get_db` dependency with a `MagicMock` for every test:

```python
@pytest.fixture(autouse=True)
def mock_db():
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.pop(get_db, None)
```

This prevents any real MongoDB connection in tests. To control repository behaviour per test, patch the repository function directly:

```python
with patch(
    "app.transcripts.router.repository.save_transcript",
    new=AsyncMock(return_value={"id": "507f1f77bcf86cd799439011", "created_at": ...}),
):
    response = await client.post("/transcripts/analyze", json={...})
```

Patch at `app.transcripts.router.repository.<function>`, not at `app.transcripts.repository.<function>`.
