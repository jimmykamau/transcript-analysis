# Style Guide

## Ruff

Configured in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py314"

[tool.ruff.lint]
extend-select = ["I", "B", "UP", "SIM", "FAST"]
fixable = ["ALL"]
```

Rule sets enabled beyond defaults:

| Code | Plugin | What it catches |
|-|-|-|
| `I` | isort | import ordering |
| `B` | flake8-bugbear | likely bugs and design issues |
| `UP` | pyupgrade | outdated Python syntax |
| `SIM` | flake8-simplify | unnecessary complexity |
| `FAST` | FastAPI-specific | FastAPI anti-patterns |

## Pre-commit

`.pre-commit-config.yaml` runs `ruff --fix` and `ruff-format` on every commit. Install once after cloning:

```bash
uv run pre-commit install
```

## CI

`.github/workflows/ci.yml` runs lint + tests on every push and on PRs targeting `main`, `staging`, or `dev`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest -n auto
```
