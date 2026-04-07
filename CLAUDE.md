# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development

```bash
uv sync                        # install all dependencies (including dev)
uv run pre-commit install      # install git pre-commit hooks (run once after cloning)
uv add <package>               # add a production dependency
uv add --group dev <package>   # add a dev dependency
uv run uvicorn app.main:app --reload  # run dev server on port 8000
```

## Testing

```bash
uv run pytest                          # run all tests
uv run pytest tests/transcripts/       # run tests for one domain
uv run pytest tests/test_foo.py::test_bar  # run a single test
```

Tests use `httpx.AsyncClient` with `pytest-asyncio` for async test patterns:

```python
async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
    response = await client.get("/endpoint")
```

## Linting & Formatting

```bash
uv run ruff check .            # lint
uv run ruff check . --fix      # lint and auto-fix
uv run ruff format .           # format
```

Ruff is configured in `pyproject.toml` with `extend-select = ["I", "B", "UP", "SIM", "FAST"]` — this adds isort, flake8-bugbear, pyupgrade, simplify, and FastAPI-specific rules on top of defaults.

**Always run `uv run ruff check .` and `uv run ruff format --check .` before committing.** Fix any issues before creating the commit.

## Architecture

**Domain-driven layout** — each feature area is a self-contained package:

```
app/
├── main.py              # FastAPI app instance, includes routers
├── config.py            # pydantic-settings BaseSettings
├── transcripts/
│   ├── router.py        # APIRouter with endpoints
│   ├── models.py        # Pydantic request/response schemas
│   └── services.py      # Business logic
└── analysis/
    ├── router.py
    ├── models.py
    └── services.py
```

- Each domain exposes an `APIRouter` in `router.py`, included in `app/main.py` via `app.include_router()`
- Shared dependencies live in `app/dependencies.py`
- Configuration uses `pydantic-settings` (`BaseSettings`) loaded from environment variables / `.env`
- No database — this is a stateless API service

## Docker

Multi-stage build using uv for fast, reproducible installs:

- **Builder stage**: install uv via `COPY --from=ghcr.io/astral-sh/uv:<version>`, sync deps with `--no-dev --locked`
- **Final stage**: copy only `.venv` from builder, set `PATH="/app/.venv/bin:$PATH"`
- Key env vars: `UV_COMPILE_BYTECODE=1` (faster startup), `UV_LINK_MODE=copy` (avoids cross-filesystem issues)
- Layer caching: copy `pyproject.toml` + `uv.lock` first, run `uv sync --no-install-project`, then copy source and run `uv sync` — source changes don't rebuild deps
- Add `.venv` to `.dockerignore`
