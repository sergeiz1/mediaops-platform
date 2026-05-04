from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "Media Operations Platform API"
    app_env: str = "development"
    debug: bool = True
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/mediaops",
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
