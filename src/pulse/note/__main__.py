"""Turn reviews_clean.json and themes.json into pulse_note.md (Phase 2 B output).

    uv run python -m pulse.note contracts/samples --out pulse_note.md

Reads only the two contract files. Calls the LLM with no tools. Writes the note
to a file; it never touches Google (delivery is a separate step).
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from pulse.config import load_config
from pulse.llm import build_llm
from pulse.schema import check_dataset, load_reviews, load_themes

from .render import make_meta
from .writer import NoteError, write_note


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="pulse.note")
    ap.add_argument("folder", type=Path, help="folder holding reviews_clean.json and themes.json")
    ap.add_argument("--out", type=Path, help="default: <folder>/pulse_note.md")
    ap.add_argument("--week-of", type=dt.date.fromisoformat, default=dt.date.today())
    args = ap.parse_args(argv)

    reviews = load_reviews(args.folder / "reviews_clean.json")
    themes = load_themes(args.folder / "themes.json")
    problems = check_dataset(reviews, themes)
    if problems:
        print("The two input files do not agree:\n- " + "\n- ".join(problems), file=sys.stderr)
        return 2

    cfg = load_config()
    meta = make_meta(reviews, cfg["product"]["name"], args.week_of)
    try:
        note, *_ = write_note(build_llm(cfg), meta, reviews, themes)
    except NoteError as exc:
        print(f"No note written: {exc}", file=sys.stderr)
        return 1

    out = args.out or args.folder / "pulse_note.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(note, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # the note has ★ and ·; Windows consoles default to cp1252
    print(note)
    print(f"Written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
