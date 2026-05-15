from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "Media Operations Platform API"
    app_env: str = "development"
    debug: bool = True
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5433/mediaops",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )
    media_storage_path: str = Field(
        default="../storage/uploads",
        validation_alias="MEDIA_STORAGE_PATH",
    )
    opensearch_enabled: bool = Field(default=True, validation_alias="OPENSEARCH_ENABLED")
    opensearch_url: str = Field(
        default="http://localhost:9200",
        validation_alias="OPENSEARCH_URL",
    )
    opensearch_index: str = Field(
        default="assets",
        validation_alias="OPENSEARCH_INDEX",
    )
    auth_secret_key: str = Field(
        default="change-this-in-production",
        validation_alias="AUTH_SECRET_KEY",
    )
    auth_algorithm: str = Field(default="HS256", validation_alias="AUTH_ALGORITHM")
    auth_access_token_expire_minutes: int = Field(
        default=60,
        validation_alias="AUTH_ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
