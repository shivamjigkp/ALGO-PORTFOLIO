"""
Entry zone math — see docs/strategy-guide.md, Part 5.

Upside (SELL):   zone = lower 50% of the D→E range
Downside (BUY):  zone = upper 50% of the D→E range
"""

from dataclasses import dataclass

from app.engine.state_machine import Direction, Structure


@dataclass(frozen=True)
class EntryZone:
    top: float
    bottom: float
    start_index: int  # E's bar — zone begins here
    end_index: int  # start_index + display_bars


def calculate_entry_zone(structure: Structure, direction: Direction, display_bars: int = 50) -> EntryZone | None:
    if structure.d is None or structure.e is None:
        return None

    d_price, e_price = structure.d.price, structure.e.price

    if direction == "upside":
        # D is a low, E is a high — zone sits in the lower half of the range.
        top = d_price + (e_price - d_price) * 0.5
        bottom = d_price
    else:
        # D is a high, E is a low — zone sits in the upper half of the range.
        top = d_price
        bottom = d_price - (d_price - e_price) * 0.5

    return EntryZone(
        top=top,
        bottom=bottom,
        start_index=structure.e.index,
        end_index=structure.e.index + display_bars,
    )
