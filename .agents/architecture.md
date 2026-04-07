# Architecture

Domain-driven layout — each feature area is a self-contained package.

```
app/
├── main.py              # FastAPI app instance, includes routers
├── config.py            # pydantic-settings BaseSettings
├── dependencies.py      # shared FastAPI dependencies (get_settings)
└── transcripts/
    ├── router.py        # APIRouter with endpoints
    ├── models.py        # Pydantic request/response schemas
    └── services.py      # Business logic (Claude API calls)
```

## Patterns

**Router registration** — each domain exposes an `APIRouter` in `router.py`; `app/main.py` includes it with a prefix:

```python
app.include_router(transcripts_router, prefix="/transcripts", tags=["transcripts"])
```

**Dependency injection** — `get_settings()` is an `@lru_cache`-wrapped factory in `app/dependencies.py`. Inject with `Annotated[Settings, Depends(get_settings)]`.

**Config** — `Settings(BaseSettings)` in `app/config.py` loads from env vars / `.env`. Fields without defaults are required — missing ones raise a `ValidationError` at startup. Current required field: `anthropic_api_key`.

**No database** — stateless service. No ORM, no migrations.

## Adding a new domain

1. Create `app/<domain>/` with `__init__.py`, `router.py`, `models.py`, `services.py`
2. Add `include_router()` call in `app/main.py`
3. Add tests in `tests/<domain>/`
