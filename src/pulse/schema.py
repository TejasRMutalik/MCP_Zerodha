"""The contract between Half A (data) and Half B (note and delivery).

Two files: reviews_clean.json (a list of Review) and themes.json (a list of
Theme). Changing anything here needs both people to agree and a decision entry.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MAX_THEMES = 5
OTHER = "other"


class Review(BaseModel):
    # extra="forbid" means a stray author, user id or link field is rejected (C4).
    model_config = ConfigDict(extra="forbid")

    store: Literal["app_store", "play_store"]
    rating: int = Field(ge=1, le=5)
    title: str = ""
    text: str = Field(min_length=1)
    date: dt.date
    theme: str = Field(min_length=1)
    redacted: bool = False


class Theme(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: str = Field(min_length=1)
    count: int = Field(ge=0)
    avg_rating: float = Field(ge=0, le=5)  # 0 only when count is 0


def load_reviews(path: Path | str) -> list[Review]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Review.model_validate(item) for item in data]


def load_themes(path: Path | str) -> list[Theme]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Theme.model_validate(item) for item in data]


def compute_themes(reviews: list[Review]) -> list[Theme]:
    """Counts and average ratings from the rows. Never ask an LLM for these."""
    groups: dict[str, list[int]] = {}
    for r in reviews:
        groups.setdefault(r.theme, []).append(r.rating)
    themes = [
        Theme(theme=name, count=len(vals), avg_rating=round(sum(vals) / len(vals), 1))
        for name, vals in groups.items()
    ]
    # Biggest first, `other` always last.
    themes.sort(key=lambda t: (t.theme == OTHER, -t.count, t.theme))
    return themes


def check_dataset(
    reviews: list[Review],
    themes: list[Theme],
    *,
    window_start: dt.date | None = None,
    window_end: dt.date | None = None,
) -> list[str]:
    """Return a list of problems. An empty list means the pair is valid."""
    problems: list[str] = []

    if len(themes) > MAX_THEMES:
        problems.append(f"{len(themes)} themes; the limit is {MAX_THEMES} (C2)")

    names = [t.theme for t in themes]
    if len(set(names)) != len(names):
        problems.append("duplicate theme names in themes.json")
    if OTHER not in names:
        problems.append(f"themes.json has no '{OTHER}' theme")

    known = set(names)
    for i, r in enumerate(reviews):
        if r.theme not in known:
            problems.append(f"review {i}: theme '{r.theme}' is not in themes.json")
        if window_start and r.date < window_start:
            problems.append(f"review {i}: date {r.date} is before the window start")
        if window_end and r.date > window_end:
            problems.append(f"review {i}: date {r.date} is after the window end")

    for t in themes:
        ratings = [r.rating for r in reviews if r.theme == t.theme]
        if t.count != len(ratings):
            problems.append(f"theme '{t.theme}': count is {t.count} but {len(ratings)} reviews match")
            continue
        if ratings:
            expected = round(sum(ratings) / len(ratings), 1)
            if abs(t.avg_rating - expected) > 0.05:
                problems.append(f"theme '{t.theme}': avg_rating is {t.avg_rating} but rows give {expected}")
        elif t.avg_rating != 0:
            problems.append(f"theme '{t.theme}': has no reviews but avg_rating is {t.avg_rating}")

    return problems
