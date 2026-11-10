"""B2.1: rank themes by impact. Plain volume would put praise first."""

from __future__ import annotations

from dataclasses import dataclass

from pulse.schema import OTHER, Theme

TOP_N = 3


@dataclass(frozen=True)
class RankedTheme:
    theme: str
    count: int
    avg_rating: float
    impact: float


def impact(theme: Theme) -> float:
    return theme.count * (5 - theme.avg_rating)


def rank_themes(themes: list[Theme], top_n: int = TOP_N) -> list[RankedTheme]:
    """Top `top_n` themes by impact. `other` is never ranked (C2).

    Ties break on higher count, then on name, so the order is stable.
    """
    candidates = [t for t in themes if t.theme != OTHER and t.count > 0]
    candidates.sort(key=lambda t: (-impact(t), -t.count, t.theme))
    return [
        RankedTheme(t.theme, t.count, t.avg_rating, round(impact(t), 2))
        for t in candidates[:top_n]
    ]
