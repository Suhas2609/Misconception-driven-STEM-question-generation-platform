"""Application configuration settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Centralised application settings object."""

    # Database & infrastructure
    mongodb_url: str = Field("mongodb://mongo:27017", env="MONGODB_URL")
    database_name: str = Field("adaptive_stem_db", env="DATABASE_NAME")
    redis_url: str = Field("redis://redis:6379", env="REDIS_URL")
    chromadb_path: Path = Field(Path("./chroma_db"), env="CHROMADB_PATH")

    # Auth / security
    secret_key: str = Field("dev-secret-key", env="SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(480, env="ACCESS_TOKEN_EXPIRE_MINUTES")  # 8 hours for development

    # LLM configuration
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", env="OPENAI_MODEL")

    # Retrieval tuning
    factual_top_k: int = Field(6, env="FACTUAL_TOP_K")
    misconception_top_k: int = Field(6, env="MISCONCEPTION_TOP_K")
    min_misconceptions: int = Field(3, env="MIN_MISCONCEPTIONS")

    chroma_telemetry_enabled: Literal[0, 1] = Field(0, env="CHROMA_TELEMETRY_ENABLED")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance so dependency overrides are straightforward."""

    return Settings()
