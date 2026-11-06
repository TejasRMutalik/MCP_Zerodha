"""Write the FAKE sample files in contracts/samples/.

Every review here is invented for testing. None comes from a real person.
Run:  uv run python scripts/make_samples.py
"""

from __future__ import annotations

import json
from pathlib import Path

from pulse.schema import Review, check_dataset, compute_themes

OUT = Path(__file__).resolve().parents[1] / "contracts" / "samples"

ORDER, OUTAGE, LOGIN, CHARTS, OTHER = (
    "order execution",
    "outages and crashes",
    "login and 2FA",
    "charts and watchlists",
    "other",
)

# (store, rating, title, text, date, theme, redacted)
ROWS = [
    ("play_store", 1, "", "Orders get stuck on pending for minutes during market open. Lost a good entry because of it.", "2026-10-14", ORDER, False),
    ("play_store", 2, "", "Stop loss order rejected without any clear reason shown.", "2026-10-02", ORDER, False),
    ("app_store", 2, "Slow order placement", "Order confirmation takes too long on volatile days.", "2026-09-19", ORDER, False),
    ("play_store", 3, "", "Basket orders are useful but the margin calculation looks off sometimes.", "2026-09-27", ORDER, False),
    ("play_store", 1, "", "Modified my order and it executed at the old price. Very frustrating.", "2026-10-21", ORDER, False),
    ("app_store", 4, "Fast and reliable", "Order execution is quick. Works fine for intraday.", "2026-10-30", ORDER, False),
    ("play_store", 1, "", "Order rejected again at 9:15. Nothing works when it matters most.", "2026-11-03", ORDER, False),
    ("play_store", 1, "", "App crashes right at market open every single day this week.", "2026-10-09", OUTAGE, False),
    ("play_store", 1, "", "Kite is down again. Cannot see my positions at all.", "2026-10-28", OUTAGE, False),
    ("app_store", 1, "Down during volatility", "Whenever the market moves a lot the app just freezes.", "2026-09-05", OUTAGE, False),
    ("play_store", 2, "", "Keeps hanging on the positions screen and I have to restart it.", "2026-09-14", OUTAGE, False),
    ("play_store", 2, "", "Everything goes blank for a few minutes randomly, then comes back.", "2026-10-17", OUTAGE, False),
    ("app_store", 2, "Crashes after update", "The latest update crashes on my phone as soon as I open it.", "2026-11-01", OUTAGE, False),
    ("play_store", 3, "", "Mostly works but gets laggy when the market is busy.", "2026-08-28", OUTAGE, False),
    ("play_store", 1, "", "TOTP keeps failing even though the time on my phone is correct.", "2026-10-12", LOGIN, False),
    ("play_store", 2, "", "Logged out every morning and I need to do the whole login again.", "2026-09-22", LOGIN, False),
    ("app_store", 2, "Login issues", "Face unlock does not work, always asks for the PIN and the code.", "2026-10-06", LOGIN, False),
    ("play_store", 1, "", "Cannot login since morning, it says invalid password but it is correct.", "2026-10-25", LOGIN, False),
    ("play_store", 3, "", "Login is secure but too many steps every day.", "2026-09-09", LOGIN, False),
    ("play_store", 1, "", "Mera account login nahi ho raha, otp aa raha hai par error aata hai.", "2026-10-31", LOGIN, False),
    ("app_store", 4, "Great charts", "Chart tools are good, would love more indicators on mobile.", "2026-09-30", CHARTS, False),
    ("play_store", 3, "", "Watchlist sorting resets every time I reopen the app.", "2026-10-08", CHARTS, False),
    ("play_store", 2, "", "Cannot draw trendlines properly on the small screen, the line keeps moving.", "2026-08-31", CHARTS, False),
    ("play_store", 4, "", "Clean interface. Charts load quickly.", "2026-11-02", CHARTS, False),
    ("play_store", 5, "", "Good app", "2026-10-10", OTHER, False),
    ("play_store", 5, "", "Best platform for investing", "2026-09-03", OTHER, False),
    ("play_store", 5, "", "Nice", "2026-09-18", OTHER, False),
    ("app_store", 5, "Simple and clean", "Easy to use and no unnecessary clutter, perfect for beginners.", "2026-10-15", OTHER, False),
    ("play_store", 1, "", "Worst app ever", "2026-10-01", OTHER, False),
    ("play_store", 2, "", "Support asked me to email my details to [redacted] and nobody replied for days.", "2026-10-23", OTHER, True),
]


def main() -> None:
    reviews = [
        Review(store=s, rating=r, title=ti, text=tx, date=d, theme=th, redacted=red)
        for (s, r, ti, tx, d, th, red) in ROWS
    ]
    themes = compute_themes(reviews)
    problems = check_dataset(reviews, themes)
    if problems:
        raise SystemExit("sample data is inconsistent:\n" + "\n".join(problems))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reviews_clean.json").write_text(
        json.dumps([r.model_dump(mode="json") for r in reviews], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (OUT / "themes.json").write_text(
        json.dumps([t.model_dump(mode="json") for t in themes], indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(reviews)} reviews and {len(themes)} themes to {OUT}")
    for t in themes:
        print(f"  {t.theme}: {t.count} reviews, avg {t.avg_rating}")


if __name__ == "__main__":
    main()
