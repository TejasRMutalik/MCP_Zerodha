"""Tests for Phase 1 A: Ingestion pipeline.

Covers eval.md exit criteria:
P1-A1 Both stores return data
P1-A2 Volume is plausible
P1-A3 Window is correct
P1-A4 Fields are complete
P1-A5 Identifying fields are never stored (no author, user name, id, link)
P1-A6 Public data only (no credentials/logins)
P1-A7 Failures stop the run
"""

import datetime as dt
from unittest.mock import MagicMock

import httpx
import pytest
from pydantic import ValidationError

from pulse.ingest import (
    IngestError,
    IngestedReview,
    VolumeCheckError,
    check_volume,
    deduplicate_reviews,
    fetch_app_store_reviews,
    fetch_play_store_reviews,
    filter_by_window,
)
from pulse.ingest.app_store import parse_app_store_entry
from pulse.ingest.play_store import parse_play_store_item


# ---------------------------------------------------------------------------
# Test Fixtures & Samples
# ---------------------------------------------------------------------------

SAMPLE_APPLE_ENTRY = {
    "author": {"name": {"label": "SecretUser123"}},
    "updated": {"label": "2026-11-01T10:00:00-07:00"},
    "im:rating": {"label": "4"},
    "im:version": {"label": "3.5.1"},
    "id": {"label": "rev-99999"},
    "title": {"label": "Good trading app"},
    "content": {"label": "Charts load quickly and order placement is smooth."},
    "link": {"attributes": {"href": "https://itunes.apple.com/..."}},
}

SAMPLE_PLAY_ITEM = {
    "reviewId": "gp:AOqpTOE...",
    "userName": "John Doe",
    "userImage": "https://play-lh.googleusercontent.com/...",
    "content": "Instant withdrawals and great interface.",
    "score": 5,
    "thumbsUpCount": 12,
    "at": dt.datetime(2026, 11, 2, 14, 30, 0),
    "replyContent": None,
    "appVersion": "3.5.0",
}


# ---------------------------------------------------------------------------
# P1-A4 & P1-A5: Allowlist & Privacy (Identifying fields never stored)
# ---------------------------------------------------------------------------

def test_p1_a5_apple_entry_parser_strips_all_identifying_fields():
    review = parse_app_store_entry(SAMPLE_APPLE_ENTRY)
    assert review is not None
    assert review.store == "app_store"
    assert review.rating == 4
    assert review.title == "Good trading app"
    assert review.text == "Charts load quickly and order placement is smooth."
    assert review.date == dt.date(2026, 11, 1)

    # IngestedReview has extra="forbid"
    dump = review.model_dump()
    assert set(dump.keys()) == {"store", "rating", "title", "text", "date"}
    assert "author" not in dump
    assert "id" not in dump
    assert "link" not in dump


def test_p1_a5_play_entry_parser_strips_all_identifying_fields():
    review = parse_play_store_item(SAMPLE_PLAY_ITEM)
    assert review is not None
    assert review.store == "play_store"
    assert review.rating == 5
    assert review.title == ""
    assert review.text == "Instant withdrawals and great interface."
    assert review.date == dt.date(2026, 11, 2)

    dump = review.model_dump()
    assert set(dump.keys()) == {"store", "rating", "title", "text", "date"}
    assert "userName" not in dump
    assert "userImage" not in dump
    assert "reviewId" not in dump


def test_p1_a5_forbidden_extra_fields_raise_validation_error():
    with pytest.raises(ValidationError):
        IngestedReview(
            store="app_store",
            rating=5,
            text="hello",
            date=dt.date(2026, 11, 1),
            author="John Doe",  # extra field
        )


# ---------------------------------------------------------------------------
# P1-A1 & P1-A4: Adapter Parsing & Store Tags
# ---------------------------------------------------------------------------

