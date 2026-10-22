"""Explicit Spot-only exposure checks; no personal limit is selected here.

Includes available-funds validation and all-capital allocation rejection.
These checks fail closed when required evidence is missing or unverified.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from .models import TargetExposure


class RiskViolation(ValueError):
    """A caller-provided target breaches the explicitly configured Spot limit."""


class InsufficientFundsError(RiskViolation):
    """Available funds evidence is missing, unverified, or insufficient for the proposal."""


class AllCapitalError(RiskViolation):
    """The proposed exposure would allocate effectively all capital, which is rejected."""


ALL_CAPITAL_THRESHOLD = Decimal("0.99")
"""Exposure fractions >= 0.99 are treated as allocating all capital."""


def validate_target_exposure(target: TargetExposure, maximum_spot_exposure: Decimal) -> None:
    if target.fraction < 0:
        raise RiskViolation("negative target exposure would imply unsupported shorting")
    if target.fraction > maximum_spot_exposure:
        raise RiskViolation("target exposure exceeds the explicitly configured Spot limit")


def validate_available_balance(
    available_balance_known: bool,
    available_balance_verified: bool,
    *,
    error_label: str = "available balance",
) -> None:
    """Reject an intent that lacks verified available-funds evidence.

    Args:
        available_balance_known: Whether the caller has reported any balance figure.
        available_balance_verified: Whether the reported balance has been
            independently verified or was provided as authoritative.
        error_label: Label for error messages (e.g. "account balance").

    Raises:
        InsufficientFundsError: If balance evidence is missing or unverified.
    """
    if not available_balance_known:
        raise InsufficientFundsError(f"{error_label} is unknown; cannot evaluate sufficiency")
    if not available_balance_verified:
        raise InsufficientFundsError(
            f"{error_label} is reported but not independently verified; "
            "cannot rely on it for exposure decisions"
        )


def validate_sufficient_funds(
    required_amount: Decimal,
    available_amount: Decimal | None,
    *,
    available_balance_known: bool = True,
    available_balance_verified: bool = True,
    error_label: str = "funds",
) -> None:
    """Check that verified available funds are known and sufficient.

    Checks the balance evidence before comparing numeric amounts.
    """
    if available_amount is None and not available_balance_known:
        raise InsufficientFundsError(f"{error_label} amount is unknown")
    validate_available_balance(
        available_balance_known,
        available_balance_verified,
        error_label=error_label,
    )
    if available_amount is not None and required_amount > available_amount:
        raise InsufficientFundsError(
            f"{error_label} ({available_amount}) is insufficient for the "
            f"required amount ({required_amount})"
        )


def validate_not_all_capital(
    exposure_fraction: Decimal,
    *,
    threshold: Decimal | None = None,
) -> None:
    """Reject an exposure that would allocate effectively all capital.

    Args:
        exposure_fraction: The proposed fraction (0..1) of capital to deploy.
        threshold: The fraction above which allocation is rejected.
            Defaults to ALL_CAPITAL_THRESHOLD (0.99).

    Raises:
        AllCapitalError: If the fraction exceeds the threshold.
    """
    effective_threshold = threshold if threshold is not None else ALL_CAPITAL_THRESHOLD
    if exposure_fraction >= effective_threshold:
        raise AllCapitalError(
            f"exposure fraction {exposure_fraction} >= {effective_threshold} "
            "would allocate effectively all capital; this is blocked"
        )


def validate_capital_evidence(
    capital: Decimal | None,
    *,
    capital_known: bool = False,
    capital_verified: bool = False,
    capital_source: str | None = None,
) -> None:
    """Validate that the capital figure being used has proper provenance.

    This is the general-purpose gate for any capital-related decision.
    It does NOT authorize trading; it only validates that the caller's
    capital evidence meets minimum requirements.

    Raises:
        RiskViolation: If capital evidence is missing or insufficiently verified.
    """
    if not capital_known:
        raise RiskViolation("capital is unknown; no evidence has been provided")
    if not capital_verified:
        raise RiskViolation(
            f"capital ({capital}) is reported but not independently verified"
            if capital is not None
            else "capital amount is not independently verified"
        )
    if capital is not None and capital <= 0:
        raise RiskViolation(f"capital must be positive, got {capital}")
