"use client";

import type { StructureItem } from "@/lib/types";

const CYCLE_UP = ["var(--cycle-up-0)", "var(--cycle-up-1)", "var(--cycle-up-2)"];
const CYCLE_DOWN = ["var(--cycle-down-0)", "var(--cycle-down-1)", "var(--cycle-down-2)"];

// Same stable per-structure color hash used by StructureChart.tsx, so a
// structure's stripe color here matches its color on the chart.
function stripeColorFor(structure: StructureItem): string {
  const palette = structure.direction === "upside" ? CYCLE_UP : CYCLE_DOWN;
  let hash = 0;
  for (const ch of String(structure.id)) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return palette[hash % palette.length];
}

function metaLine(s: StructureItem): { label: string; value: string } {
  if (s.stage_display === "ABCDE" && s.entry_zone) {
    return {
      label: "Entry zone active",
      value: `${s.entry_zone.bottom.toFixed(4)} – ${s.entry_zone.top.toFixed(4)}`,
    };
  }
  const lastPoint = s.d ?? s.c ?? s.b ?? s.a;
  return {
    label: `${s.stage_display} formed`,
    value: lastPoint ? `bar ${lastPoint.index}` : "—",
  };
}

interface SignalFeedProps {
  symbol: string;
  structures: StructureItem[];
  connected: boolean;
}

export default function SignalFeed({ symbol, structures, connected }: SignalFeedProps) {
  // CANCELLED structures aren't shown - a dead structure isn't a signal.
  const visible = structures.filter((s) => s.stage_display !== "CANCELLED");

  return (
    <div className="feed">
      <div className="feed-head">
        <span className="t">Active structures</span>
        <span className={`live ${connected ? "" : "off"}`}>
          <span className="dot" />
          {connected ? "Live" : "Offline"}
        </span>
      </div>

      {visible.length === 0 && (
        <div className="feed-empty">No structures forming on {symbol || "this symbol"} yet.</div>
      )}

      {visible.map((s) => {
        const stripe = stripeColorFor(s);
        const meta = metaLine(s);
        const filled = s.stage_display.length; // "AB"=2, "ABC"=3, "ABCD"=4, "ABCDE"=5
        const isComplete = s.stage_display === "ABCDE";

        return (
          <div key={`${s.direction}-${s.id}`} className="sig-card" style={{ ["--stripe" as string]: stripe }}>
            <div className="sig-top">
              <span className="sig-sym">
                {symbol} · {s.direction === "upside" ? "Sell" : "Buy"}
              </span>
              <span className={`sig-stage ${isComplete ? "complete" : ""}`}>
                {isComplete ? "E confirmed" : `Awaiting ${"ABCDE"[filled]}`}
              </span>
            </div>
            <div className="sig-meta">
              <span>{meta.label}</span>
              <span className="mono">{meta.value}</span>
            </div>
            <div className="sig-progress">
              {[0, 1, 2, 3, 4].map((i) => (
                <i
                  key={i}
                  className={i < filled ? "on" : ""}
                  style={i < filled ? { ["--stripe" as string]: stripe } : undefined}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