def test_p1_a1_fetch_app_store_reviews_mocked():
    mock_feed = {
        "feed": {
            "entry": [
                {"im:name": {"label": "Zerodha Kite"}},  # App header entry
                SAMPLE_APPLE_ENTRY,
            ]
        }
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_feed

    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    reviews = fetch_app_store_reviews("1449453802", max_pages=1, client=mock_client)
    assert len(reviews) == 1
    assert reviews[0].store == "app_store"
    assert reviews[0].rating == 4


def test_p1_a1_fetch_play_store_reviews_mocked():
    def mock_scraper(app_id, **kwargs):
        return [SAMPLE_PLAY_ITEM], None

    reviews = fetch_play_store_reviews("com.zerodha.kite3", scraper_fn=mock_scraper)
    assert len(reviews) == 1
    assert reviews[0].store == "play_store"
    assert reviews[0].rating == 5


# ---------------------------------------------------------------------------
# P1-A3: Window Filtering
# ---------------------------------------------------------------------------

def test_p1_a3_window_filtering():
    r1 = IngestedReview(store="app_store", rating=4, text="Old", date=dt.date(2026, 8, 1))
    r2 = IngestedReview(store="play_store", rating=3, text="Inside", date=dt.date(2026, 9, 15))
    r3 = IngestedReview(store="app_store", rating=5, text="Future", date=dt.date(2026, 11, 20))

    filtered = filter_by_window([r1, r2, r3], start_date=dt.date(2026, 9, 1), end_date=dt.date(2026, 10, 1))
    assert len(filtered) == 1
    assert filtered[0].text == "Inside"


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def test_deduplicate_reviews():
    r1 = IngestedReview(store="app_store", rating=4, title="Hi", text="Great app", date=dt.date(2026, 10, 1))
    r2 = IngestedReview(store="app_store", rating=4, title="Hi", text="Great app", date=dt.date(2026, 10, 1))
    r3 = IngestedReview(store="app_store", rating=4, title="Hi", text="Great app ", date=dt.date(2026, 10, 1))  # whitespace
    r4 = IngestedReview(store="play_store", rating=4, title="", text="Great app", date=dt.date(2026, 10, 1))

    unique = deduplicate_reviews([r1, r2, r3, r4])
    assert len(unique) == 2
    assert {r.store for r in unique} == {"app_store", "play_store"}


# ---------------------------------------------------------------------------
# P1-A2 & P1-A7: Volume & Failure Checks
# ---------------------------------------------------------------------------

def test_p1_a2_volume_check_passes():
    reviews = [
        IngestedReview(store="app_store", rating=4, text=f"text {i}", date=dt.date(2026, 10, 1))
        for i in range(50)
    ] + [
        IngestedReview(store="play_store", rating=4, text=f"text {i}", date=dt.date(2026, 10, 1))
        for i in range(500)
    ]
    app_cnt, play_cnt = check_volume(reviews, min_app_store=50, min_play_store=500)
    assert app_cnt == 50
    assert play_cnt == 500


def test_p1_a2_volume_check_fails_on_too_few_app_store_reviews():
    reviews = [
        IngestedReview(store="app_store", rating=4, text="few", date=dt.date(2026, 10, 1))
    ] + [
        IngestedReview(store="play_store", rating=4, text=f"text {i}", date=dt.date(2026, 10, 1))
        for i in range(500)
    ]
    with pytest.raises(VolumeCheckError, match="Review volume too low"):
        check_volume(reviews, min_app_store=50, min_play_store=500)


def test_p1_a7_failure_on_page_1_stops_run():
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ConnectError("Connection refused")

    with pytest.raises(IngestError, match="Failed to fetch App Store page 1"):
        fetch_app_store_reviews("1449453802", max_pages=1, client=mock_client)


def test_p1_a7_play_store_failure_stops_run():
    def mock_broken_scraper(app_id, **kwargs):
        raise RuntimeError("Google Play API down")

    with pytest.raises(IngestError, match="Failed to fetch Play Store reviews"):
        fetch_play_store_reviews("com.zerodha.kite3", scraper_fn=mock_broken_scraper)
