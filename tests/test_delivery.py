"""Tests for Phase 3 B: delivery module (B3.4 / B3.5).

Covers P3-B1 through P3-B9 where B9 is handled by test_constraints.py.

P3-B1  gate catches bad notes          -- via is_deliverable
P3-B2  gate passes good notes          -- via is_deliverable
P3-B3  retries are bounded             -- via write_note (already in test_note_writer)
P3-B4  hash lock works                 -- is_deliverable rejects a changed note
P3-B5  doc and draft are created       -- manual / end-to-end (B3.6, not automated)
P3-B6  draft only                      -- manual
P3-B7  reruns are safe                 -- load_delivery / save_delivery round-trip
P3-B8  partial failure recovers        -- load_delivery sees partial record
P3-B9  no direct Google integration    -- test_constraints.py (already passing)
"""

import json
import shutil
from pathlib import Path

import pytest

from pulse.deliver import DeliveryRecord, load_delivery, note_title, save_delivery
from pulse.deliver.runner import delivery_summary
from pulse.deliver.__main__ import main as deliver_main
from pulse.validate import is_deliverable, write_validation, validate_note
from test_note_writer import REVIEWS, THEMES, FakeLLM, good_answer, run  # noqa: F401

SAMPLES = Path(__file__).resolve().parents[1] / "contracts" / "samples"
NOTE = run(FakeLLM([good_answer()]))[0]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_valid_note(tmp_path: Path) -> tuple[Path, Path]:
    """Write pulse_note.md + validation.json (passing) into tmp_path."""
    note_path = tmp_path / "pulse_note.md"
    val_path = tmp_path / "validation.json"
    note_path.write_text(NOTE, encoding="utf-8")
    checks = validate_note(NOTE, REVIEWS, THEMES)
    write_validation(note_path, checks, val_path)
    return note_path, val_path


# ---------------------------------------------------------------------------
# P3-B2 / P3-B4  hash lock
# ---------------------------------------------------------------------------

def test_p3_b2_valid_note_is_deliverable(tmp_path):
    """P3-B2: a correctly validated note passes is_deliverable."""
    note_path, val_path = _write_valid_note(tmp_path)
    ok, reason = is_deliverable(note_path, val_path)
    assert ok, reason


def test_p3_b4_edited_note_is_blocked(tmp_path):
    """P3-B4: editing the note after validation makes delivery refuse."""
    note_path, val_path = _write_valid_note(tmp_path)
    note_path.write_text(NOTE + "\nSomething extra was injected.\n", encoding="utf-8")
    ok, reason = is_deliverable(note_path, val_path)
    assert not ok
    assert "changed" in reason


def test_p3_b4_missing_validation_blocks_delivery(tmp_path):
    """P3-B4: delivery is refused when validation.json does not exist."""
    note_path = tmp_path / "pulse_note.md"
    note_path.write_text(NOTE, encoding="utf-8")
    ok, _ = is_deliverable(note_path, tmp_path / "validation.json")
    assert not ok


def test_p3_b1_failed_note_cannot_be_delivered(tmp_path):
    """P3-B1: a note that failed validation cannot be delivered."""
    bad = NOTE + " extra " * 300  # exceeds 250 words
    note_path = tmp_path / "pulse_note.md"
    val_path = tmp_path / "validation.json"
    note_path.write_text(bad, encoding="utf-8")
    write_validation(note_path, validate_note(bad, REVIEWS, THEMES), val_path)
    ok, _ = is_deliverable(note_path, val_path)
    assert not ok


# ---------------------------------------------------------------------------
# P3-B7  reruns are safe (delivery.json round-trip)
# ---------------------------------------------------------------------------

def test_p3_b7_full_delivery_record_round_trips(tmp_path):
    """P3-B7: a fully delivered record survives a save/load cycle."""
    record = DeliveryRecord(
        week="2026-W47",
        note_sha256="abc123",
        delivered_at="2026-11-24T06:00:00+00:00",
        doc_id="1xeo3GZknwGou4JytBWC_71UGEmgVgdb5ZEAgP2SjAlM",
        doc_title="Zerodha Kite Weekly Review Pulse | 2026-W47",
        draft_id="r2995113518879698448",
    )
    path = tmp_path / "delivery.json"
    save_delivery(record, path)
    loaded = load_delivery(path)
    assert loaded == record


