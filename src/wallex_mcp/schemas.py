"""Validated, Decimal-safe models for the standalone Wallex MCP server.

These models describe the officially documented response shape of
``GET https://api.wallex.ir/hector/web/v1/markets`` (source: MARKETS,
https://developers.wallex.ir/docs/basic-services-markets). Field names,
types and optionality follow the official documentation exactly; nothing
here is inferred or relaxed.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FairPriceModel(BaseModel):
    """Fair-price quote object as documented for market metadata."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    ask: str = Field(..., description="Best ask price as a decimal string.")
    bid: str = Field(..., description="Best bid price as a decimal string.")

    @field_validator("ask", "bid")
    @classmethod
    def _validate_decimal_string(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("fair_price fields must be non-empty decimal strings")
        try:
            decimal_value = Decimal(value)
        except Exception as exc:  # InvalidOperation, ValueError
            raise ValueError(f"fair_price value is not a valid decimal: {value!r}") from exc
        if not decimal_value.is_finite() or decimal_value < 0:
            raise ValueError(f"fair_price value must be finite and non-negative: {value!r}")
        return value


class MarketMetadataModel(BaseModel):
    """One market entry from the official markets endpoint."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    symbol: str = Field(..., description="Market symbol, e.g. USDTTMN.")
    base_asset: str = Field(..., description="Trading asset, e.g. USDT.")
    quote_asset: str = Field(..., description="Quote asset, e.g. TMN.")
    price: str = Field(..., description="Last price as a decimal string.")
    is_spot: bool = Field(..., description="Whether the market is active in Spot.")
    is_otc: bool = Field(..., description="Whether the market is active in OTC.")
    is_margin: bool = Field(..., description="Whether the market is active in Margin.")
    is_tmn_based: bool = Field(..., description="Whether the market is Toman-based.")
    is_usdt_based: bool = Field(..., description="Whether the market is USDT-based.")
    amount_precision: int = Field(..., ge=0, description="Amount decimal places.")
    price_precision: int = Field(..., ge=0, description="Price decimal places.")
    flags: list[str] = Field(default_factory=list, description="Market flags, e.g. isRisky.")
    volume_24h: str = Field(..., description="24h volume as a decimal string.")
    change_24h: str = Field(..., description="24h change as a decimal string.")
    created_at: str = Field(..., description="ISO-8601 UTC creation timestamp.")
    fair_price: Optional[FairPriceModel] = Field(
        default=None, description="Optional fair-price bid/ask quote."
    )

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
            raise ValueError(f"decimal value must be finite: {value!r}")
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
            raise ValueError(f"created_at is not valid ISO-8601: {value!r}") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("created_at must include an explicit timezone")
        return value


class MarketsResponseModel(BaseModel):
    """Top-level response envelope for the markets endpoint."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    markets: list[MarketMetadataModel] = Field(
        ..., min_length=1, description="Non-empty array of market metadata."
    )
    message: str = Field(..., description="Human-readable status message.")
    success: bool = Field(..., description="Boolean success marker.")


def decimal_value(value: str) -> Decimal:
    """Convert a validated decimal string to Decimal without re-validating."""
    return Decimal(value)