"""Explicit Spot-only exposure checks; no personal limit is selected here."""
from __future__ import annotations

from decimal import Decimal

from .models import TargetExposure


class RiskViolation(ValueError):
    """A caller-provided target breaches the explicitly configured Spot limit."""


def validate_target_exposure(target: TargetExposure, maximum_spot_exposure: Decimal) -> None:
    if target.fraction < 0:
        raise RiskViolation("negative target exposure would imply unsupported shorting")
    if target.fraction > maximum_spot_exposure:
        raise RiskViolation("target exposure exceeds the explicitly configured Spot limit")
