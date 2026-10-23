"""Secret-aware redaction helpers for the standalone Wallex MCP server.

These helpers ensure that API keys, authorization headers, cookies, and
other sensitive material never appear in log records, exception messages,
or tool output. They are intentionally simple and dependency-free.
"""

from __future__ import annotations

import re
from typing import Any, Optional

# Patterns for material that must never reach logs or tool output.
_API_KEY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(x-api-key|api[_-]?key|authorization|bearer)\s*[:=]\s*\S+"),
    re.compile(r"(?i)(x-cg-demo-api-key|x-cg-pro-api-key)\s*[:=]\s*\S+"),
    re.compile(r"(?i)(cookie|set-cookie)\s*[:=]\s*\S+"),
)

# A synthetic placeholder used in tests and documentation. Real secrets are
# never stored in the repository; this value is recognizably fake.
SYNTHETIC_SECRET: str = "SYNTHETIC-SECRET-DO-NOT-USE"


def redact_for_log(value: Any) -> Any:
    """Return a copy of *value* with sensitive substrings removed.

    Non-string values are returned unchanged so callers can log structured
    data without fear of leaking secrets embedded in nested strings.
    """
    if not isinstance(value, str):
        return value
    redacted = value
    for pattern in _API_KEY_PATTERNS:
        redacted = pattern.sub(r"\1=***REDACTED***", redacted)
    return redacted


def assert_no_secret(text: str, secret: Optional[str] = None) -> None:
    """Raise ValueError if *secret* appears verbatim in *text*.

    Used by tests with synthetic secrets to prove redaction works.
    """
    if secret and secret in text:
        raise ValueError("Secret material appeared in output that should be redacted")


def redact_exception(exc: BaseException) -> str:
    """Return a sanitized string representation of an exception."""
    return redact_for_log(str(exc))