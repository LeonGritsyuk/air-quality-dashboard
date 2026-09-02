"""Centralized application configuration, loaded from environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "airquality"
    postgres_user: str = "airquality"
    postgres_password: str = "change-me"

    # Sensor
    sensor_url: str = "http://192.168.0.245/measures/current"
    collection_interval_seconds: int = 900  # 15 minutes
    sensor_request_timeout_seconds: float = 5.0

    # Time
    timezone: str = "Europe/Prague"

    # App
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    log_level: str = "INFO"
    store_raw_payload: bool = True

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
