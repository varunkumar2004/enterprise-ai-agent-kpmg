"""Request-scoped context using contextvars (async-safe)."""

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Final

_REQUEST_ID: Final = ContextVar[str | None]("request_id", default=None)


def set_request_id(value: str | None) -> None:
    _REQUEST_ID.set(value)


def get_request_id() -> str | None:
    return _REQUEST_ID.get()


@dataclass(frozen=True, slots=True)
class Principal:
    """Authenticated subject — mapped from JWT claims."""

    subject: str
    roles: frozenset[str]
    claims: dict[str, object]


_CURRENT_PRINCIPAL: Final = ContextVar[Principal | None]("principal", default=None)


def set_principal(principal: Principal | None) -> None:
    _CURRENT_PRINCIPAL.set(principal)


def get_principal() -> Principal | None:
    return _CURRENT_PRINCIPAL.get()
