import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from wallex_research import public_market_data as client


class FakeResponse:
    def __init__(self, body, headers=None, status=200):
        self.body = body
        self.headers = headers or {"Content-Type": "application/json"}
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.body


class RemoteMCPTests(unittest.TestCase):
    def test_only_approved_https_endpoints(self):
        self.assertEqual(client.ENDPOINTS["wallex"], "https://api.wallex.ir/mcp")
        self.assertTrue(client.ENDPOINTS["coingecko"].startswith("https://"))
        with self.assertRaises(ValueError):
            client.post("https://example.com/mcp", {"jsonrpc": "2.0", "id": 1})

    @patch("wallex_research.public_market_data.urllib.request.urlopen")
    def test_json_rpc_response_and_session(self, urlopen):
        payload = {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-03-26"}}
        urlopen.return_value = FakeResponse(
            json.dumps(payload).encode(),
            {"Content-Type": "application/json", "MCP-Session-Id": "session-test"},
        )
        result, session = client.post(
            client.ENDPOINTS["wallex"], {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        )
        self.assertEqual(result["protocolVersion"], "2025-03-26")
        self.assertEqual(session, "session-test")

    @patch("wallex_research.public_market_data.urllib.request.urlopen")
    def test_sse_json_rpc_response(self, urlopen):
        payload = {"jsonrpc": "2.0", "id": 2, "result": {"tools": []}}
        body = ("event: message\ndata: " + json.dumps(payload) + "\n\n").encode()
        urlopen.return_value = FakeResponse(body, {"Content-Type": "text/event-stream"})
        result, _ = client.post(
            client.ENDPOINTS["coingecko"], {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        )
        self.assertEqual(result["tools"], [])

    @patch("wallex_research.public_market_data.urllib.request.urlopen", side_effect=URLError("offline"))
    def test_network_errors_are_sanitized(self, _urlopen):
        with self.assertRaisesRegex(ValueError, "MCP HTTPS request failed"):
            client.post(client.ENDPOINTS["wallex"], {"jsonrpc": "2.0", "id": 1})

    def test_cli_network_disabled_by_default(self):
        with patch("sys.argv", ["public_market_data.py", "wallex", "list"]), patch("sys.stderr"):
            self.assertEqual(client.main(), 2)


if __name__ == "__main__":
    unittest.main()
