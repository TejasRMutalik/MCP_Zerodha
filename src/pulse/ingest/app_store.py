"""App Store customer reviews RSS feed adapter (A1.1).

Uses public Apple customer reviews RSS feeds (pages 1 to 10).
Copies only rating, title, text, and date (D-008). Never collects or stores
author, reviewer ID, version, or link (C4).
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

import httpx

from .models import IngestedReview

logger = logging.getLogger(__name__)

APPLE_RSS_URL = (
    "https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
)


class IngestError(Exception):
    """Raised when review ingestion fails critically."""
    pass


def parse_app_store_entry(entry: dict[str, Any]) -> IngestedReview | None:
    """Parse one entry from Apple's customer reviews JSON feed.

    Returns None if entry is the application header or malformed.
    """
    if "im:rating" not in entry or "content" not in entry:
        return None

    try:
        rating = int(entry["im:rating"]["label"])
        title = entry.get("title", {}).get("label", "").strip()
        text = entry["content"]["label"].strip()
        if not text:
            return None

        updated_str = entry["updated"]["label"]
        review_date = dt.datetime.fromisoformat(updated_str).date()

        return IngestedReview(
            store="app_store",
            rating=rating,
            title=title,
            text=text,
            date=review_date,
        )
    except (KeyError, ValueError, TypeError) as exc:
        logger.debug("Skipping unparseable App Store entry: %s", exc)
        return None


def fetch_app_store_reviews(
    app_id: str,
    country: str = "in",
    window_start: dt.date | None = None,
    max_pages: int = 10,
    client: httpx.Client | None = None,
) -> list[IngestedReview]:
    """Fetch reviews from Apple customer reviews RSS feed for up to max_pages.

    Stops once reviews fall past window_start or if a page returns 400 (end of feed).
    """
    reviews: list[IngestedReview] = []
    own_client = client is None
    http = client or httpx.Client(timeout=15.0)

    try:
        for page in range(1, max_pages + 1):
            url = APPLE_RSS_URL.format(country=country, page=page, app_id=app_id)
            try:
                resp = http.get(url)
            except httpx.RequestError as exc:
                if page == 1:
                    raise IngestError(f"Failed to fetch App Store page 1: {exc}") from exc
                logger.warning("Network error on App Store page %d: %s. Stopping fetch.", page, exc)
                break

            if resp.status_code == 400:
                # Apple returns 400 when page index exceeds available feed (e.g. >10 pages)
                break
            if resp.status_code != 200:
                if page == 1:
                    raise IngestError(f"App Store returned HTTP {resp.status_code} on page 1")
                break

            try:
                data = resp.json()
            except Exception as exc:
                if page == 1:
                    raise IngestError(f"Invalid JSON from App Store page 1: {exc}") from exc
                break

            entries = data.get("feed", {}).get("entry", [])
            if not entries:
                break
            if isinstance(entries, dict):
                entries = [entries]

            past_window = False
            page_review_count = 0
            for entry in entries:
                parsed = parse_app_store_entry(entry)
                if parsed is None:
                    continue
                page_review_count += 1
                if window_start and parsed.date < window_start:
                    past_window = True
                    break
                reviews.append(parsed)

            if past_window or page_review_count == 0:
                break
    finally:
        if own_client:
            http.close()

    return reviews
