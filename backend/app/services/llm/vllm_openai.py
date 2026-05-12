"""vLLM OpenAI-compatible streaming (`/v1/chat/completions`)."""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx
import structlog

from app.config import Settings
from app.schemas.chat import ChatMessage
from app.services.llm.base import StreamDelta

logger = structlog.get_logger(__name__)


class VLLMOpenAIClient:
    """Thin adapter — mirrors OpenAI SDK wire format for portability."""

    def __init__(self, *, settings: Settings, http_client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http = http_client
        if not settings.vllm_openai_base_url:
            raise ValueError("ASSISTANT_VLLM_OPENAI_BASE_URL required for vLLM backend")

    async def stream_chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float | None,
        max_tokens: int | None,
    ) -> AsyncIterator[StreamDelta]:
        base = str(self._settings.vllm_openai_base_url).rstrip("/")
        url = f"{base}/chat/completions"
        payload: dict[str, object] = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "stream": True,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        headers = {"Accept": "text/event-stream"}
        async with self._http.stream(
            "POST",
            url,
            json=payload,
            headers=headers,
            timeout=self._settings.vllm_timeout_seconds,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                if line.startswith("data:"):
                    data_str = line.removeprefix("data:").strip()
                    if data_str == "[DONE]":
                        yield StreamDelta(content=None, done=True)
                        return
                    try:
                        outer = json.loads(data_str)
                    except json.JSONDecodeError:
                        logger.warning("vllm_bad_chunk", line=line[:200])
                        continue
                    choices = outer.get("choices") or []
                    if not choices:
                        continue
                    delta = (choices[0] or {}).get("delta") or {}
                    piece = delta.get("content")
                    finish = (choices[0] or {}).get("finish_reason")
                    if isinstance(piece, str) and piece:
                        yield StreamDelta(content=piece, done=False)
                    if finish:
                        yield StreamDelta(content=None, done=True)
                        return

        yield StreamDelta(content=None, done=True)
