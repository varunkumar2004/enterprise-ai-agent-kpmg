"""Backend selection — controlled by `ASSISTANT_LLM_BACKEND`."""

from __future__ import annotations

import httpx

from app.config import LLMBackend, Settings
from app.services.llm.base import LLMClient
from app.services.llm.ollama import OllamaClient
from app.services.llm.vllm_openai import VLLMOpenAIClient


def create_llm_client(settings: Settings, http_client: httpx.AsyncClient) -> LLMClient:
    """Factory returning a protocol-compliant client."""

    if settings.llm_backend == LLMBackend.OLLAMA:
        return OllamaClient(settings=settings, http_client=http_client)
    if settings.llm_backend == LLMBackend.VLLM_OPENAI:
        return VLLMOpenAIClient(settings=settings, http_client=http_client)
    raise ValueError(f"Unsupported backend: {settings.llm_backend}")
