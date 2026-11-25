"""Normalisation, deduplication, and volume validation (A1.4, A1.5)."""

from __future__ import annotations

import datetime as dt

from .models import IngestedReview


class VolumeCheckError(Exception):
    """Raised when review volume from either store falls below plausible threshold (P1-A2)."""
    pass


def deduplicate_reviews(reviews: list[IngestedReview]) -> list[IngestedReview]:
    """Remove exact duplicate reviews based on store, rating, title, normalised text, and date."""
    seen: set[tuple[str, int, str, str, dt.date]] = set()
    unique: list[IngestedReview] = []

    for r in reviews:
        norm_text = " ".join(r.text.split())
        key = (r.store, r.rating, r.title.strip(), norm_text, r.date)
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique


def filter_by_window(
    reviews: list[IngestedReview],
    start_date: dt.date,
    end_date: dt.date,
) -> list[IngestedReview]:
    """Keep reviews strictly within [start_date, end_date]."""
    return [r for r in reviews if start_date <= r.date <= end_date]


def check_volume(
    reviews: list[IngestedReview],
    min_app_store: int = 50,
    min_play_store: int = 500,
) -> tuple[int, int]:
    """Verify minimum review volume for both stores (eval P1-A2).

    Baseline measured on Zerodha Kite over 12 weeks: ~122 App Store, ~1403 Play Store.
    Raises VolumeCheckError if either count is below minimum.
    """
    app_count = sum(1 for r in reviews if r.store == "app_store")
    play_count = sum(1 for r in reviews if r.store == "play_store")

    if app_count < min_app_store or play_count < min_play_store:
        raise VolumeCheckError(
            f"Review volume too low: App Store has {app_count} (min {min_app_store}), "
            f"Play Store has {play_count} (min {min_play_store}). Run stopped."
        )

    return app_count, play_count
