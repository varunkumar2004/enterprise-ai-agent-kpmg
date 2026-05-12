"""Operational probes — keep lightweight for kubelet."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Liveness probe")
async def healthz() -> dict[str, Any]:
    return {"status": "ok"}


@router.get("/readyz", summary="Readiness probe")
async def readyz() -> dict[str, Any]:
    """
    Extend with dependency checks (DB, Redis, inference warm) as services appear.

    Banking deployments often split `/readyz` into sync checks vs expensive inference pings.
    """

    return {"status": "ready"}
