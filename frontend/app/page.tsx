"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import StructureChart from "@/components/StructureChart";
import {
  addSymbol,
  getCandles,
  getStructures,
  getSymbols,
  type StructureQuery,
} from "@/lib/api";
import { connectStructureStream, type StructureStreamHandle } from "@/lib/websocket";
import type {
  Candle,
  ETarget,
  Strategy,
  StructureItem,
  TouchMode,
} from "@/lib/types";

const STRATEGIES: Strategy[] = ["both", "upside", "downside"];
const TOUCH_MODES: TouchMode[] = ["wick", "close", "both"];
const E_TARGETS: ETarget[] = ["A_OR_C", "A", "C"];

export default function Home() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [symbol, setSymbol] = useState<string>("");
  const [newSymbol, setNewSymbol] = useState("");

  const [strategy, setStrategy] = useState<Strategy>("both");
  const [swingLookback, setSwingLookback] = useState(5);
  const [touchMode, setTouchMode] = useState<TouchMode>("wick");
  const [eTarget, setETarget] = useState<ETarget>("A_OR_C");

  const [candles, setCandles] = useState<Candle[]>([]);
  const [structures, setStructures] = useState<StructureItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);

  const streamRef = useRef<StructureStreamHandle | null>(null);

  const query: StructureQuery = {
    strategy,
    swing_lookback: swingLookback,
    touch_mode: touchMode,
    e_target: eTarget,
  };

  // Load symbol list once.
  useEffect(() => {
    getSymbols()
      .then((res) => {
        setSymbols(res.symbols);
        if (res.symbols.length > 0) setSymbol(res.symbols[0]);
      })
      .catch((e) => setError(String(e)));
  }, []);

  // Initial fetch whenever symbol or query params change.
  useEffect(() => {
    if (!symbol) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([getCandles(symbol), getStructures(symbol, query)])
      .then(([candlesRes, structuresRes]) => {
        if (cancelled) return;
        setCandles(candlesRes.candles);
        setStructures(structuresRes.structures);
      })
      .catch((e) => !cancelled && setError(String(e)))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, strategy, swingLookback, touchMode, eTarget]);

  // Live updates over WebSocket, reconnects whenever symbol/query changes.
  useEffect(() => {
    if (!symbol) return;

    streamRef.current?.close();
    setConnected(false);

    const handle = connectStructureStream(
      symbol,
      query,
      (msg) => {
        setStructures(msg.structures);
        getCandles(symbol)
          .then((res) => setCandles(res.candles))
          .catch(() => {});
        setConnected(true);
      },
      () => setConnected(false)
    );
    streamRef.current = handle;

    return () => handle.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, strategy, swingLookback, touchMode, eTarget]);

  const handleAddSymbol = useCallback(async () => {
    const s = newSymbol.trim().toUpperCase();
    if (!s) return;
    try {
      const res = await addSymbol(s);
      setSymbols(res.symbols);
      setSymbol(s);
      setNewSymbol("");
    } catch (e) {
      setError(String(e));
    }
  }, [newSymbol]);

  return (
    <div className="flex flex-col flex-1 min-h-screen">
      <header className="flex flex-wrap items-center gap-3 border-b border-border bg-panel px-4 py-3">
        <span className="font-mono text-sm text-accent tracking-wide">QuantX</span>

        <select
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          className="rounded border border-border bg-panel-alt px-2 py-1 text-sm text-foreground"
        >
          {symbols.length === 0 && <option value="">No symbols</option>}
          {symbols.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <div className="flex items-center gap-1">
          <input
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddSymbol()}
            placeholder="Add symbol"
            className="w-28 rounded border border-border bg-panel-alt px-2 py-1 text-sm text-foreground placeholder:text-text-faint"
          />
          <button
            onClick={handleAddSymbol}
            className="rounded border border-border px-2 py-1 text-sm text-text-dim hover:text-accent"
          >
            Add
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs text-text-dim ml-auto">
          <label className="flex items-center gap-1">
            Strategy
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value as Strategy)}
              className="rounded border border-border bg-panel-alt px-1 py-0.5 text-foreground"
            >
              {STRATEGIES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>

          <label className="flex items-center gap-1">
            Swing
            <input
              type="number"
              min={1}
              value={swingLookback}
              onChange={(e) => setSwingLookback(Number(e.target.value) || 1)}
              className="w-14 rounded border border-border bg-panel-alt px-1 py-0.5 text-foreground"
            />
          </label>

          <label className="flex items-center gap-1">
            Touch
            <select
              value={touchMode}
              onChange={(e) => setTouchMode(e.target.value as TouchMode)}
              className="rounded border border-border bg-panel-alt px-1 py-0.5 text-foreground"
            >
              {TOUCH_MODES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>

          <label className="flex items-center gap-1">
            E Target
            <select
              value={eTarget}
              onChange={(e) => setETarget(e.target.value as ETarget)}
              className="rounded border border-border bg-panel-alt px-1 py-0.5 text-foreground"
            >
              {E_TARGETS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>

          <span
            className={`ml-2 h-2 w-2 rounded-full ${
              connected ? "bg-buy" : "bg-text-faint"
            }`}
            title={connected ? "Live" : "Not connected"}
          />
        </div>
      </header>

      {error && (
        <div className="border-b border-border bg-sell/10 px-4 py-2 text-xs text-sell">
          {error}
        </div>
      )}

      <main className="relative flex-1">
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/60 text-sm text-text-dim">
            Loading…
          </div>
        )}
        {symbol ? (
          <StructureChart candles={candles} structures={structures} />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-text-dim">
            Add a symbol to begin
          </div>
        )}
      </main>
    </div>
  );
}
