import json
from pathlib import Path
from wallex_agent.backtest_cli import main


def candle(ts, close="100"):
    return {"timestamp":ts,"open":close,"high":close,"low":close,"close":close,
            "volume":"1","symbol":"BTCUSDT","interval_seconds":60}


def cli_args(path, *extra):
    return ["--input",str(path),"--initial-cash","1000","--lookback-bars","1",
            "--entry-return-bps","1","--exit-return-bps","0",
            "--fee-bps-per-side","0","--slippage-bps-per-side","0",*extra]


def write_rows(path: Path, rows):
    path.write_text("".join(json.dumps(row)+"\n" for row in rows),encoding="utf-8")


def test_backtest_audit_gate_allows_clean_dataset_and_embeds_summary(tmp_path):
    data=tmp_path/"clean.jsonl"
    write_rows(data,[candle("2026-10-23T10:00:00Z"),candle("2026-10-23T10:01:00Z","101"),
                     candle("2026-10-23T10:02:00Z","102")])
    report_path=tmp_path/"backtest.json"
    status=main(cli_args(data,"--audit-input-data","--expected-symbol","BTCUSDT",
                         "--expected-interval-seconds","60","--output",str(report_path)))
    assert status==0
    report=json.loads(report_path.read_text())
    assert report["input_data_audit"]["status"]=="OK"
    assert report["order_submission_attempted"] is False


def test_backtest_blocks_review_dataset_without_explicit_override(tmp_path,capsys):
    data=tmp_path/"gap.jsonl"
    write_rows(data,[candle("2026-10-23T10:00:00Z"),candle("2026-10-23T10:02:00Z","101"),
                     candle("2026-10-23T10:03:00Z","102")])
    audit_path=tmp_path/"audit.json"
    status=main(cli_args(data,"--audit-input-data","--expected-interval-seconds","60",
                         "--audit-output",str(audit_path)))
    assert status==2
    assert "status is REVIEW" in capsys.readouterr().err
    audit=json.loads(audit_path.read_text())
    assert audit["status"]=="REVIEW"
    assert audit["potential_gaps"]==1


def test_backtest_allows_review_only_when_explicit_and_reports_it(tmp_path):
    data=tmp_path/"gap.jsonl"
    write_rows(data,[candle("2026-10-23T10:00:00Z"),candle("2026-10-23T10:02:00Z","101"),
                     candle("2026-10-23T10:03:00Z","102")])
    output=tmp_path/"allowed-review.json"
    status=main(cli_args(data,"--audit-input-data","--allow-review-data","--output",str(output)))
    assert status==0
    report=json.loads(output.read_text())
    assert report["input_data_audit"]["status"]=="REVIEW"
    assert report["input_data_audit"]["potential_gaps"]==1


def test_backtest_never_overrides_invalid_audit(tmp_path,capsys):
    data=tmp_path/"duplicate.jsonl"
    write_rows(data,[candle("2026-10-23T10:00:00Z"),candle("2026-10-23T10:00:00Z","101"),
                     candle("2026-10-23T10:01:00Z","102")])
    status=main(cli_args(data,"--audit-input-data","--allow-review-data"))
    assert status==2
    assert "status is INVALID" in capsys.readouterr().err


def test_review_override_requires_audit_flag(tmp_path,capsys):
    data=tmp_path/"any.jsonl"
    write_rows(data,[candle("2026-10-23T10:00:00Z"),candle("2026-10-23T10:01:00Z","101"),
                     candle("2026-10-23T10:02:00Z","102")])
    status=main(cli_args(data,"--allow-review-data"))
    assert status==2
    assert "requires --audit-input-data" in capsys.readouterr().err
