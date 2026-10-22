"""Opt-in, read-only public market-data clients; tests use injected offline transport."""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

MAX_BYTES = 2_000_000
USER_AGENT = "wallex-trading-research/0.1 (read-only)"

class ClientError(RuntimeError):
    pass

class Response:
    def __init__(self, status: int, body: bytes, final_url: str):
        self.status, self.body, self.final_url = status, body, final_url

def _https(url: str) -> str:
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password or p.fragment:
        raise ClientError("Only credential-free HTTPS URLs are permitted")
    return url

def _transport(url: str, headers: dict[str, str], timeout: float) -> Response:
    _https(url)
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            final = _https(r.geturl())
            body = r.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES: raise ClientError("Response too large")
            return Response(r.status, body, final)
    except urllib.error.HTTPError as e:
        return Response(e.code, e.read(MAX_BYTES + 1), e.geturl())
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise ClientError("HTTPS request failed (" + type(e).__name__ + ")") from None

def request_json(url: str, *, headers: dict[str, str] | None = None, timeout: float = 12, transport: Callable = _transport) -> tuple[dict[str, Any], Response]:
    _https(url)
    if timeout <= 0 or timeout > 30: raise ClientError("Timeout must be in (0, 30] seconds")
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    h.update(headers or {})
    r = transport(url, h, timeout)
    _https(r.final_url)
    if len(r.body) > MAX_BYTES: raise ClientError("Response too large")
    if not 200 <= r.status < 300: raise ClientError("HTTP status " + str(r.status))
    try: data = json.loads(r.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError): raise ClientError("Response was not UTF-8 JSON") from None
    if not isinstance(data, dict): raise ClientError("Expected JSON object")
    return data, r

def _snapshot(provider: str, url: str, data: dict[str, Any], response: Response) -> dict[str, Any]:
    return {"schema_version":"1.0","provider":provider,"source_url":url,"retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"http_status":response.status,"raw_response_sha256":hashlib.sha256(response.body).hexdigest(),"data":data}

def wallex_get(base_url: str, route: str, params: dict[str, str] | None = None, *, transport: Callable = _transport) -> dict[str, Any]:
    base = _https(base_url.rstrip("/") + "/")
    route = route.lstrip("/")
    if not route or route.startswith(("http:", "https:")) or ".." in route.split("/"): raise ClientError("Route must be a safe relative path")
    url = urllib.parse.urljoin(base, route)
    if urllib.parse.urlsplit(url).hostname != urllib.parse.urlsplit(base).hostname: raise ClientError("Route escaped configured host")
    query = urllib.parse.urlencode(params or {})
    if query: url += ("&" if "?" in url else "?") + query
    data, response = request_json(url, transport=transport)
    return _snapshot("wallex", url, data, response)

def coingecko_price(ids: list[str], currencies: list[str], *, api_key: str | None = None, transport: Callable = _transport) -> dict[str, Any]:
    ids = [x.strip() for x in ids if x.strip()]
    currencies = [x.strip().lower() for x in currencies if x.strip()]
    if not ids or not currencies or any("," in x for x in ids + currencies): raise ClientError("Provide explicit coin IDs and quote currencies")
    url = "https://api.coingecko.com/api/v3/simple/price?" + urllib.parse.urlencode({"ids":",".join(ids),"vs_currencies":",".join(currencies),"include_last_updated_at":"true"})
    headers = {"x-cg-demo-api-key": api_key} if api_key else {}
    data, response = request_json(url, headers=headers, transport=transport)
    return _snapshot("coingecko", url, data, response)

def write_snapshot(doc: dict[str, Any], directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = directory / (doc["provider"] + "-" + stamp + ".json")
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("--network", action="store_true"); p.add_argument("--out-dir", type=Path, default=Path("reports/public-market-data"))
    subs = p.add_subparsers(dest="provider", required=True)
    w = subs.add_parser("wallex-markets"); w.add_argument("--base-url", default=os.getenv("WALLEX_API_BASE_URL")); w.add_argument("--route", default=os.getenv("WALLEX_MARKETS_PATH", ""))
    c = subs.add_parser("coingecko-price"); c.add_argument("--ids", default="bitcoin,ethereum"); c.add_argument("--vs", default="usd")
    a = p.parse_args(argv)
    if not a.network: print("Network disabled; pass --network after reviewing endpoint configuration.", file=sys.stderr); return 2
    try:
        if a.provider == "wallex":
            if not a.base_url or not a.route: raise ClientError("Set WALLEX_API_BASE_URL and WALLEX_MARKETS_PATH from a reviewed contract")
            doc = wallex_get(a.base_url, a.route)
        elif a.provider == "wallex-markets":
            if not a.base_url or not a.route: raise ClientError("Set WALLEX_API_BASE_URL and WALLEX_MARKETS_PATH from a reviewed contract")
            doc = wallex_get(a.base_url, a.route)
        else: doc = coingecko_price(a.ids.split(","), a.vs.split(","), api_key=os.getenv("COINGECKO_DEMO_API_KEY"))
        path = write_snapshot(doc, a.out_dir)
        print(json.dumps({"provider":doc["provider"],"snapshot":str(path),"sha256":doc["raw_response_sha256"]},sort_keys=True)); return 0
    except (ClientError, OSError) as e:
        msg = re.sub(r"(?i)(key|token|authorization|api[-_]?key)([=: ]+)[^&\\s,;]+", r"\\1\\2[REDACTED]", str(e))
        print("ERROR: " + msg, file=sys.stderr); return 1

if __name__ == "__main__": raise SystemExit(main())
