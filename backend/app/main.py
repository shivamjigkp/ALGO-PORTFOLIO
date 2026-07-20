"""
FastAPI entrypoint. Starts the background data-fetcher on boot and exposes
basic routes to inspect the live cache — full detection-engine routes will
be added in app/api/ in the next step.
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import validate_settings
from app.core.symbol_registry import symbol_registry
from app.data.cache_store import candle_cache
from app.data.fetcher_worker import run_fetcher_loop
from app.engine.entry_zone import calculate_entry_zone
from app.engine.structure_manager import DetectionConfig, detect_structures, to_dict

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_settings()
    worker_task = asyncio.create_task(run_fetcher_loop())
    yield
    worker_task.cancel()


app = FastAPI(title="QuantX — ABCDE Backend", lifespan=lifespan)

# Allow the Vercel-hosted frontend to call this API. Tighten this to your
# exact frontend domain before going to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/symbols")
async def list_symbols():
    return {"symbols": await symbol_registry.list()}


@app.post("/symbols/{symbol}")
async def add_symbol(symbol: str):
    await symbol_registry.add(symbol)
    return {"symbols": await symbol_registry.list()}


@app.get("/candles/{symbol}")
async def get_candles(symbol: str):
    candles = await candle_cache.get_candles(symbol)
    updated = await candle_cache.last_updated(symbol)
    return {
        "symbol": symbol,
        "last_updated": updated,
        "count": len(candles),
        "candles": [c.__dict__ for c in candles],
    }


@app.get("/structures/{symbol}")
async def get_structures(
    symbol: str,
    strategy: str = "both",       # "upside" | "downside" | "both" — matches the dashboard's strategy selector
    swing_lookback: int = 5,
    touch_mode: str = "wick",     # "wick" | "close" | "both"
    e_target: str = "A_OR_C",     # "A" | "C" | "A_OR_C"
):
    candles = await candle_cache.get_candles(symbol)
    if not candles:
        return {"symbol": symbol, "structures": []}

    directions = ["upside", "downside"] if strategy == "both" else [strategy]
    results = []

    for direction in directions:
        cfg = DetectionConfig(
            direction=direction,
            swing_lookback=swing_lookback,
            touch_mode=touch_mode,
            e_liquidity_target=e_target,
        )
        structures = detect_structures(candles, cfg)
        for s in structures:
            entry = calculate_entry_zone(s, direction) if s.stage_name() == "ABCDE" else None
            item = to_dict(s)
            item["entry_zone"] = (
                {"top": entry.top, "bottom": entry.bottom, "start_index": entry.start_index, "end_index": entry.end_index}
                if entry else None
            )
            results.append(item)

    return {"symbol": symbol, "count": len(results), "structures": results}
