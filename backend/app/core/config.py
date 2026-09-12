"""
Shared application settings.

NOTE (Member 1 / lease story): this file is listed as a shared/team-agreement
file in the frozen design contract (Project Design Document, section 25).
It is being proposed here as the initial skeleton because nothing existed yet
on `main` and the frozen integration sequence (section 26) has the Lease
story building first. Env var names below are copied verbatim from the
contract's section 15 - nothing invented. Please review before merging.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Backend
    app_name: str = "meridian-residences"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql://user:password@localhost:5432/meridian_residences"
    cors_origins: str = "http://localhost:5173"

    # Authentication / security
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Observability
    log_level: str = "INFO"


settings = Settings()
