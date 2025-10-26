from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_url: str = Field(alias="MONGODB_URL", default="mongodb://mongo:27017")
    redis_url: str = Field(alias="REDIS_URL", default="redis://redis:6379")
    database_name: str = Field(alias="DATABASE_NAME", default="adaptive_stem_db")
    secret_key: str = Field(alias="SECRET_KEY", default="dev-secret")
    openai_api_key: str | None = Field(alias="OPENAI_API_KEY", default=None)
    chroma_db_path: str = Field(alias="CHROMADB_PATH", default="./chroma_db")
    access_token_expire_minutes: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES", default=30)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
