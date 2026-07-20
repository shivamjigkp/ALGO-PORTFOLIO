"use client";

import {
  CandlestickSeries,
  ColorType,
  createChart,
  createSeriesMarkers,
  IChartApi,
  ISeriesApi,
  LineSeries,
  LineStyle,
  SeriesMarker,
  Time,
  UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useRef } from "react";
import type { Candle, Point, StructureItem } from "@/lib/types";

const CYCLE_UP = ["var(--cycle-up-0)", "var(--cycle-up-1)", "var(--cycle-up-2)"];
const CYCLE_DOWN = ["var(--cycle-down-0)", "var(--cycle-down-1)", "var(--cycle-down-2)"];

// Resolve CSS custom properties to concrete hex — lightweight-charts draws
// on canvas and can't read var(...) itself.
function resolveVar(name: string): string {
  if (typeof window === "undefined") return "#888888";
  const v = getComputedStyle(document.documentElement).getPropertyValue(
    name.replace("var(", "").replace(")", "")
  );
  return v.trim() || "#888888";
}

// Stable per-structure cycle-color assignment (independent of array order,
// so a structure keeps its color across live updates).
function cycleColorFor(structure: StructureItem): string {
  const palette = structure.direction === "upside" ? CYCLE_UP : CYCLE_DOWN;
  let hash = 0;
  for (const ch of structure.id) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return resolveVar(palette[hash % palette.length]);
}

function timeAt(candles: Candle[], index: number): UTCTimestamp | null {
  const c = candles[Math.max(0, Math.min(index, candles.length - 1))];
  return c ? (c.timestamp as UTCTimestamp) : null;
}

// Which named points (in ABCDE order) sit on the "high" side of the swing
// vs. the "low" side, per direction — controls marker placement + shape.
const HIGH_POINTS: Record<StructureItem["direction"], (keyof StructureItem)[]> = {
  upside: ["a", "c", "e"],
  downside: ["b", "d"],
};

const LABELS: (keyof StructureItem)[] = ["a", "b", "c", "d", "e"];

export default function StructureChart({
  candles,
  structures,
}: {
  candles: Candle[];
  structures: StructureItem[];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const overlaySeriesRef = useRef<ISeriesApi<"Line">[]>([]);

  // Chart lifecycle — created once per mount.
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: resolveVar("var(--text-muted)"),
        fontFamily: "var(--font-geist-mono)",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: resolveVar("var(--border-hair)") },
        horzLines: { color: resolveVar("var(--border-hair)") },
      },
      rightPriceScale: { borderColor: resolveVar("var(--border-hair)") },
      timeScale: {
        borderColor: resolveVar("var(--border-hair)"),
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        vertLine: { color: resolveVar("var(--text-faint)"), labelBackgroundColor: "#1a2030" },
        horzLine: { color: resolveVar("var(--text-faint)"), labelBackgroundColor: "#1a2030" },
      },
      autoSize: true,
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: resolveVar("var(--up-candle)"),
      downColor: resolveVar("var(--down-candle)"),
      borderVisible: false,
      wickUpColor: resolveVar("var(--up-candle)"),
      wickDownColor: resolveVar("var(--down-candle)"),
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    return () => {
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      overlaySeriesRef.current = [];
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Candle data.
  useEffect(() => {
    if (!candleSeriesRef.current) return;
    candleSeriesRef.current.setData(
      candles.map((c) => ({
        time: c.timestamp as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }))
    );
    chartRef.current?.timeScale().fitContent();
  }, [candles]);

  // Structure overlays: ABCDE polylines + entry-zone boundary lines +
  // point markers, redrawn whenever structures or candles change.
  useEffect(() => {
    const chart = chartRef.current;
    const candleSeries = candleSeriesRef.current;
    if (!chart || !candleSeries || candles.length === 0) return;

    for (const s of overlaySeriesRef.current) chart.removeSeries(s);
    overlaySeriesRef.current = [];

    const markers: SeriesMarker<Time>[] = [];

    for (const structure of structures) {
      const color = cycleColorFor(structure);
      const isComplete = structure.stage_display === "ABCDE";
      const highSet = new Set(HIGH_POINTS[structure.direction]);

      const pathPoints: { time: UTCTimestamp; value: number }[] = [];
      for (const key of LABELS) {
        const pt = structure[key] as Point | null;
        if (!pt) continue;
        const t = timeAt(candles, pt.index);
        if (t === null) continue;
        pathPoints.push({ time: t, value: pt.price });

        markers.push({
          time: t,
          position: highSet.has(key) ? "aboveBar" : "belowBar",
          color,
          shape: highSet.has(key) ? "arrowDown" : "arrowUp",
          text: key.toUpperCase(),
          size: 1,
        });
      }

      if (pathPoints.length >= 2) {
        const line = chart.addSeries(LineSeries, {
          color,
          lineWidth: isComplete ? 2 : 1,
          lineStyle: isComplete ? LineStyle.Solid : LineStyle.Dotted,
          lastValueVisible: false,
          priceLineVisible: false,
          crosshairMarkerVisible: false,
        });
        line.setData(pathPoints);
        overlaySeriesRef.current.push(line);
      }

      if (structure.entry_zone) {
        const { top, bottom, start_index, end_index } = structure.entry_zone;
        const t0 = timeAt(candles, start_index);
        const t1 = timeAt(candles, end_index);
        if (t0 !== null && t1 !== null && t1 > t0) {
          for (const price of [top, bottom]) {
            const bound = chart.addSeries(LineSeries, {
              color,
              lineWidth: 1,
              lineStyle: LineStyle.Dashed,
              lastValueVisible: false,
              priceLineVisible: false,
              crosshairMarkerVisible: false,
            });
            bound.setData([
              { time: t0, value: price },
              { time: t1, value: price },
            ]);
            overlaySeriesRef.current.push(bound);
          }
        }
      }
    }

    createSeriesMarkers(candleSeries, markers);
  }, [structures, candles]);

  return <div ref={containerRef} className="h-full w-full" />;
}