"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import StructureChart from "@/components/StructureChart";
import Sidebar from "@/components/Sidebar";
import TickerBar from "@/components/TickerBar";
import SignalFeed from "@/components/SignalFeed";
import StatusBar from "@/components/StatusBar";
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
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  const streamRef = useRef<StructureStreamHandle | null>(null);

  const query: StructureQuery = {
    strategy,
    swing_lookback: swingLookback,
    touch_mode: touchMode,
    e_target: eTarget,
  };

  // Load symbol list once. If the backend has no symbols tracked yet
  // (fresh deploy, empty registry), seed one default so the dashboard is
  // never blank on first load.
  useEffect(() => {
    getSymbols()
      .then(async (res) => {
        if (res.symbols.length > 0) {
          setSymbols(res.symbols);
          setSymbol(res.symbols[0]);
          return;
        }
        try {
          const seeded = await addSymbol("XAU/USD");
          setSymbols(seeded.symbols);
          if (seeded.symbols.length > 0) setSymbol(seeded.symbols[0]);
        } catch (e) {
          setError(String(e));
        }
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
        setLastUpdated(candlesRes.last_updated);
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
        setLastUpdated(msg.last_updated);
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

  const lastClose = candles.length > 0 ? candles[candles.length - 1].close : null;
  const prevClose = candles.length > 1 ? candles[candles.length - 2].close : null;
  const delta = lastClose !== null && prevClose !== null ? lastClose - prevClose : null;
  const activeStructureCount = structures.filter((s) => s.stage_display !== "CANCELLED").length;

  return (
    <div className="flex flex-col min-h-screen">
      <TickerBar symbols={symbols} activeSymbol={symbol} onSelect={setSymbol} />

      <div className="shell">
        <Sidebar
          symbols={symbols}
          activeSymbol={symbol}
          activeSymbolPrice={lastClose}
          activeStructureCount={activeStructureCount}
          newSymbol={newSymbol}
          onNewSymbolChange={setNewSymbol}
          onSelect={setSymbol}
          onAddSymbol={handleAddSymbol}
        />

        <div className="main">
          {error && (
            <div
              style={{
                marginBottom: 12,
                padding: "8px 12px",
                border: "1px solid var(--hairline)",
                borderRadius: 4,
                color: "var(--sell)",
                fontSize: 12,
              }}
            >
              {error}
            </div>
          )}

          <div className="main-head">
            <div className="pair">
              {symbol || "No symbol selected"}
              {symbol && strategy !== "both" && (
                <span className="direction">
                  {strategy === "upside" ? "Upside · Sell setup" : "Downside · Buy setup"}
                </span>
              )}
            </div>
            {lastClose !== null && (
              <div className="price mono">
                {lastClose.toFixed(4)}
                {delta !== null && (
                  <span className={`delta ${delta >= 0 ? "up" : "down"}`}>
                    {delta >= 0 ? "+" : ""}
                    {delta.toFixed(4)}
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="tf-row">
            <div className="strategy-row">
              <div className="strategy-category">
                <span className="strategy-cat-label">Strategy</span>
              </div>
              <div className="strategy-group">
                <button
                  className={`strategy-btn up ${strategy === "upside" ? "active" : ""}`}
                  onClick={() => setStrategy("upside")}
                >
                  <span className="swatch" />
                  Upside · Sell
                </button>
                <button
                  className={`strategy-btn down ${strategy === "downside" ? "active" : ""}`}
                  onClick={() => setStrategy("downside")}
                >
                  <span className="swatch" />
                  Downside · Buy
                </button>
                <button
                  className={`strategy-btn both ${strategy === "both" ? "active" : ""}`}
                  onClick={() => setStrategy("both")}
                >
                  <span className="swatch" />
                  Both
                </button>
              </div>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                fontSize: 12,
                color: "var(--text-dim)",
              }}
            >
              <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
                Swing
                <input
                  type="number"
                  min={1}
                  value={swingLookback}
                  onChange={(e) => setSwingLookback(Number(e.target.value) || 1)}
                  style={{
                    width: 50,
                    background: "var(--panel-alt)",
                    border: "1px solid var(--hairline)",
                    color: "var(--foreground)",
                    borderRadius: 3,
                    padding: "3px 6px",
                  }}
                />
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
                Touch
                <select
                  value={touchMode}
                  onChange={(e) => setTouchMode(e.target.value as TouchMode)}
                  style={{
                    background: "var(--panel-alt)",
                    border: "1px solid var(--hairline)",
                    color: "var(--foreground)",
                    borderRadius: 3,
                    padding: "3px 6px",
                  }}
                >
                  {TOUCH_MODES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
                E Target
                <select
                  value={eTarget}
                  onChange={(e) => setETarget(e.target.value as ETarget)}
                  style={{
                    background: "var(--panel-alt)",
                    border: "1px solid var(--hairline)",
                    color: "var(--foreground)",
                    borderRadius: 3,
                    padding: "3px 6px",
                  }}
                >
                  {E_TARGETS.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          <div className="chart-frame" style={{ position: "relative" }}>
            {loading && (
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  zIndex: 10,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: "rgba(13,17,23,0.6)",
                  fontSize: 13,
                  color: "var(--text-dim)",
                }}
              >
                Loading…
              </div>
            )}
            {symbol ? (
              <StructureChart candles={candles} structures={structures} />
            ) : (
              <div
                style={{
                  flex: 1,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 13,
                  color: "var(--text-dim)",
                }}
              >
                Add a symbol to begin
              </div>
            )}
            <div className="legend">
              <span>
                <i style={{ background: "var(--sell-blue)" }} />
                Cycle 0 — Upside
              </span>
              <span>
                <i style={{ background: "var(--brass)", opacity: 0.5 }} />
                Entry zone
              </span>
              <span>
                <i style={{ background: "var(--text-muted)" }} />
                Forming structure
              </span>
            </div>
          </div>
        </div>

        <SignalFeed symbol={symbol} structures={structures} connected={connected} />
      </div>

      <StatusBar
        connected={connected}
        symbolsCount={symbols.length}
        activeStructuresCount={activeStructureCount}
        lastUpdated={lastUpdated}
      />
    </div>
  );
}