def test_p3_b7_load_missing_delivery_returns_none(tmp_path):
    """P3-B7: load_delivery returns None when the file does not exist."""
    assert load_delivery(tmp_path / "delivery.json") is None


def test_p3_b7_load_corrupt_delivery_returns_none(tmp_path):
    """P3-B7: a corrupt delivery.json is treated as missing."""
    p = tmp_path / "delivery.json"
    p.write_text("not json at all", encoding="utf-8")
    assert load_delivery(p) is None


def test_p3_b7_save_is_atomic(tmp_path):
    """P3-B7: save_delivery leaves no .tmp file after success."""
    record = DeliveryRecord(week="2026-W47", note_sha256="abc")
    path = tmp_path / "delivery.json"
    save_delivery(record, path)
    assert path.exists()
    assert not (tmp_path / "delivery.tmp").exists()


# ---------------------------------------------------------------------------
# P3-B8  partial failure recovery
# ---------------------------------------------------------------------------

def test_p3_b8_partial_record_has_doc_but_no_draft(tmp_path):
    """P3-B8: a partial delivery.json (doc done, draft not yet) is detected."""
    record = DeliveryRecord(
        week="2026-W47",
        note_sha256="abc123",
        doc_id="1xeo3GZknwGou4JytBWC_71UGEmgVgdb5ZEAgP2SjAlM",
        doc_title="Zerodha Kite Weekly Review Pulse | 2026-W47",
    )
    path = tmp_path / "delivery.json"
    save_delivery(record, path)
    loaded = load_delivery(path)
    assert loaded.doc_id
    assert not loaded.draft_id


def test_p3_b8_summary_reports_partial(tmp_path):
    """P3-B8: delivery_summary says 'partial' when only the doc exists."""
    record = DeliveryRecord(
        week="2026-W47",
        note_sha256="abc",
        doc_id="some-doc-id",
    )
    summary = delivery_summary(record)
    assert "partial" in summary
    assert "some-doc-id" in summary


def test_p3_b8_summary_reports_complete():
    """P3-B8: delivery_summary says 'complete' when both IDs are present."""
    record = DeliveryRecord(
        week="2026-W47",
        note_sha256="abc",
        doc_id="doc-id",
        draft_id="draft-id",
    )
    assert "complete" in delivery_summary(record)


# ---------------------------------------------------------------------------
# note_title helper
# ---------------------------------------------------------------------------

def test_note_title_format():
    assert note_title("Zerodha Kite", "2026-W47") == "Zerodha Kite Weekly Review Pulse | 2026-W47"


# ---------------------------------------------------------------------------
# CLI pre-flight check (pulse.deliver.__main__)
# ---------------------------------------------------------------------------

def test_cli_ready_on_valid_note(tmp_path):
    """CLI exits 0 when note is validated and not yet delivered."""
    for name in ("reviews_clean.json", "themes.json"):
        shutil.copy(SAMPLES / name, tmp_path / name)
    _write_valid_note(tmp_path)
    assert deliver_main([str(tmp_path)]) == 0


def test_cli_not_ready_when_note_is_missing(tmp_path):
    """CLI exits 1 when pulse_note.md does not exist."""
    assert deliver_main([str(tmp_path)]) == 1


def test_cli_not_ready_when_note_changed_after_validation(tmp_path):
    """CLI exits 1 when the note was edited after validation."""
    note_path, _ = _write_valid_note(tmp_path)
    note_path.write_text(NOTE + "\nTampered.\n", encoding="utf-8")
    assert deliver_main([str(tmp_path)]) == 1


def test_cli_already_delivered_exits_0(tmp_path):
    """CLI exits 0 (not an error) when delivery.json shows a full delivery."""
    _write_valid_note(tmp_path)
    record = DeliveryRecord(
        week="2026-W47",
        note_sha256="abc",
        doc_id="some-doc-id",
        draft_id="some-draft-id",
    )
    save_delivery(record, tmp_path / "delivery.json")
    assert deliver_main([str(tmp_path)]) == 0
