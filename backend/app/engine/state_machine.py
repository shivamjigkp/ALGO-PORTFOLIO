"""
The ABCDE state machine — one Structure instance tracks one A-B-C-D-E
sequence from the moment its A point is spawned until it either completes
(reaches E) or is invalidated.

Shared between BOTH the Upside (SELL) and Downside (BUY) variants via the
`direction` flag, exactly as planned in docs/strategy-guide.md:
  - "upside"   → A, C, E are HIGH-type points; B, D are LOW-type points
  - "downside" → A, C, E are LOW-type points;  B, D are HIGH-type points

Marking rules implemented here (see docs/strategy-guide.md Part 2/3 for the
full rationale):
  - A, B, E commit at a specific CONFIRMED SWING PIVOT (a discrete event).
  - C, D commit as the running highest/lowest raw price reached during their
    leg — i.e. "ignore internal swings, take the extreme of the whole move" —
    resolved the moment the NEXT stage's liquidity condition is met.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Literal

from app.engine.swing_detector import Pivot
from app.engine.touch_sweep import TouchMode, broke_beyond_close, touched_beyond
from app.models.schemas import Candle

Direction = Literal["upside", "downside"]


class Stage(Enum):
    PENDING_B = auto()
    PENDING_C = auto()
    PENDING_D = auto()
    PENDING_E = auto()
    DONE = auto()
    CANCELLED = auto()


@dataclass(frozen=True)
class Point:
    index: int
    price: float


# For direction "upside": A/C/E are highs. For "downside": A/C/E are lows.
_HIGH_LETTERS_BY_DIRECTION = {"upside": {"A", "C", "E"}, "downside": {"B", "D"}}


def _is_high_letter(letter: str, direction: Direction) -> bool:
    return letter in _HIGH_LETTERS_BY_DIRECTION[direction]


def _extreme_price(candle: Candle, seeking_high: bool) -> float:
    return candle.high if seeking_high else candle.low


def _more_extreme(new_price: float, current_price: float, seeking_high: bool) -> bool:
    return new_price > current_price if seeking_high else new_price < current_price


@dataclass
class Structure:
    id: int
    direction: Direction
    e_liquidity_target: Literal["A", "C", "A_OR_C"] = "A_OR_C"

    a: Point = None
    b: Point | None = None
    c: Point | None = None
    d: Point | None = None
    e: Point | None = None
    stage: Stage = Stage.PENDING_B

    # --- internal leg-tracking state (not part of the public result) ---
    _c_liquidity_taken: bool = field(default=False, repr=False)
    _c_running: Point | None = field(default=None, repr=False)
    _d_running: Point | None = field(default=None, repr=False)
    _e_watch_from_index: int = field(default=-1, repr=False)

    def is_active(self) -> bool:
        return self.stage not in (Stage.DONE, Stage.CANCELLED)

    def step(self, candle: Candle, index: int, pivots_at_index: list[Pivot], touch_mode: TouchMode) -> None:
        if self.stage == Stage.PENDING_B:
            self._step_pending_b(candle, index, pivots_at_index)
        elif self.stage == Stage.PENDING_C:
            self._step_pending_c(candle, index, touch_mode)
        elif self.stage == Stage.PENDING_D:
            self._step_pending_d(candle, index, touch_mode)
        elif self.stage == Stage.PENDING_E:
            self._step_pending_e(candle, index, pivots_at_index, touch_mode)

    # ---- PENDING_B: waiting for the first pivot that confirms B ----
    def _step_pending_b(self, candle: Candle, index: int, pivots_at_index: list[Pivot]) -> None:
        a_is_high = _is_high_letter("A", self.direction)

        if broke_beyond_close(candle, self.a.price, seeking_high=a_is_high):
            self.stage = Stage.CANCELLED
            return

        b_type = "low" if a_is_high else "high"
        for p in pivots_at_index:
            if p.type != b_type or p.index <= self.a.index:
                continue
            qualifies = p.price < self.a.price if a_is_high else p.price > self.a.price
            if qualifies:
                self.b = Point(p.index, p.price)
                self.stage = Stage.PENDING_C
                self._c_liquidity_taken = False
                self._c_running = None
                break

    # ---- PENDING_C: track the running extreme since A's level is swept ----
    def _step_pending_c(self, candle: Candle, index: int, touch_mode: TouchMode) -> None:
        a_is_high = _is_high_letter("A", self.direction)  # also C's type
        b_is_high = _is_high_letter("B", self.direction)

        # Invalidation only applies BEFORE C's liquidity is taken. Once price
        # has swept A's level, a close beyond B is no longer a failure — it's
        # D's own trigger condition firing, handled below.
        if not self._c_liquidity_taken and broke_beyond_close(candle, self.b.price, seeking_high=b_is_high):
            self.stage = Stage.CANCELLED
            return

        if not self._c_liquidity_taken:
            if touched_beyond(candle, self.a.price, touch_mode, seeking_high=a_is_high):
                self._c_liquidity_taken = True
                self._c_running = Point(index, _extreme_price(candle, a_is_high))
        else:
            price = _extreme_price(candle, a_is_high)
            if self._c_running is None or _more_extreme(price, self._c_running.price, a_is_high):
                self._c_running = Point(index, price)

        # D's liquidity condition ends C's leg (and simultaneously starts D's)
        if self._c_liquidity_taken and touched_beyond(candle, self.b.price, touch_mode, seeking_high=b_is_high):
            self.c = self._c_running or Point(index, _extreme_price(candle, a_is_high))
            self.stage = Stage.PENDING_D
            self._d_running = Point(index, _extreme_price(candle, b_is_high))

    # ---- PENDING_D: track the running extreme since B's level is swept ----
    def _step_pending_d(self, candle: Candle, index: int, touch_mode: TouchMode) -> None:
        b_is_high = _is_high_letter("B", self.direction)  # also D's type
        c_is_high = _is_high_letter("C", self.direction)
        a_is_high = _is_high_letter("A", self.direction)

        if broke_beyond_close(candle, self.c.price, seeking_high=c_is_high):
            self.stage = Stage.CANCELLED
            return

        price = _extreme_price(candle, b_is_high)
        if self._d_running is None or _more_extreme(price, self._d_running.price, b_is_high):
            self._d_running = Point(index, price)

        e_target_price = self._e_target_price()
        if touched_beyond(candle, e_target_price, touch_mode, seeking_high=a_is_high):
            self.d = self._d_running
            self.stage = Stage.PENDING_E
            self._e_watch_from_index = index

    # ---- PENDING_E: commits at the FIRST qualifying pivot (not a running extreme) ----
    def _step_pending_e(self, candle: Candle, index: int, pivots_at_index: list[Pivot], touch_mode: TouchMode) -> None:
        a_is_high = _is_high_letter("A", self.direction)  # also E's type
        d_is_high = _is_high_letter("D", self.direction)

        if broke_beyond_close(candle, self.d.price, seeking_high=d_is_high):
            self.stage = Stage.CANCELLED
            return

        e_type = "high" if a_is_high else "low"
        for p in pivots_at_index:
            if p.type == e_type and p.index > self._e_watch_from_index:
                self.e = Point(p.index, p.price)
                self.stage = Stage.DONE
                break

    def _e_target_price(self) -> float:
        """A's price, C's price, or the looser of the two, per configuration."""
        if self.e_liquidity_target == "A":
            return self.a.price
        if self.e_liquidity_target == "C":
            return self.c.price
        a_is_high = _is_high_letter("A", self.direction)
        # "A_OR_C": whichever level is EASIER to reach first (closer to D) —
        # i.e. the less extreme of the two — since either one satisfies the rule.
        return min(self.a.price, self.c.price) if a_is_high else max(self.a.price, self.c.price)

    def stage_name(self) -> str:
        letters = {
            Stage.PENDING_B: "AB",
            Stage.PENDING_C: "AB",
            Stage.PENDING_D: "ABC",
            Stage.PENDING_E: "ABCD",
            Stage.DONE: "ABCDE",
            Stage.CANCELLED: "CANCELLED",
        }
        return letters[self.stage]
