from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="HackBack Backend", validation_alias="APP_NAME")
    app_env: str = Field(default="local", validation_alias="APP_ENV")
    debug: str = Field(default="false", validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    auth_secret: str = Field(
        default="change-me-before-production",
        validation_alias="AUTH_SECRET",
    )
    cors_origins: str = Field(
        default=(
            "http://localhost:3000,"
            "http://127.0.0.1:3000,"
            "http://localhost:5173,"
            "http://127.0.0.1:5173"
        ),
        validation_alias="CORS_ORIGINS",
    )
    cors_origin_regex: str = Field(
        default=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        validation_alias="CORS_ORIGIN_REGEX",
    )

    pg_host: str = Field(default="db", validation_alias="PG_HOST")
    pg_port: int = Field(default=5432, validation_alias="PG_PORT")
    pg_db: str = Field(default="hackback", validation_alias="PG_DB")
    pg_user: str = Field(default="hackback", validation_alias="PG_USER")
    pg_pass: str = Field(default="hackback", validation_alias="PG_PASS")
    db_pool_size: int = Field(default=5, validation_alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, validation_alias="DB_MAX_OVERFLOW")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.pg_user}:{self.pg_pass}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def debug_enabled(self) -> bool:
        return self.debug.strip().lower() in {"1", "true", "yes", "on", "debug"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
