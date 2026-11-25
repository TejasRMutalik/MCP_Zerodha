"""Full pipeline orchestrator (Phase 4):

Runs the complete Weekly App Review Pulse pipeline:
  1. pulse.ingest   -> Ingest public App Store & Play Store reviews
  2. pulse.scrub    -> Strip PII, set redacted: true
  3. pulse.themes   -> LLM theme grouping & contract validation
  4. pulse.note     -> Generate structured note & render pulse_note.md
  5. pulse.validate -> Check note against contracts & write SHA-256 hash lock
  6. Ready for /deliver-pulse
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from pathlib import Path

from pulse.config import load_config
from pulse.ingest import check_volume, deduplicate_reviews, fetch_app_store_reviews, fetch_play_store_reviews, filter_by_window
from pulse.llm import build_llm
from pulse.note.render import make_meta
from pulse.note.writer import write_note
from pulse.pii import scrub_reviews
from pulse.schema import load_reviews, load_themes
from pulse.themes import DEFAULT_THEMES, group_reviews
from pulse.validate import is_deliverable, passed, validate_note, write_validation

logger = logging.getLogger(__name__)


def default_week_label(date: dt.date | None = None) -> str:
    """Return ISO week format, e.g. '2026-W47'."""
    d = date or dt.date.today()
    return f"{d.isocalendar().year}-W{d.isocalendar().week:02d}"


def run_pipeline(
    week: str | None = None,
    end_date: dt.date | None = None,
    weeks: int | None = None,
    out_dir: Path | str | None = None,
    no_volume_check: bool = False,
    llm_instance = None,
) -> Path:
    """Execute all phases 1 through 4 end-to-end for a given week."""
    cfg = load_config()
    product = cfg["product"]
    llm = llm_instance or build_llm(cfg)

    end_date = end_date or dt.date.today()
    weeks = weeks or int(product.get("window_weeks", 12))
    start_date = end_date - dt.timedelta(weeks=weeks)
    week_label = week or default_week_label(end_date)

    target_dir = Path(out_dir) if out_dir else Path(f"data/{week_label}")
    target_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"PULSE PIPELINE: {product['name']} | Week: {week_label}")
    print(f"Date window: {start_date} to {end_date} ({weeks} weeks)")
    print(f"Output folder: {target_dir}")
    print("=" * 60)

    # -----------------------------------------------------------------------
    # Step 1: Ingest
    # -----------------------------------------------------------------------
    print("\n[1/5] Ingesting reviews from public App Store and Play Store...")
    app_raw = fetch_app_store_reviews(
        app_id=str(product["app_store_id"]),
        country=product.get("country", "in"),
        window_start=start_date,
    )
    play_raw = fetch_play_store_reviews(
        app_id=str(product["play_store_id"]),
        country=product.get("country", "in"),
        language=product.get("language", "en"),
        window_start=start_date,
    )

    combined = app_raw + play_raw
    in_window = filter_by_window(combined, start_date, end_date)
    deduped = deduplicate_reviews(in_window)

    if not no_volume_check:
        n_app, n_play = check_volume(deduped)
        print(f"      Volume check OK: {n_app} App Store, {n_play} Play Store reviews.")
    else:
        n_app = sum(1 for r in deduped if r.store == "app_store")
        n_play = sum(1 for r in deduped if r.store == "play_store")
        print(f"      Volume: {n_app} App Store, {n_play} Play Store (check skipped).")

    # -----------------------------------------------------------------------
    # Step 2: PII Scrub
    # -----------------------------------------------------------------------
    print("\n[2/5] Scrubbing PII from reviews...")
    raw_dicts = [r.model_dump(mode="json") for r in deduped]
    scrubbed_dicts = scrub_reviews(raw_dicts)
    redacted_cnt = sum(1 for r in scrubbed_dicts if r.get("redacted"))
    print(f"      Scrubbed {len(scrubbed_dicts)} reviews ({redacted_cnt} redacted).")

    # -----------------------------------------------------------------------
    # Step 3: Theme Grouping
    # -----------------------------------------------------------------------
    print("\n[3/5] Classifying themes with tool-free LLM...")
    cache_path = Path(cfg.get("llm", {}).get("cache_dir", ".cache/llm")) / "themes"
    clean_reviews, themes = group_reviews(
        llm=llm,
        reviews_data=scrubbed_dicts,
        themes=DEFAULT_THEMES,
        cache_dir=cache_path,
    )

    # Persist contract files
    reviews_clean_file = target_dir / "reviews_clean.json"
    reviews_clean_file.write_text(
        json.dumps([r.model_dump(mode="json") for r in clean_reviews], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    themes_file = target_dir / "themes.json"
    themes_file.write_text(
        json.dumps([t.model_dump(mode="json") for t in themes], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"      Saved {reviews_clean_file.name} and {themes_file.name}.")

    # -----------------------------------------------------------------------
    # Step 4: Note Generation
    # -----------------------------------------------------------------------
    print("\n[4/5] Generating weekly pulse note...")
    meta = make_meta(clean_reviews, product["name"], end_date)
    note_text, content, ranked, quotes_by_id = write_note(llm, meta, clean_reviews, themes)

    note_file = target_dir / "pulse_note.md"
    note_file.write_text(note_text, encoding="utf-8")
    print(f"      Saved {note_file.name} ({len(note_text.split())} words).")

    # -----------------------------------------------------------------------
    # Step 5: Validation Gate
    # -----------------------------------------------------------------------
    print("\n[5/5] Running validation gate...")
    checks = validate_note(note_text, clean_reviews, themes)
    val_file = target_dir / "validation.json"
    val_record = write_validation(note_file, checks, val_file)

    for c in checks:
        print(f"      [{'PASS' if c.ok else 'FAIL'}] {c.id:9} {c.name}")

    if not passed(checks):
        print("\nERROR: Note failed validation. Refusing to unlock delivery.")
        raise RuntimeError("Validation gate failed.")

    deliverable, reason = is_deliverable(note_file, val_file)
    if not deliverable:
        raise RuntimeError(f"Hash check failed: {reason}")

    print("\n" + "=" * 60)
    print("SUCCESS: Weekly pulse generated and verified!")
    print(f"Note SHA-256: {val_record['note_sha256']}")
    print(f"Ready for delivery: /deliver-pulse {week_label}")
    print("=" * 60)
    return target_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pulse run")
    parser.add_argument("--week", type=str, default=None, help="Week label (e.g. 2026-W47)")
    parser.add_argument("--end-date", type=dt.date.fromisoformat, default=None, help="End date (YYYY-MM-DD)")
    parser.add_argument("--weeks", type=int, default=None, help="Window length in weeks (default 12)")
    parser.add_argument("--out-dir", type=Path, default=None, help="Custom output directory")
    parser.add_argument("--no-volume-check", action="store_true", help="Skip minimum review volume check")
    args = parser.parse_args(argv)

    try:
        run_pipeline(
            week=args.week,
            end_date=args.end_date,
            weeks=args.weeks,
            out_dir=args.out_dir,
            no_volume_check=args.no_volume_check,
        )
        return 0
    except Exception as exc:
        print(f"\nPipeline run failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
