"""RFC7807 Problem Details style errors."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProblemDetail(BaseModel):
    """application/problem+json compatible payload."""

    model_config = ConfigDict(extra="allow")

    type: str = Field(default="about:blank")
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None


class AssistantHTTPException(Exception):
    """Maps to HTTP Problem+json responses."""

    def __init__(
        self,
        *,
        status_code: int,
        title: str,
        detail: str | None = None,
        problem_type: str = "about:blank",
        extensions: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(title)
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.problem_type = problem_type
        self.extensions = extensions


def problem_from_exception(exc: AssistantHTTPException, instance: str | None = None) -> ProblemDetail:
    payload: dict[str, Any] = {
        "type": exc.problem_type,
        "title": exc.title,
        "status": exc.status_code,
        "detail": exc.detail,
        "instance": instance,
    }
    if exc.extensions:
        payload.update(exc.extensions)
    return ProblemDetail.model_validate(payload)
