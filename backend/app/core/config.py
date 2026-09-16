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

    # Invoice AI insight feature (ported from feature-annapoorna) - local
    # Ollama server, no API key needed. If unreachable, invoice_insight_agent
    # falls back to a deterministic rule-based insight. Explicit 127.0.0.1
    # (not "localhost") - "localhost" resolves IPv6 first on this stack,
    # which hangs until the connect timeout before even trying IPv4,
    # roughly doubling the fallback delay (see ai/ollama_client.py).
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:3b"

    # AI Assistant feature (ported from feature-Sanjana) - optional cloud
    # LLM path, only attempted if llm_api_key is set (see assistant_service.
    # generate_answer's 3-tier fallback: cloud LLM -> local Ollama ->
    # deterministic extraction). Names match the placeholders already
    # reserved in .env.example.
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None


settings = Settings()
