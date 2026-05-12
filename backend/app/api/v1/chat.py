"""Streaming chat completions — OpenAI-style SSE for IDE clients."""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Header, Response
from fastapi.responses import StreamingResponse

from app.api.deps import LLMClientDep, SettingsDep
from app.core.audit import emit_audit_event, fingerprint_payload
from app.core.rbac import CHAT_COMPLETE, require_permission
from app.schemas.chat import ChatCompletionRequest
from app.services.llm.base import StreamDelta

router = APIRouter(tags=["chat"])


def _sse_pack(payload: dict[str, object]) -> str:
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


async def _openai_sse_chunks(
    *,
    body: ChatCompletionRequest,
    llm_client,
    model_name: str,
    feature: str,
) -> AsyncIterator[str]:
    chunk_id = f"chatcmpl-{uuid.uuid4()}"
    created = int(time.time())

    async for delta in llm_client.stream_chat(
        model=model_name,
        messages=body.messages,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
    ):
        delta: StreamDelta
        if delta.done:
            yield _sse_pack(
                {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model_name,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
            )
            yield "data: [DONE]\n\n"
            emit_audit_event(action="chat.completion", feature=feature, model=model_name, outcome="success")
            return

        if delta.content:
            yield _sse_pack(
                {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model_name,
                    "choices": [{"index": 0, "delta": {"content": delta.content}}],
                }
            )


@router.post(
    "/chat/completions",
    dependencies=[Depends(require_permission(CHAT_COMPLETE))],
)
async def chat_completions(
    body: ChatCompletionRequest,
    settings: SettingsDep,
    llm_client: LLMClientDep,
    x_assistant_feature: str | None = Header(default=None, alias="X-Assistant-Feature"),
) -> Response:
    """
    OpenAI-compatible streaming endpoint.

    Security note: prompts are fingerprinted for audit — configure retention policies separately.
    """

    model_name = body.model or settings.default_model
    feature = x_assistant_feature or "chat"

    fingerprint_source = json.dumps([m.model_dump() for m in body.messages], sort_keys=True)
    emit_audit_event(
        action="chat.completion.request",
        feature=feature,
        model=model_name,
        body_fingerprint=fingerprint_payload(fingerprint_source),
        metadata={"stream": body.stream},
    )

    if not body.stream:
        collected: list[str] = []
        async for delta in llm_client.stream_chat(
            model=model_name,
            messages=body.messages,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        ):
            if delta.content:
                collected.append(delta.content)
            if delta.done:
                break
        text = "".join(collected)
        emit_audit_event(action="chat.completion", feature=feature, model=model_name, outcome="success")
        return Response(
            media_type="application/json",
            content=json.dumps(
                {
                    "id": f"chatcmpl-{uuid.uuid4()}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model_name,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": text},
                            "finish_reason": "stop",
                        }
                    ],
                },
                separators=(",", ":"),
            ),
        )

    generator = _openai_sse_chunks(
        body=body,
        llm_client=llm_client,
        model_name=model_name,
        feature=feature,
    )
    return StreamingResponse(generator, media_type="text/event-stream")
