"""
Runs the full ABCDE detection sweep over a candle array for one symbol +
one direction (Upside or Downside).

Mirrors Pine Script's parallel structure tracking (docs/strategy-guide.md,
Part 9): a new candidate A is spawned at EVERY confirmed pivot of A's type,
and every active structure is advanced one bar at a time in the same pass —
so many structures can be mid-formation simultaneously, each independent.

This runs as a full batch pass over the whole candle window on every fetch
cycle (see app/data/fetcher_worker.py) rather than maintaining incremental
state between polls — simpler, and correct given TwelveData already returns
the full lookback window each time.
"""

from dataclasses import dataclass

from app.engine.state_machine import Direction, Point, Stage, Structure
from app.engine.swing_detector import find_confirmed_pivots, group_pivots_by_index
from app.engine.touch_sweep import TouchMode
from app.models.schemas import Candle


@dataclass
class DetectionConfig:
    direction: Direction
    swing_lookback: int = 5
    touch_mode: TouchMode = "wick"
    e_liquidity_target: str = "A_OR_C"
    max_structures: int = 50


def detect_structures(candles: list[Candle], config: DetectionConfig) -> list[Structure]:
    if len(candles) < config.swing_lookback * 2 + 1:
        return []  # not enough bars to confirm even one pivot yet

    pivots = find_confirmed_pivots(candles, config.swing_lookback)
    pivots_by_index = group_pivots_by_index(pivots)

    a_type = "high" if config.direction == "upside" else "low"

    structures: list[Structure] = []
    next_id = 0

    for i, candle in enumerate(candles):
        pivots_here = pivots_by_index.get(i, [])

        # 1. Spawn a new candidate A for every confirmed pivot of A's type.
        for p in pivots_here:
            if p.type == a_type:
                structures.append(
                    Structure(
                        id=next_id,
                        direction=config.direction,
                        e_liquidity_target=config.e_liquidity_target,
                        a=Point(p.index, p.price),
                        stage=Stage.PENDING_B,
                    )
                )
                next_id += 1

        # FIFO eviction once over the cap — drop the oldest structures first,
        # same rule as the Pine Script version.
        if len(structures) > config.max_structures:
            structures = structures[-config.max_structures :]

        # 2. Advance every still-active structure by this bar.
        for s in structures:
            if s.is_active():
                s.step(candle, i, pivots_here, config.touch_mode)

    return structures


def to_dict(s: Structure) -> dict:
    """Serializes a Structure for the API/WebSocket layer."""

    def point_dict(p: Point | None) -> dict | None:
        return None if p is None else {"index": p.index, "price": p.price}

    return {
        "id": s.id,
        "direction": s.direction,
        "stage": s.stage.name,
        "stage_display": s.stage_name(),
        "a": point_dict(s.a),
        "b": point_dict(s.b),
        "c": point_dict(s.c),
        "d": point_dict(s.d),
        "e": point_dict(s.e),
    }
