from __future__ import annotations

import socket
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

from wallex_research.models import Candle, ConfigError, DataError, SimulationConfig, TargetExposure
from wallex_research.replay import ReplayError, run_replay


UTC = timezone.utc


def bar(minute: int, open_: str, close: str) -> Candle:
    high = str(max(Decimal(open_), Decimal(close)) + Decimal("2"))
    low = str(min(Decimal(open_), Decimal(close)) - Decimal("2"))
    return Candle(
        "SYNTHETIC_XYZ",
        datetime(2026, 1, 1, 0, minute, tzinfo=UTC),
        Decimal(open_), Decimal(high), Decimal(low), Decimal(close), Decimal("1"),
    )


def config(*, max_exposure: str = "0.9", commission: str = "0.01", slippage: str = "0.02") -> SimulationConfig:
    return SimulationConfig(
        initial_cash=Decimal("1000"),
        quote_currency="SYNTHETIC_QUOTE",
        commission_rate=Decimal(commission),
        slippage_rate=Decimal(slippage),
        maximum_spot_exposure=Decimal(max_exposure),
    )


class ReplayTests(unittest.TestCase):
    def test_close_signal_executes_only_at_next_bar_open_and_costs_reconcile(self) -> None:
        bars = [bar(0, "100", "100"), bar(1, "100", "110"), bar(2, "120", "120")]
        signals = [
            TargetExposure(bars[0].timestamp, Decimal("0.5")),
            TargetExposure(bars[1].timestamp, Decimal("0")),
        ]
        result = run_replay(bars, signals, config())
        self.assertEqual(len(result.fills), 2)
        self.assertEqual(result.fills[0].observed_at, bars[0].timestamp)
        self.assertEqual(result.fills[0].executed_at, bars[1].timestamp)
        self.assertEqual(result.fills[0].reference_price, Decimal("100"))
        self.assertEqual(result.fills[0].fill_price, Decimal("102.00"))
        self.assertEqual(result.total_commission, Decimal("10.98"))
        self.assertEqual(result.total_slippage_cost, Decimal("22.00"))
        self.assertEqual(result.final_cash, Decimal("1067.0200"))
        self.assertEqual(result.final_quantity, Decimal("0"))
        self.assertEqual(result.total_return, Decimal("0.06702"))
        self.assertTrue(any("ownership, withdrawability, credit principal" in item for item in result.limitations))
        self.assertTrue(any("credit-plan fee accrual" in item and "challenge-specific settlement" in item for item in result.limitations))
        self.assertTrue(any("no official trading fee" in item and "spread" in item for item in result.limitations))
        self.assertTrue(any("realized/unrealized P&L" in item and "final payout" in item for item in result.limitations))

    def test_final_bar_signal_is_rejected_instead_of_same_bar_fill(self) -> None:
        bars = [bar(0, "100", "100"), bar(1, "100", "100")]
        with self.assertRaises(ReplayError):
            run_replay(bars, [TargetExposure(bars[-1].timestamp, Decimal("0.5"))], config())

    def test_risk_limit_is_rejected_not_clamped(self) -> None:
        bars = [bar(0, "100", "100"), bar(1, "100", "100")]
        with self.assertRaises(ReplayError):
            run_replay(bars, [TargetExposure(bars[0].timestamp, Decimal("0.5"))], config(max_exposure="0.25"))

    def test_missing_explicit_or_invalid_cost_configuration_fails_closed(self) -> None:
        with self.assertRaises(TypeError):
            SimulationConfig(initial_cash=Decimal("100"), quote_currency="Q", commission_rate=Decimal("0"), slippage_rate=Decimal("0"))  # type: ignore[call-arg]
        with self.assertRaises(ConfigError):
            config(commission="-0.1")

    def test_partial_buy_reports_unfilled_quantity_and_cash_never_goes_negative(self) -> None:
        bars = [bar(0, "100", "100"), bar(1, "100", "100")]
        expensive = config(max_exposure="1", commission="0.5", slippage="0.2")
        result = run_replay(bars, [TargetExposure(bars[0].timestamp, Decimal("1"))], expensive)
        outcome = result.orders[0]
        self.assertEqual(outcome.status, "partial")
        self.assertGreater(outcome.unfilled_quantity, Decimal("0"))
        self.assertEqual(outcome.requested_quantity, outcome.filled_quantity + outcome.unfilled_quantity)
        self.assertGreaterEqual(result.final_cash, Decimal("0"))

    def test_replay_path_has_no_network_side_effects(self) -> None:
        bars = [bar(0, "100", "100"), bar(1, "100", "100")]
        with patch.object(socket, "create_connection", side_effect=AssertionError("network call")):
            result = run_replay(bars, [], config())
        self.assertEqual(result.fills, ())

    def test_cannot_short_and_cash_never_negative(self) -> None:
        with self.assertRaises(DataError):
            TargetExposure(datetime(2026, 1, 1, tzinfo=UTC), Decimal("-0.1"))
        bars = [bar(0, "100", "100"), bar(1, "100", "100")]
        result = run_replay(bars, [TargetExposure(bars[0].timestamp, Decimal("0.9"))], config(max_exposure="1"))
        self.assertGreaterEqual(result.ledger[-1].cash, Decimal("0"))
        self.assertLessEqual(result.ledger[-1].equity, Decimal("1000"))

    def test_drawdown_is_reported_as_a_nonnegative_fraction(self) -> None:
        bars = [bar(0, "100", "100"), bar(1, "100", "80"), bar(2, "80", "70")]
        signals = [TargetExposure(bars[0].timestamp, Decimal("0.5"))]
        result = run_replay(bars, signals, config(commission="0", slippage="0"))
        self.assertGreater(result.maximum_drawdown, Decimal("0"))
        self.assertLessEqual(result.maximum_drawdown, Decimal("1"))


if __name__ == "__main__":
    unittest.main()
