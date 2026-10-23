"""Fail-closed verification of a discovered Smart98 order-tool contract.

This module never invokes tools or performs network I/O. It compares an
operator-supplied MCP tools/list snapshot against the exact contract assumed
by MediatedExecutionClient. A name-only inventory is insufficient: input and
output schemas must be present and compatible before a verified contract can
be returned.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from .execution_client import ExecutionClientError, VerifiedExecutionToolContract


PLACE_ORDER_TOOL = "wallex_spot_post_account_orders"
GET_ORDER_TOOL = "wallex_spot_get_orders_client"
_PLACE_REQUIRED = frozenset({"side", "symbol", "type"})
_PLACE_USED = frozenset({"client_id", "side", "symbol", "type", "price", "quantity"})
_GET_REQUIRED = frozenset({"client_id"})


class Smart98ContractVerificationError(ExecutionClientError):
    """Discovered Smart98 schemas do not prove the required execution contract."""


def _schema(tool: Mapping[str, Any], key: str, tool_name: str) -> Mapping[str, Any]:
    value = tool.get(key)
    if not isinstance(value, Mapping):
        raise Smart98ContractVerificationError(
            f"{tool_name}: runtime {key} is missing; contract remains unverified"
        )
    return value


def _properties(schema: Mapping[str, Any], tool_name: str) -> Mapping[str, Any]:
    if schema.get("type") != "object":
        raise Smart98ContractVerificationError(
            f"{tool_name}: schema must explicitly declare type=object"
        )
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        raise Smart98ContractVerificationError(f"{tool_name}: schema properties are missing")
    required = schema.get("required", [])
    if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
        raise Smart98ContractVerificationError(
            f"{tool_name}: schema required must be a list of strings"
        )
    missing = set(required) - set(properties)
    if missing:
        raise Smart98ContractVerificationError(
            f"{tool_name}: required fields absent from properties: {', '.join(sorted(missing))}"
        )
    return properties


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _find_tool(tools: Sequence[Mapping[str, Any]], name: str) -> Mapping[str, Any]:
    matches = [tool for tool in tools if tool.get("name") == name]
    if len(matches) != 1:
        raise Smart98ContractVerificationError(
            f"expected exactly one discovered tool named {name}; found {len(matches)}"
        )
    return matches[0]


def _validate_response_schema(tool: Mapping[str, Any], name: str) -> None:
    output_schema = _schema(tool, "outputSchema", name)
    properties = _properties(output_schema, name + " output")
    required = set(output_schema.get("required", []))
    if not {"success", "result"}.issubset(properties):
        raise Smart98ContractVerificationError(
            f"{name}: output schema does not document the success/result envelope expected by MediatedExecutionClient"
        )
    if not {"success", "result"}.issubset(required):
        raise Smart98ContractVerificationError(
            f"{name}: success and result must be required output fields"
        )
    if properties["success"].get("type") != "boolean":
        raise Smart98ContractVerificationError(f"{name}: output success field must be boolean")
    if properties["result"].get("type") != "object":
        raise Smart98ContractVerificationError(f"{name}: output result field must be object")


def verify_smart98_execution_contract(
    tools: Sequence[Mapping[str, Any]], *, evidence_url: str, version: str
) -> VerifiedExecutionToolContract:
    """Return a verified contract only when runtime schemas match this adapter.

    tools must be a sanitized snapshot from Smart98 actual tools/list response.
    Both JSON Schema inputSchema and outputSchema must be present.
    """
    if not isinstance(evidence_url, str) or not evidence_url.startswith("https://"):
        raise Smart98ContractVerificationError("evidence_url must be an HTTPS audit/evidence URL")
    if not isinstance(version, str) or not version.strip():
        raise Smart98ContractVerificationError("contract version is required")

    place = _find_tool(tools, PLACE_ORDER_TOOL)
    get_order = _find_tool(tools, GET_ORDER_TOOL)
    place_input = _schema(place, "inputSchema", PLACE_ORDER_TOOL)
    place_properties = _properties(place_input, PLACE_ORDER_TOOL)
    place_required = set(place_input.get("required", []))
    if not _PLACE_REQUIRED.issubset(place_required):
        raise Smart98ContractVerificationError(
            "order-create required fields differ from the audited contract"
        )
    if not _PLACE_USED.issubset(place_properties):
        raise Smart98ContractVerificationError(
            "order-create schema lacks one or more fields used by the adapter"
        )

    get_input = _schema(get_order, "inputSchema", GET_ORDER_TOOL)
    get_properties = _properties(get_input, GET_ORDER_TOOL)
    get_required = set(get_input.get("required", []))
    if not _GET_REQUIRED.issubset(get_required) or "client_id" not in get_properties:
        raise Smart98ContractVerificationError("order-detail schema does not require client_id")

    _validate_response_schema(place, PLACE_ORDER_TOOL)
    _validate_response_schema(get_order, GET_ORDER_TOOL)
    fingerprint = hashlib.sha256((
        _canonical_hash(place_input)
        + _canonical_hash(_schema(place, "outputSchema", PLACE_ORDER_TOOL))
        + _canonical_hash(get_input)
        + _canonical_hash(_schema(get_order, "outputSchema", GET_ORDER_TOOL))
    ).encode("ascii")).hexdigest()
    return VerifiedExecutionToolContract(
        place_order_tool=PLACE_ORDER_TOOL, get_order_tool=GET_ORDER_TOOL,
        source_url=evidence_url, version=f"{version}:{fingerprint}", verified=True,
    )
