"""JWT authentication — HS256 for controlled environments; extend with JWKS."""

from __future__ import annotations

import uuid

import structlog
from jose import JWTError, jwt

from app.config import Settings
from app.core.errors import AssistantHTTPException
from app.core.request_context import Principal

logger = structlog.get_logger(__name__)


def _normalize_roles(raw: object) -> frozenset[str]:
    if isinstance(raw, str):
        return frozenset({raw})
    if isinstance(raw, list):
        return frozenset(str(x) for x in raw)
    return frozenset()


def decode_jwt_bearer(token: str, settings: Settings) -> Principal:
    """
    Validate Bearer JWT and map to Principal.

    Production hardening:
    - Prefer JWKS (`jwt.decode` with PyJWKClient) + rotating keys.
    - Enforce `aud`, `iss`, `nbf`, `exp` strictly.
    """
    if not settings.jwt_secret_key:
        logger.error("jwt_decode_failed", reason="jwt_secret_key_missing")
        raise AssistantHTTPException(
            status_code=500,
            title="Server Misconfiguration",
            detail="JWT validation enabled but ASSISTANT_JWT_SECRET_KEY not set",
        )
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=settings.jwt_algorithms,
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"verify_aud": settings.jwt_audience is not None},
        )
    except JWTError as exc:
        logger.info("jwt_decode_failed", error=str(exc))
        raise AssistantHTTPException(
            status_code=401,
            title="Unauthorized",
            detail="Invalid or expired token",
        ) from exc

    subject = str(payload.get("sub") or uuid.uuid4())
    realm = payload.get("realm_access")
    if isinstance(realm, dict) and "roles" in realm:
        roles_raw = realm.get("roles")
    else:
        roles_raw = payload.get("roles")
    roles = _normalize_roles(roles_raw if roles_raw is not None else [])
    return Principal(subject=subject, roles=roles, claims=dict(payload))


def anonymous_development_principal() -> Principal:
    """Explicit anonymous principal for locked-down dev — NOT for production."""

    return Principal(subject="anonymous", roles=frozenset({"assistant.user"}), claims={})
