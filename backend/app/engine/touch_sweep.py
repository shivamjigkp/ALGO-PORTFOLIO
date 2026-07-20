"""
Touch vs. Sweep rule — see docs/strategy-guide.md, Part 4.

Three modes:
  - "wick"  — a wick touch alone is sufficient
  - "close" — the candle must close beyond the level
  - "both"  — either condition validates
"""

from typing import Literal

from app.models.schemas import Candle

TouchMode = Literal["wick", "close", "both"]


def touched_above(candle: Candle, level: float, mode: TouchMode) -> bool:
    if mode == "wick":
        return candle.high >= level
    if mode == "close":
        return candle.close >= level
    return candle.high >= level or candle.close >= level  # "both"


def touched_below(candle: Candle, level: float, mode: TouchMode) -> bool:
    if mode == "wick":
        return candle.low <= level
    if mode == "close":
        return candle.close <= level
    return candle.low <= level or candle.close <= level  # "both"


def touched_beyond(candle: Candle, level: float, mode: TouchMode, seeking_high: bool) -> bool:
    """Direction-agnostic wrapper — used by the state machine, which is itself
    direction-agnostic (shared between the Upside and Downside variants)."""
    return touched_above(candle, level, mode) if seeking_high else touched_below(candle, level, mode)


def broke_beyond_close(candle: Candle, level: float, seeking_high: bool) -> bool:
    """
    Invalidation check: has price CLOSED beyond a level in the given
    direction? Always uses the close (not the wick), regardless of the
    configured touch mode — invalidation is intentionally stricter than
    entry/liquidity conditions.
    """
    return candle.close > level if seeking_high else candle.close < level
