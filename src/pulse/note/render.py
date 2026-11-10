"""B2.5: fill the problem-statement template from structured data.

Python owns the layout and every number. The model never writes a count,
a rating or a quote.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from pulse.schema import Review

from .model import NoteContent
from .quotes import Quote
from .ranker import RankedTheme

STORE_LABEL = {"app_store": "App Store", "play_store": "Play Store"}


@dataclass(frozen=True)
class NoteMeta:
    product: str
    week_of: dt.date
    window_start: dt.date
    window_end: dt.date
    n_reviews: int
    avg_rating: float


def make_meta(reviews: list[Review], product: str, week_of: dt.date) -> NoteMeta:
    dates = [r.date for r in reviews]
    return NoteMeta(
        product=product,
        week_of=week_of,
        window_start=min(dates),
        window_end=max(dates),
        n_reviews=len(reviews),
        avg_rating=round(sum(r.rating for r in reviews) / len(reviews), 1),
    )


def render_note(
    meta: NoteMeta,
    ranked: list[RankedTheme],
    quotes_by_id: dict[str, Quote],
    content: NoteContent,
) -> str:
    lines = [
        f"Subject: {meta.product} Weekly Review Pulse | Week of {meta.week_of:%d %b %Y}",
        "",
        f"Window: {meta.window_start:%d %b} – {meta.window_end:%d %b %Y} · "
        f"Reviews analysed: {meta.n_reviews} · Avg rating: {meta.avg_rating:.1f}",
        "",
        "TOP THEMES",
    ]
    for i, (r, line) in enumerate(zip(ranked, content.themes), 1):
        lines.append(f"{i}. {r.theme}: {line.summary} ({r.count} reviews, avg {r.avg_rating:.1f}★)")
    lines += ["", "WHAT USERS SAY"]
    for qid in content.quote_ids:
        q = quotes_by_id[qid]
        lines.append(f'• "{q.text}" ({q.rating}★, {STORE_LABEL[q.store]})')
    lines += ["", "ACTION IDEAS"]
    for i, a in enumerate(content.actions, 1):
        lines.append(f"{i}. {a.action}")
    return "\n".join(lines) + "\n"


def word_count(note: str) -> int:
    return len(note.split())
