"""
In-memory candle cache — the core of the "fetch once, serve to unlimited
users" pattern described in docs/strategy-guide.md.

The background worker (fetcher_worker.py) is the ONLY thing that writes here.
API routes and the WebSocket broadcaster only read. This keeps every website
visitor served from one shared cache instead of each triggering their own
TwelveData request.

NOTE: this is a single-process in-memory store — fine for one Render
instance. If you later scale to multiple backend instances, swap this for
Redis (same get/set interface) so all instances share one cache.
"""

import asyncio

from app.models.schemas import Candle


class CandleCache:
    def __init__(self):
        self._store: dict[str, list[Candle]] = {}
        self._last_updated: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def set_candles(self, symbol: str, candles: list[Candle]) -> None:
        async with self._lock:
            self._store[symbol] = candles
            import time
            self._last_updated[symbol] = time.time()

    async def get_candles(self, symbol: str) -> list[Candle]:
        async with self._lock:
            return list(self._store.get(symbol, []))

    async def last_updated(self, symbol: str) -> float | None:
        async with self._lock:
            return self._last_updated.get(symbol)

    async def tracked_symbols(self) -> list[str]:
        async with self._lock:
            return list(self._store.keys())


candle_cache = CandleCache()
