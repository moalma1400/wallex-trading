"""Offline tests for fail-closed Smart98 tool-contract verification."""
from __future__ import annotations

import copy
import pytest

from wallex_mcp.execution_client import VerifiedExecutionToolContract
from wallex_mcp.smart98_contract import (
    GET_ORDER_TOOL, PLACE_ORDER_TOOL, Smart98ContractVerificationError,
    verify_smart98_execution_contract,
)


def valid_tools():
    return [
        {
            "name": PLACE_ORDER_TOOL,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "side": {"type": "string"}, "symbol": {"type": "string"},
                    "type": {"type": "string"}, "client_id": {"type": "string"},
                    "price": {"type": "string"}, "quantity": {"type": "string"},
                    "stop_Price": {"type": "string"},
                },
                "required": ["side", "symbol", "type"],
            },
            "outputSchema": {
                "type": "object",
                "properties": {"success": {"type": "boolean"}, "result": {"type": "object"}},
                "required": ["success", "result"],
            },
        },
        {
            "name": GET_ORDER_TOOL,
            "inputSchema": {
                "type": "object", "properties": {"client_id": {"type": "string"}},
                "required": ["client_id"],
            },
            "outputSchema": {
                "type": "object",
                "properties": {"success": {"type": "boolean"}, "result": {"type": "object"}},
                "required": ["success", "result"],
            },
        },
    ]


def verify(tools):
    return verify_smart98_execution_contract(
        tools, evidence_url="https://example.invalid/audit/smart98-tools-list",
        version="audit-fixture-v1",
    )


def test_complete_runtime_schema_produces_verified_contract():
    contract = verify(valid_tools())
    assert isinstance(contract, VerifiedExecutionToolContract)
    assert contract.verified is True
    assert contract.place_order_tool == PLACE_ORDER_TOOL
    assert contract.get_order_tool == GET_ORDER_TOOL
    assert len(contract.version.split(":")[-1]) == 64


def test_name_only_inventory_is_not_enough():
    with pytest.raises(Smart98ContractVerificationError, match="inputSchema is missing"):
        verify([{"name": PLACE_ORDER_TOOL}, {"name": GET_ORDER_TOOL}])


def test_missing_order_detail_tool_fails_closed():
    with pytest.raises(Smart98ContractVerificationError, match="get_orders_client"):
        verify(valid_tools()[:1])


def test_create_tool_required_fields_must_match_audit():
    tools = valid_tools()
    tools[0]["inputSchema"]["required"] = ["side", "symbol"]
    with pytest.raises(Smart98ContractVerificationError, match="required fields differ"):
        verify(tools)


def test_adapter_fields_must_exist_even_if_optional():
    tools = valid_tools()
    del tools[0]["inputSchema"]["properties"]["client_id"]
    with pytest.raises(Smart98ContractVerificationError, match="fields used by the adapter"):
        verify(tools)


def test_response_schema_is_required():
    tools = valid_tools()
    del tools[0]["outputSchema"]
    with pytest.raises(Smart98ContractVerificationError, match="outputSchema is missing"):
        verify(tools)


def test_wrong_response_envelope_fails_closed():
    tools = valid_tools()
    tools[1]["outputSchema"]["properties"] = {"data": {"type": "object"}}
    tools[1]["outputSchema"]["required"] = ["data"]
    with pytest.raises(Smart98ContractVerificationError, match="success/result envelope"):
        verify(tools)


def test_schema_change_changes_contract_fingerprint():
    first = verify(valid_tools())
    changed = copy.deepcopy(valid_tools())
    changed[0]["inputSchema"]["properties"]["stop_Price"]["description"] = "changed"
    second = verify(changed)
    assert first.version != second.version


@pytest.mark.parametrize("url", ["http://example.invalid/audit", "", "relative/path"])
def test_evidence_reference_must_be_https(url):
    with pytest.raises(Smart98ContractVerificationError, match="HTTPS"):
        verify_smart98_execution_contract(valid_tools(), evidence_url=url, version="audit-v1")
