"""Check <folder>/pulse_note.md against the two contract files.

    uv run python -m pulse.validate data/2026-W45

Writes validation.json (with the note's SHA-256 only if every check passes).
Exit code 0 means the note may be delivered; 1 means it may not.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pulse.schema import load_reviews, load_themes

from .gate import passed, validate_note, write_validation


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="pulse.validate")
    ap.add_argument("folder", type=Path)
    args = ap.parse_args(argv)

    note_path = args.folder / "pulse_note.md"
    checks = validate_note(
        note_path.read_text(encoding="utf-8"),
        load_reviews(args.folder / "reviews_clean.json"),
        load_themes(args.folder / "themes.json"),
    )
    write_validation(note_path, checks, args.folder / "validation.json")

    sys.stdout.reconfigure(encoding="utf-8")
    for c in checks:
        print(f"{'PASS' if c.ok else 'FAIL'}  {c.id:9} {c.name}" + (f"  ({c.detail})" if c.detail and not c.ok else ""))
    print("\nVALID: the note may be delivered." if passed(checks) else "\nINVALID: nothing may be delivered.")
    return 0 if passed(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
