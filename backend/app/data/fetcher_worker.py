"""
Background loop — the piece that makes "unlimited website users, one API key"
actually work.

For each tracked symbol, this worker:
  1. fetches fresh candles from TwelveData (rate-limited automatically by
     TwelveDataClient's RateLimiter)
  2. writes them into the shared CandleCache
  3. sleeps, then repeats

Website users never trigger a TwelveData call themselves — they only ever
read from CandleCache via the REST/WebSocket routes. This is what keeps a
free 800-request/day plan viable no matter how many people are on the site.

Run this as a long-lived asyncio task started from main.py's startup event —
Render's web service keeps the process alive, so this loop runs continuously
alongside the FastAPI app.
"""

import asyncio
import logging

from app.core.config import settings
from app.core.symbol_registry import symbol_registry
from app.data.cache_store import candle_cache
from app.data.twelvedata_client import twelvedata_client

logger = logging.getLogger("fetcher_worker")


async def _fetch_one(symbol: str) -> None:
    try:
        candles = await twelvedata_client.fetch_candles(symbol)
        if candles:
            await candle_cache.set_candles(symbol, candles)
            logger.info("Updated %s — %d candles cached", symbol, len(candles))
    except Exception as exc:
        # A single symbol failing (e.g. bad ticker, transient API error)
        # should never take down the whole worker loop.
        logger.warning("Failed to fetch %s: %s", symbol, exc)


async def run_fetcher_loop() -> None:
    """
    Fetches every tracked symbol once, waits `poll_interval_seconds`, repeats.
    Symbols are fetched sequentially (not with asyncio.gather) so the shared
    RateLimiter naturally spaces out requests across the whole minute instead
    of bursting all of them at once.
    """
    logger.info("Fetcher worker started — polling every %ss", settings.poll_interval_seconds)
    while True:
        symbols = await symbol_registry.list()
        for symbol in symbols:
            await _fetch_one(symbol)
        await asyncio.sleep(settings.poll_interval_seconds)
