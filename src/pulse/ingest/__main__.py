"""CLI runner for review ingestion:

    uv run python -m pulse.ingest [output_dir] [--end-date YYYY-MM-DD] [--weeks 12]

Fetches App Store RSS and Play Store reviews for Zerodha Kite,
normalises, deduplicates, verifies volume thresholds, and saves reviews_ingested.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from pulse.config import load_config

from .app_store import fetch_app_store_reviews
from .normalise import check_volume, deduplicate_reviews, filter_by_window
from .play_store import fetch_play_store_reviews


def run_ingest(
    out_dir: Path,
    end_date: dt.date | None = None,
    weeks: int | None = None,
    skip_volume_check: bool = False,
) -> Path:
    cfg = load_config()
    product = cfg["product"]

    end_date = end_date or dt.date.today()
    weeks = weeks or int(product.get("window_weeks", 12))
    start_date = end_date - dt.timedelta(weeks=weeks)

    print(f"Ingesting reviews for {product['name']}")
    print(f"Window: {start_date} to {end_date} ({weeks} weeks)")

    # 1. Fetch App Store
    print(f"Fetching App Store reviews (id={product['app_store_id']})...")
    app_reviews = fetch_app_store_reviews(
        app_id=str(product["app_store_id"]),
        country=product.get("country", "in"),
        window_start=start_date,
    )
    print(f"-> Fetched {len(app_reviews)} raw App Store reviews.")

    # 2. Fetch Play Store
    print(f"Fetching Play Store reviews (id={product['play_store_id']})...")
    play_reviews = fetch_play_store_reviews(
        app_id=str(product["play_store_id"]),
        country=product.get("country", "in"),
        language=product.get("language", "en"),
        window_start=start_date,
    )
    print(f"-> Fetched {len(play_reviews)} raw Play Store reviews.")

    # 3. Combine, window filter, and deduplicate
    combined = app_reviews + play_reviews
    in_window = filter_by_window(combined, start_date, end_date)
    unique_reviews = deduplicate_reviews(in_window)

    # 4. Volume verification
    if not skip_volume_check:
        app_count, play_count = check_volume(unique_reviews)
        print(f"Volume check passed: {app_count} App Store, {play_count} Play Store.")
    else:
        app_count = sum(1 for r in unique_reviews if r.store == "app_store")
        play_count = sum(1 for r in unique_reviews if r.store == "play_store")
        print(f"Volume: {app_count} App Store, {play_count} Play Store (check skipped).")

    # 5. Save output
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "reviews_ingested.json"
    data = [r.model_dump(mode="json") for r in unique_reviews]
    out_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f"Saved {len(unique_reviews)} reviews to {out_file}")
    return out_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pulse.ingest")
    parser.add_argument("folder", type=Path, nargs="?", default=Path("data/live"))
    parser.add_argument("--end-date", type=dt.date.fromisoformat, default=None)
    parser.add_argument("--weeks", type=int, default=None)
    parser.add_argument("--no-volume-check", action="store_true")
    args = parser.parse_args(argv)

    try:
        run_ingest(
            out_dir=args.folder,
            end_date=args.end_date,
            weeks=args.weeks,
            skip_volume_check=args.no_volume_check,
        )
        return 0
    except Exception as exc:
        print(f"Ingestion failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
