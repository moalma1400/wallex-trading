"""Offline-only coverage for the shadow screening loop."""
import json
from pathlib import Path
import pytest
from wallex_agent.engine import ScreenConfig, ScreeningError, assess_markets
from wallex_agent.runner import run_shadow

def market(symbol="BTCUSDT", quote="USDT", spot=True, bid="99.9", ask="100", price="99.95", change="1.2"):
    return {"symbol":symbol,"base_asset":symbol.removesuffix(quote),"quote_asset":quote,"price":price,
        "is_spot":spot,"is_otc":False,"is_margin":False,"is_tmn_based":False,"is_usdt_based":True,
        "amount_precision":6,"price_precision":2,"flags":[],"volume_24h":"100000","change_24h":change,
        "created_at":"2025-01-01T00:00:00Z","fair_price":{"bid":bid,"ask":ask}}

def test_screen_filters_quote_spot_spread_change_and_sorts_candidates():
    config=ScreenConfig("USDT","0","150")
    rows=assess_markets([market("BTCUSDT"),market("ETHUSDT",quote="TMN"),
       market("SOLUSDT",bid="90",ask="100",change="4"),market("ADAUSDT",change="-1"),
       market("OTCUSDT",spot=False)],config)
    by_symbol={x.symbol:x for x in rows}
    assert rows[0].symbol=="BTCUSDT" and rows[0].eligible
    assert "QUOTE_ASSET_MISMATCH" in by_symbol["ETHUSDT"].reason_codes
    assert "SPREAD_ABOVE_SCREENING_LIMIT" in by_symbol["SOLUSDT"].reason_codes
    assert "CHANGE_BELOW_SCREENING_THRESHOLD" in by_symbol["ADAUSDT"].reason_codes
    assert "NOT_ACTIVE_SPOT" in by_symbol["OTCUSDT"].reason_codes
    assert all(x.as_dict()["status"]!="BUY" for x in rows)

def test_missing_and_invalid_bid_ask_are_skipped():
    missing=market(); missing.pop("fair_price")
    invalid=market(); invalid["fair_price"]={"bid":"NaN","ask":"100"}
    got=assess_markets([missing,invalid],ScreenConfig("USDT"))
    assert not any(x.eligible for x in got)
    assert "MISSING_BID_ASK" in got[0].reason_codes
    assert "INVALID_NUMERIC_MARKET_DATA" in got[1].reason_codes

def test_config_fails_closed():
    with pytest.raises(ScreeningError): ScreenConfig("USDT",maximum_spread_bps="NaN")
    with pytest.raises(ScreeningError): ScreenConfig("USDT",maximum_spread_bps="10001")
    with pytest.raises(ScreeningError): ScreenConfig("")

class FakeClient:
    def __init__(self,items): self.items=list(items); self.calls=0
    def get_markets(self):
        self.calls+=1; item=self.items.pop(0)
        if isinstance(item,Exception): raise item
        return item

def test_shadow_runner_appends_audit_records_without_order_writes(tmp_path:Path):
    client=FakeClient([{"markets":[market()]},{"markets":[]}]); output=tmp_path/"nested"/"shadow.jsonl"
    emitted=[]
    count=run_shadow(client,ScreenConfig("USDT"),output,interval_seconds=1,max_cycles=2,
      sleep=lambda _:None,clock=lambda:"2026-10-23T00:00:00Z",on_cycle=emitted.append)
    rows=[json.loads(line) for line in output.read_text().splitlines()]
    assert count==2 and client.calls==2 and len(rows)==len(emitted)==2
    assert rows[0]["mode"]=="shadow" and rows[0]["watch_candidates"]==1
    assert rows[0]["order_submission_attempted"] is False and rows[1]["markets_seen"]==0

def test_shadow_runner_records_errors_and_continues(tmp_path:Path):
    output=tmp_path/"shadow.jsonl"
    run_shadow(FakeClient([RuntimeError("synthetic"),{"markets":[market()]}]),ScreenConfig("USDT"),output,
               interval_seconds=1,max_cycles=2,sleep=lambda _:None)
    rows=[json.loads(line) for line in output.read_text().splitlines()]
    assert rows[0]["cycle_status"]=="error" and rows[0]["error_type"]=="RuntimeError"
    assert rows[0]["order_submission_attempted"] is False and rows[1]["watch_candidates"]==1

def test_runner_rejects_invalid_interval(tmp_path:Path):
    with pytest.raises(ValueError): run_shadow(FakeClient([]),ScreenConfig("USDT"),tmp_path/"x",interval_seconds=0,max_cycles=1)
