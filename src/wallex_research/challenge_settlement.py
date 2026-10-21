"""Offline end-of-challenge TMN settlement readiness; no conversion is executed."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Mapping

from .challenge import ChallengePolicyError, _decimal
from .historical import utc_time


@dataclass(frozen=True, slots=True)
class SettlementSnapshot:
    snapshot_at_utc: datetime
    balances: Mapping[str, Decimal | str | int]
    realized_pnl_tmn: Decimal | str | int
    unrealized_pnl_tmn: Decimal | str | int | None
    fees_tmn: Decimal | str | int | None
    fees_known: bool
    account_reconciled: bool
    valuation_status: str = "INTERNAL_ESTIMATE"
    evidence_status: str = "UNRESOLVED"
    source_id: str | None = None
    source_url: str | None = None
    source_sha256: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_at_utc", utc_time(self.snapshot_at_utc, "settlement snapshot time"))
        normalized: dict[str, Decimal] = {}
        for asset, value in self.balances.items():
            if not isinstance(asset, str) or not asset.strip() or asset.strip().upper() in normalized:
                raise ChallengePolicyError("settlement balances require unique non-empty asset codes")
            amount = _decimal(value, f"balance[{asset}]")
            normalized[asset.strip().upper()] = amount
        object.__setattr__(self, "balances", MappingProxyType(dict(sorted(normalized.items()))))
        object.__setattr__(self, "realized_pnl_tmn", _decimal(self.realized_pnl_tmn, "realized_pnl_tmn", nonnegative=False))
        if self.unrealized_pnl_tmn is not None:
            object.__setattr__(self, "unrealized_pnl_tmn", _decimal(self.unrealized_pnl_tmn, "unrealized_pnl_tmn", nonnegative=False))
        if self.fees_tmn is not None:
            object.__setattr__(self, "fees_tmn", _decimal(self.fees_tmn, "fees_tmn"))
        if not isinstance(self.fees_known, bool) or not isinstance(self.account_reconciled, bool):
            raise ChallengePolicyError("fees_known and account_reconciled must be explicit booleans")
        if self.valuation_status not in {"OFFICIAL", "INTERNAL_ESTIMATE"}:
            raise ChallengePolicyError("valuation_status must distinguish OFFICIAL from INTERNAL_ESTIMATE")
        if self.evidence_status not in {"OFFICIAL_SOURCE_VERIFIED", "SYNTHETIC_FIXTURE", "PROVIDED_BY_CHALLENGE_BRIEF", "INFERRED", "UNRESOLVED", "REQUIRES_ORGANIZER_CONFIRMATION"}:
            raise ChallengePolicyError("settlement evidence_status is unsupported")
        if self.evidence_status == "OFFICIAL_SOURCE_VERIFIED":
            if self.valuation_status != "OFFICIAL":
                raise ChallengePolicyError("official source evidence must be distinguished from internal estimates")
            if not isinstance(self.source_id, str) or not self.source_id.strip():
                raise ChallengePolicyError("official settlement valuation requires a source_id")
            if not isinstance(self.source_url, str) or not self.source_url.startswith("https://"):
                raise ChallengePolicyError("official settlement valuation requires an exact HTTPS source URL")
            if not isinstance(self.source_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", self.source_sha256):
                raise ChallengePolicyError("official settlement valuation requires a SHA-256 evidence fingerprint")


@dataclass(frozen=True, slots=True)
class SettlementReadiness:
    ready: bool
    reason_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    final_value_tmn: Decimal | None
    net_return_percent: Decimal | None
    realized_pnl_tmn: Decimal
    unrealized_pnl_tmn: Decimal | None
    fees_tmn: Decimal | None
    valuation_status: str
    evidence_status: str
    cutoff_evidence_status: str
    cutoff_source_id: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "reason_codes": list(self.reason_codes),
            "warning_codes": list(self.warning_codes),
            "final_value_tmn": str(self.final_value_tmn) if self.final_value_tmn is not None else None,
            "net_return_percent": str(self.net_return_percent) if self.net_return_percent is not None else None,
            "realized_pnl_tmn": str(self.realized_pnl_tmn),
            "unrealized_pnl_tmn": str(self.unrealized_pnl_tmn) if self.unrealized_pnl_tmn is not None else None,
            "fees_tmn": str(self.fees_tmn) if self.fees_tmn is not None else None,
            "valuation_status": self.valuation_status,
            "evidence_status": self.evidence_status,
            "cutoff_evidence_status": self.cutoff_evidence_status,
            "cutoff_source_id": self.cutoff_source_id,
        }


def validate_settlement_readiness(
    snapshot: SettlementSnapshot,
    *,
    official_cutoff_utc: datetime | None,
    cutoff_evidence_status: str,
    initial_capital_tmn: Decimal | str | int = "5000000",
    allow_synthetic_fixture_evidence: bool = False,
    cutoff_source_id: str | None = None,
    cutoff_source_url: str | None = None,
    cutoff_source_sha256: str | None = None,
) -> SettlementReadiness:
    """Readiness requires an exact official cutoff and realized TMN-only balances."""
    capital = _decimal(initial_capital_tmn, "initial_capital_tmn")
    if capital != Decimal("5000000"):
        raise ChallengePolicyError("challenge baseline must match the user-provided 5,000,000-TMN brief")
    reasons: list[str] = []
    warnings: list[str] = []
    cutoff_synthetic = cutoff_evidence_status == "SYNTHETIC_FIXTURE" and allow_synthetic_fixture_evidence
    cutoff_official = cutoff_evidence_status == "OFFICIAL_SOURCE_VERIFIED"
    cutoff_provenance_valid = (
        isinstance(cutoff_source_id, str) and bool(cutoff_source_id.strip())
        and isinstance(cutoff_source_url, str) and cutoff_source_url.startswith("https://")
        and isinstance(cutoff_source_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", cutoff_source_sha256) is not None
    )
    if cutoff_official and not cutoff_provenance_valid:
        reasons.append("OFFICIAL_CUTOFF_PROVENANCE_MISSING")
    if cutoff_synthetic:
        warnings.append("SYNTHETIC_CUTOFF_NOT_OFFICIAL_EVIDENCE")
    cutoff_ok = (cutoff_official and cutoff_provenance_valid) or cutoff_synthetic
    if official_cutoff_utc is None or not cutoff_ok:
        reasons.append("OFFICIAL_CUTOFF_UNRESOLVED")
    else:
        cutoff = utc_time(official_cutoff_utc, "official_cutoff_utc")
        if snapshot.snapshot_at_utc != cutoff:
            reasons.append("SNAPSHOT_NOT_AT_OFFICIAL_CUTOFF")
    valuation_official = snapshot.evidence_status == "OFFICIAL_SOURCE_VERIFIED" and snapshot.valuation_status == "OFFICIAL"
    valuation_synthetic = snapshot.evidence_status == "SYNTHETIC_FIXTURE" and allow_synthetic_fixture_evidence
    if valuation_synthetic:
        warnings.append("SYNTHETIC_FIXTURE_NOT_OFFICIAL_SETTLEMENT_EVIDENCE")
    if not valuation_official and not valuation_synthetic:
        reasons.append("FINAL_VALUATION_NOT_OFFICIALLY_VERIFIED")
    if not snapshot.account_reconciled:
        reasons.append("ACCOUNT_BALANCES_NOT_RECONCILED")
    if not snapshot.fees_known or snapshot.fees_tmn is None:
        reasons.append("FEES_UNKNOWN")
    if snapshot.unrealized_pnl_tmn is None:
        reasons.append("UNREALIZED_PNL_STATUS_UNKNOWN")
    elif snapshot.unrealized_pnl_tmn != 0:
        reasons.append("UNREALIZED_PNL_REMAINS")
    tmn_balance = snapshot.balances.get("TMN")
    if tmn_balance is None:
        reasons.append("TMN_FINAL_BALANCE_MISSING")
    non_tmn = {asset: amount for asset, amount in snapshot.balances.items() if asset != "TMN" and amount != 0}
    if non_tmn:
        reasons.append("NON_TMN_INVENTORY_REMAINS")
    final_value = None
    net_return = None
    ready = not reasons
    if ready and tmn_balance is not None:
        final_value = tmn_balance
        net_return = ((final_value - capital) / capital) * Decimal(100)
    return SettlementReadiness(
        ready,
        tuple(dict.fromkeys(reasons)),
        tuple(dict.fromkeys(warnings)),
        final_value,
        net_return,
        snapshot.realized_pnl_tmn,
        snapshot.unrealized_pnl_tmn,
        snapshot.fees_tmn,
        snapshot.valuation_status,
        snapshot.evidence_status,
        cutoff_evidence_status,
        cutoff_source_id,
    )
