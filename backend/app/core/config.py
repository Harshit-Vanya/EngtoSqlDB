"""Application configuration via environment variables.

Uses pydantic-settings to load and validate all configuration from
environment variables or .env file. Every external service is configurable.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "ai-text-to-sql"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_version: str = "0.1.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # --- Authentication ---
    jwt_secret_key: str = "CHANGE_ME_GENERATE_A_RANDOM_256_BIT_KEY"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # --- Primary Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/analytics_platform"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False

    # --- Analytics Database ---
    analytics_database_url: str = (
        "postgresql+asyncpg://readonly_user:readonly_pass@localhost:5432/analytics_db"
    )

    # --- LLM Provider ---
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048
    llm_timeout_seconds: int = 30

    # --- Embedding Provider ---
    embedding_provider: str = "openai"
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # --- Vector Store ---
    vector_store_provider: str = "chromadb"
    vector_store_url: str = "http://localhost:8001"
    vector_store_collection: str = "schema_embeddings"

    # --- Query Safety ---
    max_query_cost: int = 1_000_000
    max_execution_time_seconds: int = 30
    max_rows_returned: int = 1000
    max_retries: int = 3

    # --- Rate Limiting ---
    rate_limit_requests_per_minute: int = 60
    rate_limit_queries_per_hour: int = 100

    # --- Observability ---
    otel_exporter_endpoint: str = "http://localhost:4317"
    enable_tracing: bool = False
    enable_metrics: bool = True

    # --- CORS ---
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS origins string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    # Convenience: sync database URL for Alembic
    @property
    def sync_database_url(self) -> str:
        """Convert async URL to sync for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings instance."""
    return Settings()
