# Copilot PR Review Instructions

## Project context

FastAPI service that accepts call center transcripts, returns structured QA analysis via the Claude API, and persists results to MongoDB. Python 3.14, `uv` for package management.

Full references: [architecture](../.agents/architecture.md), [testing](../.agents/testing.md), [style guide](../.agents/style-guide.md), [docker](../.agents/docker.md), [api design](../.agents/api-design.md).

---

## What to check on every PR

### Architecture

- Domain layout: `router.py` (endpoints) → `services.py` (business logic) → `schemas.py` (API types) / `models.py` (DB types). Business logic must not live in `router.py`.
- `models.py` holds DB document types. `schemas.py` holds API-facing types; where shapes overlap, API types inherit from the DB model rather than duplicating fields.
- Persistence: MongoDB operations belong in `repository.py`. Repository functions return typed model instances, not plain dicts. Routers call repository functions and catch exceptions to return 503.
- New domains must be registered in `app/main.py` via `app.include_router()`.
- Shared dependencies belong in `app/dependencies.py`, not duplicated across routers.
- `Settings` is the only config source — no `os.environ` calls outside of `app/config.py`.
- MongoDB client must be initialised in the lifespan context manager and accessed via the `get_db` dependency, never instantiated per request.

**Topic search specifics:**

- `GET /transcripts/topics` calls `repository.list_topics()` (MongoDB `distinct("topics")`), returns a plain list of strings, and raises 503 on failure.
- `POST /transcripts/search` must follow this call chain: `repository.list_topics` → `services.interpret_query` → `repository.search_by_topics`. No inline query logic in the router.
- `services.interpret_query` must use `CLAUDE_SEARCH_MODEL`, not `CLAUDE_MODEL`. Verify the settings field is read from `Settings`, not hardcoded.
- If `interpret_query` returns an empty list, the router returns `[]` with status 200 — this is not an error.
- Topics are assigned at analyze time in `services.analyze_transcript` and stored on the document. They are not computed on read.

### Code quality

- `uv run ruff check .` and `uv run ruff format --check .` must pass (enforced by pre-commit and CI).
- No magic numbers for API parameters — `max_tokens`, `max_retries`, and similar values should be named constants or `Settings` fields.
- No duplicate string literals for tool names, error messages, or model identifiers — reference a single definition.
- Pydantic models must enforce constraints with `Field(...)` matching any corresponding JSON schema (e.g. `ge=1, le=10` for `qa_score`).
- `topics` fields must default to an empty list via `Field(default_factory=list)`, not `default=[]` or `Optional`.
- List endpoints must be paginated — bare `find({})` with no `.limit()` is not acceptable.

### Claude API usage

- Use `anthropic.AsyncAnthropic` (async client only).
- The client must not be instantiated per request — use `@lru_cache` or a module-level cached factory.
- Structured output must use `tool_use` with `tool_choice={"type": "tool", "name": ...}`.
- `tool_choice["name"]` must reference the tool definition's `"name"` field, not a duplicate string.
- Error handling in routers must map to the correct HTTP status codes:
  - `anthropic.AuthenticationError` → 500 `"Service configuration error"`
  - `anthropic.APIStatusError` / `anthropic.APIConnectionError` → 502 `"Upstream API error"`
  - `ValueError` (unexpected LLM response) → 500 `"Unexpected response from LLM"`
- `interpret_query` uses the lighter `CLAUDE_SEARCH_MODEL` — flag any PR that uses `CLAUDE_MODEL` for the search/topic-mapping call.
- Both Claude and MongoDB failures in `POST /transcripts/search` must return 503 — callers do not need to distinguish them.

### Storage error handling

- Any MongoDB failure must return 503 `"Storage unavailable"`.
- `POST /analyze` must save before returning — a failed save must not silently return a 200.
- `GET /{id}` must return 400 for an invalid ObjectId format (use `ObjectId.is_valid()`) and 404 for a valid but missing document.
- `GET /transcripts/topics` must return 503 on any MongoDB failure.
- `POST /transcripts/search` must return 503 on any MongoDB or Claude failure.

### MongoDB indexes

- `created_at` descending index must exist for the list endpoint.
- `topics` ascending index must exist and be created in the lifespan context manager in `app/main.py`. MongoDB indexes array fields natively — no special handling needed.

### Testing

- Every new endpoint needs tests covering: success, validation failure (422), and upstream failure.
- Storage endpoints additionally need: 503 on repository failure, 400/404 for `GET /{id}`.
- Async tests use `@pytest.mark.anyio` (not `@pytest.mark.asyncio`).
- Claude API calls must be mocked via `unittest.mock.patch` targeting `app.<domain>.services.anthropic.AsyncAnthropic`. No real API calls in tests.
- MongoDB is never contacted in tests. The `mock_db` autouse fixture in `conftest.py` overrides `get_db`. Repository functions are patched per test at `app.transcripts.router.repository.<function>`.
- Tests use the shared `client` fixture from `tests/conftest.py`.

**Topic search test requirements:**

| Test | Endpoint | Expected |
|-|-|-|
| Topic filter forwarded | `GET /?topic=apology` | `repository.list_transcripts` called with `topic="apology"` |
| No topic filter | `GET /` | `repository.list_transcripts` called with `topic=None` |
| List topics success | `GET /topics` | 200 with slug array |
| List topics storage failure | `GET /topics` | 503 `"Storage unavailable"` |
| Search success | `POST /search` | 200 with matching summaries |
| Search no matches | `POST /search` | 200 with `[]` (not an error) |
| Search empty query | `POST /search` | 422 |
| Search storage failure | `POST /search` | 503 |
| Search Claude failure | `POST /search` | 503 |

`services.interpret_query` must be patched directly (not via `AsyncAnthropic`) when testing the router — only the services unit tests should patch the Claude client.

### Security

- `ANTHROPIC_API_KEY` must never appear in committed files. Reject any PR that includes it in source, tests, or config files.
- `.env` must remain in `.gitignore`. `.env.example` must not contain real keys.

### Dependencies

- Production dependencies: `uv add <package>`
- Dev dependencies: `uv add --group dev <package>`
- Both `pyproject.toml` and `uv.lock` must be committed together.
