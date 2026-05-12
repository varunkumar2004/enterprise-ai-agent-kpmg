"""Chat completion schemas — OpenAI-compatible subset for IDE interoperability."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str | None = Field(default=None)
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)


class ChatCompletionChoiceDelta(BaseModel):
    role: str | None = None
    content: str | None = None


class ChatCompletionChunk(BaseModel):
    """Streaming chunk compatible with OpenAI SSE payloads."""

    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[dict[str, object]]
