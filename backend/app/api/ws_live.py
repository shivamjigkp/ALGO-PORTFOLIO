"""
Live updates over WebSocket — one connection per symbol, pushed every time
the background fetcher writes a fresh candle set for that symbol to
app/data/cache_store.py.

Reuses app.engine.structure_manager.build_structures_payload — the exact
same function routes_structures.py calls for the REST endpoint — so the
WebSocket feed and a manual GET /structures/{symbol} can never disagree.

Connect at: ws(s)://<host>/ws/{symbol}?strategy=both&swing_lookback=5&touch_mode=wick&e_target=A_OR_C
Same query params as GET /structures/{symbol}, same defaults.
"""

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.data.cache_store import candle_cache
from app.engine.structure_manager import build_structures_payload

logger = logging.getLogger(__name__)

router = APIRouter(tags=["live"])

# How often each connection checks the cache for a newer fetch. This is a
# cheap poll against in-memory data (not a new TwelveData call — the
# background worker in fetcher_worker.py owns that), so a short interval
# here just controls broadcast latency, not API usage.
POLL_INTERVAL_SECONDS = 2


@router.websocket("/ws/{symbol:path}")
async def stream_structures(
    websocket: WebSocket,
    symbol: str,
    strategy: str = "both",
    swing_lookback: int = 5,
    touch_mode: str = "wick",
    e_target: str = "A_OR_C",
):
    await websocket.accept()
    last_sent_update: float | None = None

    try:
        while True:
            updated = await candle_cache.last_updated(symbol)

            # Nothing new since the last push (or symbol not fetched yet at
            # all) — wait and check again rather than resending unchanged data.
            if updated is not None and updated != last_sent_update:
                candles = await candle_cache.get_candles(symbol)
                structures = build_structures_payload(
                    candles,
                    strategy=strategy,
                    swing_lookback=swing_lookback,
                    touch_mode=touch_mode,
                    e_target=e_target,
                )
                await websocket.send_json(
                    {
                        "type": "update",
                        "symbol": symbol,
                        "last_updated": updated,
                        "count": len(structures),
                        "structures": structures,
                    }
                )
                last_sent_update = updated

            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", symbol)
