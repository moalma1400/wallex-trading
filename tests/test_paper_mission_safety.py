"""Offline safety + 20-candle mission tests.

Covers the paper kill switch, structural separation of paper/offline modules
from any network or live-order code, audit staleness, secret non-leakage in
provider configuration reporting, workflow trigger hygiene, and a
deterministic end-to-end run over the committed synthetic 20x1m fixture.
The fixture is invented test data, not market data.
"""

import ast
import importlib.util
import json
from pathlib import Path

import pytest

from wallex_agent.data_quality import audit_candles, audit_file
from wallex_agent.paper_trading import (
    PaperBroker,
    PaperTradingError,
    ensure_paper_trading_allowed,
)
from wallex_agent.paper_candle_cli import main as paper_candles_main

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_20x1m_candles.jsonl"

BROKER_KWARGS = dict(
    initial_cash="1000000", fee_bps="10", slippage_bps="20",
    max_order_notional="100000", max_daily_loss_percent="3",
)


def make_broker(tmp_path):
    return PaperBroker(tmp_path / "paper.sqlite3", **BROKER_KWARGS)


def test_kill_switch_blocks_broker_creation(tmp_path, monkeypatch):
    monkeypatch.setenv("WALLEX_PAPER_DISABLE", "1")
    with pytest.raises(PaperTradingError, match="kill switch"):
        make_broker(tmp_path)


def test_live_mode_environment_blocks_paper(tmp_path, monkeypatch):
    monkeypatch.setenv("WALLEX_ENABLE_LIVE_TRADING", "1")
    with pytest.raises(PaperTradingError, match="separate process"):
        make_broker(tmp_path)


def test_kill_switch_blocks_orders_after_startup_without_recording_fill(tmp_path, monkeypatch):
    broker = make_broker(tmp_path)
    monkeypatch.setenv("WALLEX_PAPER_DISABLE", "1")
    with pytest.raises(PaperTradingError, match="kill switch"):
        broker.execute_market_order(
            event_id="e1", timestamp="2026-01-01T00:00:00Z", symbol="BTCUSDT",
            side="buy", quantity="1", reference_price="100",
        )
    monkeypatch.delenv("WALLEX_PAPER_DISABLE")
    assert broker.snapshot()["cash"] == "1000000"
    assert ensure_paper_trading_allowed({}) is None
    assert ensure_paper_trading_allowed({"WALLEX_PAPER_DISABLE": "0"}) is None


OFFLINE_MODULES = [
    "src/wallex_agent/paper_trading.py",
    "src/wallex_agent/paper_trading_cli.py",
    "src/wallex_agent/paper_candle_strategy.py",
    "src/wallex_agent/paper_candle_cli.py",
    "src/wallex_agent/provider_reconciliation.py",
    "src/wallex_agent/reconciliation_cli.py",
    "src/wallex_agent/data_quality.py",
]
FORBIDDEN_IMPORT_ROOTS = {
    "httpx", "websockets", "socket", "requests", "wallex_mcp", "coingecko_mcp",
    "urllib",
}
FORBIDDEN_TEXT = [
    "/v1/account", "placeOrder", "create_order", "cancel_order", "withdraw",
]


@pytest.mark.parametrize("relative", OFFLINE_MODULES)
def test_paper_and_offline_modules_have_no_network_or_live_imports(relative):
    path = ROOT / relative
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not (imported & FORBIDDEN_IMPORT_ROOTS), f"{relative}: {imported}"
    text = path.read_text(encoding="utf-8")
    for marker in FORBIDDEN_TEXT:
        assert marker not in text, f"{relative} contains {marker!r}"


def fixture_lines():
    return FIXTURE.read_text(encoding="utf-8").splitlines()


def test_audit_stale_dataset_flagged_at_as_of():
    report = audit_candles(
        fixture_lines(), expected_symbol="BTCUSDT", expected_interval_seconds=60,
        as_of="2026-06-01T00:00:00Z", max_staleness_seconds=86400,
    )
    assert report["status"] == "REVIEW"
    assert any(issue["code"] == "STALE_DATASET" for issue in report["issues"])


def test_audit_fresh_at_as_of_and_future_detection():
    fresh = audit_candles(
        fixture_lines(), expected_symbol="BTCUSDT", expected_interval_seconds=60,
        as_of="2026-01-01T00:20:00Z", max_staleness_seconds=600,
    )
    assert fresh["status"] == "OK"
    assert fresh["dataset_age_seconds_at_as_of"] == 60  # last bucket starts 00:19
    future = audit_candles(
        fixture_lines(), as_of="2026-01-01T00:05:00Z", max_staleness_seconds=600,
    )
    assert any(issue["code"] == "DATASET_ENDS_AFTER_AS_OF" for issue in future["issues"])


