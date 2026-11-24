"""Idempotency support for the weekly delivery (B3.5).

delivery.json lives in the same folder as pulse_note.md and records the
Google Doc ID and Gmail draft ID after a successful delivery.  On a rerun the
command reads this file first and skips any step whose ID is already recorded.

Nothing in here makes a network call or imports a Google library.  All MCP
tool calls happen in .claude/commands/deliver-pulse.md.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class DeliveryRecord:
    """Written to delivery.json after each step succeeds."""

    week: str                        # ISO week label, e.g. "2026-W45"
    note_sha256: str                 # hash of the validated note (from validation.json)
    delivered_at: str = ""           # ISO timestamp set when delivery finishes
    doc_id: str = ""                 # Google Doc ID; empty until Drive/Docs step done
    doc_title: str = ""              # e.g. "Zerodha Kite Weekly Review Pulse | 2026-W45"
    draft_id: str = ""               # Gmail draft ID; empty until Gmail step done
    errors: list[str] = field(default_factory=list)


def note_title(product: str, week: str) -> str:
    """Canonical Google Doc title used for the duplicate-title search."""
    return f"{product} Weekly Review Pulse | {week}"


def load_delivery(path: Path) -> DeliveryRecord | None:
    """Return the existing DeliveryRecord, or None if the file is absent/corrupt."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return DeliveryRecord(**data)
    except (OSError, ValueError, TypeError):
        return None


def save_delivery(record: DeliveryRecord, path: Path) -> None:
    """Persist the record atomically (write-then-rename so a crash leaves a good file)."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(record), indent=2), encoding="utf-8")
    tmp.replace(path)


def delivery_summary(record: DeliveryRecord) -> str:
    """Human-readable one-liner for the command output."""
    parts = []
    if record.doc_id:
        parts.append(f"doc {record.doc_id}")
    if record.draft_id:
        parts.append(f"draft {record.draft_id}")
    if not parts:
        return "nothing delivered yet"
    status = "complete" if record.doc_id and record.draft_id else "partial"
    return f"{status}: " + ", ".join(parts)
