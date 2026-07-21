"""
Thin async client around TwelveData's REST API.

Handles:
  - building the correct request for OHLC candles
  - a simple sliding-window rate limiter so we never exceed the free-plan cap
  - basic error handling (TwelveData returns HTTP 200 even on errors, with
    {"status": "error", ...} in the body — we check for that explicitly)
"""

import asyncio
import time
from collections import deque

import httpx

from app.core.config import settings
from app.models.schemas import Candle


def _dedupe_and_sort(candles: list[Candle]) -> list[Candle]:
    """
    TwelveData occasionally returns a repeated bar with an identical
    timestamp for continuously-traded instruments like Gold/Silver, usually
    around the daily session rollover. Charting libraries (and our own
    swing/structure detection, which assumes strictly increasing bar
    indices) require unique, ascending timestamps — so we enforce that here,
    once, at the source, rather than downstream in every consumer.

    Keeps the LAST candle seen for any given timestamp (the more complete
    one if TwelveData is correcting a partial bar), then sorts ascending.
    """
    by_timestamp: dict[int, Candle] = {}
    for c in candles:
        by_timestamp[c.timestamp] = c
    return [by_timestamp[ts] for ts in sorted(by_timestamp)]


class RateLimiter:
    """
    Sliding-window limiter: allows at most `max_calls` requests within any
    rolling `period_seconds` window. Shared across all symbols since TwelveData
    rate-limits per API key, not per symbol.
    """

    def __init__(self, max_calls: int, period_seconds: float):
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self._calls: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            while self._calls and now - self._calls[0] > self.period_seconds:
                self._calls.popleft()

            if len(self._calls) >= self.max_calls:
                wait_time = self.period_seconds - (now - self._calls[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            self._calls.append(time.monotonic())


class TwelveDataClient:
    def __init__(self):
        self._rate_limiter = RateLimiter(
            max_calls=settings.max_requests_per_minute,
            period_seconds=60,
        )
        self._client = httpx.AsyncClient(
            base_url=settings.twelvedata_base_url,
            timeout=15,
        )

    async def fetch_candles(
        self,
        symbol: str,
        interval: str = None,
        outputsize: int = None,
    ) -> list[Candle]:
        """
        Fetches the most recent OHLC candles for a symbol.
        `symbol` should be TwelveData format, e.g. "XAU/USD", "EUR/USD".
        """
        await self._rate_limiter.acquire()

        params = {
            "symbol": symbol,
            "interval": interval or settings.default_interval,
            "outputsize": outputsize or settings.candles_per_fetch,
            "apikey": settings.twelvedata_api_key,
            "order": "ASC",
        }

        response = await self._client.get("/time_series", params=params)
        response.raise_for_status()
        payload = response.json()

        if payload.get("status") == "error":
            raise RuntimeError(
                f"TwelveData error for {symbol}: {payload.get('message', 'unknown error')}"
            )

        rows = payload.get("values", [])
        candles = [Candle.from_twelvedata_row(row) for row in rows]
        return _dedupe_and_sort(candles)

    async def close(self) -> None:
        await self._client.aclose()


# Single shared instance — the rate limiter must be shared across every
# symbol fetch, so this should not be re-instantiated per request.
twelvedata_client = TwelveDataClient()
