"""Theme grouping logic (A3.1 to A3.4).

Groups reviews into <= 5 themes using the tool-free LLM interface.
Validates no PII is present before sending to LLM (P3-A9).
Computes count and avg_rating in Python (P3-A3).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Protocol

from pulse.llm.base import LLMError
from pulse.llm.batch import ResultCache, run_batched
from pulse.pii import find_pii
from pulse.schema import OTHER, Review, Theme, check_dataset, compute_themes

from .prompts import DEFAULT_THEMES, build_prompt, build_theme_schema

logger = logging.getLogger(__name__)


class PIIInLLMRequestError(Exception):
    """Raised when unscrubbed PII is detected prior to an LLM call (eval P3-A9)."""
    pass


class _LLM(Protocol):
    def complete(self, prompt: str, schema: dict) -> dict[str, Any]: ...


def group_reviews(
    llm: _LLM,
    reviews_data: list[dict[str, Any]],
    themes: list[str] = DEFAULT_THEMES,
    *,
    batch_size: int = 50,
    cache_dir: Path | str | None = None,
    task_name: str = "theme-grouping-v1",
) -> tuple[list[Review], list[Theme]]:
    """Assign every review to a theme and compute summary themes.

    Returns (validated Review objects, Theme summary objects).
    """
    if len(themes) > 5:
        raise ValueError(f"At most 5 themes allowed (C2), got {len(themes)}")
    if OTHER not in themes:
        raise ValueError(f"'{OTHER}' theme must be present in themes list")

    # Step 1: Pre-flight PII check (P3-A9: No PII sent to LLM provider)
    for i, r in enumerate(reviews_data):
        pii = find_pii(r.get("text", "")) + find_pii(r.get("title", ""))
        if pii:
            raise PIIInLLMRequestError(
                f"Review {i} contains unscrubbed PII ('{pii[0].text}'). "
                f"Run PII scrubber before theme grouping."
            )

    # Step 2: Prepare indexed items for batching
    items = []
    for i, r in enumerate(reviews_data):
        item = dict(r)
        item["id"] = f"r{i}"
        items.append(item)

    schema = build_theme_schema(themes)
    cache = ResultCache(cache_dir) if cache_dir else None

    def make_prompt_fn(batch):
        return build_prompt(batch, themes)

    def extract_fn(resp_data, batch):
        out = {}
        for item in resp_data.get("labels", []):
            out[item["id"]] = item["theme"]
        return out

    # Step 3: Run batched classification
    theme_assignments = run_batched(
        llm=llm,  # type: ignore[arg-type]
        task=task_name,
        items=items,
        item_id=lambda x: x["id"],
        make_prompt=make_prompt_fn,
        schema=schema,
        extract=extract_fn,
        cache=cache,
        batch_size=batch_size,
    )

    # Step 4: Construct Review objects with validated themes (P3-A2)
    reviewed_rows: list[Review] = []
    for item in items:
        assigned_theme = theme_assignments.get(item["id"], OTHER)
        if assigned_theme not in themes:
            assigned_theme = OTHER

        reviewed_rows.append(
            Review(
                store=item["store"],
                rating=int(item["rating"]),
                title=item.get("title", ""),
                text=item["text"],
                date=item["date"],
                theme=assigned_theme,
                redacted=bool(item.get("redacted", False)),
            )
        )

    # Step 5: Compute themes in Python (P3-A3)
    computed_themes = compute_themes(reviewed_rows)
    if not any(t.theme == OTHER for t in computed_themes):
        computed_themes.append(Theme(theme=OTHER, count=0, avg_rating=0.0))

    # Step 6: Verify shared contract (P3-A7)
    problems = check_dataset(reviewed_rows, computed_themes)
    if problems:
        raise LLMError(f"Dataset contract validation failed: {'; '.join(problems)}")

    return reviewed_rows, computed_themes
