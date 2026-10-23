"""Safe configuration for the standalone Wallex MCP server.

Only explicitly allowlisted GET endpoints can be called. Account endpoints
require WALLEX_API_KEY; no account-changing route is included.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

WALLEX_OFFICIAL_HOST: Final[str] = "api.wallex.ir"
MARKETS_PATH: Final[str] = "/hector/web/v1/markets"
BALANCES_PATH: Final[str] = "/v1/account/balances"
OPEN_ORDERS_PATH: Final[str] = "/v1/account/openOrders"

DEFAULT_TIMEOUT_SECONDS: Final[float] = 10.0
DEFAULT_MAX_RESPONSE_BYTES: Final[int] = 5 * 1024 * 1024
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
    """Immutable allowlist of permitted read-only endpoints."""

    entries: tuple[EndpointAllowlistEntry, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))
        if any(entry.method.upper() != "GET" for entry in self.entries):
            raise ValueError("EndpointAllowlist may only contain safe GET endpoints")
        if any(not entry.host or not entry.path.startswith("/") for entry in self.entries):
            raise ValueError("Allowlist entries require an exact host and absolute path")

    @classmethod
    def default(cls) -> "EndpointAllowlist":
        return cls(entries=(
            EndpointAllowlistEntry(
                method="GET", host=WALLEX_OFFICIAL_HOST, path=MARKETS_PATH,
                requires_key=False, description="Verified public Spot market metadata.",
            ),
            EndpointAllowlistEntry(
                method="GET", host=WALLEX_OFFICIAL_HOST, path=BALANCES_PATH,
                requires_key=True, description="Authenticated read-only main-account balances.",
            ),
            EndpointAllowlistEntry(
                method="GET", host=WALLEX_OFFICIAL_HOST, path=OPEN_ORDERS_PATH,
                requires_key=True, description="Authenticated read-only open Spot orders.",
            ),
        ))

    def is_allowed(self, method: str, host: str, path: str) -> bool:
        normalized_method = method.upper()
        normalized_host = host.lower()
        # Query parameters are not included in the path passed to this method.
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
