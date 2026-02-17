"""Application settings loaded from environment variables and .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Datadog connection settings.

    Reads DD_API_KEY, DD_APP_KEY, and DD_SITE from the environment
    or a .env file in the project root.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    dd_api_key: str
    dd_app_key: str
    dd_site: str = "datadoghq.com"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Returns:
        The validated application settings.

    Raises:
        pydantic.ValidationError: If required env vars are missing.
    """
    return Settings()
