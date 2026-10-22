"""Fail-closed, offline Wallex hackathon policy and market eligibility primitives.

Nothing in this module submits orders or establishes that a market is available
on Wallex. Caller-provided/fixture metadata is evidence input, not a live feed.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from .historical import canonical_json_bytes, utc_time


class ChallengePolicyError(ValueError):
    """Challenge configuration or supplied market evidence is ambiguous."""


PAIR_RE = re.compile(r"^[A-Za-z0-9]+/[A-Za-z0-9]+$")
CANONICAL_PAIR_RE = re.compile(r"^[A-Z0-9]+/[A-Z0-9]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_TAGS = {
    "PROVIDED_BY_CHALLENGE_BRIEF",
    "OFFICIAL_SOURCE_VERIFIED",
    "INFERRED",
    "UNRESOLVED",
    "REQUIRES_ORGANIZER_CONFIRMATION",
    "SYNTHETIC_FIXTURE",
}


def normalize_spot_pair(value: str) -> str:
    """Trim surrounding whitespace, uppercase ASCII symbols, never guess syntax."""
    if not isinstance(value, str):
        raise ChallengePolicyError("pair must be text in BASE/QUOTE form")
    token = value.strip()
    if not PAIR_RE.fullmatch(token):
        raise ChallengePolicyError("pair must contain exactly two ASCII alphanumeric symbols separated by one slash")
    base, quote = token.split("/", 1)
    if not base or not quote:
        raise ChallengePolicyError("pair base and quote symbols must be non-empty")
    return f"{base.upper()}/{quote.upper()}"


def build_disabled_pair_registry(raw_bytes: bytes, *, source_id: str = "USER-WALLEX-HACKATHON-BRIEF") -> dict[str, Any]:
    """Derive deterministic JSON data and diagnostics without discarding raw evidence."""
    if not isinstance(raw_bytes, bytes):
        raise ChallengePolicyError("raw disabled-pair evidence must be bytes")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ChallengePolicyError("disabled-pair source_id must be non-empty")
    try:
        lines = raw_bytes.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ChallengePolicyError("raw disabled-pair evidence must be UTF-8") from exc
    normalized: list[str] = []
    malformed: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        try:
            normalized.append(normalize_spot_pair(line))
        except ChallengePolicyError:
            malformed.append({"line": line_number, "raw": line})
    counts: dict[str, int] = {}
    for pair in normalized:
        counts[pair] = counts.get(pair, 0) + 1
    duplicates = sorted((pair, count) for pair, count in counts.items() if count > 1)
    return {
        "schema_version": "1.0",
        "source_id": source_id,
        "evidence_status": "PROVIDED_BY_CHALLENGE_BRIEF",
        "raw_source_file": "config/challenge/wallex_disabled_spot_pairs_raw.txt",
        "raw_source_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "raw_entry_count": len(lines),
        "unique_pair_count": len(counts),
        "duplicate_pair_count": len(duplicates),
        "duplicate_excess_entry_count": sum(count - 1 for _, count in duplicates),
        "duplicate_entries": [{"pair": pair, "count": count} for pair, count in duplicates],
        "malformed_entry_count": len(malformed),
        "malformed_entries": malformed,
        "normalization": {
            "trim_outer_whitespace": True,
            "uppercase": True,
            "separator": "/",
            "syntax": "BASE/QUOTE with ASCII alphanumeric symbols",
            "runtime_source": "disabled_pairs",
        },
        "disabled_pairs": sorted(counts),
    }


def _decimal(value: Any, name: str, *, nonnegative: bool = True) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float) or not isinstance(value, (Decimal, int, str)):
        raise ChallengePolicyError(f"{name} must be exact Decimal-compatible text or integer")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ChallengePolicyError(f"{name} is not a valid decimal") from exc
    if not result.is_finite() or (nonnegative and result < 0):
        raise ChallengePolicyError(f"{name} must be finite and nonnegative")
    return result


def _truth(value: Any, name: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ChallengePolicyError(f"{name} must be true, false, or unknown")
    return value


@dataclass(frozen=True, slots=True)
class DisabledPairRegistry:
    disabled_pairs: frozenset[str]
    raw_entry_count: int
    duplicate_entries: tuple[tuple[str, int], ...]
    malformed_entries: tuple[tuple[int, str], ...]
    raw_source_sha256: str
    source_id: str

    def __post_init__(self) -> None:
        for pair in self.disabled_pairs:
            if not isinstance(pair, str) or not CANONICAL_PAIR_RE.fullmatch(pair):
                raise ChallengePolicyError(f"registry contains non-canonical pair: {pair!r}")
        if self.raw_entry_count < 0 or not SHA256_RE.fullmatch(self.raw_source_sha256):
            raise ChallengePolicyError("registry count or raw source SHA-256 is invalid")
        if self.duplicate_entries or self.malformed_entries:
            raise ChallengePolicyError("disabled-pair source has duplicate or malformed entries; refusing runtime use")

    def contains(self, pair: str) -> bool:
        return normalize_spot_pair(pair) in self.disabled_pairs

    @classmethod
    def load(cls, config_path: str | Path, *, repository_root: str | Path | None = None) -> "DisabledPairRegistry":
        config_file = Path(config_path)
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ChallengePolicyError(f"cannot read disabled-pair config: {exc}") from exc
        if not isinstance(config, dict) or config.get("schema_version") != "1.0":
            raise ChallengePolicyError("disabled-pair config must use schema_version 1.0")
        if config.get("evidence_status") != "PROVIDED_BY_CHALLENGE_BRIEF":
            raise ChallengePolicyError("disabled-pair source evidence status is missing or unsupported")
        root = Path(repository_root).resolve() if repository_root else config_file.resolve().parents[2]
        relative = config.get("raw_source_file")
        if not isinstance(relative, str):
            raise ChallengePolicyError("disabled-pair config must name its raw source file")
        raw_path = (root / relative).resolve()
        try:
            raw_path.relative_to(root)
        except ValueError as exc:
            raise ChallengePolicyError("raw source path escapes repository root") from exc
        try:
            raw_bytes = raw_path.read_bytes()
            raw_lines = raw_bytes.decode("utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            raise ChallengePolicyError(f"cannot read UTF-8 raw pair source: {exc}") from exc
        raw_hash = hashlib.sha256(raw_bytes).hexdigest()
        if raw_hash != config.get("raw_source_sha256"):
            raise ChallengePolicyError("raw disabled-pair source fingerprint does not match config")
        normalized: list[str] = []
        malformed: list[tuple[int, str]] = []
        for index, line in enumerate(raw_lines, 1):
            try:
                normalized.append(normalize_spot_pair(line))
            except ChallengePolicyError:
                malformed.append((index, line))
        counts: dict[str, int] = {}
        for pair in normalized:
            counts[pair] = counts.get(pair, 0) + 1
        duplicates = tuple(sorted((pair, count) for pair, count in counts.items() if count > 1))
        declared_duplicates = tuple(sorted((row.get("pair"), row.get("count")) for row in config.get("duplicate_entries", []) if isinstance(row, dict)))
        declared_malformed = tuple((row.get("line"), row.get("raw")) for row in config.get("malformed_entries", []) if isinstance(row, dict))
        if len(raw_lines) != config.get("raw_entry_count") or len(set(normalized)) != config.get("unique_pair_count"):
            raise ChallengePolicyError("raw/unique entry counts disagree with disabled-pair config")
        if declared_duplicates != duplicates or declared_malformed != tuple(malformed):
            raise ChallengePolicyError("duplicate/malformed entry report disagrees with raw pair source")
        if len(duplicates) != config.get("duplicate_pair_count") or sum(count - 1 for _, count in duplicates) != config.get("duplicate_excess_entry_count"):
            raise ChallengePolicyError("duplicate pair counts disagree with source report")
        pairs = config.get("disabled_pairs")
        if not isinstance(pairs, list) or pairs != sorted(set(normalized)):
            raise ChallengePolicyError("canonical disabled_pairs must be sorted, unique and derived from the raw source")
        source_id = config.get("source_id")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ChallengePolicyError("disabled-pair source_id must be non-empty")
        return cls(
            frozenset(pairs), len(raw_lines), duplicates, tuple(malformed), raw_hash,
            source_id,
        )


@dataclass(frozen=True, slots=True)
class ConversionPathEvidence:
    route_id: str
    source_status: str
    source_url: str
    permitted_for_challenge: bool
    executable_within_deadline: bool
    verified_at_utc: datetime
    valid_until_utc: datetime

    def __post_init__(self) -> None:
        if not self.route_id.strip():
            raise ChallengePolicyError("conversion route ID must be non-empty")
        if self.source_status != "OFFICIAL_SOURCE_VERIFIED":
            raise ChallengePolicyError("conversion route requires independently verified official-source evidence")
        if not isinstance(self.source_url, str) or not self.source_url.startswith("https://"):
            raise ChallengePolicyError("conversion route requires its exact official HTTPS source URL")
        if not self.permitted_for_challenge or not self.executable_within_deadline:
            raise ChallengePolicyError("conversion route must be documented as permitted and executable before cutoff")
        object.__setattr__(self, "verified_at_utc", utc_time(self.verified_at_utc, "conversion verification time"))
        object.__setattr__(self, "valid_until_utc", utc_time(self.valid_until_utc, "conversion validity end"))
        if self.valid_until_utc < self.verified_at_utc:
            raise ChallengePolicyError("conversion evidence expires before it was verified")


@dataclass(frozen=True, slots=True)
class ChallengeModePolicy:
    initial_capital_tmn: Decimal = Decimal("5000000")
    spot_only: bool = True
    leverage_enabled: bool = False
    margin_enabled: bool = False
    borrowing_enabled: bool = False
    short_selling_enabled: bool = False
    withdrawals_enabled: bool = False
    transfers_enabled: bool = False
    deposits_enabled: bool = False
    manual_trading_counts: bool = False
    live_trading_enabled_by_default: bool = False
    require_algorithmic_decision_log: bool = True
    require_end_state_tmn: bool = True
    enabled_quote_assets: tuple[str, ...] = ("TMN",)
    usdt_quote_enabled: bool = False
    usdt_conversion_evidence: ConversionPathEvidence | None = None
    maximum_market_metadata_age_seconds: int | None = None
    official_cutoff_utc: datetime | None = None
    official_cutoff_status: str = "REQUIRES_ORGANIZER_CONFIRMATION"
    explicit_configuration: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.explicit_configuration, bool):
            raise ChallengePolicyError("explicit_configuration must be a boolean")
        object.__setattr__(self, "initial_capital_tmn", _decimal(self.initial_capital_tmn, "initial_capital_tmn"))
        if self.initial_capital_tmn != Decimal("5000000"):
            raise ChallengePolicyError("challenge baseline must match the user-provided 5,000,000-TMN brief")
        required_true = {"spot_only": self.spot_only, "require_algorithmic_decision_log": self.require_algorithmic_decision_log, "require_end_state_tmn": self.require_end_state_tmn}
        required_false = {
            "leverage_enabled": self.leverage_enabled, "margin_enabled": self.margin_enabled,
            "borrowing_enabled": self.borrowing_enabled, "short_selling_enabled": self.short_selling_enabled,
            "withdrawals_enabled": self.withdrawals_enabled, "transfers_enabled": self.transfers_enabled,
            "deposits_enabled": self.deposits_enabled, "manual_trading_counts": self.manual_trading_counts,
            "live_trading_enabled_by_default": self.live_trading_enabled_by_default,
        }
        if any(value is not True for value in required_true.values()):
            raise ChallengePolicyError("challenge policy must be Spot-only and require decision logs/TMN settlement")
        if any(value is not False for value in required_false.values()):
            raise ChallengePolicyError("unsafe challenge mode flags are forbidden in this offline implementation")
        quotes = tuple(sorted({normalize_spot_pair(f"X/{quote}").split("/", 1)[1] for quote in self.enabled_quote_assets}))
        if not quotes or any(quote not in {"TMN", "USDT"} for quote in quotes):
            raise ChallengePolicyError("only explicit TMN or USDT quote assets are recognized for this brief")
        if "TMN" not in quotes:
            raise ChallengePolicyError("TMN must remain an eligible quote asset for settlement planning")
        object.__setattr__(self, "enabled_quote_assets", quotes)
        if self.usdt_quote_enabled:
            if "USDT" not in quotes or self.usdt_conversion_evidence is None:
                raise ChallengePolicyError("USDT quotes require explicit enabled status and verified conversion evidence")
            if self.official_cutoff_utc is None:
                raise ChallengePolicyError("USDT quotes require an organizer-confirmed official cutoff")
            cutoff = utc_time(self.official_cutoff_utc, "official_cutoff_utc")
            if self.official_cutoff_status != "OFFICIAL_SOURCE_VERIFIED" or self.usdt_conversion_evidence.valid_until_utc < cutoff:
                raise ChallengePolicyError("USDT conversion evidence must cover the official challenge cutoff")
            object.__setattr__(self, "official_cutoff_utc", cutoff)
        elif "USDT" in quotes:
            raise ChallengePolicyError("USDT in enabled_quote_assets requires usdt_quote_enabled and a verified conversion route")
        if self.maximum_market_metadata_age_seconds is not None and self.maximum_market_metadata_age_seconds < 0:
            raise ChallengePolicyError("maximum_market_metadata_age_seconds must be nonnegative")
        if self.official_cutoff_utc is not None:
            object.__setattr__(self, "official_cutoff_utc", utc_time(self.official_cutoff_utc, "official_cutoff_utc"))


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    pair: str
    active: bool | None
    orderable: bool | None
    is_spot: bool | None
    challenge_enabled: bool | None
    observed_at_utc: datetime
    source_id: str
    evidence_status: str
    source_url: str | None = None
    source_sha256: str | None = None
    price_precision: int | None = None
    amount_precision: int | None = None
    precision_semantics_verified: bool | None = None
    minimum_order_value_tmn: Decimal | str | int | None = None
    minimum_order_value_verified: bool | None = None

    def __post_init__(self) -> None:
        canonical = normalize_spot_pair(self.pair)
        object.__setattr__(self, "pair", canonical)
        for name in ("active", "orderable", "is_spot", "challenge_enabled", "precision_semantics_verified", "minimum_order_value_verified"):
            object.__setattr__(self, name, _truth(getattr(self, name), name))
        for name in ("price_precision", "amount_precision"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise ChallengePolicyError(f"{name} must be a nonnegative integer when present")
        if self.minimum_order_value_tmn is not None:
            object.__setattr__(self, "minimum_order_value_tmn", _decimal(self.minimum_order_value_tmn, "minimum_order_value_tmn"))
        object.__setattr__(self, "observed_at_utc", utc_time(self.observed_at_utc, "market metadata observed_at_utc"))
        if not self.source_id.strip():
            raise ChallengePolicyError("market snapshot requires source_id")
        if self.evidence_status not in EVIDENCE_TAGS:
            raise ChallengePolicyError("market snapshot evidence_status is not a recognized evidence tag")
        if self.evidence_status == "OFFICIAL_SOURCE_VERIFIED":
            if not isinstance(self.source_url, str) or not self.source_url.startswith("https://"):
                raise ChallengePolicyError("official market metadata requires its exact HTTPS source URL")
            if not isinstance(self.source_sha256, str) or not SHA256_RE.fullmatch(self.source_sha256):
                raise ChallengePolicyError("official market metadata requires a SHA-256 evidence fingerprint")


@dataclass(frozen=True, slots=True)
class MarketRequest:
    pair: str
    instrument_type: str
    leverage: Decimal | str | int
    margin: bool
    borrowed: bool
    short_selling: bool
    strategy_allows_pair: bool
    risk_approved: bool = False
    algorithmic_decision: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_type, str) or not self.instrument_type.strip():
            raise ChallengePolicyError("instrument_type must be explicit")
        for name in ("margin", "borrowed", "short_selling", "strategy_allows_pair", "risk_approved", "algorithmic_decision"):
            if not isinstance(getattr(self, name), bool):
                raise ChallengePolicyError(f"{name} must be an explicit boolean")
        object.__setattr__(self, "instrument_type", self.instrument_type.strip().lower())
        object.__setattr__(self, "leverage", _decimal(self.leverage, "leverage"))
        if self.leverage < Decimal(1):
            raise ChallengePolicyError("leverage multiplier cannot be below one")


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    eligible: bool
    pair: str | None
    reason_codes: tuple[str, ...]
    evidence_status: str
    warning_codes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {"eligible": self.eligible, "pair": self.pair, "reason_codes": list(self.reason_codes), "warning_codes": list(self.warning_codes), "evidence_status": self.evidence_status}


def is_challenge_spot_market_allowed(
    request: MarketRequest,
    market_metadata: MarketSnapshot | None,
    challenge_config: ChallengeModePolicy,
    disabled_registry: DisabledPairRegistry,
    *,
    now_utc: datetime,
    allow_synthetic_fixture_evidence: bool = False,
) -> EligibilityDecision:
    """Explain the fail-closed eligibility decision; never implies exchange access."""
    if not isinstance(allow_synthetic_fixture_evidence, bool):
        raise ChallengePolicyError("allow_synthetic_fixture_evidence must be an explicit boolean")
    reasons: list[str] = []
    warnings: list[str] = []
    try:
        pair = normalize_spot_pair(request.pair)
    except ChallengePolicyError:
        return EligibilityDecision(False, None, ("MALFORMED_PAIR",), "UNRESOLVED")
    if not challenge_config.explicit_configuration:
        reasons.append("CHALLENGE_CONFIGURATION_NOT_EXPLICIT")
    if request.instrument_type.lower() != "spot":
        reasons.append("NON_SPOT_INSTRUMENT")
    if request.leverage != Decimal(1):
        reasons.append("LEVERAGE_FORBIDDEN")
    if request.margin:
        reasons.append("MARGIN_FORBIDDEN")
    if request.borrowed:
        reasons.append("BORROWING_FORBIDDEN")
    if request.short_selling:
        reasons.append("SHORT_SELLING_FORBIDDEN")
    if not request.strategy_allows_pair:
        reasons.append("STRATEGY_POLICY_REJECTED")
    if not request.algorithmic_decision:
        reasons.append("NON_ALGORITHMIC_INTENT")
    if not request.risk_approved:
        reasons.append("RISK_POLICY_NOT_APPROVED")

    quote = pair.split("/", 1)[1]
    if quote not in challenge_config.enabled_quote_assets:
        reasons.append("UNSUPPORTED_QUOTE_ASSET")
    if quote == "USDT" and not challenge_config.usdt_quote_enabled:
        reasons.append("TMN_CONVERSION_UNVERIFIED")
    if disabled_registry.contains(pair):
        reasons.append("PAIR_DISABLED_BY_CHALLENGE_BRIEF")

    if market_metadata is None:
        reasons.append("MARKET_METADATA_MISSING")
        evidence = "UNRESOLVED"
    else:
        evidence = market_metadata.evidence_status
        if market_metadata.pair != pair:
            reasons.append("MARKET_METADATA_PAIR_MISMATCH")
        disabled_but_reported_available = pair in disabled_registry.disabled_pairs and (
            market_metadata.active is True or market_metadata.orderable is True or market_metadata.challenge_enabled is True
        )
        if disabled_but_reported_available:
            reasons.append("CONTRADICTORY_DISABLED_MARKET_ACTIVE")
        if market_metadata.active is False and (market_metadata.orderable is True or market_metadata.challenge_enabled is True):
            reasons.append("MARKET_METADATA_STATE_CONTRADICTORY")
        if market_metadata.is_spot is False and market_metadata.challenge_enabled is True:
            reasons.append("MARKET_METADATA_STATE_CONTRADICTORY")
        if market_metadata.evidence_status != "OFFICIAL_SOURCE_VERIFIED":
            if allow_synthetic_fixture_evidence and market_metadata.evidence_status == "SYNTHETIC_FIXTURE":
                warnings.append("SYNTHETIC_FIXTURE_NOT_RUNTIME_AUTHORIZATION")
            else:
                reasons.append("MARKET_METADATA_NOT_OFFICIALLY_VERIFIED")
        now = utc_time(now_utc, "now_utc")
        age_seconds = (now - market_metadata.observed_at_utc).total_seconds()
        if age_seconds < 0:
            reasons.append("MARKET_METADATA_FROM_FUTURE")
        elif challenge_config.maximum_market_metadata_age_seconds is None:
            reasons.append("MARKET_METADATA_MAX_AGE_UNCONFIGURED")
        elif age_seconds > challenge_config.maximum_market_metadata_age_seconds:
            reasons.append("MARKET_METADATA_STALE")
        for field, value, unknown, rejected in (
            ("active", market_metadata.active, "MARKET_ACTIVE_STATUS_UNKNOWN", "MARKET_INACTIVE"),
            ("orderable", market_metadata.orderable, "MARKET_ORDERABILITY_UNKNOWN", "MARKET_NOT_ORDERABLE"),
            ("is_spot", market_metadata.is_spot, "MARKET_SPOT_STATUS_UNKNOWN", "MARKET_NOT_SPOT"),
            ("challenge_enabled", market_metadata.challenge_enabled, "CHALLENGE_MARKET_STATUS_UNKNOWN", "MARKET_NOT_ENABLED_FOR_CHALLENGE"),
            ("precision_semantics_verified", market_metadata.precision_semantics_verified, "ORDER_PRECISION_SEMANTICS_UNKNOWN", "ORDER_PRECISION_SEMANTICS_UNVERIFIED"),
            ("minimum_order_value_verified", market_metadata.minimum_order_value_verified, "MINIMUM_ORDER_VALUE_UNKNOWN", "MINIMUM_ORDER_VALUE_UNVERIFIED"),
        ):
            if value is None:
                reasons.append(unknown)
            elif value is False:
                reasons.append(rejected)
    if market_metadata is not None:
        if market_metadata.price_precision is None or market_metadata.amount_precision is None:
            reasons.append("ORDER_PRECISION_METADATA_MISSING")
        if market_metadata.minimum_order_value_tmn is None:
            reasons.append("MINIMUM_ORDER_VALUE_METADATA_MISSING")
    return EligibilityDecision(not reasons, pair, tuple(dict.fromkeys(reasons)), evidence, tuple(dict.fromkeys(warnings)))


@dataclass(frozen=True, slots=True)
class OrderAmountDecision:
    allowed: bool
    reason_codes: tuple[str, ...]
    notional_quote: Decimal | None


def validate_market_order_amounts(
    market: MarketSnapshot,
    quantity: Decimal | str | int,
    price: Decimal | str | int,
    *,
    allow_synthetic_fixture_evidence: bool = False,
) -> OrderAmountDecision:
    """Validate caller-supplied decimal scale/minimums only when their semantics are verified."""
    if not isinstance(allow_synthetic_fixture_evidence, bool):
        raise ChallengePolicyError("allow_synthetic_fixture_evidence must be an explicit boolean")
    reasons: list[str] = []
    try:
        exact_quantity = _decimal(quantity, "quantity")
        exact_price = _decimal(price, "price")
    except ChallengePolicyError:
        return OrderAmountDecision(False, ("INVALID_ORDER_DECIMAL",), None)
    if exact_quantity <= 0 or exact_price <= 0:
        return OrderAmountDecision(False, ("NONPOSITIVE_ORDER_QUANTITY_OR_PRICE",), None)
    if market.evidence_status != "OFFICIAL_SOURCE_VERIFIED" and not (allow_synthetic_fixture_evidence and market.evidence_status == "SYNTHETIC_FIXTURE"):
        reasons.append("ORDER_METADATA_NOT_OFFICIALLY_VERIFIED")
    if market.precision_semantics_verified is not True or market.price_precision is None or market.amount_precision is None:
        reasons.append("ORDER_PRECISION_SEMANTICS_UNKNOWN")
    else:
        if max(0, -exact_price.as_tuple().exponent) > market.price_precision:
            reasons.append("PRICE_PRECISION_EXCEEDED")
        if max(0, -exact_quantity.as_tuple().exponent) > market.amount_precision:
            reasons.append("AMOUNT_PRECISION_EXCEEDED")
    if market.minimum_order_value_verified is not True or market.minimum_order_value_tmn is None:
        reasons.append("MINIMUM_ORDER_VALUE_UNKNOWN")
    quote = market.pair.split("/", 1)[1]
    if quote != "TMN":
        reasons.append("TMN_MINIMUM_NOTIONAL_NOT_APPLICABLE_TO_NON_TMN_QUOTE")
        notional = None
    else:
        notional = exact_quantity * exact_price
        if market.minimum_order_value_tmn is not None and notional < market.minimum_order_value_tmn:
            reasons.append("MINIMUM_ORDER_VALUE_NOT_MET")
    return OrderAmountDecision(not reasons, tuple(dict.fromkeys(reasons)), notional)


def load_challenge_mode_policy(path: str | Path) -> ChallengeModePolicy:
    """Load the checked-in policy while refusing any attempt to turn on execution."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ChallengePolicyError(f"cannot read challenge mode policy: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != "1.0":
        raise ChallengePolicyError("challenge mode policy must use schema_version 1.0")
    if data.get("evidence_status") != "PROVIDED_BY_CHALLENGE_BRIEF":
        raise ChallengePolicyError("challenge mode facts must remain tagged as user-provided")
    if data.get("execution_scope") != "offline_only":
        raise ChallengePolicyError("challenge policy must explicitly restrict execution to offline-only")
    return ChallengeModePolicy(
        initial_capital_tmn=_decimal(data.get("initial_capital_tmn"), "initial_capital_tmn"),
        spot_only=data.get("spot_only"), leverage_enabled=data.get("leverage_enabled"),
        margin_enabled=data.get("margin_enabled"), borrowing_enabled=data.get("borrowing_enabled"),
        short_selling_enabled=data.get("short_selling_enabled"), withdrawals_enabled=data.get("withdrawals_enabled"),
        transfers_enabled=data.get("transfers_enabled"), deposits_enabled=data.get("deposits_enabled"),
        manual_trading_counts=data.get("manual_trading_counts"),
        live_trading_enabled_by_default=data.get("live_trading_enabled_by_default"),
        require_algorithmic_decision_log=data.get("require_algorithmic_decision_log"),
        require_end_state_tmn=data.get("require_end_state_tmn"),
        enabled_quote_assets=tuple(data.get("enabled_quote_assets", [])),
        usdt_quote_enabled=data.get("usdt_quote_enabled"),
        maximum_market_metadata_age_seconds=data.get("maximum_market_metadata_age_seconds"),
        official_cutoff_utc=data.get("official_cutoff_utc"),
        official_cutoff_status=data.get("official_cutoff_status", "REQUIRES_ORGANIZER_CONFIRMATION"),
        explicit_configuration=True,
    )


def sha256_canonical(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
