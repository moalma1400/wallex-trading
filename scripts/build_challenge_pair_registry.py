#!/usr/bin/env python3
"""Build or verify the deterministic disabled-pair JSON from preserved raw text."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "config/challenge/wallex_disabled_spot_pairs_raw.txt"
DEFAULT_OUTPUT = ROOT / "config/challenge/wallex_disabled_spot_pairs.json"

sys.path.insert(0, str(ROOT / "src"))
from wallex_research.challenge import ChallengePolicyError, build_disabled_pair_registry  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW, help="raw UTF-8 pair-list source")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="derived JSON registry")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true", help="write the derived JSON; raw evidence is never modified")
    action.add_argument("--check", action="store_true", help="verify the checked-in JSON matches raw evidence")
    args = parser.parse_args()
    raw_path = args.raw if args.raw.is_absolute() else ROOT / args.raw
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    try:
        registry = build_disabled_pair_registry(raw_path.read_bytes())
    except (OSError, ChallengePolicyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    serialized = json.dumps(registry, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read derived registry: {exc}", file=sys.stderr)
            return 2
        if existing != registry:
            print("ERROR: derived registry differs from raw source; inspect diagnostics and regenerate intentionally", file=sys.stderr)
            return 1
        print(
            "OK: derived registry matches raw source; "
            f"raw={registry['raw_entry_count']} unique={registry['unique_pair_count']} "
            f"duplicate_pairs={registry['duplicate_pair_count']} "
            f"duplicate_excess={registry['duplicate_excess_entry_count']} "
            f"malformed={registry['malformed_entry_count']}"
        )
        return 0
    if args.write:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized, encoding="utf-8")
        print(f"Wrote derived registry to {output_path}")
        print(
            f"raw={registry['raw_entry_count']} unique={registry['unique_pair_count']} "
            f"duplicate_pairs={registry['duplicate_pair_count']} "
            f"duplicate_excess={registry['duplicate_excess_entry_count']} "
            f"malformed={registry['malformed_entry_count']}"
        )
        return 0
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
