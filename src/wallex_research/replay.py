"""Deterministic offline target-exposure replay using a deliberately simple fill model."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Sequence

from .data_quality import audit_candles
from .models import (
    Candle,
    LedgerPoint,
    ReplayResult,
    SimulationConfig,
    SimulatedFill,
    SimulatedOrderOutcome,
    TargetExposure,
)
from .risk import RiskViolation, validate_not_all_capital, validate_target_exposure


class ReplayError(ValueError):
    """Replay input violates chronology, causality, or risk assumptions."""


def run_replay(
    candles: Sequence[Candle],
    exposures: Sequence[TargetExposure],
    config: SimulationConfig,
    *,
    expected_interval: timedelta | None = None,
) -> ReplayResult:
    """Run a local-only simulation; close-time decisions fill at a later bar's open.

    This is not an exchange connector or a claim about actual market execution.
    """
    if not candles:
        raise ReplayError("at least one candle is required")
    report = audit_candles(candles, expected_interval=expected_interval)
    if not report.is_valid:
        codes = ", ".join(issue.code for issue in report.issues if issue.severity == "error")
        raise ReplayError(f"invalid candle dataset: {codes}")

    by_timestamp = {candle.timestamp: index for index, candle in enumerate(candles)}
    exposure_by_time: dict = {}
    previous_time = None
    for target in exposures:
        if previous_time is not None and target.timestamp <= previous_time:
            raise ReplayError("target exposure timestamps must be strictly increasing")
        previous_time = target.timestamp
        candle_index = by_timestamp.get(target.timestamp)
        if candle_index is None:
            raise ReplayError("each target exposure must match an input candle close")
        if candle_index == len(candles) - 1:
            raise ReplayError("final-candle target has no later bar open and cannot be executed causally")
        try:
            validate_target_exposure(target, config.maximum_spot_exposure)
            # Reuse the established 99% all-capital rule even when a caller sets
            # maximum_spot_exposure=1.0. Do not silently clamp the target.
            validate_not_all_capital(target.fraction)
        except RiskViolation as exc:
            raise ReplayError(str(exc)) from exc
        exposure_by_time[target.timestamp] = target

    cash = config.initial_cash
    quantity = Decimal(0)
    peak_equity = config.initial_cash
    total_commission = Decimal(0)
    total_slippage = Decimal(0)
    orders: list[SimulatedOrderOutcome] = []
    fills: list[SimulatedFill] = []
    ledger: list[LedgerPoint] = []

    first = candles[0]
    ledger.append(LedgerPoint(first.timestamp, cash, quantity, first.close, cash, peak_equity, Decimal(0)))
    for index in range(1, len(candles)):
        observed = candles[index - 1]
        execution_bar = candles[index]
        target = exposure_by_time.get(observed.timestamp)
        if target is not None:
            previous_equity = ledger[-1].equity
            reference_price = execution_bar.open
            desired_quantity = target.fraction * previous_equity / reference_price
            delta = desired_quantity - quantity
            if delta > 0:
                side = "BUY"
                requested = delta
                fill_price = reference_price * (Decimal(1) + config.slippage_rate)
                affordability_denominator = fill_price * (Decimal(1) + config.commission_rate)
                affordable = cash / affordability_denominator
                fill_quantity = min(requested, affordable)
                notional = fill_quantity * fill_price
                commission = notional * config.commission_rate
                if notional + commission > cash:
                    fill_quantity = max(Decimal(0), fill_quantity.next_minus())
                    notional = fill_quantity * fill_price
                    commission = notional * config.commission_rate
                if fill_quantity > 0:
                    slippage = fill_quantity * (fill_price - reference_price)
                    cash -= notional + commission
                    quantity += fill_quantity
                    fills.append(SimulatedFill(observed.timestamp, execution_bar.timestamp, side, fill_quantity, reference_price, fill_price, notional, commission, slippage))
                    total_commission += commission
                    total_slippage += slippage
                unfilled = requested - fill_quantity
                status = "filled" if unfilled == 0 else ("partial" if fill_quantity > 0 else "no_fill")
                orders.append(SimulatedOrderOutcome(observed.timestamp, execution_bar.timestamp, side, status, requested, fill_quantity, unfilled))
            elif delta < 0:
                side = "SELL"
                requested = -delta
                fill_quantity = min(requested, quantity)
                fill_price = reference_price * (Decimal(1) - config.slippage_rate)
                notional = fill_quantity * fill_price
                commission = notional * config.commission_rate
                slippage = fill_quantity * (reference_price - fill_price)
                if fill_quantity > 0:
                    cash += notional - commission
                    quantity -= fill_quantity
                    fills.append(SimulatedFill(observed.timestamp, execution_bar.timestamp, side, fill_quantity, reference_price, fill_price, notional, commission, slippage))
                    total_commission += commission
                    total_slippage += slippage
                unfilled = requested - fill_quantity
                status = "filled" if unfilled == 0 else ("partial" if fill_quantity > 0 else "no_fill")
                orders.append(SimulatedOrderOutcome(observed.timestamp, execution_bar.timestamp, side, status, requested, fill_quantity, unfilled))
            else:
                orders.append(SimulatedOrderOutcome(observed.timestamp, execution_bar.timestamp, "NONE", "no_change", Decimal(0), Decimal(0), Decimal(0)))

        equity = cash + quantity * execution_bar.close
        peak_equity = max(peak_equity, equity)
        drawdown = (peak_equity - equity) / peak_equity if peak_equity > 0 else Decimal(0)
        ledger.append(LedgerPoint(execution_bar.timestamp, cash, quantity, execution_bar.close, equity, peak_equity, drawdown))

    final = ledger[-1]
    maximum_drawdown = max((point.drawdown for point in ledger), default=Decimal(0))
    return ReplayResult(
        symbol=candles[0].symbol,
        config=config,
        orders=tuple(orders),
        fills=tuple(fills),
        ledger=tuple(ledger),
        final_cash=cash,
        final_quantity=quantity,
        final_equity=final.equity,
        total_commission=total_commission,
        total_slippage_cost=total_slippage,
        maximum_drawdown=maximum_drawdown,
    )
