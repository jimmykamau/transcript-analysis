# Scaffolding Spec

## Goal

Stand up the project skeleton so that a developer can add domain features immediately. After this work is complete, the dev server boots, tests run (with one placeholder passing), linting is clean, and Docker builds succeed.

## 1. App Package Structure

Create the `app/` package with the following files:

| File | Purpose |
|-|-|
| `app/__init__.py` | Empty package init |
| `app/main.py` | FastAPI app instance, includes domain routers, health-check endpoint (`GET /health`) |
| `app/config.py` | `Settings(BaseSettings)` class — loads from env / `.env` via `model_config = SettingsConfigDict(env_file=".env")` |
| `app/dependencies.py` | Shared FastAPI dependencies (initially exposes a `get_settings` dependency) |

### `app/main.py` detail

```python
from fastapi import FastAPI
from app.transcripts.router import router as transcripts_router

app = FastAPI(title="Transcript Analysis")

app.include_router(transcripts_router, prefix="/transcripts", tags=["transcripts"])

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### `app/config.py` detail

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "Transcript Analysis"
    debug: bool = False
```

### `app/dependencies.py` detail

```python
from functools import lru_cache
from app.config import Settings

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

## 2. Domain Packages

Create the `transcripts` domain package:

| File | Purpose |
|-|-|
| `app/<domain>/__init__.py` | Empty package init |
| `app/<domain>/router.py` | `APIRouter` with a stub `GET /` endpoint returning `{"status": "ok"}` |
| `app/<domain>/models.py` | Empty module (placeholder for Pydantic schemas) |
| `app/<domain>/services.py` | Empty module (placeholder for business logic) |

### `app/transcripts/router.py`

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {"status": "ok"}
```

## 3. Test Structure

```
tests/
├── __init__.py
├── conftest.py          # shared fixtures
└── transcripts/
    ├── __init__.py
    └── test_router.py   # smoke test for GET /transcripts/
```

### `tests/conftest.py`

```python
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

### `tests/transcripts/test_router.py`

```python
import pytest

@pytest.mark.anyio
async def test_root(client):
    response = await client.get("/transcripts/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Also add a `tests/test_health.py`:

```python
import pytest

@pytest.mark.anyio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

## 4. Missing Dependencies

The following packages are referenced in CLAUDE.md but missing from `pyproject.toml`:

| Package | Group | Why |
|-|-|-|
| `uvicorn` | production | ASGI server (`uv run uvicorn app.main:app --reload`) |
| `httpx` | dev | Async test client (`AsyncClient`) |
| `pytest-asyncio` or `anyio` + `pytest-anyio` | dev | Async test support |
| `pre-commit` | dev | Git pre-commit hook framework |
| `pytest-xdist` | dev | Parallel test execution (`pytest -n auto`) |

Add via:

```bash
uv add uvicorn
uv add --group dev httpx anyio pytest-anyio pre-commit pytest-xdist
```

## 5. Pytest Configuration

Remove `asyncio_mode = "auto"` from `[tool.pytest.ini_options]` in `pyproject.toml` — it belongs to `pytest-asyncio` and is not recognized by `pytest-anyio`.

## 6. Docker

### `Dockerfile`

```dockerfile
# --- builder ---
FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# cache deps
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --locked --no-install-project

# install project
COPY . .
RUN uv sync --no-dev --locked

# --- final ---
FROM python:3.14-slim
WORKDIR /app
COPY --from=builder /app/.venv .venv
COPY --from=builder /app .
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `Dockerfile.dev`

Development image that includes dev dependencies, mounts source via volume, and runs with hot-reload. Also used for running tests and linting in CI or locally.

```dockerfile
FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# install all deps (including dev)
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .
RUN uv sync --locked

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### `docker-compose.yml`

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/.venv
    env_file:
      - .env
```

The `/app/.venv` anonymous volume prevents the host mount from overwriting the container's installed venv.

Usage:

```bash
# start dev server (hot-reload via volume mount)
docker compose up

# run tests
docker compose run --rm app uv run pytest

# run linting
docker compose run --rm app uv run ruff check .
```

### `.dockerignore`

```
.venv
.git
__pycache__
*.pyc
.env
.ruff_cache
```

## 7. Environment Config

Create `.env.example`:

```
APP_NAME=Transcript Analysis
DEBUG=false
```

Add `.env` to `.gitignore` (already present).

## 8. CI — GitHub Actions

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Set up Python
        run: uv python install

      - name: Install dependencies
        run: uv sync

      - name: Lint
        run: |
          uv run ruff check .
          uv run ruff format --check .

      - name: Test
        run: uv run pytest -n auto
```

## 9. Pre-commit Hooks

Enforce linting and formatting on every commit, matching the CLAUDE.md rule: "Always run `uv run ruff check .` and `uv run ruff format --check .` before committing."

### `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.9  # match version in pyproject.toml
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

### Setup

```bash
uv run pre-commit install
```

Add the setup instruction to CLAUDE.md's Development section so new developers know to run it after cloning.

## 10. Cleanup

- Remove root `main.py` — it is a placeholder superseded by `app/main.py`.

## Checklist

After scaffolding is complete, all of the following must pass:

- [ ] `uv sync` installs without errors
- [ ] `uv run uvicorn app.main:app` boots and `GET /health` returns `{"status": "ok"}`
- [ ] `uv run pytest` discovers and passes all smoke tests
- [ ] `uv run ruff check .` reports no issues
- [ ] `uv run ruff format --check .` reports no issues
- [ ] `docker build -t transcript-analysis .` succeeds
- [ ] `docker compose up` boots and `GET http://localhost:8000/health` returns `{"status": "ok"}`
- [ ] `docker compose run --rm app uv run pytest` passes all tests
- [ ] `uv run pre-commit run --all-files` passes cleanly
