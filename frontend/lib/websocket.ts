import type { StructureQuery } from "./api";
import type { WsUpdateMessage } from "./types";

// Derived from NEXT_PUBLIC_API_BASE — turns http(s):// into ws(s)://.
// Set NEXT_PUBLIC_WS_BASE explicitly instead if the WebSocket is served
// from a different host than the REST API.
function wsBase(): string {
  if (process.env.NEXT_PUBLIC_WS_BASE) {
    return process.env.NEXT_PUBLIC_WS_BASE.replace(/\/$/, "");
  }
  const apiBase =
    process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8000";
  return apiBase.replace(/^http/, "ws");
}

export interface StructureStreamHandle {
  socket: WebSocket;
  close: () => void;
}

/**
 * Opens a WebSocket to backend/app/api/ws_live.py for one symbol and calls
 * onMessage with every "update" push. Mirrors the same strategy /
 * swing_lookback / touch_mode / e_target query params as getStructures().
 */
export function connectStructureStream(
  symbol: string,
  query: StructureQuery,
  onMessage: (msg: WsUpdateMessage) => void,
  onError?: (ev: Event) => void
): StructureStreamHandle {
  const params = new URLSearchParams();
  if (query.strategy) params.set("strategy", query.strategy);
  if (query.swing_lookback !== undefined)
    params.set("swing_lookback", String(query.swing_lookback));
  if (query.touch_mode) params.set("touch_mode", query.touch_mode);
  if (query.e_target) params.set("e_target", query.e_target);

  const qs = params.toString();
  const url = `${wsBase()}/ws/${encodeURIComponent(symbol)}${qs ? `?${qs}` : ""}`;
  const socket = new WebSocket(url);

  socket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data) as WsUpdateMessage;
      onMessage(msg);
    } catch {
      // Ignore malformed frames rather than crashing the UI.
    }
  };
  if (onError) socket.onerror = onError;

  return {
    socket,
    close: () => socket.close(),
  };
}