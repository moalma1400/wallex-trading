"""Safe configuration for the standalone Wallex MCP server.

The endpoint allowlist is the single source of truth for which upstream
Wallex hosts and paths this server may contact. Nothing outside the
allowlist is reachable, and no caller-supplied URL, header, or method can
expand it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


WALLEX_OFFICIAL_HOST: Final[str] = "api.wallex.ir"

# Verified public, read-only Spot market-data endpoint.
# Source: MARKETS (https://developers.wallex.ir/docs/basic-services-markets),
# cross-checked against MOD-GENERATED-GET-MARKETS.
MARKETS_PATH: Final[str] = "/hector/web/v1/markets"

# Conservative operational bounds. These are safety defaults, not
# documented Wallex limits; the official rate limit is not published
# numerically, so we stay well under any plausible ceiling.
DEFAULT_TIMEOUT_SECONDS: Final[float] = 10.0
DEFAULT_MAX_RESPONSE_BYTES: Final[int] = 5 * 1024 * 1024  # 5 MiB
DEFAULT_MAX_RETRIES: Final[int] = 2
DEFAULT_BACKOFF_SECONDS: Final[float] = 0.5


@dataclass(frozen=True)
class EndpointAllowlistEntry:
    method: str
    host: str
    path: str
    requires_key: bool = False
    description: str = ""


@dataclass(frozen=True)
class EndpointAllowlist:
    """Immutable allowlist of permitted upstream endpoints."""

    entries: tuple[EndpointAllowlistEntry, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))
        methods = {entry.method for entry in self.entries}
        if any(method.upper() != "GET" for method in methods):
            raise ValueError("EndpointAllowlist may only contain safe GET endpoints")

    @classmethod
    def default(cls) -> "EndpointAllowlist":
        return cls(
            entries=(
                EndpointAllowlistEntry(
                    method="GET",
                    host=WALLEX_OFFICIAL_HOST,
                    path=MARKETS_PATH,
                    requires_key=False,
                    description="Verified public Spot market metadata list.",
                ),
            )
        )

    def is_allowed(self, method: str, host: str, path: str) -> bool:
        normalized_method = method.upper()
        normalized_host = host.lower()
        normalized_path = path if path.startswith("/") else "/" + path
        return any(
            entry.method.upper() == normalized_method
            and entry.host.lower() == normalized_host
            and entry.path == normalized_path
            for entry in self.entries
        )

    def requires_key(self, method: str, host: str, path: str) -> bool:
        normalized_method = method.upper()
        normalized_host = host.lower()
        normalized_path = path if path.startswith("/") else "/" + path
        for entry in self.entries:
            if (
                entry.method.upper() == normalized_method
                and entry.host.lower() == normalized_host
                and entry.path == normalized_path
            ):
                return entry.requires_key
        return False


DEFAULT_ALLOWLIST: Final[EndpointAllowlist] = EndpointAllowlist.default()