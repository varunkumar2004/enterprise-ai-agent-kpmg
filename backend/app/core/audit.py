"""Structured audit events — stdout-first for Fluent Bit / SIEM ingestion."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

import structlog

from app.core.request_context import get_principal, get_request_id

logger = structlog.get_logger("audit")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def emit_audit_event(
    *,
    action: str,
    feature: str,
    model: str | None = None,
    outcome: str = "success",
    metadata: dict[str, Any] | None = None,
    body_fingerprint: str | None = None,
) -> None:
    """
    Emit a single JSON line suitable for centralized logging.

    Banking posture: default path avoids storing raw prompts/code in audit logs.
    Use body_hash when compliance allows fingerprinting without retention.
    """

    principal = get_principal()
    event: dict[str, Any] = {
        "event_type": "assistant.audit",
        "event_id": str(uuid.uuid4()),
        "ts_ms": int(time.time() * 1000),
        "action": action,
        "feature": feature,
        "outcome": outcome,
        "request_id": get_request_id(),
        "subject": principal.subject if principal else None,
        "roles": sorted(principal.roles) if principal else [],
        "model": model,
    }
    if body_fingerprint:
        event["body_sha256"] = body_fingerprint
    if metadata:
        event["metadata"] = metadata
    logger.info(json.dumps(event, separators=(",", ":"), sort_keys=True))


def fingerprint_payload(payload: str) -> str:
    return _sha256_text(payload)
