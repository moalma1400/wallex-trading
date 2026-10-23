import json
from pathlib import Path
from wallex_agent.cost_model import CostModelConfig
from wallex_agent.engine import ScreenConfig
from wallex_agent.runner import run_shadow

def row(price, bid, ask):
    return {"symbol":"BTCUSDT","base_asset":"BTC","quote_asset":"USDT","price":price,
      "is_spot":True,"is_otc":False,"is_margin":False,"is_tmn_based":False,"is_usdt_based":True,
      "amount_precision":6,"price_precision":2,"flags":[],"volume_24h":"100000","change_24h":"1.2",
      "created_at":"2025-01-01T00:00:00Z","fair_price":{"bid":bid,"ask":ask}}

class FakeClient:
    def __init__(self, payloads): self.payloads=list(payloads)
    def get_markets(self): return {"markets":self.payloads.pop(0)}

def test_runner_warms_up_then_calculates_net_edge_and_persists_state(tmp_path:Path):
    output=tmp_path/"shadow.jsonl"; state=tmp_path/"prices.sqlite3"
    client=FakeClient([[row("100","99.9","100.1")],[row("101","100.9","101.1")]])
    times=iter(["2026-10-23T10:00:00Z","2026-10-23T10:01:00Z"])
    run_shadow(client,ScreenConfig("USDT"),output,interval_seconds=1,max_cycles=2,
      sleep=lambda _:None,clock=lambda:next(times),cost_config=CostModelConfig("5","2","1",120),state_path=state)
    rows=[json.loads(line) for line in output.read_text().splitlines()]
    result=rows[0]["assessments"][0]["cost_adjusted_momentum"]
    assert result["status"]=="WARMUP_NO_BASELINE"
    result=rows[1]["assessments"][0]["cost_adjusted_momentum"]
    assert result["status"]=="WATCH_EDGE"
    assert result["net_estimated_edge_bps"]
    assert rows[1]["cost_edge_candidates"]==1
    assert len(rows[1]["ranked_opportunities"]) == 1
    assert rows[1]["ranked_opportunities"][0]["symbol"] == "BTCUSDT"
    assert rows[1]["ranked_opportunities"][0]["classification"] == "SHADOW_CANDIDATE"
    assert rows[1]["live_trading_enabled"] is False
    assert rows[1]["order_submission_attempted"] is False
    # Restart safety: the persisted previous observation is available to a new store instance.
    from wallex_agent.state import ObservationStore
    assert ObservationStore(state).get("BTCUSDT")==("101","2026-10-23T10:01:00Z")

def test_cost_model_disabled_is_explicit(tmp_path:Path):
    output=tmp_path/"shadow.jsonl"
    run_shadow(FakeClient([[row("100","99.9","100.1")]]),ScreenConfig("USDT"),output,
      max_cycles=1,clock=lambda:"2026-10-23T10:00:00Z",sleep=lambda _:None,state_path=tmp_path/"state.db")
    data=json.loads(output.read_text().splitlines()[0])
    assert data["cost_model_enabled"] is False
    assert data["assessments"][0]["cost_adjusted_momentum"]["status"]=="COST_MODEL_DISABLED"
