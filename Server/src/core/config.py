"""Environment settings for the API."""

from typing import Annotated, Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    """Validate the environment when the application is created."""

    app_env: Literal["development", "test", "production"] = "development"
    cors_allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    database_url: PostgresDsn | None = None
    redis_url: RedisDsn | None = None
    ollama_base_url: AnyHttpUrl | None = None
    embedding_model: str | None = None
    llm_model: str | None = None
    query_rewrite_model: str | None = None
    readiness_timeout_seconds: float = Field(default=3, gt=0)

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        """Parse the comma-separated allow-list in the environment."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url")
    @classmethod
    def require_async_driver(cls, value: PostgresDsn | None) -> PostgresDsn | None:
        """Require the PostgreSQL driver installed by the server."""
        if value and value.scheme != "postgresql+asyncpg":
            raise ValueError("DATABASE_URL must use postgresql+asyncpg")
        return value

    @field_validator("cors_allowed_origins")
    @classmethod
    def reject_wildcard(cls, value: list[str]) -> list[str]:
        """Require explicit origins when credentialed requests are enabled."""
        if "*" in value:
            raise ValueError("CORS origins must be explicit")
        return value
