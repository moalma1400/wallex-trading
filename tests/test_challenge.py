from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

from wallex_research.challenge import (
    ChallengeModePolicy,
    ChallengePolicyError,
    ConversionPathEvidence,
    DisabledPairRegistry,
    MarketRequest,
    MarketSnapshot,
    is_challenge_spot_market_allowed,
    build_disabled_pair_registry,
    load_challenge_mode_policy,
    normalize_spot_pair,
    validate_market_order_amounts,
)
from wallex_research.challenge_execution import ChallengeExecutionError, ExecutionMode, dispatch_order_intent
from wallex_research.challenge_risk import (
    ChallengeRiskLimits,
    RiskObservation,
    RiskProposal,
    evaluate_challenge_risk,
    load_challenge_risk_limits,
)
from wallex_research.challenge_settlement import SettlementSnapshot, validate_settlement_readiness
from wallex_research.decision_log import (
    DecisionAuditLog,
    DecisionEvent,
    DecisionLogError,
    EventOrigin,
    StructuredAIOutput,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/challenge/wallex_disabled_spot_pairs.json"
POLICY_FILE = ROOT / "config/challenge/wallex_hackathon_policy.json"
FIXTURES = ROOT / "tests/fixtures"
UTC = timezone.utc
NOW = datetime(2026, 10, 20, 12, 5, tzinfo=UTC)


def good_market(pair="SYNTHETICGOOD/TMN", **overrides):
    values = dict(
        pair=pair,
        active=True,
        orderable=True,
        is_spot=True,
        challenge_enabled=True,
        observed_at_utc=NOW - timedelta(minutes=1),
        source_id="SYNTHETIC-MARKET-FIXTURE",
        evidence_status="SYNTHETIC_FIXTURE",
        price_precision=2,
        amount_precision=4,
        precision_semantics_verified=True,
        minimum_order_value_tmn="1000",
        minimum_order_value_verified=True,
    )
    values.update(overrides)
    return MarketSnapshot(**values)


def request(pair="SYNTHETICGOOD/TMN", **overrides):
    values = dict(
        pair=pair,
        instrument_type="spot",
        leverage="1",
        margin=False,
        borrowed=False,
        short_selling=False,
        strategy_allows_pair=True,
        risk_approved=True,
        algorithmic_decision=True,
    )
    values.update(overrides)
    return MarketRequest(**values)


def configured_policy(**overrides):
    values = {"explicit_configuration": True}
    values.update(overrides)
    return ChallengeModePolicy(**values)


def good_risk_limits():
    return ChallengeRiskLimits(
        maximum_order_notional_tmn="500000",
        maximum_asset_exposure_tmn="2000000",
        maximum_total_deployed_tmn="4000000",
        maximum_open_orders=3,
        maximum_orders_per_window=5,
        maximum_daily_loss_tmn="250000",
        maximum_peak_drawdown_percent="8",
        maximum_consecutive_losses=4,
        maximum_consecutive_errors=3,
        maximum_market_data_age_seconds=30,
        maximum_ai_signal_age_seconds=10,
        maximum_spread_basis_points="100",
        maximum_total_cost_basis_points="150",
        maximum_slippage_basis_points="50",
        maximum_liquidity_utilization_percent="20",
    )


def good_observation(**overrides):
    values = dict(
        open_orders=0,
        orders_in_window=0,
        daily_loss_tmn="0",
        peak_drawdown_percent="0",
        consecutive_losses=0,
        consecutive_errors=0,
        market_data_age_seconds=2,
        ai_signal_age_seconds=1,
        account_reconciled=True,
        orders_reconciled=True,
        emergency_stop_active=False,
    )
    values.update(overrides)
    return RiskObservation(**values)


def good_proposal(**overrides):
    values = dict(
        pair="SYNTHETICGOOD/TMN",
        notional_tmn="10000",
        asset_exposure_after_tmn="20000",
        total_deployed_after_tmn="30000",
        worst_case_loss_tmn="1000",
        projected_drawdown_percent="1",
        estimated_spread_basis_points="5",
        estimated_slippage_basis_points="2",
        liquidity_utilization_percent="5",
        estimated_total_cost_basis_points="10",
        side="BUY",
        fees_known=True,
    )
    values.update(overrides)
    return RiskProposal(**values)


def evaluate_with_synthetic_evidence(proposal=None, observation=None, limits=None, **evidence):
    values = dict(
        initial_capital_tmn="5000000",
        capital_evidence_status="SYNTHETIC_FIXTURE",
        capital_source_id="SYNTHETIC_FIXTURE:capital",
        available_balance_tmn="1000000",
        available_balance_evidence_status="SYNTHETIC_FIXTURE",
        available_balance_source_id="SYNTHETIC_FIXTURE:balance",
        allow_synthetic_fixture_evidence=True,
    )
    values.update(evidence)
    return evaluate_challenge_risk(
        proposal or good_proposal(),
        observation or good_observation(),
        limits or good_risk_limits(),
        **values,
    )


class DisabledPairsAndEligibilityTests(unittest.TestCase):
    def test_registry_builder_deduplicates_canonical_data_but_preserves_diagnostics(self):
        result = build_disabled_pair_registry(b"a/tmn\nA/TMN\nBAD_PAIR/TMN\n")
        self.assertEqual(result["disabled_pairs"], ["A/TMN"])
        self.assertEqual(result["raw_entry_count"], 3)
        self.assertEqual(result["unique_pair_count"], 1)
        self.assertEqual(result["duplicate_pair_count"], 1)
        self.assertEqual(result["duplicate_excess_entry_count"], 1)
        self.assertEqual(result["malformed_entries"], [{"line": 3, "raw": "BAD_PAIR/TMN"}])

    def test_machine_list_matches_raw_source_and_reports_counts(self):
        registry = DisabledPairRegistry.load(CONFIG)
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(registry.raw_entry_count, 345)
        self.assertEqual(len(registry.disabled_pairs), 345)
        self.assertEqual(config["raw_entry_count"], config["unique_pair_count"])
        self.assertEqual(config["duplicate_entries"], [])
        self.assertEqual(config["malformed_entries"], [])
        self.assertEqual(config["disabled_pairs"], sorted(registry.disabled_pairs))
        self.assertEqual(build_disabled_pair_registry((ROOT / config["raw_source_file"]).read_bytes()), config)
        self.assertEqual(registry.raw_source_sha256, config["raw_source_sha256"])
        self.assertTrue(registry.contains(" A/TMN "))
        self.assertTrue(registry.contains("a/tmn"))

    def test_registry_rejects_raw_file_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "config", root / "config")
            raw = root / "config/challenge/wallex_disabled_spot_pairs_raw.txt"
            raw.write_text(raw.read_text(encoding="utf-8") + "NEW/TMN\n", encoding="utf-8")
            with self.assertRaisesRegex(ChallengePolicyError, "fingerprint"):
                DisabledPairRegistry.load(root / "config/challenge/wallex_disabled_spot_pairs.json", repository_root=root)

    def test_duplicate_raw_pairs_are_reported_and_registry_refuses_runtime_use(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_dir = root / "config/challenge"
            config_dir.mkdir(parents=True)
            raw_path = config_dir / "raw.txt"
            raw_path.write_text("A/TMN\na/tmn\n", encoding="utf-8")
            raw_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
            config = {
                "schema_version": "1.0", "source_id": "SYNTHETIC-TEST",
                "evidence_status": "PROVIDED_BY_CHALLENGE_BRIEF", "raw_source_file": "config/challenge/raw.txt",
                "raw_source_sha256": raw_hash, "raw_entry_count": 2, "unique_pair_count": 1,
                "duplicate_pair_count": 1, "duplicate_excess_entry_count": 1,
                "duplicate_entries": [{"pair": "A/TMN", "count": 2, "extra_occurrences": 1}],
                "malformed_entry_count": 0, "malformed_entries": [], "disabled_pairs": ["A/TMN"],
            }
            config_path = config_dir / "pairs.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ChallengePolicyError, "duplicate or malformed"):
                DisabledPairRegistry.load(config_path, repository_root=root)

    def test_pair_syntax_and_normalization_are_explicit(self):
        self.assertEqual(normalize_spot_pair("  btc/tMn  "), "BTC/TMN")
        for malformed in ("BTC /TMN", "BTC/TMN/ETH", "/TMN", "BTC/", "BTC-TMN", "BTC/USDT?", "ß/TMN"):
            with self.subTest(malformed=malformed), self.assertRaises(ChallengePolicyError):
                normalize_spot_pair(malformed)

    def test_fixture_pair_passes_only_under_explicit_synthetic_test_mode(self):
        policy = configured_policy(maximum_market_metadata_age_seconds=600)
        markets = json.loads((FIXTURES / "challenge_market_metadata.json").read_text(encoding="utf-8"))["markets"]
        row = next(item for item in markets if item["pair"] == "SYNTHETICGOOD/TMN")
        snapshot = MarketSnapshot(**{**row, "observed_at_utc": NOW - timedelta(minutes=1), "source_id": "SYNTHETIC-MARKET-FIXTURE", "evidence_status": "SYNTHETIC_FIXTURE"})
        denied = is_challenge_spot_market_allowed(request(), snapshot, policy, DisabledPairRegistry.load(CONFIG), now_utc=NOW)
        self.assertFalse(denied.eligible)
        self.assertIn("MARKET_METADATA_NOT_OFFICIALLY_VERIFIED", denied.reason_codes)
        allowed_for_fixture_test = is_challenge_spot_market_allowed(
            request(), snapshot, policy, DisabledPairRegistry.load(CONFIG), now_utc=NOW,
            allow_synthetic_fixture_evidence=True,
        )
        self.assertTrue(allowed_for_fixture_test.eligible, allowed_for_fixture_test.reason_codes)
        self.assertIn("SYNTHETIC_FIXTURE_NOT_RUNTIME_AUTHORIZATION", allowed_for_fixture_test.warning_codes)

    def test_explicit_challenge_config_and_risk_approval_are_required(self):
        registry = DisabledPairRegistry.load(CONFIG)
        metadata = good_market()
        unconfigured = is_challenge_spot_market_allowed(
            request(), metadata, ChallengeModePolicy(maximum_market_metadata_age_seconds=600),
            registry, now_utc=NOW, allow_synthetic_fixture_evidence=True,
        )
        self.assertIn("CHALLENGE_CONFIGURATION_NOT_EXPLICIT", unconfigured.reason_codes)
        no_risk_approval = is_challenge_spot_market_allowed(
            request(risk_approved=False), metadata,
            configured_policy(maximum_market_metadata_age_seconds=600), registry,
            now_utc=NOW, allow_synthetic_fixture_evidence=True,
        )
        self.assertIn("RISK_POLICY_NOT_APPROVED", no_risk_approval.reason_codes)
        manual = is_challenge_spot_market_allowed(
            request(algorithmic_decision=False), metadata,
            configured_policy(maximum_market_metadata_age_seconds=600), registry,
            now_utc=NOW, allow_synthetic_fixture_evidence=True,
        )
        self.assertIn("NON_ALGORITHMIC_INTENT", manual.reason_codes)

    def test_disabled_pair_is_denied_even_when_metadata_says_active(self):
        decision = is_challenge_spot_market_allowed(
            request("A/TMN"), good_market("A/TMN"), configured_policy(maximum_market_metadata_age_seconds=600),
            DisabledPairRegistry.load(CONFIG), now_utc=NOW, allow_synthetic_fixture_evidence=True,
        )
        self.assertFalse(decision.eligible)
        self.assertIn("PAIR_DISABLED_BY_CHALLENGE_BRIEF", decision.reason_codes)
        self.assertIn("CONTRADICTORY_DISABLED_MARKET_ACTIVE", decision.reason_codes)

    def test_missing_unknown_stale_future_and_contradictory_metadata_fail_closed(self):
        registry = DisabledPairRegistry.load(CONFIG)
        policy = configured_policy(maximum_market_metadata_age_seconds=60)
        missing = is_challenge_spot_market_allowed(request(), None, policy, registry, now_utc=NOW)
        self.assertIn("MARKET_METADATA_MISSING", missing.reason_codes)
        stale = is_challenge_spot_market_allowed(
            request(), good_market(observed_at_utc=NOW - timedelta(minutes=2)), policy, registry,
            now_utc=NOW, allow_synthetic_fixture_evidence=True,
        )
        self.assertIn("MARKET_METADATA_STALE", stale.reason_codes)
        future = is_challenge_spot_market_allowed(
            request(), good_market(observed_at_utc=NOW + timedelta(seconds=1)), policy, registry,
            now_utc=NOW, allow_synthetic_fixture_evidence=True,
        )
        self.assertIn("MARKET_METADATA_FROM_FUTURE", future.reason_codes)
        unknown = is_challenge_spot_market_allowed(
            request(), good_market(orderable=None), policy, registry, now_utc=NOW,
            allow_synthetic_fixture_evidence=True,
        )
        self.assertIn("MARKET_ORDERABILITY_UNKNOWN", unknown.reason_codes)
        contradictory = is_challenge_spot_market_allowed(
            request(), good_market(active=False, orderable=True), policy, registry, now_utc=NOW,
            allow_synthetic_fixture_evidence=True,
        )
        self.assertIn("MARKET_INACTIVE", contradictory.reason_codes)
        self.assertIn("MARKET_METADATA_STATE_CONTRADICTORY", contradictory.reason_codes)

    def test_unconfigured_metadata_age_and_unknown_quote_fail(self):
        registry = DisabledPairRegistry.load(CONFIG)
        unknown_age = is_challenge_spot_market_allowed(
            request(), good_market(), configured_policy(), registry, now_utc=NOW,
            allow_synthetic_fixture_evidence=True,
        )
        self.assertIn("MARKET_METADATA_MAX_AGE_UNCONFIGURED", unknown_age.reason_codes)
        unknown_quote = is_challenge_spot_market_allowed(
            request("SYNTHETIC/BTC"), None, configured_policy(maximum_market_metadata_age_seconds=30), registry, now_utc=NOW,
        )
        self.assertIn("UNSUPPORTED_QUOTE_ASSET", unknown_quote.reason_codes)

    def test_order_precision_and_minimum_value_require_verified_market_metadata(self):
        market = good_market()
        valid = validate_market_order_amounts(market, "1.2300", "1000.00", allow_synthetic_fixture_evidence=True)
        self.assertTrue(valid.allowed, valid.reason_codes)
        self.assertEqual(valid.notional_quote, Decimal("1230.000000"))
        price_scale = validate_market_order_amounts(market, "1", "1000.001", allow_synthetic_fixture_evidence=True)
        self.assertIn("PRICE_PRECISION_EXCEEDED", price_scale.reason_codes)
        amount_scale = validate_market_order_amounts(market, "1.00001", "1000", allow_synthetic_fixture_evidence=True)
        self.assertIn("AMOUNT_PRECISION_EXCEEDED", amount_scale.reason_codes)
        below_minimum = validate_market_order_amounts(market, "0.5", "1000", allow_synthetic_fixture_evidence=True)
        self.assertIn("MINIMUM_ORDER_VALUE_NOT_MET", below_minimum.reason_codes)
        unknown = validate_market_order_amounts(good_market(precision_semantics_verified=None), "1", "1000", allow_synthetic_fixture_evidence=True)
        self.assertIn("ORDER_PRECISION_SEMANTICS_UNKNOWN", unknown.reason_codes)

    def test_usdt_quote_requires_verified_permitted_conversion_and_cutoff(self):
        with self.assertRaisesRegex(ChallengePolicyError, "USDT quotes require"):
            ChallengeModePolicy(enabled_quote_assets=("TMN", "USDT"), usdt_quote_enabled=True)
        with self.assertRaisesRegex(ChallengePolicyError, "official cutoff"):
            ChallengeModePolicy(enabled_quote_assets=("TMN", "USDT"), usdt_quote_enabled=True, usdt_conversion_evidence=object())
        with self.assertRaises(ChallengePolicyError):
            ConversionPathEvidence("route", "PROVIDED_BY_CHALLENGE_BRIEF", "https://example.invalid", True, True, NOW, NOW)
        denied = is_challenge_spot_market_allowed(
            request("SYNTHETIC/USDT"), None, configured_policy(maximum_market_metadata_age_seconds=30),
            DisabledPairRegistry.load(CONFIG), now_utc=NOW,
        )
        self.assertIn("TMN_CONVERSION_UNVERIFIED", denied.reason_codes)

    def test_nonspot_leverage_margin_borrow_and_short_attempts_are_rejected(self):
        registry = DisabledPairRegistry.load(CONFIG)
        policy = configured_policy(maximum_market_metadata_age_seconds=600)
        attempted = request(instrument_type="margin", leverage="2", margin=True, borrowed=True, short_selling=True)
        decision = is_challenge_spot_market_allowed(
            attempted, good_market(), policy, registry, now_utc=NOW, allow_synthetic_fixture_evidence=True,
        )
        self.assertFalse(decision.eligible)
        for code in ("NON_SPOT_INSTRUMENT", "LEVERAGE_FORBIDDEN", "MARGIN_FORBIDDEN", "BORROWING_FORBIDDEN", "SHORT_SELLING_FORBIDDEN"):
            self.assertIn(code, decision.reason_codes)

    def test_synthetic_evidence_flag_requires_boolean_type(self):
        with self.assertRaises(ChallengePolicyError):
            is_challenge_spot_market_allowed(
                request(), good_market(), configured_policy(), DisabledPairRegistry.load(CONFIG),
                now_utc=NOW, allow_synthetic_fixture_evidence=1,
            )  # type: ignore[arg-type]
        with self.assertRaises(ChallengePolicyError):
            validate_market_order_amounts(
                good_market(), "1", "1", allow_synthetic_fixture_evidence=1,
            )  # type: ignore[arg-type]

    def test_unsafe_mode_flags_cannot_be_enabled(self):
        for field in ("leverage_enabled", "margin_enabled", "borrowing_enabled", "short_selling_enabled", "withdrawals_enabled", "transfers_enabled", "deposits_enabled", "manual_trading_counts", "live_trading_enabled_by_default"):
            with self.subTest(field=field), self.assertRaises(ChallengePolicyError):
                ChallengeModePolicy(**{field: True})
        loaded = load_challenge_mode_policy(POLICY_FILE)
        self.assertEqual(loaded.initial_capital_tmn, Decimal("5000000"))
        self.assertFalse(loaded.live_trading_enabled_by_default)
        self.assertTrue(loaded.explicit_configuration)
        self.assertEqual(loaded.official_cutoff_status, "REQUIRES_ORGANIZER_CONFIRMATION")
        configured_risk_limits = load_challenge_risk_limits(POLICY_FILE)
        self.assertEqual(len(configured_risk_limits.missing_limits), 15)


class RiskAndModeIsolationTests(unittest.TestCase):
    def test_unreviewed_risk_config_cannot_enable_a_numeric_limit(self):
        config = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
        config["risk_limits"]["maximum_order_notional_tmn"] = "100000"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            limits = load_challenge_risk_limits(path)
        self.assertEqual(len(limits.missing_limits), 15)

    def test_missing_risk_limits_and_unknown_state_block(self):
        result = evaluate_challenge_risk(good_proposal(), good_observation(), ChallengeRiskLimits())
        self.assertFalse(result.allowed)
        self.assertIn("RISK_LIMIT_MISSING:maximum_order_notional_tmn", result.reason_codes)
        self.assertIn("UNVERIFIED_BASELINE", result.reason_codes)
        self.assertIn("AVAILABLE_BALANCE_UNKNOWN", result.reason_codes)
        limits = good_risk_limits()
        missing_state = evaluate_with_synthetic_evidence(
            good_proposal(), good_observation(account_reconciled=None), limits,
        )
        self.assertFalse(missing_state.allowed)
        self.assertIn("ACCOUNT_RECONCILIATION_NOT_CONFIRMED", missing_state.reason_codes)

    def test_sell_side_blocks_without_base_asset_balance_validation(self):
        result = evaluate_with_synthetic_evidence(good_proposal(side="SELL"))
        self.assertFalse(result.allowed)
        self.assertIn("SELL_BASE_BALANCE_VALIDATION_NOT_IMPLEMENTED", result.reason_codes)

    def test_synthetic_evidence_cannot_clear_live_style_gate_without_fixture_opt_in(self):
        result = evaluate_challenge_risk(
            good_proposal(), good_observation(), good_risk_limits(),
            capital_evidence_status="SYNTHETIC_FIXTURE",
            capital_source_id="SYNTHETIC_FIXTURE:capital",
            available_balance_tmn="1000000",
            available_balance_evidence_status="SYNTHETIC_FIXTURE",
            available_balance_source_id="SYNTHETIC_FIXTURE:balance",
        )
        self.assertFalse(result.allowed)
        self.assertIn("UNVERIFIED_BASELINE", result.reason_codes)
        self.assertIn("AVAILABLE_BALANCE_PROVENANCE_MISSING", result.reason_codes)

    def test_capital_and_available_balance_evidence_are_mandatory(self):
        no_capital = evaluate_with_synthetic_evidence(capital_evidence_status="UNRESOLVED")
        self.assertFalse(no_capital.allowed)
        self.assertIn("UNVERIFIED_BASELINE", no_capital.reason_codes)

        no_balance = evaluate_with_synthetic_evidence(available_balance_tmn=None)
        self.assertFalse(no_balance.allowed)
        self.assertIn("AVAILABLE_BALANCE_UNKNOWN", no_balance.reason_codes)

        insufficient = evaluate_with_synthetic_evidence(available_balance_tmn="1")
        self.assertFalse(insufficient.allowed)
        self.assertIn("AVAILABLE_BALANCE_INSUFFICIENT", insufficient.reason_codes)

    def test_explicit_risk_limits_allow_only_with_all_gates_and_block_breaches(self):
        limits = good_risk_limits()
        allowed = evaluate_with_synthetic_evidence(good_proposal(), good_observation(), limits)
        self.assertTrue(allowed.allowed, allowed.reason_codes)
        blocked = evaluate_with_synthetic_evidence(
            good_proposal(notional_tmn="600000", projected_drawdown_percent="9", estimated_spread_basis_points="120", estimated_slippage_basis_points="60", liquidity_utilization_percent="25"),
            good_observation(market_data_age_seconds=31, consecutive_errors=3), limits,
        )
        for code in ("ORDER_NOTIONAL_LIMIT_EXCEEDED", "PROJECTED_DRAWDOWN_LIMIT_EXCEEDED", "SPREAD_LIMIT_EXCEEDED", "SLIPPAGE_LIMIT_EXCEEDED", "LIQUIDITY_UTILIZATION_LIMIT_EXCEEDED", "MARKET_DATA_STALE", "ERROR_COOLDOWN_ACTIVE"):
            self.assertIn(code, blocked.reason_codes)

    def test_risk_limits_never_allow_full_capital_single_order(self):
        values = {name: getattr(good_risk_limits(), name) for name in good_risk_limits().__dataclass_fields__}
        values["maximum_order_notional_tmn"] = "5000000"
        decision = evaluate_with_synthetic_evidence(
            good_proposal(), good_observation(), ChallengeRiskLimits(**values),
        )
        self.assertIn("MAX_ORDER_MUST_BE_LESS_THAN_INITIAL_CAPITAL", decision.reason_codes)

    def test_backtest_shadow_and_dry_run_never_call_submit_adapter_live_fails_closed(self):
        submit = Mock(side_effect=AssertionError("must never be called"))
        for mode in (ExecutionMode.BACKTEST, ExecutionMode.SHADOW, ExecutionMode.DRY_RUN):
            result = dispatch_order_intent("intent-1", mode, submit_order=submit)
            self.assertFalse(result.submitted)
            self.assertEqual(result.status, "recorded_only")
        self.assertEqual(submit.call_count, 0)
        live = dispatch_order_intent("intent-2", ExecutionMode.LIVE, submit_order=submit)
        self.assertFalse(live.submitted)
        self.assertEqual(live.reason_code, "LIVE_EXECUTION_NOT_IMPLEMENTED")
        self.assertEqual(submit.call_count, 0)
        with self.assertRaises(ChallengeExecutionError):
            dispatch_order_intent("intent-3", "dry_run", live_trading_enabled_by_default=True)


class DecisionLogAndSettlementTests(unittest.TestCase):
    def test_ai_output_schema_falls_back_to_hold_and_preserves_evidence(self):
        result = StructuredAIOutput.from_mapping_or_hold({
            "action": "buy", "confidence": "0.75", "horizon": "user-configured",
            "supporting_feature_refs": ["snapshot:1"], "counter_evidence": ["spread elevated"],
            "rationale": "Fixture-only example",
        })
        self.assertEqual(result.action, "BUY")
        self.assertEqual(result.as_dict()["confidence"], "0.75")
        fallback = StructuredAIOutput.from_mapping_or_hold({"action": "BUY", "confidence": 2})
        self.assertEqual(fallback.action, "HOLD")
        self.assertIsNotNone(fallback.fallback_reason)

    def test_audit_events_have_stable_ids_and_log_rejects_secrets_pii_and_exchange_origin(self):
        event = DecisionEvent(
            run_id="synthetic-run", sequence=1, occurred_at_utc=NOW, event_type="risk_check",
            origin=EventOrigin.DRY_RUN, code_commit="b" * 40, config_sha256="a" * 64,
            strategy_version="synthetic-no-strategy", payload={"proposal_id": "proposal-1", "allowed": False, "reason_codes": ["RISK_VETO"], "risk_config_sha256": "c" * 64},
            feature_snapshot_refs=("fixture:market-1",),
        )
        same = DecisionEvent(
            run_id="synthetic-run", sequence=1, occurred_at_utc=NOW, event_type="risk_check",
            origin=EventOrigin.DRY_RUN, code_commit="b" * 40, config_sha256="a" * 64,
            strategy_version="synthetic-no-strategy", payload={"proposal_id": "proposal-1", "allowed": False, "reason_codes": ["RISK_VETO"], "risk_config_sha256": "c" * 64},
            feature_snapshot_refs=("fixture:market-1",),
        )
        self.assertEqual(event.event_id, same.event_id)
        with tempfile.TemporaryDirectory() as directory:
            log = DecisionAuditLog(Path(directory) / "events.jsonl")
            log.append(event)
            self.assertEqual(log.event_count, 1)
            with self.assertRaises(DecisionLogError):
                log.append(same)
            with self.assertRaises(DecisionLogError):
                DecisionEvent(
                    run_id="bad", sequence=1, occurred_at_utc=NOW, event_type="order_intent", origin="dry_run",
                    code_commit="d" * 40, config_sha256="a" * 64, strategy_version="x", payload={"intent_id": "i", "idempotency_key": "k", "pair": "BTC/TMN", "side": "BUY", "quantity": "1", "notional_tmn": "1000", "risk_event_id": "r", "phone": "SYNTHETIC-REDACTED"},
                )
            with self.assertRaises(DecisionLogError):
                DecisionEvent(
                    run_id="bad", sequence=1, occurred_at_utc=NOW, event_type="order_intent", origin="dry_run",
                    code_commit="d" * 40, config_sha256="a" * 64, strategy_version="x", payload={"intent_id": "i", "idempotency_key": "k", "pair": "BTC/TMN", "side": "BUY", "quantity": "1", "notional_tmn": "1000", "risk_event_id": "r", "key": "Bearer " + "synthetic-" + "x" * 24},
                )
            with self.assertRaisesRegex(DecisionLogError, "allowed must be boolean"):
                DecisionEvent(
                    run_id="bad", sequence=2, occurred_at_utc=NOW, event_type="risk_check", origin="dry_run",
                    code_commit="d" * 40, config_sha256="a" * 64, strategy_version="x",
                    payload={"proposal_id": "p", "allowed": "false", "reason_codes": ["blocked"], "risk_config_sha256": "c" * 64},
                )
            with self.assertRaises(DecisionLogError):
                DecisionEvent(
                    run_id="bad", sequence=1, occurred_at_utc=NOW, event_type="order_intent", origin="exchange",
                    code_commit="d" * 40, config_sha256="a" * 64, strategy_version="x", payload={"proposal_id": "p", "allowed": False, "reason_codes": ["blocked"], "risk_config_sha256": "c" * 64},
                )
            with self.assertRaises(DecisionLogError):
                DecisionEvent(
                    run_id="bad", sequence=1, occurred_at_utc=NOW, event_type="market_snapshot", origin="dry_run",
                    code_commit="d" * 40, config_sha256="a" * 64, strategy_version="x", payload={"snapshot_ref": "s", "pair": "BTC/TMN", "observed_at_utc": NOW, "source_id": "test", "evidence_status": "SYNTHETIC_FIXTURE", "price": 1.25},
                )

    def test_ai_event_requires_model_and_prompt_provenance(self):
        with self.assertRaisesRegex(DecisionLogError, "AI analysis events require"):
            DecisionEvent(
                run_id="run", sequence=1, occurred_at_utc=NOW, event_type="ai_analysis", origin="backtest",
                code_commit="c" * 40, config_sha256="a" * 64, strategy_version="demo",
                payload={"action": "HOLD", "confidence": "0", "horizon": "test", "supporting_feature_refs": [], "counter_evidence": [], "rationale": "No model output"},
            )

    def test_unresolved_cutoff_and_residual_inventory_fail_settlement_readiness(self):
        snap = SettlementSnapshot(NOW, {"TMN": "4900000", "BTC": "0.1"}, "-100000", None, None, False, False)
        result = validate_settlement_readiness(
            snap, official_cutoff_utc=None, cutoff_evidence_status="REQUIRES_ORGANIZER_CONFIRMATION",
        )
        self.assertFalse(result.ready)
        for code in ("OFFICIAL_CUTOFF_UNRESOLVED", "NON_TMN_INVENTORY_REMAINS", "FEES_UNKNOWN", "UNREALIZED_PNL_STATUS_UNKNOWN"):
            self.assertIn(code, result.reason_codes)
        self.assertIsNone(result.final_value_tmn)
        self.assertIsNone(result.net_return_percent)

    def test_synthetic_tmn_only_end_state_cannot_clear_baseline_blocker(self):
        cutoff = NOW
        snap = SettlementSnapshot(
            cutoff, {"TMN": "5250000", "BTC": "0"}, "300000", "0", "50000", True, True,
            valuation_status="INTERNAL_ESTIMATE", evidence_status="SYNTHETIC_FIXTURE",
        )
        result = validate_settlement_readiness(
            snap, official_cutoff_utc=cutoff, cutoff_evidence_status="SYNTHETIC_FIXTURE",
            allow_synthetic_fixture_evidence=True, capital_evidence_status="SYNTHETIC_FIXTURE",
        )
        self.assertFalse(result.ready, result.reason_codes)
        self.assertIn("UNVERIFIED_BASELINE", result.reason_codes)
        self.assertIn("UNVERIFIED_BASELINE", result.warning_codes)
        self.assertIn("SYNTHETIC_FIXTURE_NOT_OFFICIAL_SETTLEMENT_EVIDENCE", result.warning_codes)
        self.assertIn("SYNTHETIC_CAPITAL_NOT_OFFICIAL_EVIDENCE", result.warning_codes)
        self.assertEqual(result.valuation_status, "INTERNAL_ESTIMATE")
        self.assertEqual(result.evidence_status, "SYNTHETIC_FIXTURE")
        self.assertIsNone(result.final_value_tmn)
        self.assertIsNone(result.net_return_percent)
        self.assertEqual(result.realized_pnl_tmn, Decimal("300000"))
        self.assertEqual(result.fees_tmn, Decimal("50000"))
        self.assertEqual(result.capital_evidence_status, "SYNTHETIC_FIXTURE")

    def test_unverified_baseline_blocks_settlement_readiness(self):
        cutoff = NOW
        snap = SettlementSnapshot(
            cutoff, {"TMN": "5250000", "BTC": "0"}, "300000", "0", "50000", True, True,
            valuation_status="INTERNAL_ESTIMATE", evidence_status="SYNTHETIC_FIXTURE",
        )
        result = validate_settlement_readiness(
            snap, official_cutoff_utc=cutoff, cutoff_evidence_status="SYNTHETIC_FIXTURE",
            allow_synthetic_fixture_evidence=True,
        )
        self.assertFalse(result.ready)
        self.assertIn("UNVERIFIED_BASELINE", result.reason_codes)
        self.assertIn("UNVERIFIED_BASELINE", result.warning_codes)
        self.assertIsNone(result.final_value_tmn)

    def test_synthetic_settlement_flag_requires_boolean_type(self):
        snapshot = SettlementSnapshot(NOW, {"TMN": "5000000"}, "0", "0", "0", True, True)
        with self.assertRaises(ChallengePolicyError):
            validate_settlement_readiness(
                snapshot, official_cutoff_utc=NOW, cutoff_evidence_status="SYNTHETIC_FIXTURE",
                allow_synthetic_fixture_evidence=1,
            )  # type: ignore[arg-type]

    def test_official_cutoff_requires_source_provenance(self):
        snapshot = SettlementSnapshot(
            NOW, {"TMN": "5000000"}, "0", "0", "0", True, True,
            valuation_status="INTERNAL_ESTIMATE", evidence_status="SYNTHETIC_FIXTURE",
        )
        result = validate_settlement_readiness(
            snapshot, official_cutoff_utc=NOW, cutoff_evidence_status="OFFICIAL_SOURCE_VERIFIED",
            allow_synthetic_fixture_evidence=True,
        )
        self.assertIn("OFFICIAL_CUTOFF_PROVENANCE_MISSING", result.reason_codes)
        self.assertIsNone(result.final_value_tmn)

    def test_internal_estimate_cannot_be_reported_as_official_settlement_value(self):
        snapshot = SettlementSnapshot(NOW, {"TMN": "5200000"}, "200000", "0", "0", True, True)
        result = validate_settlement_readiness(
            snapshot, official_cutoff_utc=NOW, cutoff_evidence_status="SYNTHETIC_FIXTURE",
            allow_synthetic_fixture_evidence=True,
        )
        self.assertFalse(result.ready)
        self.assertIn("FINAL_VALUATION_NOT_OFFICIALLY_VERIFIED", result.reason_codes)
        self.assertIsNone(result.final_value_tmn)
        self.assertEqual(result.valuation_status, "INTERNAL_ESTIMATE")

    def test_cutoff_mismatch_and_unrealized_pnl_block_settlement(self):
        snap = SettlementSnapshot(NOW - timedelta(seconds=1), {"TMN": "5000000"}, "0", "1", "0", True, True)
        result = validate_settlement_readiness(snap, official_cutoff_utc=NOW, cutoff_evidence_status="SYNTHETIC_FIXTURE", allow_synthetic_fixture_evidence=True)
        self.assertIn("SNAPSHOT_NOT_AT_OFFICIAL_CUTOFF", result.reason_codes)
        self.assertIn("UNREALIZED_PNL_REMAINS", result.reason_codes)
        self.assertFalse(result.ready)


if __name__ == "__main__":
    unittest.main()
