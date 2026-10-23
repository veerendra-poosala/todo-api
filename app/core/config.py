"""Application settings loaded from environment variables (and the local .env file).

Priority: real environment variables > values in .env > defaults below.
Fields without a default are required, so the app fails fast at startup if they are missing.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Todo API"
    APP_ENV: str = "development"

    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
