from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    api_key: str = "dev-api-key"

    northwind_url: str
    raw_db_path: str = "data/raw/northwind.db"
    runtime_db_path: str = "data/runtime/northwind.db"
    app_db_path: str = "data/app/app.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()