def test_audit_staleness_arguments_must_be_paired_and_valid():
    with pytest.raises(ValueError, match="supplied together"):
        audit_candles(fixture_lines(), as_of="2026-01-01T00:20:00Z")
    with pytest.raises(ValueError):
        audit_candles(fixture_lines(), as_of="2026-01-01 00:20", max_staleness_seconds=60)


def test_audit_rejects_non_finite_prices():
    lines = fixture_lines()
    row = json.loads(lines[0])
    row["close"] = "NaN"
    report = audit_candles([json.dumps(row)] + lines[1:],
                           expected_symbol="BTCUSDT", expected_interval_seconds=60)
    assert report["status"] == "INVALID"
    assert any(issue["code"] == "INVALID_CANDLE" for issue in report["issues"])


def load_connectivity_script():
    spec = importlib.util.spec_from_file_location(
        "check_provider_connectivity", ROOT / "scripts/check_provider_connectivity.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_provider_config_report_never_contains_secret_values(monkeypatch):
    monkeypatch.setenv("COINGECKO_DEMO_API_KEY", "synthetic-demo-secret-value")
    monkeypatch.setenv("WALLEX_API_KEY", "synthetic-wallex-secret-value")
    module = load_connectivity_script()
    encoded = json.dumps(module.config_report())
    assert "synthetic-demo-secret-value" not in encoded
    assert "synthetic-wallex-secret-value" not in encoded
    assert '"COINGECKO_DEMO_API_KEY_configured": true' in encoded
    assert '"WALLEX_API_KEY_configured": true' in encoded


def test_workflow_secret_and_trigger_hygiene():
    provider = (ROOT / ".github/workflows/provider-readonly-check.yml").read_text(encoding="utf-8")
    trigger_block = "\n".join(
        line for line in provider.split("jobs:")[0].splitlines()
        if not line.lstrip().startswith("#")
    )
    assert "workflow_dispatch" in trigger_block
    assert "pull_request" not in trigger_block
    assert "push:" not in trigger_block
    assert "${{ secrets.COINGECKO_DEMO_API_KEY }}" in provider
    assert "${{ secrets.WALLEX_API_KEY }}" in provider
    offline_ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "secrets." not in offline_ci


def run_mission(tmp_path, name):
    db = tmp_path / f"{name}.sqlite3"
    output = tmp_path / f"{name}.json"
    rc = paper_candles_main([
        "--input", str(FIXTURE), "--symbol", "BTCUSDT", "--db", str(db),
        "--initial-cash", "1000000", "--max-order-notional", "100000",
        "--fee-bps", "10", "--slippage-bps", "20",
        "--lookback-bars", "5", "--entry-return-bps", "20", "--exit-return-bps", "0",
        "--max-daily-loss-percent", "3",
        "--audit-input-data", "--expected-interval-seconds", "60",
        "--audit-as-of", "2026-01-01T00:20:00Z", "--audit-max-staleness-seconds", "600",
        "--output", str(output),
    ])
    assert rc == 0
    return json.loads(output.read_text(encoding="utf-8")), db


def test_twenty_candle_synthetic_mission_is_deterministic_and_audited(tmp_path):
    audit = audit_file(FIXTURE, expected_symbol="BTCUSDT", expected_interval_seconds=60)
    assert audit["status"] == "OK"
    assert audit["input_rows_valid"] == 20
    assert audit["duplicate_timestamps"] == 0
    assert audit["potential_gaps"] == 0

    first, db = run_mission(tmp_path, "first")
    second, _ = run_mission(tmp_path, "second")
    assert first["bars"] == 20
    assert first["mode"] == "paper_candle_simulation"
    assert first["input_data_audit"]["status"] == "OK"
    assert first["live_trading_enabled"] is False
    assert first["order_submission_attempted"] is False
    sides = [fill["side"] for fill in first["fills"]]
    assert "buy" in sides
    assert all(float(fill["fee"]) >= 0 for fill in first["fills"])
    # Deterministic: a fresh ledger over the same input reproduces the run.
    assert first["fills"] == second["fills"]
    assert first["signals"] == second["signals"]
    assert first["account"] == second["account"]
    # Ledger persists and can be reopened with the original settings.
    reopened = PaperBroker(db, **BROKER_KWARGS)
    assert reopened.snapshot() == first["account"]


def test_mission_blocks_review_data_without_explicit_override(tmp_path):
    lines = [json.loads(line) for line in fixture_lines()]
    gapped = tmp_path / "gapped.jsonl"
    gapped.write_text("".join(
        json.dumps(row) + "\n" for row in lines[:5] + lines[7:]
    ), encoding="utf-8")
    rc = paper_candles_main([
        "--input", str(gapped), "--symbol", "BTCUSDT",
        "--db", str(tmp_path / "g.sqlite3"),
        "--initial-cash", "1000000", "--max-order-notional", "100000",
        "--audit-input-data", "--expected-interval-seconds", "60",
    ])
    assert rc == 2
