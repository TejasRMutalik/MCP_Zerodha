"""CLI runner for PII scrubbing:

    uv run python -m pulse.scrub <input_file> [--out output_file]

Scrubs reviews from reviews_ingested.json, replaces all PII with '[redacted]',
sets redacted=True on altered reviews, and outputs reviews_clean.json (or specified out path).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .scrubber import scrub_reviews


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pulse.scrub")
    parser.add_argument("input_path", type=Path, help="Path to JSON file containing ingested reviews")
    parser.add_argument("--out", type=Path, default=None, help="Output path (default: <parent>/reviews_clean.json)")
    args = parser.parse_args(argv)

    if not args.input_path.exists():
        print(f"Error: input file '{args.input_path}' not found.")
        return 1

    try:
        raw_reviews = json.loads(args.input_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Error reading input JSON: {exc}")
        return 1

    print(f"Loaded {len(raw_reviews)} reviews from {args.input_path}")
    scrubbed = scrub_reviews(raw_reviews)

    redacted_count = sum(1 for r in scrubbed if r.get("redacted"))
    print(f"Scrubbing complete: {redacted_count} of {len(scrubbed)} reviews redacted.")

    out_path = args.out or args.input_path.parent / "reviews_clean.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(scrubbed, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved scrubbed dataset to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
