"""FastAPI application factory — wiring order matches enterprise middleware guidance."""

from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.errors import AssistantHTTPException, problem_from_exception
from app.core.middleware import RequestContextMiddleware, configure_structlog
from app.services.llm.factory import create_llm_client

logger = structlog.get_logger(__name__)


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject oversized payloads early — complements ingress limits."""

    def __init__(self, app, max_body_bytes: int) -> None:
        super().__init__(app)
        self._max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit():
            if int(content_length) > self._max_body_bytes:
                problem = problem_from_exception(
                    AssistantHTTPException(
                        status_code=413,
                        title="Payload Too Large",
                        detail="Request body exceeds configured maximum",
                    ),
                    instance=str(request.url),
                )
                return JSONResponse(
                    status_code=413,
                    content=problem.model_dump(mode="json", exclude_none=True),
                    media_type="application/problem+json",
                )
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage shared httpx pool — critical for streaming throughput."""

    configure_structlog()
    settings = get_settings()
    limits = httpx.Limits(max_connections=256, max_keepalive_connections=64)
    timeout = httpx.Timeout(connect=5.0, read=None, write=30.0, pool=5.0)
    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        app.state.http_client = client
        app.state.llm_client = create_llm_client(settings, client)
        logger.info("startup_complete", environment=settings.environment)
        yield
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Enterprise Coding Assistant API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url=settings.openapi_url if settings.docs_enabled else None,
    )

    if settings.trusted_hosts:
        application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

    if settings.cors_allow_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["authorization", "content-type", "x-request-id", "x-assistant-feature"],
        )

    application.add_middleware(MaxBodySizeMiddleware, max_body_bytes=settings.max_request_body_bytes)
    application.add_middleware(RequestContextMiddleware)

    @application.exception_handler(AssistantHTTPException)
    async def assistant_http_exception_handler(request: Request, exc: AssistantHTTPException) -> JSONResponse:
        problem = problem_from_exception(exc, instance=str(request.url))
        return JSONResponse(
            status_code=exc.status_code,
            content=problem.model_dump(mode="json", exclude_none=True),
            media_type="application/problem+json",
        )

    prefix = f"{settings.api_prefix}/{settings.api_version}"
    application.include_router(api_router, prefix=prefix)

    return application


app = create_app()
