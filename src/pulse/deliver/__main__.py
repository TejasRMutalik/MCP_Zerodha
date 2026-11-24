"""Check whether a folder is ready to deliver, without making any MCP calls.

    uv run python -m pulse.deliver .cache/w

Reads pulse_note.md and validation.json.  Prints the delivery status and exits
with code 0 (ready) or 1 (not ready).  This is the pre-flight check the
/deliver-pulse command runs first.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pulse.validate import is_deliverable

from .runner import delivery_summary, load_delivery


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="pulse.deliver")
    ap.add_argument("folder", type=Path)
    args = ap.parse_args(argv)

    note_path = args.folder / "pulse_note.md"
    val_path = args.folder / "validation.json"
    delivery_path = args.folder / "delivery.json"

    ok, reason = is_deliverable(note_path, val_path)
    if not ok:
        print(f"NOT READY: {reason}", file=sys.stderr)
        return 1

    record = load_delivery(delivery_path)
    if record and record.doc_id and record.draft_id:
        print(f"ALREADY DELIVERED: {delivery_summary(record)}")
        return 0

    sys.stdout.reconfigure(encoding="utf-8")
    print("READY TO DELIVER")
    if record:
        print(f"Partial delivery found: {delivery_summary(record)}")
    else:
        print("No previous delivery.json — this will be a fresh delivery.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
