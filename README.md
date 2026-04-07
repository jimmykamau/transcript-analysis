# Transcript Analysis

Stateless FastAPI service for transcript analysis.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager

## Getting Started

```bash
# install dependencies
uv sync

# install pre-commit hooks
uv run pre-commit install

# copy environment config and set ANTHROPIC_API_KEY
cp .env.example .env

# run dev server (port 8000)
uv run uvicorn app.main:app --reload
```

## Development with Docker

```bash
# start dev server (hot-reload)
docker compose up

# run tests
docker compose run --rm app uv run pytest -n auto

# run linting
docker compose run --rm app uv run ruff check .
```

## Testing

```bash
uv run pytest -n auto
```

## Linting & Formatting

```bash
uv run ruff check .       # lint
uv run ruff format .      # format
```

Pre-commit hooks run ruff checks automatically on each commit.
