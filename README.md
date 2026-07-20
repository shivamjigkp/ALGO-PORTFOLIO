# ABCDE Reversal Structure — Pine Script v5 Indicator Suite

A pure price-action liquidity-sweep reversal detector for TradingView, built entirely on swing-point structure — no oscillators, no moving averages, no external indicators. It identifies a 5-point **A–B–C–D–E** liquidity sweep pattern that precedes trend reversals, and plots a defined entry zone once the pattern completes.

The suite ships as two mirrored scripts:

| Script | Market Context | Signal | Pattern |
|---|---|---|---|
| `ABCDE_Upside_Reversal.pine` | Downtrend | SELL reversal | A=High, B=Low, C=High, D=Low, E=High |
| `ABCDE_Downside_Reversal.pine` | Uptrend | BUY reversal | A=Low, B=High, C=Low, D=High, E=Low |

Both scripts run independently, support unlimited parallel structure tracking on a single chart, and are timeframe-agnostic (works on any chart timeframe the user selects in TradingView — 1m to 1D+).

---

## Table of Contents

1. [Concept](#concept)
2. [The A–B–C–D–E Structure](#the-abcde-structure)
3. [Touch vs. Sweep Rule](#touch-vs-sweep-rule)
4. [Entry Zone](#entry-zone)
5. [E2 — Liquidity Extension Point](#e2--liquidity-extension-point)
6. [Visual Language](#visual-language)
7. [Inputs Reference](#inputs-reference)
8. [Parallel Structure Tracking](#parallel-structure-tracking)
9. [Edge Cases](#edge-cases)
10. [Known Limitations](#known-limitations)
11. [Installation](#installation)
12. [Disclaimer](#disclaimer)

---

## Concept

Reversals are frequently preceded by a repeatable liquidity-sweep sequence: price sweeps a prior extreme to trigger stop-losses and trap late entries, then reverses. This indicator codifies that sequence into five confirmable swing points and automatically marks the resulting entry zone — removing discretionary guesswork from the pattern-recognition step while leaving trade execution entirely in the trader's hands.

The logic is direction-symmetric: the **Upside** script hunts for SELL reversals inside a downtrend, and the **Downside** script hunts for BUY reversals inside an uptrend. Internally, the state machine, invalidation rules, and structure lifecycle are identical between the two — only the swing direction is mirrored.

## The ABCDE Structure

> The description below follows the **Upside** (SELL) script. For the **Downside** script, every high/low reference is mirrored (A/C/E become lows, B/D become highs).

### A — Swing High (Candidate)
The first swing high formed during a downtrend. It is **not yet valid** on its own — it becomes confirmed only once B forms.

### B — Lower Low (Confirms A)
A subsequent swing low that closes below A's origin. The moment B forms, both A and B are confirmed simultaneously and the structure becomes active.

**Invalidation:** If price closes above A before B forms, the structure is discarded.

### C — Highest Swing After A's Liquidity Is Taken
After B, price rallies back up. C is validated once price touches or sweeps above A's high.

**Critical marking rule:** Any number of minor internal swings can form during the move up to A's level — these are ignored. C is always the single highest swing pivot of that entire move, not the sweep candle itself.

**Invalidation:** If price closes below B before C forms, the structure is discarded.

### D — Lowest Swing After B's Liquidity Is Taken
After C, price sells off again. D is validated once price touches or sweeps below B's low.

**Marking rule:** Same principle as C — internal swings during the down-move are ignored. D is the single lowest swing pivot of the move.

**Invalidation:** If price closes above C before D forms, the structure is discarded.

### E — Highest Swing After A or C's Liquidity Is Taken
After D, price rallies once more. E is validated once price touches or sweeps above **either** A's high or C's high (configurable — see [Inputs](#inputs-reference)).

**Marking rule:** As above — E is the single highest swing pivot after the liquidity condition is met, not the sweep candle.

**Invalidation:** If price closes below D before E forms, the structure is discarded.

Once E confirms, the structure is complete, the entry zone is drawn, and all prior labels/lines (A–D) are recolored from the neutral "incomplete" style to a solid cycle color.

## Touch vs. Sweep Rule

This rule governs how C, D, and E are validated:

- **Touch:** Price reaches the target level exactly. The main swing pivot formed immediately after that touch is marked as C/D/E.
- **Sweep:** Price wicks beyond the target level and returns. The sweep candle itself is *never* the marked point — the main pivot that forms after the sweep is.

In both cases, only the single dominant high or low following the liquidity event is marked. Minor internal swings are always discarded.

## Entry Zone

Once E confirms, the indicator draws a shaded box representing the lower 50% of the D→E range (Upside script) or the upper 50% of the D→E range (Downside script):

```
Upside:    Zone Top    = D.low + (E.high − D.low) × 0.5
           Zone Bottom = D.low
           Zone Right  = E.bar + Entry Zone Bars (input)

Downside:  Zone Top    = D.high
           Zone Bottom = D.high − (D.high − E.low) × 0.5
           Zone Right  = E.bar + Entry Zone Bars (input)
```

The zone is rendered as a light, low-opacity box — visual reference only. **The script does not plot entry arrows, signals, or alerts by default** — trade timing and confirmation within the zone are left to the trader's discretion.

## E2 — Liquidity Extension Point

E2 is an optional, independently-toggled extension tracked *after* E has confirmed.

- **Upside:** E2 = the highest swing high formed after D that specifically trades above C (i.e., C's liquidity was taken, which may extend beyond E).
- **Downside:** E2 = the lowest swing low formed after D that specifically trades below C.

**Why it exists:** E locks in on the *first* valid swing that satisfies the A-or-C liquidity condition. E2 continues tracking how far price extends once C specifically has been swept, updating to a new pivot each time a more extreme swing forms.

**Behavior:**
- E2 tracking only starts once the parent structure reaches `STATE_DONE` (i.e., E has confirmed).
- E2 requires C's level to have been swept — if only A was touched, E2 never forms.
- Each new qualifying swing replaces the previous E2 (old objects are deleted, new ones drawn).
- Label, line, and zone visibility are independently controlled (see [Inputs](#inputs-reference)).

## Visual Language

| Element | Incomplete Structure (A–D, pre-E) | Complete Structure (post-E) |
|---|---|---|
| Label background | Fully transparent | Solid cycle color |
| Label text | Light gray (`#B0B0B0`) | White |
| Line style | Dotted gray, extends to current bar | Solid cycle color, fixed at E bar |

**Cycle colors** (rotate per structure to visually separate overlapping patterns):

- **Upside:** Cycle 0 `#2962FF` (Blue) → Cycle 1 `#FF6D00` (Orange) → Cycle 2 `#6A1B9A` (Purple)
- **Downside:** Cycle 0 `#00897B` (Teal) → Cycle 1 `#E53935` (Red) → Cycle 2 `#2E7D32` (Green)

**Gray Mode:** When `Show Colors` is disabled, every element (labels, lines, zones, E2) renders in a single neutral gray (`#787878`) — useful for a clean, distraction-free monochrome view or when overlapping colors reduce readability.

## Inputs Reference

### Structure Settings

| Input | Default | Description |
|---|---|---|
| Swing Lookback | 5 | Bars on each side required to confirm a pivot high/low. Increase to filter out minor swings; decrease to catch smaller structures. |
| Touch Condition | Wick | `Wick` — a wick touch is sufficient. `Close` — the candle must close beyond the level. `Both` — either condition validates (loosest, produces more structures). |
| Minimum Structure To Display | AB | Earliest stage at which a structure becomes visible on the chart. |
| Enable Minimum Filter | ON | Toggles the minimum-stage filter above. |
| Maximum Structure To Display | ABCDE | Latest stage up to which a structure remains visible. |
| Enable Maximum Filter | OFF | Toggles the maximum-stage filter above. Combine with Minimum to isolate a specific stage range (e.g., show only ABC–ABCD). |
| Show Overlapping Structures | ON | When OFF, structures whose A points fall within `2 × Swing Lookback` bars of each other are visually hidden (tracking continues regardless — display only). |
| Max Structures (Heavy) | 50 | Maximum concurrent structures tracked (FIFO eviction). Raising this significantly increases script load. |
| Entry Zone Display Bars | 50 | How many bars forward the entry zone box extends before disappearing. |
| Show Colors | ON | OFF activates Gray Mode (see above). |
| E Liquidity Target | A or C | Which prior level(s) E's liquidity condition checks against: `A Only`, `C Only`, or `A or C`. |

### E2 Settings

| Input | Default | Description |
|---|---|---|
| Show E2 | OFF | Master toggle — enables E2 tracking after E confirms. |
| Show E2 Label | ON | Independent label visibility (requires Show E2 = ON). |
| Show E2 Zone | ON | Independent zone box visibility (requires Show E2 = ON). |

## Parallel Structure Tracking

Multiple ABCDE structures are tracked simultaneously and independently on the same chart. One structure invalidating has no effect on any other structure in progress. For example, at any given moment the chart may simultaneously show:

- Structure 1 — A confirmed, awaiting B
- Structure 2 — A/B confirmed, awaiting C
- Structure 3 — A/B/C/D confirmed, awaiting E

Each is tracked in its own array slot and rendered independently. The script also plots historically on load, so all past structures on the visible chart range are marked for backtesting review.

## Edge Cases

**Structure invalidation (per stage):**
| Stage reached | Cancels if |
|---|---|
| A pending B | Close breaks back above A before B forms |
| B pending C | Close breaks below B before C forms |
| C pending D | Close breaks above C before D forms |
| D pending E | Close breaks below D before E forms |

On invalidation, all associated labels/lines are removed immediately and the search for a new A resumes from that point, in parallel with any other active structures.

**A/C on the same bar:** If a single candle simultaneously forms a new A and satisfies C's condition, it is marked with a combined "AC" label.

**Repeated structures at the same level:** If price later revisits a level where a structure previously completed and forms a new qualifying swing, it is treated as an independent new structure — the prior one is left untouched.

**Flat markets:** If no valid pivot highs/lows form (e.g., an extremely low-volatility range), no structures are detected. This pattern is not designed for flat/rangebound conditions.

## Known Limitations

- **Backtest depth** is limited to the bar history currently loaded in the chart. Use a higher timeframe or a higher TradingView plan tier for deeper historical coverage.
- **Object limits:** TradingView caps labels and lines at 500 per script; this suite is configured for 499 of each. Once the cap is reached, the oldest structure's objects are evicted first (FIFO).
- **No repainting:** All signals are confirmed only after the relevant bar closes — nothing is plotted retroactively based on future data.
- **No built-in alerts or order execution** in the current version — this is a charting/detection tool, not an automated strategy. (See Roadmap below for planned additions.)

## Installation

1. Open TradingView → Pine Editor.
2. Paste the contents of `ABCDE_Upside_Reversal.pine` (and/or `ABCDE_Downside_Reversal.pine`) into a new script.
3. Click **Add to Chart**.
4. Select your desired timeframe directly in TradingView — the script has no fixed timeframe dependency.
5. Adjust inputs under **Structure Settings** and **E2 Settings** as needed.

## Disclaimer

This project is a technical pattern-recognition tool intended for chart analysis and backtesting. It does not constitute financial advice, and it does not guarantee profitability. Past pattern occurrences visible on a chart are not indicative of future performance. Use appropriate risk management and, where relevant, consult a licensed financial advisor before trading live capital.

---

## License

*(Add your preferred license here — MIT is a common choice for open-source Pine Script projects.)*
