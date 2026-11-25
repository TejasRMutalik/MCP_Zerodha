"""PII scrubbing functionality (A2.2).

Replaces detected PII spans with '[redacted]' and sets redacted=True.
"""

from __future__ import annotations

from typing import Any

from .detector import find_pii
from .models import PIIMatch

REDACTED_LABEL = "[redacted]"


def scrub_text(text: str) -> tuple[str, bool, list[PIIMatch]]:
    """Replace all PII in text with '[redacted]'.

    Returns (scrubbed_text, was_redacted, matches).
    """
    matches = find_pii(text)
    if not matches:
        return text, False, []

    # Rebuild string right-to-left so slice offsets remain valid
    chars = list(text)
    for m in reversed(matches):
        chars[m.start:m.end] = list(REDACTED_LABEL)

    scrubbed = "".join(chars)
    return scrubbed, True, matches


def scrub_review(review_dict: dict[str, Any]) -> dict[str, Any]:
    """Scrub text and title fields of a review dictionary.

    Sets 'redacted': True if any PII was replaced, otherwise retains existing or False.
    """
    row = dict(review_dict)

    text_scrubbed, text_redacted, _ = scrub_text(row.get("text", ""))
    row["text"] = text_scrubbed

    title = row.get("title", "")
    title_redacted = False
    if title:
        title_scrubbed, title_redacted, _ = scrub_text(title)
        row["title"] = title_scrubbed

    row["redacted"] = bool(row.get("redacted", False) or text_redacted or title_redacted)
    return row


def scrub_reviews(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Scrub a list of review dictionaries."""
    return [scrub_review(r) for r in reviews]
