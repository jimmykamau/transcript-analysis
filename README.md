# Transcript Analysis

FastAPI service that analyzes call center transcripts via the Claude API and persists results to MongoDB.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager
- MongoDB (or use Docker Compose, which includes it)

## Getting Started

```bash
# install dependencies
uv sync

# install pre-commit hooks
uv run pre-commit install

# copy environment config and set ANTHROPIC_API_KEY
cp .env.example .env

# start MongoDB (if not using Docker)
mongod

# run dev server (port 8000)
uv run uvicorn app.main:app --reload
```

## Development with Docker

Docker Compose starts both the app and MongoDB:

```bash
# start dev server + MongoDB (hot-reload)
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
