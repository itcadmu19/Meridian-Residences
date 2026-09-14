from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Shared backend configuration (Design Contract §15, §25). Common env vars only."""

    app_name: str = "meridian-residences"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg2://meridian:change-me@localhost:5432/meridian_residences"
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    jwt_secret_key: str = "do-not-commit"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Local Ollama server used for the Story 2 invoice payment-insight feature (no API key needed).
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


settings = Settings()
