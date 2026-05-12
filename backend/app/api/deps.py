"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.config import Settings, get_settings
from app.services.llm.base import LLMClient


def settings_dep() -> Settings:
    return get_settings()


SettingsDep = Annotated[Settings, Depends(settings_dep)]


def get_llm_client(request: Request) -> LLMClient:
    client = getattr(request.app.state, "llm_client", None)
    if client is None:
        raise RuntimeError("LLM client not initialized — application lifespan misconfigured")
    return client


LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]
