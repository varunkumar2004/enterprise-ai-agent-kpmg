"""Abstract inference boundary — enables Ollama ↔ vLLM swaps without router churn."""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Protocol

from app.schemas.chat import ChatMessage


@dataclass(frozen=True, slots=True)
class StreamDelta:
    """Normalized streaming token — routers serialize to OpenAI SSE."""

    content: str | None = None
    done: bool = False


class LLMClient(Protocol):
    """Inference client contract."""

    async def stream_chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float | None,
        max_tokens: int | None,
    ) -> AsyncIterator[StreamDelta]:
        """Yield incremental content until terminal delta with done=True."""
