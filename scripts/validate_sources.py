#!/usr/bin/env python3
"""Offline structural validator for the source register's JSON-compatible YAML subset."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs/research/source-register.yaml"
ALLOWED_STATUS = {"not_started", "in_progress", "reviewed", "validated", "blocked"}
ALLOWED_CURRENTNESS = {"current", "legacy", "unclear", "changed", "inaccessible", "superseded"}
REQUIRED_FIELDS = {
    "source_id", "title", "url", "official_domain", "documentation_type",
    "discovery_path", "retrieved_at_utc", "published_or_updated_at",
    "currentness_classification", "topics", "claims_summary",
    "confidence_and_evidence_notes", "related_source_ids", "research_status",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, default=REGISTER, help="Register path (JSON-compatible YAML subset)")
    args = parser.parse_args()
    try:
        data = json.loads(args.register.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: Cannot read JSON-compatible YAML source register: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    if not isinstance(data, dict) or data.get("schema_version") != "1.0":
        errors.append("top-level schema_version must be '1.0'")
    sources = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(sources, list):
        errors.append("top-level sources must be a list")
        sources = []

    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    statuses: Counter[str] = Counter()
    for index, source in enumerate(sources, start=1):
        prefix = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        missing = REQUIRED_FIELDS - source.keys()
        if missing:
            errors.append(f"{prefix} missing fields: {', '.join(sorted(missing))}")
            continue
        sid = source["source_id"]
        if not isinstance(sid, str) or not sid.strip():
            errors.append(f"{prefix}.source_id must be a non-empty string")
        elif sid in seen_ids:
            errors.append(f"duplicate source_id: {sid}")
        else:
            seen_ids.add(sid)

        url = source["url"]
        parsed = urlparse(url if isinstance(url, str) else "")
        if parsed.scheme != "https" or not parsed.hostname:
            errors.append(f"{prefix}.url must be an absolute https URL")
        else:
            if url in seen_urls:
                errors.append(f"duplicate URL: {url}")
            seen_urls.add(url)
            domain = source["official_domain"]
            if not isinstance(domain, str) or not (parsed.hostname == domain or parsed.hostname.endswith("." + domain)):
                errors.append(f"{prefix}.official_domain does not match URL host {parsed.hostname}")

        retrieved = source["retrieved_at_utc"]
        if not isinstance(retrieved, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", retrieved):
            errors.append(f"{prefix}.retrieved_at_utc must be UTC ISO-8601 ending in Z")
        else:
            try:
                datetime.strptime(retrieved, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                errors.append(f"{prefix}.retrieved_at_utc is not a valid UTC datetime")

        pub = source["published_or_updated_at"]
        if pub is not None and (not isinstance(pub, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:T.*)?", pub)):
            errors.append(f"{prefix}.published_or_updated_at must be null or a source-provided date")
        if source["currentness_classification"] not in ALLOWED_CURRENTNESS:
            errors.append(f"{prefix}.currentness_classification is invalid")
        status = source["research_status"]
        if status not in ALLOWED_STATUS:
            errors.append(f"{prefix}.research_status is invalid")
        statuses[str(status)] += 1
        if status in {"reviewed", "validated"}:
            for field in ("title", "discovery_path", "claims_summary", "confidence_and_evidence_notes"):
                if not isinstance(source[field], str) or not source[field].strip():
                    errors.append(f"{prefix}.{field} is required for {status} sources")
        if not isinstance(source["topics"], list) or not all(isinstance(x, str) for x in source["topics"]):
            errors.append(f"{prefix}.topics must be a list of strings")
        if not isinstance(source["related_source_ids"], list):
            errors.append(f"{prefix}.related_source_ids must be a list")

    # Resolve cross-references after collecting all stable IDs.
    for index, source in enumerate(sources, start=1):
        if isinstance(source, dict):
            for related in source.get("related_source_ids", []):
                if related not in seen_ids:
                    errors.append(f"sources[{index}] references unknown source_id {related}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {len(sources)} records; {len(seen_ids)} unique IDs and URLs")
    print("Research statuses: " + ", ".join(f"{k}={v}" for k, v in sorted(statuses.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
