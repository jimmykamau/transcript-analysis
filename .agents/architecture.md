# Architecture

Domain-driven layout — each feature area is a self-contained package.

```
app/
├── main.py              # FastAPI app instance, lifespan, router registration
├── config.py            # pydantic-settings BaseSettings
├── dependencies.py      # shared FastAPI dependencies (get_settings)
└── transcripts/
    ├── router.py        # APIRouter with endpoints; get_db dependency
    ├── schemas.py       # API-facing Pydantic types (request/response)
    ├── models.py        # DB document model (TranscriptDocument)
    ├── repository.py    # MongoDB CRUD (save, get_by_id, list)
    └── services.py      # Business logic (Claude API calls)
```

## Patterns

**Router registration** — each domain exposes an `APIRouter` in `router.py`; `app/main.py` includes it with a prefix:

```python
app.include_router(transcripts_router, prefix="/transcripts", tags=["transcripts"])
```

**Dependency injection** — `get_settings()` is an `@lru_cache`-wrapped factory in `app/dependencies.py`. Inject with `Annotated[Settings, Depends(get_settings)]`.

**Config** — `Settings(BaseSettings)` in `app/config.py` loads from env vars / `.env`. Fields without defaults are required — missing ones raise a `ValidationError` at startup.

Required fields: `anthropic_api_key`.
Optional fields with defaults: `mongodb_url`, `mongodb_db_name`.

**MongoDB** — `AsyncMongoClient` is initialised in the `lifespan` context manager in `app/main.py` and attached to `app.state.db`. Endpoints access it via a `get_db` dependency in `router.py`:

```python
def get_db(request: Request):
    return request.app.state.db

DbDep = Annotated[object, Depends(get_db)]
```

All MongoDB operations are in `repository.py`. Routers call repository functions and map exceptions to HTTP 503.

**models vs schemas** — `models.py` holds DB document types (`TranscriptDocument`). `schemas.py` holds API-facing types; where the shapes overlap, API types inherit from the DB model (e.g. `TranscriptDetail(TranscriptDocument)`). `repository.py` returns typed model instances, not plain dicts.

## Adding a new domain

1. Create `app/<domain>/` with `__init__.py`, `router.py`, `schemas.py`, `services.py`
2. Add `models.py` and `repository.py` if the domain needs persistence
3. Add `include_router()` call in `app/main.py`
4. Add tests in `tests/<domain>/`
