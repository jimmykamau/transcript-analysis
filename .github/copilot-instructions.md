# Copilot PR Review Instructions

## Project context

Stateless FastAPI service that analyzes call center transcripts via the Claude API. No database. Python 3.14, `uv` for package management.

Full references: [architecture](../.agents/architecture.md), [testing](../.agents/testing.md), [style guide](../.agents/style-guide.md), [docker](../.agents/docker.md).

---

## What to check on every PR

### Architecture

- New features must follow the domain-driven layout: `router.py` (endpoints) → `services.py` (business logic) → `models.py` (Pydantic schemas). Business logic must not live in `router.py`.
- New domains must be registered in `app/main.py` via `app.include_router()`.
- Shared dependencies belong in `app/dependencies.py`, not duplicated across routers.
- `Settings` is the only config source — no `os.environ` calls outside of `app/config.py`.

### Code quality

- `uv run ruff check .` and `uv run ruff format --check .` must pass (enforced by pre-commit and CI).
- No magic numbers for API parameters — `max_tokens`, `max_retries`, and similar values should be named constants or `Settings` fields.
- No duplicate string literals for tool names, error messages, or model identifiers — reference a single definition.
- Pydantic models must enforce constraints with `Field(...)` that match any corresponding JSON schema definitions (e.g. `ge=1, le=10` for `qa_score`).

### Claude API usage

- Use `anthropic.AsyncAnthropic` (async client only).
- The client must not be instantiated per request — use `@lru_cache` or a module-level cached factory.
- Structured output must use `tool_use` with `tool_choice={"type": "tool", "name": ...}`.
- `tool_choice["name"]` must reference the tool definition's `"name"` field, not a duplicate string.
- Error handling in routers must map to the correct HTTP status codes:
  - `anthropic.AuthenticationError` → 500 `"Service configuration error"`
  - `anthropic.APIStatusError` / `anthropic.APIConnectionError` → 502 `"Upstream API error"`
  - `ValueError` (unexpected LLM response) → 500 `"Unexpected response from LLM"`

### Testing

- Every new endpoint needs tests covering: success, validation failure (422), and upstream API failure (502).
- Async tests use `@pytest.mark.anyio` (not `@pytest.mark.asyncio`).
- Claude API calls must be mocked via `unittest.mock.patch` targeting `app.<domain>.services.anthropic.AsyncAnthropic`. No real API calls in tests.
- Tests use the shared `client` fixture from `tests/conftest.py`.

### Security

- `ANTHROPIC_API_KEY` must never appear in committed files. Reject any PR that includes it in source, tests, or config files.
- `.env` must remain in `.gitignore`. `.env.example` must not contain real keys.

### Dependencies

- Production dependencies: `uv add <package>`
- Dev dependencies: `uv add --group dev <package>`
- Both `pyproject.toml` and `uv.lock` must be committed together.
