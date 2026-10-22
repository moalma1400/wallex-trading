"""Minimal opt-in Streamable HTTP MCP client for public market-data discovery."""
import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENDPOINTS = {
    "wallex": "https://api.wallex.ir/mcp",
    "coingecko": "https://mcp.api.coingecko.com/mcp",
}


def post(url, message, session=None, version="2025-03-26"):
    if url not in ENDPOINTS.values():
        raise ValueError("Endpoint is not in the reviewed allowlist")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "wallex-trading-github-mcp/0.1",
        "MCP-Protocol-Version": version,
    }
    if session:
        headers["MCP-Session-Id"] = session
    req = urllib.request.Request(
        url, data=json.dumps(message).encode("utf-8"), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise ValueError("MCP response too large")
            sid = response.headers.get("MCP-Session-Id", session)
            ctype = response.headers.get("Content-Type", "")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ValueError("MCP HTTPS request failed: " + type(exc).__name__) from None
    if "text/event-stream" in ctype:
        rows = []
        for block in body.decode("utf-8").split("\n\n"):
            data = "\n".join(line[5:].strip() for line in block.splitlines() if line.startswith("data:"))
            if data:
                try:
                    rows.append(json.loads(data))
                except json.JSONDecodeError:
                    pass
        result = next((x for x in reversed(rows) if x.get("id") == message.get("id")), None)
    else:
        result = json.loads(body.decode("utf-8")) if body else None
    if message.get("id") is not None:
        if not isinstance(result, dict) or result.get("id") != message["id"]:
            raise ValueError("Invalid MCP JSON-RPC response")
        if "error" in result:
            raise ValueError("MCP returned JSON-RPC error")
        return result.get("result"), sid
    return result, sid


def run(provider, mode, tool=None, arguments=None):
    url = ENDPOINTS[provider]
    init, session = post(url, {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "wallex-trading-github", "version": "0.1"},
        },
    }, version="2025-03-26")
    version = init.get("protocolVersion", "2025-03-26")
    post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, session, version)
    tools, session = post(url, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, session, version)
    if mode == "list":
        result = {"tools": tools.get("tools", []), "serverInfo": init.get("serverInfo", {})}
    else:
        available = {item.get("name"): item for item in tools.get("tools", [])}
        if tool not in available:
            raise ValueError("Tool name was not returned by tools/list")
        item = available[tool]
        name = item.get("name", "").lower()
        annotations = item.get("annotations", {})
        blocked = ("order", "account", "balance", "withdraw", "transfer", "deposit", "cancel", "delete", "submit", "private")
        if any(word in name for word in blocked):
            raise ValueError("Tool is outside the read-only public-data scope")
        if annotations.get("destructiveHint") is True or annotations.get("readOnlyHint") is False:
            raise ValueError("Tool annotations do not permit read-only execution")
        result, session = post(url, {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": tool, "arguments": arguments or {}},
        }, session, version)
    return {
        "schema_version": "1.0",
        "provider": provider,
        "endpoint": url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "result": result,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", action="store_true")
    parser.add_argument("--out-dir", default="reports/public-market-data")
    sub = parser.add_subparsers(dest="provider", required=True)
    for provider in ENDPOINTS:
        p = sub.add_parser(provider)
        p.add_argument("mode", choices=["list", "call"])
        p.add_argument("--tool")
        p.add_argument("--arguments-json", default="{}")
    args = parser.parse_args()
    if not args.network:
        print("Network disabled; pass --network to explicitly enable remote MCP.", file=sys.stderr)
        return 2
    try:
        arguments = json.loads(args.arguments_json)
        if not isinstance(arguments, dict):
            raise ValueError("--arguments-json must be a JSON object")
        doc = run(args.provider, args.mode, args.tool, arguments)
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / (args.provider + "-" + args.mode + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"provider": args.provider, "mode": args.mode, "artifact": str(path)}))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print("ERROR: " + str(exc)[:240], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
