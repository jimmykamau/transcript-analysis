from functools import lru_cache

from app.config import Settings


@lru_cache  # parse env/file once per process lifetime
def get_settings() -> Settings:
    return Settings()
