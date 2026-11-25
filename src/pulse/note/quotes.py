"""B2.2: which reviews may be quoted (architecture section 5).

A quote must be unredacted, in a Top 3 theme, 6 to 25 words, English, free of
PII and free of a person's name. Quotes are chosen by ID, never retyped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from pulse.schema import Review

MIN_WORDS = 6
MAX_WORDS = 25

from pulse.pii import find_pii


@dataclass(frozen=True)
class Quote:
    id: str  # "r<index>" into reviews_clean.json
    text: str
    rating: int
    store: str
    theme: str


def word_count(text: str) -> int:
    return len(text.split())


def is_english(text: str) -> bool:
    """Cheap check: almost every letter is a basic Latin letter.

    Catches Hindi, Kannada and other scripts. It cannot tell English from
    romanised Hindi; the LLM name check and the manual rubric cover that.
    """
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    ascii_letters = sum(1 for c in letters if c.isascii())
    return ascii_letters / len(letters) >= 0.95


def quote_id(index: int) -> str:
    return f"r{index}"


def eligible_quotes(
    reviews: list[Review],
    top_themes: set[str],
    name_check: Callable[[str], bool] | None = None,
) -> list[Quote]:
    """Reviews that pass every rule. `name_check(text)` returns True if the text
    contains a person's name (an LLM call, supplied by the note writer)."""
    result: list[Quote] = []
    for i, r in enumerate(reviews):
        if r.redacted or r.theme not in top_themes:
            continue
        if not MIN_WORDS <= word_count(r.text) <= MAX_WORDS:
            continue
        if not is_english(r.text) or find_pii(r.text):
            continue
        if name_check is not None and name_check(r.text):
            continue
        result.append(Quote(quote_id(i), r.text, r.rating, r.store, r.theme))
    return result
