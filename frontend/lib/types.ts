// Mirrors backend/app/models/schemas.py and structure_manager.to_dict /
// build_structures_payload — keep these in sync with the backend response
// shape, they are not independently guessed.

export type Direction = "upside" | "downside";
export type Strategy = "upside" | "downside" | "both";
export type TouchMode = "wick" | "close" | "both";
export type ETarget = "A" | "C" | "A_OR_C";

export interface Candle {
  timestamp: number; // unix epoch seconds, UTC
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface Point {
  index: number;
  price: number;
}

export interface Zone {
  top: number;
  bottom: number;
  start_index: number;
  end_index: number;
}

export interface StructureItem {
  id: number;
  direction: Direction;
  stage: string; // enum name, e.g. "AWAITING_B"
  stage_display: string; // human label, e.g. "Awaiting B" / "ABCDE"
  a: Point | null;
  b: Point | null;
  c: Point | null;
  d: Point | null;
  e: Point | null;
  entry_zone: Zone | null;
  e2: Point | null;
  e2_zone: Zone | null;
}

export interface CandlesResponse {
  symbol: string;
  last_updated: number | null;
  count: number;
  candles: Candle[];
}

export interface StructuresResponse {
  symbol: string;
  count: number;
  structures: StructureItem[];
}

export interface SymbolsResponse {
  symbols: string[];
}

export interface WsUpdateMessage {
  type: "update";
  symbol: string;
  last_updated: number;
  count: number;
  structures: StructureItem[];
}