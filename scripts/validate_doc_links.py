#!/usr/bin/env python3
"""Offline check for relative Markdown links in repository documentation."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
SOURCE_CITATION = re.compile(r"\[([A-Z][A-Z0-9-]+)\]\((https://[^)]+)\)")


def main() -> int:
    errors: list[str] = []
    checked = 0
    source_citations = 0
    try:
        register = json.loads((ROOT / "docs/research/source-register.yaml").read_text(encoding="utf-8"))
        sources = {item["source_id"]: item["url"] for item in register["sources"]}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: Cannot load source register for citation checks: {exc}", file=sys.stderr)
        return 2
    for file in ROOT.rglob("*.md"):
        if ".git" in file.parts or any(part.startswith(".") for part in file.relative_to(ROOT).parts[:-1]):
            continue
        text = file.read_text(encoding="utf-8")
        for citation in SOURCE_CITATION.finditer(text):
            source_id, citation_url = citation.groups()
            source_citations += 1
            if source_id not in sources:
                errors.append(f"{file.relative_to(ROOT)}: unknown source ID {source_id}")
            elif sources[source_id] != citation_url:
                errors.append(f"{file.relative_to(ROOT)}: URL for {source_id} does not exactly match source register")
        for match in LINK.finditer(text):
            target = match.group(1).strip().split()[0].strip("<>")
            split = urlsplit(target)
            if split.scheme or split.netloc or not split.path:
                continue
            candidate = (file.parent / unquote(split.path)).resolve()
            checked += 1
            try:
                candidate.relative_to(ROOT)
            except ValueError:
                errors.append(f"{file.relative_to(ROOT)}: link escapes repository: {target}")
                continue
            if not candidate.exists():
                errors.append(f"{file.relative_to(ROOT)}: missing local target: {target}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {checked} relative Markdown links resolve locally; {source_citations} source citations match register IDs and exact URLs (network links not tested)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
