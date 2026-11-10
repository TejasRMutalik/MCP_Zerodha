import datetime as dt

from pulse.note.quotes import MAX_WORDS, MIN_WORDS, eligible_quotes, is_english
from pulse.note.ranker import rank_themes
from pulse.schema import Review, Theme


def theme(name, count, avg):
    return Theme(theme=name, count=count, avg_rating=avg)


def review(text, theme="a", rating=2, redacted=False):
    return Review(store="play_store", rating=rating, text=text, date=dt.date(2026, 10, 1),
                  theme=theme, redacted=redacted)


GOOD = "The app froze twice during market open today"  # 9 words


def test_p2_b1_ranking_matches_hand_worked_example():
    themes = [theme("a", 10, 4.0), theme("b", 6, 1.5), theme("c", 8, 2.0), theme("d", 4, 1.0)]
    # impacts: a=10, b=21, c=24, d=16
    assert [t.theme for t in rank_themes(themes)] == ["c", "b", "d"]
    assert rank_themes(themes)[0].impact == 24


def test_p2_b2_other_never_reaches_top_3():
    themes = [theme("other", 500, 1.0), theme("a", 3, 4.0), theme("b", 2, 4.0), theme("c", 1, 4.0)]
    assert "other" not in [t.theme for t in rank_themes(themes)]


def test_ties_are_stable():
    themes = [theme("b", 5, 3.0), theme("a", 5, 3.0)]
    assert [t.theme for t in rank_themes(themes)] == ["a", "b"]


def test_empty_themes_are_skipped():
    assert rank_themes([theme("a", 0, 0)]) == []


def test_p2_b3_ineligible_quotes_are_excluded():
    reviews = [
        review(GOOD),                                              # r0 ok
        review(GOOD, redacted=True),                               # r1 redacted
        review("Too short here", ),                                # r2 short
        review(" ".join(["word"] * (MAX_WORDS + 1))),              # r3 long
        review(GOOD, theme="z"),                                   # r4 wrong theme
        review("Call me on 9876543210 about this app issue now"),  # r5 phone
        review("Mail me at someone@example.com about this bug"),   # r6 email
        review("ऐप बहुत धीमा है और बार बार बंद हो जाता है"),          # r7 not English
    ]
    got = eligible_quotes(reviews, {"a"})
    assert [q.id for q in got] == ["r0"]


def test_word_limits_are_inclusive():
    six = review("one two three four five six")
    assert MIN_WORDS == 6
    assert [q.id for q in eligible_quotes([six], {"a"})] == ["r0"]
    twenty_five = review(" ".join(["w"] * MAX_WORDS))
    assert len(eligible_quotes([twenty_five], {"a"})) == 1


def test_name_check_excludes_quotes_with_names():
    reviews = [review(GOOD), review("Ask Rahul Sharma about the login problem here")]
    got = eligible_quotes(reviews, {"a"}, name_check=lambda t: "Rahul" in t)
    assert [q.id for q in got] == ["r0"]


def test_quote_text_is_the_source_text_unchanged():
    r = review(GOOD)
    assert eligible_quotes([r], {"a"})[0].text == r.text


def test_is_english():
    assert is_english("Orders stuck on pending")
    assert not is_english("ऐप बहुत धीमा है")
    assert not is_english("12345 !!!")
