from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "Transcript Analysis"
    debug: bool = False
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-6"
    claude_max_tokens: int = 1024
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "transcript_analysis"
    claude_search_model: str = "claude-haiku-4-5"
