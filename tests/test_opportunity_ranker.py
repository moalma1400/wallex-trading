from wallex_agent.opportunity_ranker import rank_cost_adjusted_opportunities


def row(symbol, edge, spread="5", status="WATCH_EDGE", eligible=True):
    return {
        "symbol": symbol, "eligible": eligible, "spread_bps": spread,
        "cost_adjusted_momentum": {
            "status": status, "net_estimated_edge_bps": edge,
        },
    }


def test_rank_prefers_higher_positive_net_edge_then_lower_spread():
    ranked = rank_cost_adjusted_opportunities([
        row("AAAUSDT", "8", "2"),
        row("CCCUSDT", "12", "7"),
        row("BBBUSDT", "12", "3"),
    ])
    assert [x["symbol"] for x in ranked] == ["BBBUSDT", "CCCUSDT", "AAAUSDT"]
    assert [x["rank"] for x in ranked] == [1, 2, 3]
    assert all(x["order_submission_attempted"] is False for x in ranked)


def test_fail_closed_for_ineligible_or_non_edge_rows():
    ranked = rank_cost_adjusted_opportunities([
        row("AAAUSDT", "99", eligible=False),
        row("BBBUSDT", "99", status="NET_EDGE_BELOW_COST"),
        row("CCCUSDT", "0"),
        row("DDDUSDT", "NaN"),
        row("EEEUSDT", "3", spread="-1"),
        {"symbol": "MISSING", "eligible": True, "spread_bps": "1"},
    ])
    assert ranked == []


def test_deterministic_tie_breaking_and_symbol_normalization():
    ranked = rank_cost_adjusted_opportunities([
        row("zzzusdt", "4", "2"),
        row("AAAUSDT", "4", "2"),
        row("BBBUSDT", "4", "1"),
    ])
    assert [x["symbol"] for x in ranked] == ["BBBUSDT", "AAAUSDT", "ZZZUSDT"]
    assert ranked[0]["rank"] == 1
