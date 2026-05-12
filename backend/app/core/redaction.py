"""Best-effort secret redaction before logging or forwarding."""

from __future__ import annotations

import re

_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+"), r"\1=<redacted>"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer <redacted>"),
)


def redact_text(text: str) -> str:
    """Apply conservative regex redaction — extend with ML/classifiers as needed."""

    out = text
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    return out
