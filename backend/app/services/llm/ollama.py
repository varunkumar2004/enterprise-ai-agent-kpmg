"""Ollama HTTP adapter — streams `/api/chat` NDJSON."""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx
import structlog

from app.config import Settings
from app.schemas.chat import ChatMessage
from app.services.llm.base import StreamDelta

logger = structlog.get_logger(__name__)


class OllamaClient:
    def __init__(self, *, settings: Settings, http_client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http = http_client

    async def stream_chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float | None,
        max_tokens: int | None,
    ) -> AsyncIterator[StreamDelta]:
        url = f"{str(self._settings.ollama_base_url).rstrip('/')}/api/chat"
        payload: dict[str, object] = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "stream": True,
        }
        options: dict[str, object] = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if options:
            payload["options"] = options

        async with self._http.stream("POST", url, json=payload, timeout=self._settings.ollama_timeout_seconds) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("ollama_bad_chunk", line=line[:200])
                    continue
                if data.get("done"):
                    yield StreamDelta(content=None, done=True)
                    return
                message = data.get("message") or {}
                content = message.get("content")
                if isinstance(content, str) and content:
                    yield StreamDelta(content=content, done=False)

        yield StreamDelta(content=None, done=True)
