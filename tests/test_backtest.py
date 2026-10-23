from decimal import Decimal
import pytest
from wallex_agent.backtest import BacktestConfig, BacktestError, load_candles, partition_walk_forward, run_momentum_backtest

def candle(i, close, open_price=None, high=None, low=None, timestamp=None):
    o=Decimal(str(open_price if open_price is not None else close))
    c=Decimal(str(close))
    return {"timestamp":timestamp or f"2026-01-{i+1:02d}T00:00:00Z","open":str(o),
        "high":str(high if high is not None else max(o,c)),"low":str(low if low is not None else min(o,c)),
        "close":str(c),"volume":"100"}

def cfg(**kw):
    values={"initial_cash":"1000","lookback_bars":2,"entry_return_bps":"20","exit_return_bps":"0",
        "fee_bps_per_side":"5","slippage_bps_per_side":"2","spread_bps_per_side":"1"}
    values.update(kw)
    return BacktestConfig(**values)

def test_backtest_uses_next_bar_open_and_records_costs_and_equity():
    rows=[candle(0,100),candle(1,101),candle(2,103),candle(3,104,open_price=105),candle(4,106,open_price=106),candle(5,100,open_price=99)]
    report=run_momentum_backtest(rows,cfg())
    assert report["mode"]=="historical_backtest"
    assert report["bars"]==6
    assert report["order_submission_attempted"] is False
    assert Decimal(report["cost_model_per_side_bps"])==Decimal("8.00")
    assert report["trades"][0]["entry_timestamp"]==rows[3]["timestamp"]
    assert report["trades"][0]["entry_price"]=="105"
    assert len(report["equity_curve"])==6

def test_backtest_rejects_naive_duplicate_and_unsorted_timestamps():
    rows=[candle(0,100,timestamp="2026-01-01T00:00:00"),candle(1,101)]
    with pytest.raises(BacktestError,match="naive timestamps"): load_candles(rows)
    rows=[candle(0,100,timestamp="2026-01-01T00:00:00Z"),candle(1,101,timestamp="2026-01-01T00:00:00Z")]
    with pytest.raises(BacktestError,match="strictly increasing"): load_candles(rows)
    rows=[candle(1,101,timestamp="2026-01-02T00:00:00Z"),candle(0,100,timestamp="2026-01-01T00:00:00Z")]
    with pytest.raises(BacktestError,match="strictly increasing"): load_candles(rows)

def test_backtest_rejects_invalid_ohlc_and_config():
    rows=[candle(0,100),candle(1,101),candle(2,102,high=99),candle(3,103)]
    with pytest.raises(BacktestError): load_candles(rows)
    with pytest.raises(BacktestError): cfg(fee_bps_per_side="-1")
    with pytest.raises(BacktestError): cfg(initial_cash="0")

def test_walk_forward_partitions_are_chronological_and_disjoint():
    folds=partition_walk_forward(100,3,20,10)
    assert [(f.train_start,f.train_end,f.test_start,f.test_end) for f in folds]==[
      (0,20,20,30),(30,50,50,60),(60,80,80,90)]
    spans=[]
    for f in folds: spans.extend([set(range(f.train_start,f.train_end)),set(range(f.test_start,f.test_end))])
    assert all(not spans[i].intersection(spans[j]) for i in range(len(spans)) for j in range(i+1,len(spans)))
    with pytest.raises(BacktestError): partition_walk_forward(50,3,20,10)

def test_backtest_fails_when_not_enough_bars_for_signal_and_next_fill():
    with pytest.raises(BacktestError): run_momentum_backtest([candle(0,100),candle(1,101),candle(2,102)],cfg())
