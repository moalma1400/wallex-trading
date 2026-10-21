"""Typed, strict domain objects for local OHLCV validation and replay."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


class DataError(ValueError):
    """An input value violates the local market-data contract."""


class ConfigError(ValueError):
    """A required simulation assumption is missing or invalid."""


def decimal_value(value: Decimal | str | int, name: str, *, error_type: type[ValueError] = DataError) -> Decimal:
    """Convert exact decimal text/integer input; reject float and non-finite values."""
    if isinstance(value, bool) or isinstance(value, float):
        raise error_type(f"{name} must be supplied as Decimal, decimal text, or integer (not float)")
    if not isinstance(value, (Decimal, str, int)):
        raise error_type(f"{name} must be supplied as Decimal, decimal text, or integer")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise error_type(f"{name} is not a valid decimal") from exc
    if not result.is_finite():
        raise error_type(f"{name} must be finite")
    return result


def utc_datetime(value: datetime, name: str, *, error_type: type[ValueError] = DataError) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise error_type(f"{name} must be a timezone-aware datetime")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class Candle:
    symbol: str
    timestamp: datetime
    open: Decimal | str | int
    high: Decimal | str | int
    low: Decimal | str | int
    close: Decimal | str | int
    volume: Decimal | str | int

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise DataError("symbol must be a non-empty string")
        object.__setattr__(self, "symbol", self.symbol.strip())
        object.__setattr__(self, "timestamp", utc_datetime(self.timestamp, "timestamp"))
        for name in ("open", "high", "low", "close", "volume"):
            object.__setattr__(self, name, decimal_value(getattr(self, name), name))
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise DataError("OHLC prices must be greater than zero")
        if self.volume < 0:
            raise DataError("volume must be nonnegative")
        if self.low > self.high or not (self.low <= self.open <= self.high) or not (self.low <= self.close <= self.high):
            raise DataError("OHLC values violate low <= open/close <= high")


@dataclass(frozen=True, slots=True)
class TargetExposure:
    """A caller-supplied Spot target observed at a candle close; not a strategy."""

    timestamp: datetime
    fraction: Decimal | str | int

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", utc_datetime(self.timestamp, "signal timestamp"))
        object.__setattr__(self, "fraction", decimal_value(self.fraction, "target exposure"))
        if not Decimal(0) <= self.fraction <= Decimal(1):
            raise DataError("target exposure must be in the range [0, 1]; shorting/leverage is unsupported")


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Generic offline inputs; initial_cash is not an ownership or credit-account claim."""

    initial_cash: Decimal | str | int
    quote_currency: str
    commission_rate: Decimal | str | int
    slippage_rate: Decimal | str | int
    maximum_spot_exposure: Decimal | str | int

    def __post_init__(self) -> None:
        object.__setattr__(self, "initial_cash", decimal_value(self.initial_cash, "initial cash", error_type=ConfigError))
        object.__setattr__(self, "commission_rate", decimal_value(self.commission_rate, "commission rate", error_type=ConfigError))
        object.__setattr__(self, "slippage_rate", decimal_value(self.slippage_rate, "slippage rate", error_type=ConfigError))
        object.__setattr__(self, "maximum_spot_exposure", decimal_value(self.maximum_spot_exposure, "maximum Spot exposure", error_type=ConfigError))
        if self.initial_cash <= 0:
            raise ConfigError("initial cash must be greater than zero")
        if not isinstance(self.quote_currency, str) or not self.quote_currency.strip():
            raise ConfigError("quote currency label must be explicit and non-empty")
        object.__setattr__(self, "quote_currency", self.quote_currency.strip())
        if not Decimal(0) <= self.commission_rate < Decimal(1):
            raise ConfigError("commission rate must be in [0, 1)")
        if not Decimal(0) <= self.slippage_rate < Decimal(1):
            raise ConfigError("slippage rate must be in [0, 1)")
        if not Decimal(0) <= self.maximum_spot_exposure <= Decimal(1):
            raise ConfigError("maximum Spot exposure must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class SimulatedOrderOutcome:
    observed_at: datetime
    executed_at: datetime
    side: str
    status: str
    requested_quantity: Decimal
    filled_quantity: Decimal
    unfilled_quantity: Decimal


@dataclass(frozen=True, slots=True)
class SimulatedFill:
    observed_at: datetime
    executed_at: datetime
    side: str
    quantity: Decimal
    reference_price: Decimal
    fill_price: Decimal
    notional: Decimal
    commission: Decimal
    slippage_cost: Decimal


@dataclass(frozen=True, slots=True)
class LedgerPoint:
    timestamp: datetime
    cash: Decimal
    quantity: Decimal
    mark_price: Decimal
    equity: Decimal
    peak_equity: Decimal
    drawdown: Decimal


REPLAY_LIMITATIONS = (
    "initial_cash is a generic caller-supplied simulation balance; asset ownership, withdrawability, credit principal, registration balance, and repayment liability are not represented.",
    "No credit-plan fee accrual, forced-liquidation threshold or sale mechanics, account-permission model, or challenge-specific settlement is modeled.",
    "commission_rate and slippage_rate are generic simulation assumptions; no official trading fee, credit fee, or separately modeled spread is inferred.",
    "Marked equity is not a settlement ledger; realized/unrealized P&L, residual assets, principal repayment, and final payout are not separately reconciled.",
)


@dataclass(frozen=True, slots=True)
class ReplayResult:
    symbol: str
    config: SimulationConfig
    orders: tuple[SimulatedOrderOutcome, ...]
    fills: tuple[SimulatedFill, ...]
    ledger: tuple[LedgerPoint, ...]
    final_cash: Decimal
    final_quantity: Decimal
    final_equity: Decimal
    total_commission: Decimal
    total_slippage_cost: Decimal
    maximum_drawdown: Decimal
    limitations: tuple[str, ...] = REPLAY_LIMITATIONS

    @property
    def total_return(self) -> Decimal:
        """Arithmetic model return only; not net financing return or withdrawable cash."""
        return self.final_equity / self.config.initial_cash - Decimal(1)
