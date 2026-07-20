import type {
  CandlesResponse,
  ETarget,
  Strategy,
  StructuresResponse,
  SymbolsResponse,
  TouchMode,
} from "./types";

// Set NEXT_PUBLIC_API_BASE in .env.local / Vercel project settings, e.g.
// NEXT_PUBLIC_API_BASE=https://quantx-backend.onrender.com
// Falls back to localhost for local `uvicorn` development.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function getSymbols(): Promise<SymbolsResponse> {
  return getJson<SymbolsResponse>("/symbols");
}

export async function addSymbol(symbol: string): Promise<SymbolsResponse> {
  const res = await fetch(`${API_BASE}/symbols/${encodeURIComponent(symbol)}`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`POST /symbols/${symbol} failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<SymbolsResponse>;
}

export function getCandles(symbol: string): Promise<CandlesResponse> {
  return getJson<CandlesResponse>(`/candles/${encodeURIComponent(symbol)}`);
}

export interface StructureQuery {
  strategy?: Strategy;
  swing_lookback?: number;
  touch_mode?: TouchMode;
  e_target?: ETarget;
}

export function getStructures(
  symbol: string,
  query: StructureQuery = {}
): Promise<StructuresResponse> {
  const params = new URLSearchParams();
  if (query.strategy) params.set("strategy", query.strategy);
  if (query.swing_lookback !== undefined)
    params.set("swing_lookback", String(query.swing_lookback));
  if (query.touch_mode) params.set("touch_mode", query.touch_mode);
  if (query.e_target) params.set("e_target", query.e_target);

  const qs = params.toString();
  return getJson<StructuresResponse>(
    `/structures/${encodeURIComponent(symbol)}${qs ? `?${qs}` : ""}`
  );
}