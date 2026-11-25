"""CLI runner for theme grouping:

    uv run python -m pulse.themes <input_file_or_folder> [--out-dir out_dir]

Reads scrubbed reviews (reviews_clean.json or reviews_scrubbed.json),
classifies into <= 5 themes using configured LLM, computes theme metrics,
and writes reviews_clean.json and themes.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pulse.config import load_config
from pulse.llm import build_llm

from .grouper import group_reviews
from .prompts import DEFAULT_THEMES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pulse.themes")
    parser.add_argument("path", type=Path, help="Path to scrubbed reviews JSON or directory")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory")
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache/llm/themes"))
    args = parser.parse_args(argv)

    input_file = args.path
    if input_file.is_dir():
        for candidate in ("reviews_clean.json", "reviews_scrubbed.json", "reviews_ingested.json"):
            if (input_file / candidate).exists():
                input_file = input_file / candidate
                break

    if not input_file.exists():
        print(f"Error: input file '{input_file}' not found.")
        return 1

    reviews_data = json.loads(input_file.read_text(encoding="utf-8"))
    print(f"Loaded {len(reviews_data)} reviews from {input_file}")

    cfg = load_config()
    llm = build_llm(cfg)

    print("Running theme classification with tool-free LLM...")
    try:
        clean_reviews, themes = group_reviews(
            llm=llm,
            reviews_data=reviews_data,
            themes=DEFAULT_THEMES,
            cache_dir=args.cache_dir,
        )
    except Exception as exc:
        print(f"Theme grouping failed: {exc}")
        return 1

    out_dir = args.out_dir or input_file.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save reviews_clean.json
    reviews_file = out_dir / "reviews_clean.json"
    reviews_file.write_text(
        json.dumps([r.model_dump(mode="json") for r in clean_reviews], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Save themes.json
    themes_file = out_dir / "themes.json"
    themes_file.write_text(
        json.dumps([t.model_dump(mode="json") for t in themes], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Successfully generated:")
    print(f"-> {reviews_file} ({len(clean_reviews)} reviews)")
    print(f"-> {themes_file} ({len(themes)} themes)")
    for t in themes:
        print(f"   - {t.theme}: {t.count} reviews, avg {t.avg_rating}★")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
