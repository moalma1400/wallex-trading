import json
from pathlib import Path

import pytest
from wallex_agent.walk_forward import run_walk_forward
from wallex_agent.walk_forward_cli import main


def rows(n=48):
    result=[]
    price=100.0
    for i in range(n):
        # deterministic price series with several trend changes
        delta = 1.2 if (i // 6) % 2 == 0 else -0.7
        price += delta
        stamp = f"2026-01-{1 + i // 24:02d}T{(i % 24):02d}:00:00Z"
        result.append({"timestamp": stamp, "open": str(price), "high": str(price + 0.5),
                       "low": str(price - 0.5), "close": str(price), "volume": "10"})
    return result


def kwargs():
    return dict(initial_cash="1000", folds=2, train_size=12, test_size=8,
                lookbacks=[2, 3], entry_thresholds_bps=["1", "5"],
                exit_thresholds_bps=["0"], fee_bps_per_side="2",
                slippage_bps_per_side="1", spread_bps_per_side="1")


def test_walk_forward_returns_disjoint_folds_and_never_submits_orders():
    report = run_walk_forward(rows(), **kwargs())
    assert report["mode"] == "walk_forward_research"
    assert report["aggregate"]["fold_count"] == 2
    assert report["order_submission_attempted"] is False
    assert all(f["test"]["order_submission_attempted"] is False for f in report["folds"])
    assert report["folds"][0]["test_indices"][1] <= report["folds"][1]["train_indices"][0]


def test_walk_forward_rejects_insufficient_data_and_bad_grids():
    with pytest.raises(ValueError):
        run_walk_forward(rows(20), **kwargs())
    with pytest.raises(ValueError):
        run_walk_forward(rows(), **{**kwargs(), "lookbacks": [0]})


def test_cli_writes_json_report(tmp_path):
    data=tmp_path/"candles.jsonl"
    data.write_text("".join(json.dumps(row)+"\n" for row in rows()), encoding="utf-8")
    output=tmp_path/"reports"/"walk-forward.json"
    code=main(["--input",str(data),"--initial-cash","1000","--folds","2",
      "--train-size","12","--test-size","8","--lookbacks","2,3",
      "--entry-thresholds-bps","1,5","--exit-thresholds-bps","0",
      "--fee-bps-per-side","2","--slippage-bps-per-side","1",
      "--spread-bps-per-side","1","--output",str(output)])
    assert code == 0
    report=json.loads(output.read_text())
    assert report["aggregate"]["fold_count"] == 2
