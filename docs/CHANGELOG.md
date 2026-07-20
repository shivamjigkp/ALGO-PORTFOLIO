# Changelog

All notable bug fixes and feature additions for the ABCDE Reversal Structure indicator suite are documented in this file, in chronological order of development.

---

## Bug Fixes

### Fix 1 — Cannot modify global variable `offsetCounter` inside a function
**Session:** 1
**Issue:** Pine Script v5 does not allow a global `var` to be reassigned with `:=` from inside a function scope.
**Location:** `offsetCounter := offsetCounter + 1` inside `f_addStructure()`.
**Resolution:** Moved the increment operation for `offsetCounter` out of the function and into the global scope.
**Status:** Fixed

---

### Fix 2 — `f_atr` needs to be called consistently on every calculation
**Session:** 1
**Issue:** `ta.atr()` was being called conditionally, inside an `if` block, which Pine Script does not permit for series functions that must execute unconditionally on every bar.
**Resolution:** Removed the `f_atr()` helper entirely. `atrValue` is now calculated unconditionally at the top level of the script.
**Status:** Fixed

---

### Fix 3 — `f_makeLabel` needs to be called consistently on every calculation
**Session:** 1
**Issue:** `f_makeLabel()` contained an internal call to `f_atr()`, which was itself inside a conditional scope, propagating the same rule violation.
**Resolution:** Removed the internal `f_atr()` call; ATR value is now passed in as a parameter (`atrVal`).
**Status:** Fixed

---

### Fix 4 — Runtime error RE10045: `array.get()` index out of bounds (array size 0)
**Session:** 2 (Bar 38)
**Issue:** `f_deleteStructure()` crashed because the target array was empty. Root cause: a structure was both added and deleted on the same bar, creating a race condition between array mutations.
**Resolution:** Implemented a pending queue. A newly detected point A is not committed directly to the main tracking array — it first enters a pending queue and is only committed to the main array on the following bar. Processing order per bar:
1. Commit any pending items into the main array.
2. Add any new point-A candidates to the pending queue only (not the main array).
3. Process the main array (the newly queued point A is not yet present, avoiding same-bar conflicts).
**Status:** Fixed

---

### Fix 5 — Runtime error RE10045: same crash recurring (Bar 37)
**Session:** 3
**Issue:** The same out-of-bounds crash recurred; bounds checks and duplicate-prevention logic alone were insufficient.
**Resolution:** Properly implemented the full 3-step pending-queue flow described in Fix 4, enforced strictly on every bar.
**Status:** Fixed

---

### Fix 6 — Labels rendering far away from their corresponding lines
**Session:** 4
**Issue:** The ATR-based offset multiplier used for label placement was too large, causing labels to appear visibly detached from their lines on high-price instruments (e.g., Gold, Silver).
**Resolution:** Switched to `yloc.price`, anchoring each label exactly at its price level, and removed the ATR-based offset system entirely. Introduced a 3-style label cycling system via `switch`:
- Cycle 0 → `label_down` / `label_up`
- Cycle 1 → `label_lower_left` / `label_upper_left`
- Cycle 2 → `label_lower_right` / `label_upper_right`
**Status:** Fixed

---

### Fix 7 — Syntax error: "end of line without line continuation"
**Session:** 5 (Line 46)
**Issue:** A multi-line ternary expression is not valid syntax in Pine Script v5. `f_getLabelStyleHigh()` and `f_getLabelStyleLow()` had their ternary chains split across multiple lines.
**Resolution:** Replaced the ternary chains with `switch` statements, which is the correct v5 pattern for this case.
**Status:** Fixed — 23 May 2026, 15:27

---

### Fix 8 — Labels not clearly visible on chart
**Session:** 6 — 23 May 2026
**Issue:** The gray background used for labels appeared washed out on both light and dark chart themes, and there was no visual distinction between separate structures.
**Resolution:** Introduced a two-tier visual state:
- **Incomplete:** transparent background, gray text, dotted lines.
- **Complete:** solid cycle colors (Blue / Orange / Purple for Upside; Teal / Red / Green for Downside), white text, solid lines.

Added helper functions `f_makeLabel()`, `f_colorLabel()`, and `f_colorLine()`. Once E confirms, all prior A–D labels and lines are recolored via `label.set_color()`.
**Status:** Fixed — 23 May 2026

---

