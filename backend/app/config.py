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
    s3_endpoint: str = Field("http://localhost:9000", validation_alias="S3_ENDPOINT")
    s3_access_key: str = Field("minio", validation_alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field("minio12345", validation_alias="S3_SECRET_KEY")
    s3_bucket: str = Field("dpa-guard", validation_alias="S3_BUCKET")
    s3_region: str = Field("us-east-1", validation_alias="S3_REGION")
    s3_secure: bool = Field(False, validation_alias="S3_SECURE")
    redis_url: str = Field("redis://localhost:6379/0", validation_alias="REDIS_URL")
    max_file_size_mb: int = Field(25, validation_alias="MAX_FILE_SIZE_MB")
    text_density_threshold: float = Field(0.1, validation_alias="TEXT_DENSITY_THRESHOLD")
    use_llm_classification: bool = Field(False, validation_alias="USE_LLM_CLASSIFICATION")
    classify_rules_min_conf: float = Field(0.5, validation_alias="CLASSIFY_RULES_MIN_CONF")
    classify_top_k: int = Field(3, validation_alias="CLASSIFY_TOP_K")
    playbook_yaml_path: str = Field(
        "playbook/rules.yaml", validation_alias="PLAYBOOK_YAML_PATH"
    )
    use_llm_eval: bool = Field(False, validation_alias="USE_LLM_EVAL")
    openai_api_key: str | None = Field(None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4.1-mini", validation_alias="OPENAI_MODEL")
    llm_max_input_chars: int = Field(60000, validation_alias="LLM_MAX_INPUT_CHARS")
    llm_temperature: float = Field(0.2, validation_alias="LLM_TEMPERATURE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
