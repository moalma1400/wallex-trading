# MCP adapter for Wallex market data via Smart98.
# Smart98 is the mandatory intermediary between the trading application and Wallex.
# All market data flows through the Smart98 Wallex MCP connector exclusively.

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple


class DataSource(Enum):
    """Provenance of market data."""
    MCP_SMART98 = auto()


@dataclass(frozen=True)
class MarketMeta:
    """Normalized metadata for one spot market."""
    symbol: str
    base_asset: str
    quote_asset: str
    is_spot: bool
    amount_precision: int
    price_precision: int
    min_notional: Optional[Decimal]
    is_risky: bool
    is_tmn_based: bool
    is_usdt_based: bool
    created_at: datetime.datetime
    source: DataSource = DataSource.MCP_SMART98


@dataclass(frozen=True)
class Candle:
    """One OHLCV candle in UTC."""
    timestamp: datetime.datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    symbol: str
    interval: str
    source: DataSource = DataSource.MCP_SMART98
    retrieved_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


@dataclass(frozen=True)
class Ticker:
    """Current market ticker data (point-in-time)."""
    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume_24h: Decimal
    change_24h: Decimal
    high_24h: Decimal
    low_24h: Decimal
    retrieved_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    source: DataSource = DataSource.MCP_SMART98


@dataclass(frozen=True)
class OrderBookLevel:
    price: Decimal
    quantity: Decimal


@dataclass(frozen=True)
class OrderBook:
    symbol: str
    asks: Tuple[OrderBookLevel, ...]
    bids: Tuple[OrderBookLevel, ...]
    retrieved_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    source: DataSource = DataSource.MCP_SMART98


@dataclass(frozen=True)
class PublicTrade:
    symbol: str
    price: Decimal
    quantity: Decimal
    is_buy: bool
    timestamp: datetime.datetime
    source: DataSource = DataSource.MCP_SMART98


class Eligibility(Enum):
    ELIGIBLE = auto()
    UNKNOWN = auto()
    PROHIBITED = auto()
    NOT_SPOT = auto()
    NO_METADATA = auto()
    STALE = auto()


@dataclass(frozen=True)
class EligibilityResult:
    market: str
    eligibility: Eligibility
    reason: str = ""


class MCPError(Exception):
    """Base exception for Smart98 MCP adapter failures."""
    def __init__(self, message: str, tool: str, raw: Any = None):
        self.tool = tool
        self.raw = raw
        super().__init__(f"[{tool}] {message}")


class MCPTimeout(MCPError):
    """MCP call did not complete within the expected time."""


class InvalidDataError(ValueError):
    """Data from MCP failed validation."""


class StaleDataError(InvalidDataError):
    """Data exceeds maximum acceptable age."""


class MarketDataProvider:
    """Provider-agnostic interface for market data ingestion."""

    def get_markets(self) -> List[MarketMeta]:
        raise NotImplementedError

    def get_candles(
        self,
        symbol: str,
        interval: str,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> List[Candle]:
        raise NotImplementedError

    def get_order_book(self, symbol: str) -> OrderBook:
        raise NotImplementedError

    def get_recent_trades(self, symbol: str) -> List[PublicTrade]:
        raise NotImplementedError

    def get_ticker(self, symbol: str) -> Ticker:
        raise NotImplementedError
