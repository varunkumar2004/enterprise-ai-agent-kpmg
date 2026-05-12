"""Cross-cutting middleware — request correlation and authentication."""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings
from app.core.errors import AssistantHTTPException, problem_from_exception
from app.core.request_context import Principal, set_principal, set_request_id
from app.core.security import anonymous_development_principal, decode_jwt_bearer

logger = structlog.get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign request ID + optional JWT principal before routing."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        header_rid = request.headers.get("x-request-id")
        rid = header_rid or str(uuid.uuid4())
        set_request_id(rid)

        principal: Principal | None = None
        if settings.auth_enabled:
            auth = request.headers.get("authorization")
            if auth and auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1].strip()
                try:
                    principal = decode_jwt_bearer(token, settings)
                except AssistantHTTPException as exc:
                    problem = problem_from_exception(exc, instance=str(request.url))
                    return JSONResponse(
                        status_code=exc.status_code,
                        content=problem.model_dump(mode="json", exclude_none=True),
                        media_type="application/problem+json",
                        headers={"x-request-id": rid},
                    )
            else:
                principal = None
        else:
            principal = anonymous_development_principal()

        set_principal(principal)

        response = await call_next(request)
        response.headers["x-request-id"] = rid
        return response


def configure_structlog() -> None:
    """JSON logs for machine ingestion — compatible with Loki/ELK stacks."""

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        cache_logger_on_first_use=True,
    )
