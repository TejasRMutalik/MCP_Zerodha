import datetime as dt
from pathlib import Path

import pytest
from pydantic import ValidationError

from pulse.schema import (
    MAX_THEMES,
    Review,
    Theme,
    check_dataset,
    compute_themes,
    load_reviews,
    load_themes,
)

SAMPLES = Path(__file__).resolve().parents[1] / "contracts" / "samples"


def review(**over):
    base = dict(store="play_store", rating=3, title="", text="ok", date="2026-10-01", theme="other")
    base.update(over)
    return Review(**base)


def test_sample_files_are_valid_and_consistent():
    reviews = load_reviews(SAMPLES / "reviews_clean.json")
    themes = load_themes(SAMPLES / "themes.json")
    assert len(reviews) == 30
    assert check_dataset(reviews, themes) == []


def test_sample_covers_the_hard_cases():
    reviews = load_reviews(SAMPLES / "reviews_clean.json")
    assert any(r.redacted for r in reviews)
    assert any(r.title == "" for r in reviews)
    assert any(len(r.text.split()) <= 3 for r in reviews)
    assert {r.store for r in reviews} == {"app_store", "play_store"}


def test_identifying_fields_are_rejected():
    with pytest.raises(ValidationError):
        Review(store="play_store", rating=3, text="x", date="2026-10-01", theme="other", author="someone")


@pytest.mark.parametrize("rating", [0, 6])
def test_rating_out_of_range_is_rejected(rating):
    with pytest.raises(ValidationError):
        review(rating=rating)


def test_unknown_store_is_rejected():
    with pytest.raises(ValidationError):
        review(store="web")


def test_count_mismatch_is_flagged():
    reviews = [review(), review()]
    themes = [Theme(theme="other", count=3, avg_rating=3.0)]
    assert any("count is 3" in p for p in check_dataset(reviews, themes))


def test_average_mismatch_is_flagged():
    reviews = [review(rating=1), review(rating=2)]
    themes = [Theme(theme="other", count=2, avg_rating=4.0)]
    assert any("avg_rating" in p for p in check_dataset(reviews, themes))


def test_more_than_five_themes_is_flagged():
    names = ["a", "b", "c", "d", "e", "other"]
    reviews = [review(theme=n) for n in names]
    themes = compute_themes(reviews)
    assert len(themes) == MAX_THEMES + 1
    assert any("limit" in p for p in check_dataset(reviews, themes))


def test_missing_other_theme_is_flagged():
    reviews = [review(theme="a")]
    assert any("'other'" in p for p in check_dataset(reviews, compute_themes(reviews)))


def test_unknown_theme_on_a_review_is_flagged():
    themes = [Theme(theme="other", count=0, avg_rating=0)]
    assert any("not in themes.json" in p for p in check_dataset([review(theme="zzz")], themes))


def test_dates_outside_the_window_are_flagged():
    reviews = [review(date="2026-01-01")]
    problems = check_dataset(
        reviews,
        compute_themes(reviews),
        window_start=dt.date(2026, 8, 14),
        window_end=dt.date(2026, 11, 6),
    )
    assert any("before the window" in p for p in problems)


def test_compute_themes_puts_other_last_and_rounds():
    reviews = [review(theme="a", rating=1), review(theme="a", rating=2), review(theme="other", rating=5)] * 2
    themes = compute_themes(reviews)
    assert [t.theme for t in themes] == ["a", "other"]
    assert themes[0].avg_rating == 1.5
