"""
E2 — Liquidity Extension Point. See docs/strategy-guide.md, Part 6.

E2 is tracked only for COMPLETED (DONE / "ABCDE") structures, as a separate,
stateless pass over the pivots formed *after* D's bar — this mirrors how the
rest of the engine recomputes fresh from the full window on every fetch
cycle (see structure_manager.py's module docstring) rather than carrying
incremental state between polls.

Upside:   E2 = the topmost swing high formed after D, once some pivot has
          traded beyond C's level (C's own liquidity swept — a stricter
          condition than the one that produced Structure.c, which only
          requires A's level to have been swept).
Downside: E2 = the bottommost swing low formed after D, once some pivot has
          traded beyond C's level.

E2 never forms if C's level is never swept (only A's was), and never forms
before the structure reaches "ABCDE" (E confirmed) — matching the spec's
"tracking starts only once the structure reaches STATE_DONE".

This is intentionally computed independently of Structure.c's own sweep
flag (`_c_liquidity_taken` in state_machine.py, which is private and tracks
A's liquidity, not C's) — reusing it would silently give the wrong
condition, so e2 does its own pivot scan against structure.c.price instead.
"""

from app.engine.state_machine import Point, Structure
from app.engine.swing_detector import Pivot


def calculate_e2(structure: Structure, pivots_by_index: dict[int, list[Pivot]]) -> Point | None:
    """Returns the current E2 point for a completed structure, or None if
    E2 hasn't formed yet (C never swept, or the structure isn't ABCDE)."""

    if structure.stage_name() != "ABCDE" or structure.d is None or structure.c is None:
        return None

    a_is_high = structure.direction == "upside"  # A/C/E are highs on Upside
    e2_type = "high" if a_is_high else "low"

    c_swept = False
    running: Point | None = None

    # Walk every confirmed pivot after D's bar, in bar order.
    for index in sorted(k for k in pivots_by_index if k > structure.d.index):
        for p in pivots_by_index[index]:
            if p.type != e2_type:
                continue

            beyond_c = p.price > structure.c.price if a_is_high else p.price < structure.c.price

            if not c_swept:
                if beyond_c:
                    # This pivot is the one that sweeps C — it becomes the
                    # first E2 candidate.
                    c_swept = True
                    running = Point(p.index, p.price)
                continue

            more_extreme = p.price > running.price if a_is_high else p.price < running.price
            if more_extreme:
                running = Point(p.index, p.price)

    return running if c_swept else None


def calculate_e2_zone(structure: Structure, e2: Point, display_bars: int = 50) -> dict:
    """D -> E2 zone: lower 50% (Upside) / upper 50% (Downside), same shape
    as the primary entry zone in engine/entry_zone.py but measured to E2
    instead of E."""

    d_price = structure.d.price

    if structure.direction == "upside":
        top = d_price + (e2.price - d_price) * 0.5
        bottom = d_price
    else:
        top = d_price
        bottom = d_price - (d_price - e2.price) * 0.5

    return {
        "top": top,
        "bottom": bottom,
        "start_index": e2.index,
        "end_index": e2.index + display_bars,
    }
