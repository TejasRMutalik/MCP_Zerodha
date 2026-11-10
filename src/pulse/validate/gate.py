"""The validation gate: decides whether a note may leave the machine.

It reads the finished note text and checks it against the two contract files,
independently of the writer, so a bug or a hostile review in the writer cannot
get past it. On a pass it records the SHA-256 of the note; delivery refuses to
run if the note on disk no longer matches (architecture section 5).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from pulse.note.quotes import find_pii
from pulse.note.ranker import rank_themes
from pulse.schema import Review, Theme

MAX_WORDS = 250
STORES = {"App Store": "app_store", "Play Store": "play_store"}

_THEME = re.compile(r"^(\d)\. (.+?): .* \((\d+) reviews, avg (\d\.\d)★\)$")
_QUOTE = re.compile(r'^• "(.+)" \((\d)★, (App Store|Play Store)\)$')
_ACTION = re.compile(r"^(\d)\. (.+)$")
_WINDOW = re.compile(r"Reviews analysed: (\d+) · Avg rating: (\d\.\d)")


@dataclass
class Check:
    id: str
    name: str
    ok: bool
    detail: str = ""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _norm(text: str) -> str:
    return " ".join(text.split())


def _sections(note: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"head": []}
    current = "head"
    for line in note.splitlines():
        if line in ("TOP THEMES", "WHAT USERS SAY", "ACTION IDEAS"):
            current = line
            out[current] = []
        elif line.strip():
            out[current].append(line)
    return out


def validate_note(note: str, reviews: list[Review], themes: list[Theme]) -> list[Check]:
    sec = _sections(note)
    theme_lines = sec.get("TOP THEMES", [])
    quote_lines = sec.get("WHAT USERS SAY", [])
    action_lines = sec.get("ACTION IDEAS", [])
    checks: list[Check] = []

    words = len(note.split())
    checks.append(Check("length", f"Whole note at most {MAX_WORDS} words", words <= MAX_WORDS, f"{words} words"))

    parsed_themes = [m for m in map(_THEME.match, theme_lines) if m]
    parsed_quotes = [m for m in map(_QUOTE.match, quote_lines) if m]
    parsed_actions = [m for m in map(_ACTION.match, action_lines) if m]
    shape_ok = (len(parsed_themes), len(parsed_quotes), len(parsed_actions)) == (3, 3, 3) and (
        len(theme_lines), len(quote_lines), len(action_lines)
    ) == (3, 3, 3)
    checks.append(Check(
        "shape", "Exactly 3 themes, 3 quotes, 3 action ideas", shape_ok,
        f"found {len(parsed_themes)}/{len(theme_lines)} themes, {len(parsed_quotes)}/{len(quote_lines)} quotes, "
        f"{len(parsed_actions)}/{len(action_lines)} actions",
    ))

    # Ranking: the 3 themes are the top 3 by impact, in order.
    expected = [r.theme for r in rank_themes(themes)]
    shown = [m.group(2) for m in parsed_themes]
    checks.append(Check("ranking", "Themes are the top 3 by impact, in order", shown == expected,
                        f"shown {shown}, expected {expected}"))

    # Numbers: every count and rating matches the data.
    by_name = {t.theme: t for t in themes}
    problems = []
    for m in parsed_themes:
        t = by_name.get(m.group(2))
        if t is None:
            problems.append(f"unknown theme '{m.group(2)}'")
        elif int(m.group(3)) != t.count or abs(float(m.group(4)) - t.avg_rating) > 0.05:
            problems.append(f"{t.theme}: note says {m.group(3)} / {m.group(4)}, data says {t.count} / {t.avg_rating}")
    head = _WINDOW.search(" ".join(sec["head"]))
    if reviews:
        true_avg = round(sum(r.rating for r in reviews) / len(reviews), 1)
        if not head:
            problems.append("window line is missing")
        elif int(head.group(1)) != len(reviews) or abs(float(head.group(2)) - true_avg) > 0.05:
            problems.append(f"window line says {head.group(1)} / {head.group(2)}, data says {len(reviews)} / {true_avg}")
    checks.append(Check("numbers", "Counts and ratings match the data", not problems, "; ".join(problems)))

    # Verbatim and attribution: each quote is a real review's text, with its rating and store.
    top3 = set(expected)
    problems = []
    for m in parsed_quotes:
        text, rating, store = _norm(m.group(1)), int(m.group(2)), STORES[m.group(3)]
        sources = [r for r in reviews if text in _norm(r.text)]
        if not sources:
            problems.append(f"not verbatim: {text[:40]}…")
        elif not any(r.rating == rating and r.store == store for r in sources):
            problems.append(f"rating or store does not match the source: {text[:40]}…")
        elif not any(r.theme in top3 and r.rating == rating and r.store == store for r in sources):
            problems.append(f"quote is not from a top 3 theme: {text[:40]}…")
    checks.append(Check("verbatim", "Quotes are exact, with the right rating and store", not problems and shape_ok,
                        "; ".join(problems)))

    pii = find_pii(note)
    checks.append(Check("pii", "No PII in the note", not pii, f"{len(pii)} match(es)" if pii else ""))
    return checks


def passed(checks: list[Check]) -> bool:
    return all(c.ok for c in checks)


def write_validation(note_path: Path, checks: list[Check], out_path: Path) -> dict:
    note = note_path.read_text(encoding="utf-8")
    record = {
        "passed": passed(checks),
        # No hash is recorded for a failed note, so a failure can never unlock delivery.
        "note_sha256": sha256_text(note) if passed(checks) else None,
        "validated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "checks": [asdict(c) for c in checks],
    }
    out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def is_deliverable(note_path: Path, validation_path: Path) -> tuple[bool, str]:
    """Delivery calls this first. True only if validation passed for exactly this note."""
    try:
        record = json.loads(validation_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False, "validation.json is missing or unreadable"
    if record.get("passed") is not True or not record.get("note_sha256"):
        return False, "the note did not pass validation"
    if sha256_text(note_path.read_text(encoding="utf-8")) != record["note_sha256"]:
        return False, "the note changed after validation"
    return True, "ok"
