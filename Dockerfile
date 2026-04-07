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
