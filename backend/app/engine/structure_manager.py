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

from app.engine.e2_tracker import calculate_e2, calculate_e2_zone
from app.engine.entry_zone import calculate_entry_zone
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


def build_structures_payload(
    candles: list[Candle],
    strategy: str = "both",       # "upside" | "downside" | "both"
    swing_lookback: int = 5,
    touch_mode: TouchMode = "wick",
    e_target: str = "A_OR_C",
) -> list[dict]:
    """Single source of truth for turning a candle window into the
    structure list the frontend renders — entry_zone and e2 included.

    Used by BOTH app/api/routes_structures.py (REST) and
    app/api/ws_live.py (WebSocket) so the two transports can never drift
    out of sync with each other.
    """
    if not candles:
        return []

    # Pivots are recomputed here (same cost as inside detect_structures)
    # rather than threaded through, since e2 needs them post-D and nothing
    # in this codebase carries incremental state between fetch cycles
    # (see this module's docstring above).
    pivots_by_index = group_pivots_by_index(find_confirmed_pivots(candles, swing_lookback))

    directions = ["upside", "downside"] if strategy == "both" else [strategy]
    results: list[dict] = []

    for direction in directions:
        cfg = DetectionConfig(
            direction=direction,
            swing_lookback=swing_lookback,
            touch_mode=touch_mode,
            e_liquidity_target=e_target,
        )
        for s in detect_structures(candles, cfg):
            item = to_dict(s)

            entry = calculate_entry_zone(s, direction) if s.stage_name() == "ABCDE" else None
            item["entry_zone"] = (
                {"top": entry.top, "bottom": entry.bottom, "start_index": entry.start_index, "end_index": entry.end_index}
                if entry else None
            )

            e2 = calculate_e2(s, pivots_by_index) if s.stage_name() == "ABCDE" else None
            item["e2"] = {"index": e2.index, "price": e2.price} if e2 else None
            item["e2_zone"] = calculate_e2_zone(s, e2) if e2 else None

            results.append(item)

    return results
