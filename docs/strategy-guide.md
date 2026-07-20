# ABCDE Reversal Structure — Strategy Guide

This is the full technical reference for the ABCDE liquidity-sweep reversal pattern. It covers both directional variants — **Upside** (SELL reversal in a downtrend) and **Downside** (BUY reversal in an uptrend) — in complete detail, plus all shared mechanics (touch/sweep rules, entry zone math, the E2 extension, visuals, inputs, and edge cases).

For a quick project overview, see the root [`README.md`](../README.md).

---

## Table of Contents

- [Part 1 — Concept](#part-1--concept)
- [Part 2 — Upside Structure (Downtrend → SELL Reversal)](#part-2--upside-structure-downtrend--sell-reversal)
- [Part 3 — Downside Structure (Uptrend → BUY Reversal)](#part-3--downside-structure-uptrend--buy-reversal)
- [Part 4 — Touch vs. Sweep Rule](#part-4--touch-vs-sweep-rule)
- [Part 5 — Entry Zone](#part-5--entry-zone)
- [Part 6 — E2: Liquidity Extension Point](#part-6--e2-liquidity-extension-point)
- [Part 7 — Visual Language](#part-7--visual-language)
- [Part 8 — Inputs Reference](#part-8--inputs-reference)
- [Part 9 — Parallel Structure Tracking](#part-9--parallel-structure-tracking)
- [Part 10 — Edge Cases](#part-10--edge-cases)
- [Part 11 — Known Limitations](#part-11--known-limitations)

---

## Part 1 — Concept

This is a pure price-action reversal framework — no indicators, no oscillators, no moving averages. It is built entirely on swing-point structure and liquidity behavior.

There are two mirrored variants:

| Variant | Market Context | Signal | Structure |
|---|---|---|---|
| **Upside** | Downtrend | SELL reversal | A=High, B=Low, C=High, D=Low, E=High |
| **Downside** | Uptrend | BUY reversal | A=Low, B=High, C=Low, D=High, E=Low |

Both variants detect a 5-point liquidity-sweep sequence and mark a defined entry zone once the sequence completes. The underlying state machine, invalidation rules, and lifecycle are identical between the two — only the swing direction is mirrored.

---

## Part 2 — Upside Structure (Downtrend → SELL Reversal)

### A — Swing High (Candidate)
A downtrend is in progress. Price forms a swing high. A is **not yet valid** on its own — it is only confirmed once B forms.

**Marking:** A small label and a thin horizontal line at A's swing high.

---

### B — Lower Low (Confirms A)
After A, price moves down and forms a new low below A's base. The moment B forms, both A and B are confirmed together.

**Invalidation:** If price closes above A before B forms, the structure is discarded.

**Marking:** A small label and a thin horizontal line at B's swing low.

---

### C — Highest Swing After A's Liquidity Is Taken
After B, price rallies. C becomes valid once price:
- touches A's high exactly, **or**
- sweeps above A's high

**Critical rule — where C is marked:** After A's liquidity is taken, price may pull back down through several minor internal swings before continuing. These internal swings are ignored entirely. C is always the single **highest** swing pivot of that entire up-move — not the candle that performed the sweep.

**Invalidation:** If price closes below B before C forms, the structure is discarded.

**Marking:** A small label and a thin horizontal line at the topmost swing high.

---

### D — Lowest Swing After B's Liquidity Is Taken
After C, price sells off. D becomes valid once price:
- touches B's low exactly, **or**
- sweeps below B's low

**Critical rule — where D is marked:** Same principle as C. Any internal swings during the down-move are ignored — D is the single **lowest** swing pivot of that move.

**Invalidation:** If price closes above C before D forms, the structure is discarded.

**Marking:** A small label and a thin horizontal line at the bottommost swing low.

---

### E — Highest Swing After A or C's Liquidity Is Taken
After D, price rallies again. E becomes valid once price touches or sweeps:
- A's high, **or**
- C's high

(Which of these is required is configurable — see [E Liquidity Target](#part-8--inputs-reference).)

**Critical rule — where E is marked:** Same principle again — internal swings are ignored. E is the single **highest** swing pivot formed after the liquidity condition is satisfied.

**Invalidation:** If price closes below D before E forms, the structure is discarded.

**Marking:** A small label and a thin horizontal line at the topmost swing high. Once E confirms, all prior A–D labels and lines recolor from the neutral "incomplete" style into a solid cycle color.

---

## Part 3 — Downside Structure (Uptrend → BUY Reversal)

This is a complete mirror image of the Upside structure — every direction is reversed.

### A — Swing Low (Candidate)
An uptrend is in progress. Price forms a swing low. A is only a candidate — confirmed once B forms.

---

### B — Higher High (Confirms A)
After A, price rallies and forms a new high above A's base. Both A and B confirm together.

**Invalidation:** If price closes below A before B forms, the structure is discarded.

---

### C — Lowest Swing After A's Liquidity Is Taken
After B, price pulls back down and touches or sweeps below A's low. C is the single **lowest** swing pivot of that down-move (internal swings ignored).

**Invalidation:** If price closes above B before C forms, the structure is discarded.

---

### D — Highest Swing After B's Liquidity Is Taken
After C, price rallies and touches or sweeps above B's high. D is the single **highest** swing pivot of that up-move.

**Invalidation:** If price closes below C before D forms, the structure is discarded.

---

### E — Lowest Swing After A or C's Liquidity Is Taken
After D, price pulls back down and touches or sweeps A's or C's low. D is the single **lowest** swing pivot after the liquidity condition is met. This is the BUY signal point.

**Invalidation:** If price closes above D before E forms, the structure is discarded.

---

## Part 4 — Touch vs. Sweep Rule

This rule applies identically to C, D, and E in **both** variants.

**If Touch occurs:** Price reaches the target level exactly. The main swing pivot formed after that touch is marked as C/D/E.

**If Sweep occurs:** Price wicks beyond the target level and returns. The sweep candle itself is **never** the marked point — the main swing pivot formed after the sweep is what gets marked.

**Common rule in both cases:** Only the single dominant highest/lowest point formed after the liquidity event is marked. Minor internal swings are always ignored.

---

## Part 5 — Entry Zone

Once E confirms, a shaded box marks the entry zone.

**Upside — lower 50% of the D→E range:**
```
Zone Top    = D.low + (E.high − D.low) × 0.5    [midpoint]
Zone Bottom = D.low
Zone Right  = E.bar + Entry Zone Bars (input)
```

**Downside — upper 50% of the D→E range:**
```
Zone Top    = D.high
Zone Bottom = D.high − (D.high − E.low) × 0.5    [midpoint]
Zone Right  = E.bar + Entry Zone Bars (input)
```
The zone sits near D because the reversal target is upward in this variant.

The zone renders as a light, low-opacity box — a visual reference only. **No entry arrows or signal markers are plotted** — trade timing within the zone is left to the trader.

---

## Part 6 — E2: Liquidity Extension Point

E2 is an optional point tracked **after** E confirms.

**Upside:** E2 = the topmost swing high formed after D that specifically trades above C (C's liquidity taken). This can extend beyond E.

**Downside:** E2 = the bottommost swing low formed after D that specifically trades below C. This can extend beyond E.

**Why it exists:** E locks onto the *first* valid swing satisfying the A-or-C liquidity condition. E2 continues tracking how far price extends once C specifically has been swept.

**Formation logic:**
- Tracking starts only once the structure reaches `STATE_DONE` (E confirmed).
- A new swing pivot beyond C's level sets `c_swept = true`.
- Once `c_swept` is true, the extreme pivot is tracked continuously.
- Any new, more extreme pivot replaces the previous E2 (old chart objects deleted, new ones drawn).

**When E2 does NOT form:**
- If C was never swept (only A was touched) — E2 never forms.
- If the E2 master toggle is OFF — no E2 logic runs at all.

**Visual:**
- E2 label — colored using the same cycle color once E confirms.
- E2 line — a fixed horizontal line at the E2 bar.
- E2 zone — lower 50% (Upside) / upper 50% (Downside) of D→E2, same styling as the primary entry zone.

---

## Part 7 — Visual Language

| Element | Incomplete Structure (A–D, pre-E) | Complete Structure (post-E) |
|---|---|---|
| Label background | Fully transparent | Solid cycle color |
| Label text | Light gray (`#B0B0B0`) | White |
| Line style | Dotted gray, extends to current bar | Solid cycle color, fixed at E bar |

**Cycle colors:**
- **Upside:** Cycle 0 `#2962FF` (Blue) → Cycle 1 `#FF6D00` (Orange) → Cycle 2 `#6A1B9A` (Purple)
- **Downside:** Cycle 0 `#00897B` (Teal) → Cycle 1 `#E53935` (Red) → Cycle 2 `#2E7D32` (Green)

**Gray Mode:** When colors are disabled, everything — labels, lines, zones, E2 — renders in a single neutral gray (`#787878`). Useful for a clean monochrome view or when overlapping colors reduce readability.

**Line range:**
- Incomplete — extends live to the current bar while the structure is still forming.
- Complete — fixed at the E bar once confirmed.

---

## Part 8 — Inputs Reference

### Structure Settings

| Input | Default | Description |
|---|---|---|
| Swing Lookback | 5 | Bars on each side required to confirm a pivot high/low. Increase to filter minor swings; decrease to catch smaller structures. |
| Touch Condition | Wick | `Wick` — a wick touch is enough. `Close` — the candle must close beyond the level. `Both` — either condition validates (loosest, produces more structures). |
| Minimum Structure To Display | AB | Earliest stage at which a structure becomes visible. |
| Enable Minimum Filter | ON | Toggles the minimum-stage filter. |
| Maximum Structure To Display | ABCDE | Latest stage up to which a structure remains visible. |
| Enable Maximum Filter | OFF | Toggles the maximum-stage filter. Combine with Minimum to isolate a specific stage range. |
| Show Overlapping Structures | ON | When OFF, structures whose A points fall within `2 × Swing Lookback` bars of each other are visually hidden (tracking continues regardless). |
| Max Structures (Heavy) | 50 | Maximum concurrent structures tracked (FIFO eviction). Raising this increases computational load significantly. |
| Entry Zone Display Bars | 50 | How many bars forward the entry zone box extends before disappearing. |
| Show Colors | ON | OFF activates Gray Mode. |
| E Liquidity Target | A or C | Which prior level(s) E's liquidity condition checks: `A Only`, `C Only`, or `A or C`. |

### E2 Settings

| Input | Default | Description |
|---|---|---|
| Show E2 | OFF | Master toggle — enables E2 tracking after E confirms. |
| Show E2 Label | ON | Independent label visibility (requires Show E2 = ON). |
| Show E2 Zone | ON | Independent zone box visibility (requires Show E2 = ON). |

---

## Part 9 — Parallel Structure Tracking

Multiple ABCDE structures are tracked simultaneously and independently on the same chart/symbol. One structure invalidating does not affect any other in progress. For example, at any given moment the following can coexist:

- Structure 1 — A confirmed, awaiting B
- Structure 2 — A/B confirmed, awaiting C
- Structure 3 — A/B/C/D confirmed, awaiting E

Each is tracked independently and rendered separately. Historical structures across the loaded chart range are also marked, supporting backtesting review.

---

## Part 10 — Edge Cases

**Structure invalidation (per stage):**

| Stage reached | Cancels if |
|---|---|
| A, pending B | Close breaks back above A (Upside) / below A (Downside) before B forms |
| B, pending C | Close breaks below B (Upside) / above B (Downside) before C forms |
| C, pending D | Close breaks above C (Upside) / below C (Downside) before D forms |
| D, pending E | Close breaks below D (Upside) / above D (Downside) before E forms |

On invalidation, all associated labels/lines are removed immediately, and the search for a new A resumes from that point — in parallel with any other active structures.

**A/C on the same bar:** If a single candle simultaneously forms a new A and satisfies C's condition, it is marked with a combined "AC" label.

**Repeated structures at the same level:** If price later revisits a level where a structure previously completed and forms a new qualifying swing, it is treated as an independent new structure — the prior one is left untouched.

**Flat markets:** If no valid pivot highs/lows form (e.g., an extremely low-volatility range), no structures are detected. This pattern is not designed for flat/rangebound conditions.

---

## Part 11 — Known Limitations

- **Backtest depth** is limited to the bar history currently loaded/fetched. Deeper history requires a higher timeframe or a data provider with more history.
- **Object/render limits** apply when running inside TradingView (500 labels/lines cap); the web dashboard version is not bound by this limit since rendering is handled independently.
- **No repainting:** all signals are confirmed only after the relevant bar closes — nothing is plotted retroactively based on future data.
- **This is a pattern-detection tool, not financial advice** — it does not guarantee profitable outcomes. Always apply independent risk management.
