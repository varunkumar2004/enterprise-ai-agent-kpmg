"""Role → permission mapping — centralize to avoid sprawl across routers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import Depends

from app.core.errors import AssistantHTTPException
from app.core.request_context import Principal, get_principal


@dataclass(frozen=True, slots=True)
class Permission:
    name: str


# Canonical permission strings — stable API contract for audits / policies.
CHAT_COMPLETE = Permission("chat:complete")
EXPLAIN_CODE = Permission("explain:use")
DEBUG_ASSIST = Permission("debug:use")
ADMIN_POLICY = Permission("admin:policy")

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "assistant.user": frozenset(
        {
            CHAT_COMPLETE.name,
            EXPLAIN_CODE.name,
            DEBUG_ASSIST.name,
        }
    ),
    "assistant.admin": frozenset(
        {
            CHAT_COMPLETE.name,
            EXPLAIN_CODE.name,
            DEBUG_ASSIST.name,
            ADMIN_POLICY.name,
        }
    ),
}


def principal_permissions(principal: Principal) -> frozenset[str]:
    perms: set[str] = set()
    for role in principal.roles:
        perms |= set(ROLE_PERMISSIONS.get(role, frozenset()))
    return frozenset(perms)


def require_permission(permission: Permission) -> Callable[..., Principal]:
    """FastAPI dependency enforcing RBAC on a route."""

    def _inner(principal: Principal = Depends(get_authenticated_principal)) -> Principal:
        allowed = principal_permissions(principal)
        if permission.name not in allowed:
            raise AssistantHTTPException(
                status_code=403,
                title="Forbidden",
                detail=f"Missing permission: {permission.name}",
                extensions={"permission": permission.name},
            )
        return principal

    return _inner


def get_authenticated_principal() -> Principal:
    principal = get_principal()
    if principal is None:
        raise AssistantHTTPException(status_code=401, title="Unauthorized", detail="Missing principal")
    return principal
