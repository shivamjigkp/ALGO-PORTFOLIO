"""
Confirmed swing pivot detection — the Python equivalent of Pine Script's
ta.pivothigh() / ta.pivotlow().

A pivot at index i is only "confirmed" once `lookback` bars exist on BOTH
sides of it. This means the most recent `lookback` bars can never produce a
newly confirmed pivot yet — which is exactly what gives the strategy its
no-repaint guarantee (see docs/strategy-guide.md, Part 11).
"""

from dataclasses import dataclass
from typing import Literal

from app.models.schemas import Candle

PivotType = Literal["high", "low"]


@dataclass(frozen=True)
class Pivot:
    index: int
    type: PivotType
    price: float


def find_confirmed_pivots(candles: list[Candle], lookback: int) -> list[Pivot]:
    """
    Scans the full candle list and returns every confirmed pivot high/low.
    A single bar can be both a pivot high and a pivot low in rare cases
    (e.g. a doji at a local extreme) — both are returned independently.
    """
    pivots: list[Pivot] = []
    n = len(candles)

    for i in range(lookback, n - lookback):
        window = candles[i - lookback : i + lookback + 1]
        candle = candles[i]

        if all(candle.high >= w.high for w in window):
            pivots.append(Pivot(index=i, type="high", price=candle.high))

        if all(candle.low <= w.low for w in window):
            pivots.append(Pivot(index=i, type="low", price=candle.low))

    return pivots


def group_pivots_by_index(pivots: list[Pivot]) -> dict[int, list[Pivot]]:
    """Convenience lookup used by the state machine's bar-by-bar sweep."""
    grouped: dict[int, list[Pivot]] = {}
    for p in pivots:
        grouped.setdefault(p.index, []).append(p)
    return grouped
