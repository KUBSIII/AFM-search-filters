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


def _settings_from_env() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        db_url=os.getenv("DB_URL", "sqlite+pysqlite:///./afm_search.db"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    if BaseSettings is None:
        return _settings_from_env()
    return Settings()
