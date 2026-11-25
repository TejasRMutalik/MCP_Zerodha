"""Google Play Store reviews adapter (A1.2).

Uses google-play-scraper without authentication (C1, D-006).
Copies only rating (score), text (content), and date (at) (D-008). Title is empty.
Identifying fields (reviewId, userName, userImage, replyContent) are never collected.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Callable

from .app_store import IngestError
from .models import IngestedReview

logger = logging.getLogger(__name__)


def parse_play_store_item(item: dict[str, Any]) -> IngestedReview | None:
    """Parse one raw dictionary from google-play-scraper."""
    try:
        content = (item.get("content") or "").strip()
        if not content:
            return None

        score = int(item["score"])
        at_val = item["at"]
        if isinstance(at_val, dt.datetime):
            review_date = at_val.date()
        elif isinstance(at_val, dt.date):
            review_date = at_val
        elif isinstance(at_val, str):
            review_date = dt.date.fromisoformat(at_val[:10])
        else:
            return None

        return IngestedReview(
            store="play_store",
            rating=score,
            title="",
            text=content,
            date=review_date,
        )
    except (KeyError, ValueError, TypeError) as exc:
        logger.debug("Skipping unparseable Play Store item: %s", exc)
        return None


def fetch_play_store_reviews(
    app_id: str,
    country: str = "in",
    language: str = "en",
    window_start: dt.date | None = None,
    batch_size: int = 200,
    max_reviews: int = 4000,
    scraper_fn: Callable[..., tuple[list[dict], Any]] | None = None,
) -> list[IngestedReview]:
    """Fetch reviews from Google Play Store using google-play-scraper.

    Paginates newest-first reviews and stops when reviews are older than window_start.
    """
    if scraper_fn is None:
        try:
            from google_play_scraper import Sort, reviews
            scraper_fn = reviews
            sort_order = Sort.NEWEST
        except ImportError as exc:
            raise IngestError("google-play-scraper is not installed") from exc
    else:
        sort_order = None

    results: list[IngestedReview] = []
    continuation_token = None
    fetched_total = 0

    while fetched_total < max_reviews:
        count_to_fetch = min(batch_size, max_reviews - fetched_total)
        try:
            kwargs: dict[str, Any] = {
                "lang": language,
                "country": country,
                "count": count_to_fetch,
            }
            if sort_order is not None:
                kwargs["sort"] = sort_order
            if continuation_token is not None:
                kwargs["continuation_token"] = continuation_token

            batch, continuation_token = scraper_fn(app_id, **kwargs)
        except Exception as exc:
            if not results:
                raise IngestError(f"Failed to fetch Play Store reviews: {exc}") from exc
            logger.warning("Error fetching Play Store batch: %s. Stopping fetch.", exc)
            break

        if not batch:
            break

        fetched_total += len(batch)
        past_window = False

        for raw_item in batch:
            parsed = parse_play_store_item(raw_item)
            if parsed is None:
                continue
            if window_start and parsed.date < window_start:
                past_window = True
                break
            results.append(parsed)

        if past_window or not continuation_token:
            break

    return results