### Fix 9 — Lines extending too far across the chart
**Session:** 7 — 23 May 2026
**Issue:** All structure lines used `extend.right`, causing them to stretch indefinitely to the right edge of the chart and clutter the view.
**Resolution:**
- Incomplete-structure lines: `x2 = bar_index`, `extend = none`, dotted gray — extends only while the structure is still forming.
- Complete-structure lines: `x2 = E bar`, fixed at the E point, solid color.

Result: each completed structure now renders as a clean, tightly bounded group spanning only A through E.
**Status:** Fixed — 23 May 2026

---

## Feature Additions

### Feature 1 — E2 Point (C-Sweep Extension)
**Session:** 8 — 23 May 2026

**Definition:** E2 is the topmost (Upside) or bottommost (Downside) swing pivot formed after D that specifically trades through C's level, i.e., C's liquidity has been taken.

**Logic:**
- Tracking begins once the parent structure reaches `STATE_DONE` (after E confirms).
- Any new swing pivot that trades beyond C's level sets `c_swept = true`.
- Once `c_swept` is true, the extreme pivot continues to be tracked.
- Each new, more extreme pivot replaces the previous E2 (old chart objects deleted, new ones drawn).

**New arrays:** `st_c_swept`, `st_e2_high`/`st_e2_low`, `st_e2_bar`, `st_le2_label`, `st_le2_line`, `st_zone2_box`

**Toggle:** `i_showE2` (master switch, OFF by default)

**Status:** Complete — 23 May 2026

---

### Feature 2 — Downside ABCDE Script (Uptrend BUY Reversal)
**Session:** 9 — 24 May 2026

Added a new script, `ABCDE_Downside_Reversal.pine`, as a complete mirror of the Upside script:
- A = swing Low, B = swing High, C = swing Low, D = swing High, E = swing Low
- Entry zone = upper 50% of the D–E range (near D, since the reversal target is upward)
- Distinct color set: Teal (`#00897B`), Red (`#E53935`), Green (`#2E7D32`)
- Identical pending-queue mechanism, parallel structure tracking, and invalidation rules as the Upside script

**Status:** Complete — 24 May 2026

---

### Feature 3 — Independent E2 Label / Zone Toggles
**Session:** 9 — 24 May 2026

Previously, a single `i_showE2` toggle controlled all E2 visuals together. Split into three independent controls:
- `i_showE2` — master toggle (starts/stops E2 tracking entirely)
- `i_showE2Label` — controls only the label (the line is always drawn when E2 is active, since it marks the price level)
- `i_showE2Zone` — controls only the zone box

Applied identically to both the Upside and Downside scripts.

**Status:** Complete — 24 May 2026

---

### Feature 4 — Maximum Structure Display Filter
**Session:** 9 — 24 May 2026

Previously only a minimum-stage display filter existed. Added a corresponding maximum-stage filter:
- `i_minDisplay` + `i_minOn` — minimum display stage + on/off toggle
- `i_maxDisplay` + `i_maxOn` — maximum display stage + on/off toggle

Example: Minimum = AB (ON), Maximum = ABCD (ON) → only AB, ABC, and ABCD stage structures are shown; ABCDE (fully complete) structures are hidden.

Applied identically to both scripts.

**Status:** Complete — 24 May 2026

---

### Feature 5 — Show Colors Toggle (Gray Mode)
**Session:** 9 — 24 May 2026

Previously, cycle colors were always active. Added `i_showColors`:
- **ON** — normal cycle colors (Blue/Orange/Purple or Teal/Red/Green)
- **OFF** — everything (labels, lines, zones, E2) renders in a single neutral gray (`#787878`)

Implementation is centralized entirely within `f_cycleColor()`, so the entire script is controlled from one location.

Applied identically to both scripts.

**Status:** Complete — 24 May 2026

---

### Feature 6 — "Both" Touch Condition Option
**Session:** 9 — 24 May 2026

Previously, only Wick and Close touch conditions were available. Added a third option:
- **Wick** — a wick touch alone is sufficient
- **Close** — the candle must close beyond the level
- **Both** — either a wick touch or a close beyond the level validates the condition

Added the corresponding condition branch to `f_touchedAbove()` and `f_touchedBelow()`. Applied identically to both scripts.

**Status:** Complete — 24 May 2026

---

*This changelog reflects the internal development history of the indicator suite across all debugging and feature-development sessions.*
