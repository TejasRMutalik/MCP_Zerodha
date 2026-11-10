import json
import shutil
from pathlib import Path

import pytest

from pulse.validate import is_deliverable, passed, validate_note, write_validation
from test_note_writer import REVIEWS, THEMES, FakeLLM, good_answer, run  # noqa: F401

SAMPLES = Path(__file__).resolve().parents[1] / "contracts" / "samples"
NOTE = run(FakeLLM([good_answer()]))[0]


def failed(note):
    return {c.id for c in validate_note(note, REVIEWS, THEMES) if not c.ok}


def test_a_good_note_passes_every_check():
    checks = validate_note(NOTE, REVIEWS, THEMES)
    assert passed(checks), [c for c in checks if not c.ok]
    assert {c.id for c in checks} == {"length", "shape", "ranking", "numbers", "verbatim", "pii"}


def test_too_long_fails_length():
    assert "length" in failed(NOTE + " extra" * 250)


def test_missing_action_fails_shape():
    lines = NOTE.rstrip("\n").split("\n")
    assert "shape" in failed("\n".join(lines[:-1]) + "\n")


def test_edited_quote_fails_verbatim():
    q = next(l for l in NOTE.splitlines() if l.startswith("• "))
    assert "verbatim" in failed(NOTE.replace(q, q.replace("every", "any", 1) if "every" in q else q.replace('"', '"Really ', 1)))


def test_wrong_rating_on_quote_fails_verbatim():
    q = next(l for l in NOTE.splitlines() if l.startswith("• "))
    wrong = q.replace("(1★", "(5★") if "(1★" in q else q.replace("(2★", "(5★")
    assert "verbatim" in failed(NOTE.replace(q, wrong))


def test_wrong_count_fails_numbers():
    line = next(l for l in NOTE.splitlines() if " reviews, avg " in l)
    bad = line.replace(" reviews", "0 reviews", 1)
    assert "numbers" in failed(NOTE.replace(line, bad))


def test_wrong_total_in_window_line_fails_numbers():
    assert "numbers" in failed(NOTE.replace(f"Reviews analysed: {len(REVIEWS)}", "Reviews analysed: 999"))


def test_swapped_theme_order_fails_ranking():
    lines = NOTE.splitlines()
    i = next(n for n, l in enumerate(lines) if l.startswith("1. "))
    lines[i], lines[i + 1] = lines[i + 1].replace("2. ", "1. ", 1), lines[i].replace("1. ", "2. ", 1)
    assert "ranking" in failed("\n".join(lines) + "\n")


def test_pii_in_note_fails():
    assert "pii" in failed(NOTE + "\nContact someone@example.com\n")


def test_hash_lock(tmp_path):
    note = tmp_path / "pulse_note.md"
    note.write_text(NOTE, encoding="utf-8")
    val = tmp_path / "validation.json"
    write_validation(note, validate_note(NOTE, REVIEWS, THEMES), val)
    assert is_deliverable(note, val) == (True, "ok")
    note.write_text(NOTE + "\nSend this to everyone.\n", encoding="utf-8")
    ok, why = is_deliverable(note, val)
    assert not ok and "changed" in why


def test_failed_note_gets_no_hash_and_cannot_be_delivered(tmp_path):
    bad = NOTE.replace(f"Reviews analysed: {len(REVIEWS)}", "Reviews analysed: 999")
    note = tmp_path / "pulse_note.md"
    note.write_text(bad, encoding="utf-8")
    val = tmp_path / "validation.json"
    record = write_validation(note, validate_note(bad, REVIEWS, THEMES), val)
    assert record["passed"] is False and record["note_sha256"] is None
    assert is_deliverable(note, val)[0] is False


def test_missing_validation_file_blocks_delivery(tmp_path):
    note = tmp_path / "pulse_note.md"
    note.write_text(NOTE, encoding="utf-8")
    assert is_deliverable(note, tmp_path / "validation.json")[0] is False


def test_cli_exit_codes(tmp_path):
    from pulse.validate.__main__ import main

    for name in ("reviews_clean.json", "themes.json"):
        shutil.copy(SAMPLES / name, tmp_path / name)
    (tmp_path / "pulse_note.md").write_text(NOTE, encoding="utf-8")
    assert main([str(tmp_path)]) == 0
    assert json.loads((tmp_path / "validation.json").read_text())["passed"] is True
    (tmp_path / "pulse_note.md").write_text(NOTE + " " + "x " * 300, encoding="utf-8")
    assert main([str(tmp_path)]) == 1
