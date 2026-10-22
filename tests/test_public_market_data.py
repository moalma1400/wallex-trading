import hashlib
import unittest
from wallex_research.public_market_data import ClientError, Response, request_json, wallex_get, coingecko_price

class Fake:
    def __init__(self, status=200, body=b'{"ok":true}', final="https://example.invalid/data"):
        self.response = Response(status, body, final); self.calls = []
    def __call__(self, url, headers, timeout):
        self.calls.append((url, headers, timeout)); return self.response

class PublicMarketDataTests(unittest.TestCase):
    def test_json_and_hash(self):
        body=b'{"ok":true}'; fake=Fake(body=body)
        data, response=request_json("https://example.invalid/data", transport=fake)
        self.assertTrue(data["ok"]); self.assertEqual(hashlib.sha256(response.body).hexdigest(), hashlib.sha256(body).hexdigest())
    def test_http_and_url_credentials_rejected(self):
        with self.assertRaises(ClientError): request_json("http://example.com")
        with self.assertRaises(ClientError): request_json("https://user:pass@example.com/a")
    def test_non_2xx_rejected(self):
        with self.assertRaisesRegex(ClientError, "429"): request_json("https://example.invalid/a", transport=Fake(status=429))
    def test_invalid_json_rejected(self):
        with self.assertRaisesRegex(ClientError, "JSON"): request_json("https://example.invalid/a", transport=Fake(body=b"nope"))
    def test_non_object_json_rejected(self):
        with self.assertRaisesRegex(ClientError, "object"): request_json("https://example.invalid/a", transport=Fake(body=b"[]"))
    def test_insecure_final_url_rejected(self):
        with self.assertRaises(ClientError): request_json("https://example.invalid/a", transport=Fake(final="http://example.invalid/a"))
    def test_wallex_requires_relative_route(self):
        fake=Fake(final="https://example.invalid/v1/markets")
        doc=wallex_get("https://example.invalid", "/v1/markets", transport=fake)
        self.assertEqual(doc["provider"], "wallex")
        with self.assertRaises(ClientError): wallex_get("https://example.invalid", "https://evil.invalid/a", transport=fake)
    def test_coingecko_key_only_in_header(self):
        fake=Fake(final="https://api.coingecko.com/api/v3/simple/price")
        coingecko_price(["bitcoin"], ["usd"], api_key="test-secret", transport=fake)
        url, headers, _=fake.calls[0]
        self.assertNotIn("test-secret", url); self.assertEqual(headers["x-cg-demo-api-key"], "test-secret")
    def test_timeout_bound(self):
        with self.assertRaisesRegex(ClientError, "Timeout"): request_json("https://example.invalid/a", timeout=99, transport=Fake())

if __name__ == "__main__": unittest.main()
