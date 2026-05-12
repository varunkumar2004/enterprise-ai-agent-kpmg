from enum import StrEnum
from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMBackend(StrEnum):
    """Inference backend selector — swap without router changes."""

    OLLAMA = "ollama"
    VLLM_OPENAI = "vllm_openai"


class Settings(BaseSettings):
    """
    12-factor configuration. Prefix ASSISTANT_* maps env vars for Kubernetes clarity.

    Secrets MUST come from environment / secret stores — never bake into images.
    """

    model_config = SettingsConfigDict(
        env_prefix="ASSISTANT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "assistant-api"
    environment: str = Field(default="development", description="e.g. development|staging|production")

    api_prefix: str = "/api"
    api_version: str = "v1"

    docs_enabled: bool = True
    openapi_url: str | None = "/openapi.json"

    cors_allow_origins: list[str] = Field(default_factory=list)
    cors_allow_credentials: bool = False

    trusted_hosts: list[str] | None = Field(default=None)

    auth_enabled: bool = Field(
        default=False,
        description="When False, requests run under anonymous principal (local dev only).",
    )
    jwt_audience: str | None = Field(default=None)
    jwt_issuer: str | None = Field(default=None)
    jwt_algorithms: list[str] = Field(default_factory=lambda: ["HS256"])
    jwt_secret_key: str | None = Field(
        default=None,
        description="HS256 dev secret — prefer JWKS (future) in production.",
    )

    llm_backend: LLMBackend = LLMBackend.OLLAMA
    ollama_base_url: HttpUrl = Field(default="http://127.0.0.1:11434")
    ollama_timeout_seconds: float = 120.0

    vllm_openai_base_url: HttpUrl | None = Field(
        default=None,
        description="OpenAI-compatible base URL for vLLM, e.g. http://vllm:8000/v1",
    )
    vllm_timeout_seconds: float = 120.0

    default_model: str = "deepseek-coder"

    audit_log_body_hashes: bool = Field(
        default=True,
        description="Emit SHA256 of bodies when prompts are not logged verbatim.",
    )

    max_request_body_bytes: int = 2 * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton suitable for FastAPI dependency injection."""

    return Settings()
