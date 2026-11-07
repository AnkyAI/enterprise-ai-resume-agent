from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="RESUME_", env_file=".env", extra="ignore", case_sensitive=False
    )

    app_name: str = "Enterprise AI Resume Agent"
    environment: str = "development"
    log_level: str = "INFO"
    api_keys: Annotated[tuple[str, ...], NoDecode] = ("dev-secret-key",)
    rate_limit_requests: int = Field(default=60, ge=1, le=10_000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3_600)
    max_request_bytes: int = Field(default=100_000, ge=1_000, le=1_000_000)

    @field_validator("api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, value: object) -> object:
        if isinstance(value, str):
            keys = tuple(key.strip() for key in value.split(",") if key.strip())
            if not keys:
                raise ValueError("At least one API key is required")
            return keys
        return value

    @model_validator(mode="after")
    def reject_development_key_in_production(self) -> "Settings":
        if self.environment.lower() == "production" and "dev-secret-key" in self.api_keys:
            raise ValueError("RESUME_API_KEYS must be changed in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
