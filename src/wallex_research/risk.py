"""Explicit Spot-only exposure checks; missing evidence fails closed."""
from __future__ import annotations

from decimal import Decimal

from .models import TargetExposure, decimal_value


class RiskViolation(ValueError):
    """A caller-provided target or evidence breaches a research risk gate."""


class InsufficientFundsError(RiskViolation):
    """Available-funds evidence is missing, unverified, invalid, or insufficient."""


class AllCapitalError(RiskViolation):
    """The proposed exposure would allocate effectively all capital."""


ALL_CAPITAL_THRESHOLD = Decimal("0.99")
"""Exposure fractions >= 0.99 are treated as allocating all capital."""


def validate_target_exposure(target: TargetExposure, maximum_spot_exposure: Decimal) -> None:
    maximum = decimal_value(maximum_spot_exposure, "maximum Spot exposure", error_type=RiskViolation)
    if not Decimal(0) <= maximum <= Decimal(1):
        raise RiskViolation("maximum Spot exposure must be within [0, 1]")
    fraction = decimal_value(target.fraction, "target exposure", error_type=RiskViolation)
    if fraction < 0:
        raise RiskViolation("negative target exposure would imply unsupported shorting")
    if fraction > maximum:
        raise RiskViolation("target exposure exceeds the explicitly configured Spot limit")


def validate_available_balance(
    available_balance_known: bool,
    available_balance_verified: bool,
    *,
    error_label: str = "available balance",
) -> None:
    """Reject missing or unverified available-funds evidence."""
    if not isinstance(available_balance_known, bool) or not isinstance(available_balance_verified, bool):
        raise InsufficientFundsError("available-balance evidence flags must be explicit booleans")
    if not available_balance_known:
        raise InsufficientFundsError(f"{error_label} is unknown; cannot evaluate sufficiency")
    if not available_balance_verified:
        raise InsufficientFundsError(
            f"{error_label} is reported but not independently verified; cannot rely on it"
        )


def validate_sufficient_funds(
    required_amount: Decimal | str | int,
    available_amount: Decimal | str | int | None,
    *,
    available_balance_known: bool = False,
    available_balance_verified: bool = False,
    error_label: str = "funds",
) -> None:
    """Require exact, nonnegative amounts and verified available-balance evidence."""
    validate_available_balance(
        available_balance_known,
        available_balance_verified,
        error_label=error_label,
    )
    if available_amount is None:
        raise InsufficientFundsError(f"{error_label} amount is unknown")
    required = decimal_value(required_amount, "required amount", error_type=InsufficientFundsError)
    available = decimal_value(available_amount, "available amount", error_type=InsufficientFundsError)
    if required < 0:
        raise InsufficientFundsError("required amount must be nonnegative")
    if available < 0:
        raise InsufficientFundsError("available amount must be nonnegative")
    if required > available:
        raise InsufficientFundsError(
            f"{error_label} ({available}) is insufficient for the required amount ({required})"
        )


def validate_not_all_capital(
    exposure_fraction: Decimal | str | int,
    *,
    threshold: Decimal | str | int | None = None,
) -> None:
    """Reject an exposure that would allocate effectively all capital."""
    fraction = decimal_value(exposure_fraction, "exposure fraction", error_type=RiskViolation)
    effective_threshold = decimal_value(
        threshold if threshold is not None else ALL_CAPITAL_THRESHOLD,
        "all-capital threshold",
        error_type=RiskViolation,
    )
    if not Decimal(0) <= fraction <= Decimal(1):
        raise RiskViolation("exposure fraction must be within [0, 1]")
    if not Decimal(0) < effective_threshold <= Decimal(1):
        raise RiskViolation("all-capital threshold must be within (0, 1]")
    if fraction >= effective_threshold:
        raise AllCapitalError(
            f"exposure fraction {fraction} >= {effective_threshold} would allocate effectively all capital; blocked"
        )


def validate_capital_evidence(
    capital: Decimal | str | int | None,
    *,
    capital_known: bool = False,
    capital_verified: bool = False,
    capital_source: str | None = None,
) -> None:
    """Require a positive capital value and explicit traceable verification.

    This validates evidence only; it does not authorize trading or equate a
    challenge allocation with owned or withdrawable user funds.
    """
    if not isinstance(capital_known, bool) or not isinstance(capital_verified, bool):
        raise RiskViolation("capital evidence flags must be explicit booleans")
    if not capital_known or capital is None:
        raise RiskViolation("capital is unknown; no usable amount has been provided")
    amount = decimal_value(capital, "capital", error_type=RiskViolation)
    if not capital_verified:
        raise RiskViolation(f"capital ({amount}) is reported but not independently verified")
    if not isinstance(capital_source, str) or not capital_source.strip():
        raise RiskViolation("verified capital requires a traceable source identifier")
    if amount <= 0:
        raise RiskViolation(f"capital must be positive, got {amount}")
