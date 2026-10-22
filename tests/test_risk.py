"""Tests for risk module: available-balance, all-capital, and capital-evidence checks."""
from __future__ import annotations

import unittest
from decimal import Decimal

from wallex_research.risk import (
    AllCapitalError,
    InsufficientFundsError,
    RiskViolation,
    validate_available_balance,
    validate_capital_evidence,
    validate_not_all_capital,
    validate_sufficient_funds,
    validate_target_exposure,
)
from wallex_research.models import TargetExposure, DataError
from datetime import datetime, timezone


UTC = timezone.utc


def _t(fraction: str) -> TargetExposure:
    return TargetExposure(datetime(2026, 1, 1, tzinfo=UTC), Decimal(fraction))


class TestValidateAvailableBalance(unittest.TestCase):
    """AUDIT-001: Balance/funds checks."""

    def test_known_and_verified_passes(self) -> None:
        validate_available_balance(True, True)

    def test_unknown_raises(self) -> None:
        with self.assertRaises(InsufficientFundsError):
            validate_available_balance(False, True)

    def test_unverified_raises(self) -> None:
        with self.assertRaises(InsufficientFundsError):
            validate_available_balance(True, False)

    def test_unknown_and_unverified_raises(self) -> None:
        with self.assertRaises(InsufficientFundsError):
            validate_available_balance(False, False)

    def test_custom_error_label(self) -> None:
        with self.assertRaisesRegex(InsufficientFundsError, "custom balance"):
            validate_available_balance(False, True, error_label="custom balance")


class TestValidateSufficientFunds(unittest.TestCase):
    """AUDIT-001: Numeric sufficiency checks."""

    def test_sufficient_funds_passes(self) -> None:
        validate_sufficient_funds(Decimal("100"), Decimal("200"))

    def test_insufficient_funds_raises(self) -> None:
        with self.assertRaises(InsufficientFundsError):
            validate_sufficient_funds(Decimal("300"), Decimal("200"))

    def test_exact_funds_passes(self) -> None:
        validate_sufficient_funds(Decimal("200"), Decimal("200"))

    def test_unknown_amount_raises(self) -> None:
        with self.assertRaises(InsufficientFundsError):
            validate_sufficient_funds(Decimal("100"), None, available_balance_known=False)

    def test_unverified_balance_raises(self) -> None:
        with self.assertRaises(InsufficientFundsError):
            validate_sufficient_funds(Decimal("100"), Decimal("200"), available_balance_verified=False)


class TestValidateNotAllCapital(unittest.TestCase):
    """AUDIT-001: All-capital allocation rejection."""

    def test_small_exposure_passes(self) -> None:
        validate_not_all_capital(Decimal("0.5"))

    def test_zero_passes(self) -> None:
        validate_not_all_capital(Decimal("0"))

    def test_099_raises(self) -> None:
        with self.assertRaises(AllCapitalError):
            validate_not_all_capital(Decimal("0.99"))

    def test_1_raises(self) -> None:
        with self.assertRaises(AllCapitalError):
            validate_not_all_capital(Decimal("1"))

    def test_custom_threshold(self) -> None:
        with self.assertRaises(AllCapitalError):
            validate_not_all_capital(Decimal("0.8"), threshold=Decimal("0.8"))
        # Below custom threshold passes
        validate_not_all_capital(Decimal("0.79"), threshold=Decimal("0.8"))


class TestValidateCapitalEvidence(unittest.TestCase):
    """AUDIT-002: Capital provenance checks."""

    def test_known_and_verified_passes(self) -> None:
        validate_capital_evidence(Decimal("5000000"), capital_known=True, capital_verified=True)

    def test_unknown_raises(self) -> None:
        with self.assertRaises(RiskViolation):
            validate_capital_evidence(None, capital_known=False)

    def test_unverified_raises(self) -> None:
        with self.assertRaises(RiskViolation):
            validate_capital_evidence(
                Decimal("5000000"), capital_known=True, capital_verified=False
            )

    def test_zero_capital_raises(self) -> None:
        with self.assertRaises(RiskViolation):
            validate_capital_evidence(
                Decimal("0"), capital_known=True, capital_verified=True
            )


class TestValidateTargetExposure(unittest.TestCase):
    """Existing risk check, regression test."""

    def test_negative_raises(self) -> None:
        with self.assertRaises(DataError):
            _t("-0.1")

    def test_above_limit_raises(self) -> None:
        with self.assertRaises(RiskViolation):
            validate_target_exposure(_t("0.5"), Decimal("0.25"))

    def test_within_limit_passes(self) -> None:
        validate_target_exposure(_t("0.5"), Decimal("0.75"))


if __name__ == "__main__":
    unittest.main()
