from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        "postgresql+psycopg2://postgres:postgres@localhost:5432/dpa_guard",
        validation_alias="DATABASE_URL",
    )
    app_env: str = Field("dev", validation_alias="APP_ENV")
    app_name: str = Field("dpa-guard", validation_alias="APP_NAME")
    app_version: str = Field("0.1.0", validation_alias="APP_VERSION")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
