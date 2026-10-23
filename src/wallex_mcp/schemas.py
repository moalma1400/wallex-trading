"""Validated, Decimal-safe models for the standalone Wallex MCP server.

The public markets endpoint currently wraps the market list in result.markets.
The client normalizes that transport envelope before these models are applied.
Known fields remain type-checked; additional documented market metadata is
ignored so additive API fields do not break read-only market discovery.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FairPriceModel(BaseModel):
    """Fair-price quote object when supplied by the API."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    ask: str
    bid: str

    @field_validator("ask", "bid")
    @classmethod
    def _validate_decimal_string(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("fair_price fields must be non-empty decimal strings")
        decimal_value = Decimal(value)
        if not decimal_value.is_finite() or decimal_value < 0:
            raise ValueError("fair_price value must be finite and non-negative")
        return value


class MarketMetadataModel(BaseModel):
    """Validated subset of one market entry from Wallex's public markets API."""

    # Wallex adds localized labels and market flags over time. Validate the
    # fields consumed by this project, while tolerating additive metadata.
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    symbol: str
    base_asset: str
    quote_asset: str
    price: str
    is_spot: bool
    is_otc: bool
    is_margin: bool
    is_tmn_based: bool
    is_usdt_based: bool
    amount_precision: int = Field(..., ge=0)
    price_precision: int = Field(..., ge=0)
    flags: list[str] = Field(default_factory=list)
    volume_24h: str
    change_24h: str
    created_at: str
    fair_price: Optional[FairPriceModel] = None

    @field_validator("symbol", "base_asset", "quote_asset")
    @classmethod
    def _validate_nonempty(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("string field must be non-empty")
        return value.strip()

    @field_validator("price", "volume_24h", "change_24h")
    @classmethod
    def _validate_decimal_string(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("decimal field must be a non-empty string")
        decimal_value = Decimal(value)
        if not decimal_value.is_finite():
            raise ValueError("decimal value must be finite")
        return value

    @field_validator("created_at")
    @classmethod
    def _validate_iso_timestamp(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("created_at must be a non-empty ISO-8601 string")
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError("created_at is not valid ISO-8601") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("created_at must include an explicit timezone")
        return value


class MarketsResponseModel(BaseModel):
    """Normalized market response envelope consumed by the MCP tools."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    markets: list[MarketMetadataModel] = Field(..., min_length=1)
    message: str
    success: bool


def decimal_value(value: str) -> Decimal:
    """Convert a validated decimal string to Decimal without re-validating."""
    return Decimal(value)
