from decimal import Decimal
from wallex_agent.cost_model import CostModelConfig, CostModelError, evaluate_momentum
from wallex_agent.state import ObservationStore
import pytest

def cfg(**kwargs):
    values={"fee_bps_per_side":"5","slippage_bps_per_side":"2","minimum_net_edge_bps":"1","maximum_observation_gap_seconds":120}
    values.update(kwargs)
    return CostModelConfig(**values)

def test_net_edge_subtracts_full_spread_two_sided_fees_and_slippage():
    result=evaluate_momentum(previous_price="100",current_price="101",bid="100.9",ask="101.1",elapsed_seconds=60,config=cfg())
    assert result["status"]=="WATCH_EDGE"
    assert Decimal(result["gross_change_bps"])==Decimal("100.00")
    assert Decimal(result["round_trip_fee_reserve_bps"])==Decimal("10.00")
    assert Decimal(result["round_trip_slippage_reserve_bps"])==Decimal("4.00")
    assert Decimal(result["net_estimated_edge_bps"]) < Decimal("100")
    assert result["order_submission_attempted"] is False

def test_costs_can_consume_entire_raw_momentum():
    result=evaluate_momentum(previous_price="100",current_price="100.05",bid="100",ask="100.1",elapsed_seconds=60,config=cfg())
    assert result["status"]=="NET_EDGE_BELOW_COST"

def test_non_positive_momentum_and_staleness_do_not_become_candidates():
    args=dict(previous_price="100",current_price="99",bid="98.9",ask="99.1",config=cfg())
    assert evaluate_momentum(**args,elapsed_seconds=30)["status"]=="NON_POSITIVE_MOMENTUM"
    assert evaluate_momentum(**{**args,"current_price":"101"},elapsed_seconds=121)["status"]=="STALE_BASELINE"

def test_invalid_inputs_fail_closed_and_config_requires_valid_values():
    assert evaluate_momentum(previous_price="NaN",current_price="1",bid="1",ask="2",elapsed_seconds=10,config=cfg())["status"]=="INVALID_DATA"
    with pytest.raises(CostModelError): cfg(fee_bps_per_side="-1")
    with pytest.raises(CostModelError): cfg(slippage_bps_per_side="Infinity")

def test_observation_store_persists_and_updates(tmp_path):
    path=tmp_path/"state"/"prices.db"; store=ObservationStore(path)
    assert store.get("BTCUSDT") is None
    store.put("BTCUSDT","100","2026-10-23T10:00:00Z")
    assert store.get("BTCUSDT")==("100","2026-10-23T10:00:00Z")
    store.put("BTCUSDT","101","2026-10-23T10:01:00Z")
    assert store.get("BTCUSDT")==("101","2026-10-23T10:01:00Z")
