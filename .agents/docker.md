# Docker

| File | Purpose |
|-|-|
| `Dockerfile` | Production multi-stage build |
| `Dockerfile.dev` | Dev single-stage with hot-reload |
| `docker-compose.yml` | Local dev via `Dockerfile.dev` |

## Production build

Two-stage build:

1. **Builder** — installs uv, syncs only prod deps (`--no-dev --locked --no-install-project`), then copies source and syncs again to install the project
2. **Final** — copies only `.venv` and source from builder; sets `PATH="/app/.venv/bin:$PATH"`

Layer caching: `pyproject.toml` + `uv.lock` are copied and synced before source — source changes don't invalidate the dep layer.

Key env vars set in both Dockerfiles:
- `UV_COMPILE_BYTECODE=1` — faster startup (bytecode pre-compiled at install time)
- `UV_LINK_MODE=copy` — avoids cross-filesystem hardlink issues

## docker-compose (dev)

```bash
docker compose up                                # start app + MongoDB
docker compose run --rm app uv run pytest        # run tests
docker compose run --rm app uv run ruff check .  # lint
```

Two services: `mongo` (mongo:8, port 27017) and `app`. The app service sets `MONGODB_URL=mongodb://mongo:27017` and declares `depends_on: mongo`.

Source is bind-mounted to `/app`. An anonymous volume at `/app/.venv` prevents the host mount from overwriting the container's installed venv. Env vars load from `.env` via `env_file`.

## .dockerignore

`.venv`, `.git`, `__pycache__`, `*.pyc`, `.env`, `.ruff_cache` are excluded.
