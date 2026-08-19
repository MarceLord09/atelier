from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ATELIER API"
    app_version: str = "0.1.0"
    environment: Literal["development", "production"] = "development"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str = "sqlite+aiosqlite:///./atelier.db"
    jwt_secret: str = "dev-only-change-me-use-a-long-random-secret"
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.6-27b"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    allow_self_assign_role: bool = True
    llm_provider: Literal["template", "live"] = "template"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
