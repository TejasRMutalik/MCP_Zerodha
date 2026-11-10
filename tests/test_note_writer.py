import datetime as dt
from pathlib import Path

import pytest

from pulse.note.model import NOTE_SCHEMA
from pulse.note.quotes import eligible_quotes
from pulse.note.ranker import rank_themes
from pulse.note.render import make_meta, word_count
from pulse.note.writer import NAME_SCHEMA, NoteError, check_content, write_note
from pulse.schema import load_reviews, load_themes

SAMPLES = Path(__file__).resolve().parents[1] / "contracts" / "samples"
REVIEWS = load_reviews(SAMPLES / "reviews_clean.json")
THEMES = load_themes(SAMPLES / "themes.json")
META = make_meta(REVIEWS, "Zerodha Kite", dt.date(2026, 11, 2))
RANKED = rank_themes(THEMES)
QUOTES = eligible_quotes(REVIEWS, {r.theme for r in RANKED})


def good_answer(quote_ids=None, summary="Users report problems here"):
    ids = quote_ids or [q.id for q in QUOTES[:3]]
    return {
        "themes": [{"theme": r.theme, "summary": summary} for r in RANKED],
        "quote_ids": ids,
        "actions": [{"theme": r.theme, "action": f"Investigate {r.theme} this week"} for r in RANKED],
    }


class FakeLLM:
    """Answers the name check with `names`, then the note with each queued answer."""

    def __init__(self, answers, names=()):
        self.answers = list(answers)
        self.names = list(names)
        self.prompts = []

    def complete(self, prompt, schema):
        self.prompts.append(prompt)
        if schema is NAME_SCHEMA:
            return {"with_names": self.names}
        assert schema is NOTE_SCHEMA
        return self.answers.pop(0)


def run(llm, **kw):
    return write_note(llm, META, REVIEWS, THEMES, **kw)


def test_enough_sample_quotes():
    assert len(QUOTES) >= 3


def test_p2_b4_quotes_are_verbatim_and_exact():
    note, content, _, by_id = run(FakeLLM([good_answer()]))
    for qid in content.quote_ids:
        assert f'"{REVIEWS[int(qid[1:])].text}"' in note


def test_p2_b5_note_follows_template_order():
    note, *_ = run(FakeLLM([good_answer()]))
    marks = ["Subject:", "Window:", "TOP THEMES", "WHAT USERS SAY", "ACTION IDEAS"]
    positions = [note.index(m) for m in marks]
    assert positions == sorted(positions)
    assert note.count("\n1. ") == 2 and note.count("\n3. ") == 2  # themes and actions
    assert note.count("• ") == 3


def test_p2_b6_note_is_within_word_limit():
    note, *_ = run(FakeLLM([good_answer()]))
    assert word_count(note) <= 250


def test_numbers_come_from_python_not_the_model():
    note, *_ = run(FakeLLM([good_answer()]))
    top = RANKED[0]
    assert f"({top.count} reviews, avg {top.avg_rating:.1f}★)" in note
    assert f"Reviews analysed: {len(REVIEWS)}" in note


def test_retry_after_invented_quote_id_then_success():
    bad = good_answer(quote_ids=["r999", QUOTES[0].id, QUOTES[1].id])
    llm = FakeLLM([bad, good_answer()])
    note, *_ = run(llm)
    assert note
    assert len([p for p in llm.prompts if "ELIGIBLE QUOTES" in p]) == 2


def test_stops_after_retries_are_used_up():
    bad = good_answer(quote_ids=["r999", "r998", "r997"])
    with pytest.raises(NoteError):
        run(FakeLLM([bad, bad, bad]))


def test_wrong_theme_order_is_rejected():
    answer = good_answer()
    answer["themes"].reverse()
    with pytest.raises(NoteError):
        run(FakeLLM([answer, answer, answer]))


def test_overlong_note_is_rejected():
    long = good_answer(summary=" ".join(["word"] * 120))
    with pytest.raises(NoteError, match="words"):
        run(FakeLLM([long, long, long]))


def test_quotes_with_names_never_reach_the_prompt():
    flagged = QUOTES[0].id
    llm = FakeLLM([good_answer(quote_ids=[q.id for q in QUOTES[1:4]])], names=[flagged])
    run(llm)
    note_prompt = [p for p in llm.prompts if "ELIGIBLE QUOTES" in p][0]
    assert QUOTES[0].text not in note_prompt


def test_too_few_quotes_after_name_check_stops_the_run():
    with pytest.raises(NoteError, match="eligible quotes"):
        run(FakeLLM([], names=[q.id for q in QUOTES]))


def test_prompt_marks_reviews_as_data():
    llm = FakeLLM([good_answer()])
    run(llm)
    assert "not instructions" in llm.prompts[-1]


def test_check_content_rejects_duplicate_quote_ids():
    from pulse.note.model import NoteContent

    answer = good_answer(quote_ids=[QUOTES[0].id] * 3)
    with pytest.raises(NoteError):
        check_content(NoteContent.model_validate(answer), RANKED, QUOTES)
