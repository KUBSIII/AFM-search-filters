import os
from functools import lru_cache

from pydantic import BaseModel, Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:  # pragma: no cover - fallback for environments without extras
    BaseSettings = None
    SettingsConfigDict = None


if BaseSettings is not None:

    class Settings(BaseSettings):
        app_env: str = Field(default="development", validation_alias="APP_ENV")
        app_host: str = Field(default="127.0.0.1", validation_alias="APP_HOST")
        app_port: int = Field(default=8000, validation_alias="APP_PORT")
        db_url: str = Field(default="sqlite+pysqlite:///./afm_search.db", validation_alias="DB_URL")
        log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

        sync_api_key: str = Field(default="change-me", validation_alias="SYNC_API_KEY")
        tm_http_timeout_s: float = Field(default=10.0, validation_alias="TM_HTTP_TIMEOUT_S")
        tm_max_retries: int = Field(default=2, validation_alias="TM_MAX_RETRIES")
        tm_backoff_base_s: float = Field(default=0.5, validation_alias="TM_BACKOFF_BASE_S")
        tm_rate_limit_rps: float = Field(default=1.0, validation_alias="TM_RATE_LIMIT_RPS")
        sync_max_batch: int = Field(default=100, validation_alias="SYNC_MAX_BATCH")
        sync_max_club_players: int = Field(default=200, validation_alias="SYNC_MAX_CLUB_PLAYERS")

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

else:

    class Settings(BaseModel):
        app_env: str = "development"
        app_host: str = "127.0.0.1"
        app_port: int = 8000
        db_url: str = "sqlite+pysqlite:///./afm_search.db"
        log_level: str = "INFO"

        sync_api_key: str = "change-me"
        tm_http_timeout_s: float = 10.0
        tm_max_retries: int = 2
        tm_backoff_base_s: float = 0.5
        tm_rate_limit_rps: float = 1.0
        sync_max_batch: int = 100
        sync_max_club_players: int = 200


def _settings_from_env() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        db_url=os.getenv("DB_URL", "sqlite+pysqlite:///./afm_search.db"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        sync_api_key=os.getenv("SYNC_API_KEY", "change-me"),
        tm_http_timeout_s=float(os.getenv("TM_HTTP_TIMEOUT_S", "10.0")),
        tm_max_retries=int(os.getenv("TM_MAX_RETRIES", "2")),
        tm_backoff_base_s=float(os.getenv("TM_BACKOFF_BASE_S", "0.5")),
        tm_rate_limit_rps=float(os.getenv("TM_RATE_LIMIT_RPS", "1.0")),
        sync_max_batch=int(os.getenv("SYNC_MAX_BATCH", "100")),
        sync_max_club_players=int(os.getenv("SYNC_MAX_CLUB_PLAYERS", "200")),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    if BaseSettings is None:
        return _settings_from_env()
    return Settings()
