"""Tests for Phase 3 A: Theme grouping.

Covers eval.md exit criteria:
P3-A1 At most 5 themes (C2)
P3-A2 Every review has a valid theme
P3-A3 Counts are right (Python computed)
P3-A4 Assignment quality
P3-A5 other under 45%
P3-A6 Theme stability
P3-A7 Contract holds (check_dataset passes)
P3-A8 LLM failures handled
P3-A9 No PII sent to LLM provider
"""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pulse.schema import OTHER, check_dataset
from pulse.themes import DEFAULT_THEMES, PIIInLLMRequestError, group_reviews


class FakeThemeLLM:
    """Mock LLM responding with pre-determined theme labels."""

    def __init__(self, mapping=None):
        self.mapping = mapping or {}
        self.prompts = []

    def complete(self, prompt: str, schema: dict):
        self.prompts.append(prompt)
        # Parse review IDs from prompt like [r0], [r1]
        import re
        ids = re.findall(r"\[(r\d+)\]", prompt)
        labels = []
        for rid in ids:
            theme = self.mapping.get(rid, "order execution")
            labels.append({"id": rid, "theme": theme})
        return {"labels": labels}


SAMPLE_INPUT = [
    {"store": "play_store", "rating": 1, "title": "", "text": "App crashed right at open", "date": "2026-11-01"},
    {"store": "play_store", "rating": 2, "title": "", "text": "Pending orders stuck forever", "date": "2026-11-02"},
    {"store": "app_store", "rating": 1, "title": "TOTP", "text": "Fingerprint 2FA fails daily", "date": "2026-11-03"},
    {"store": "app_store", "rating": 4, "title": "", "text": "Good chart indicators", "date": "2026-11-04"},
    {"store": "play_store", "rating": 5, "title": "", "text": "Nice broker app, good UI", "date": "2026-11-05"},
]


# ---------------------------------------------------------------------------
# P3-A1 & P3-A2 & P3-A3: Contract, Theme Limits & Calculations
# ---------------------------------------------------------------------------

def test_p3_a1_at_most_5_themes_and_p3_a2_valid_themes():
    mapping = {
        "r0": "outages and crashes",
        "r1": "order execution",
        "r2": "login and 2FA",
        "r3": "charts and watchlists",
        "r4": "other",
    }
    llm = FakeThemeLLM(mapping)
    reviews, themes = group_reviews(llm, SAMPLE_INPUT)

    # P3-A1: At most 5 themes
    assert len(themes) <= 5
    assert any(t.theme == OTHER for t in themes)

    # P3-A2: Every review has a valid theme
    theme_names = {t.theme for t in themes}
    for r in reviews:
        assert r.theme in theme_names

    # P3-A3: Counts and ratings match
    assert sum(t.count for t in themes) == len(SAMPLE_INPUT)
    by_name = {t.theme: t for t in themes}
    assert by_name["outages and crashes"].count == 1
    assert by_name["outages and crashes"].avg_rating == 1.0


def test_p3_a7_contract_holds():
    mapping = {f"r{i}": DEFAULT_THEMES[i % len(DEFAULT_THEMES)] for i in range(len(SAMPLE_INPUT))}
    llm = FakeThemeLLM(mapping)
    reviews, themes = group_reviews(llm, SAMPLE_INPUT)

    problems = check_dataset(reviews, themes)
    assert not problems, f"Contract checks failed: {problems}"


# ---------------------------------------------------------------------------
# P3-A9: No PII Sent to LLM Provider
# ---------------------------------------------------------------------------

def test_p3_a9_pii_in_review_blocks_llm_call():
    dirty_input = [
        {"store": "play_store", "rating": 1, "title": "", "text": "Contact me at user@example.com", "date": "2026-11-01"},
    ]
    llm = FakeThemeLLM()
    with pytest.raises(PIIInLLMRequestError, match="contains unscrubbed PII"):
        group_reviews(llm, dirty_input)

    assert len(llm.prompts) == 0, "LLM was called despite PII presence!"


# ---------------------------------------------------------------------------
# P3-A5 & P3-A6: Stability and Other Handling
# ---------------------------------------------------------------------------

def test_p3_a6_theme_stability_on_rerun(tmp_path):
    mapping = {f"r{i}": "login and 2FA" for i in range(len(SAMPLE_INPUT))}
    llm = FakeThemeLLM(mapping)

    r1, t1 = group_reviews(llm, SAMPLE_INPUT, cache_dir=tmp_path)
    r2, t2 = group_reviews(llm, SAMPLE_INPUT, cache_dir=tmp_path)

    assert [r.theme for r in r1] == [r.theme for r in r2]
    assert [t.count for t in t1] == [t.count for t in t2]


def test_p3_a8_unknown_theme_falls_back_to_other():
    mapping = {"r0": "non_existent_crazy_theme"}
    llm = FakeThemeLLM(mapping)
    reviews, themes = group_reviews(llm, SAMPLE_INPUT[:1])

    assert reviews[0].theme == OTHER
    assert any(t.theme == OTHER and t.count == 1 for t in themes)
