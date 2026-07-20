"""
Candle and structure-detection routes — raw candle data plus the ABCDE
structure detection results for a given symbol.
"""

from fastapi import APIRouter

from app.data.cache_store import candle_cache
from app.engine.structure_manager import build_structures_payload

router = APIRouter(tags=["structures"])


@router.get("/candles/{symbol}")
async def get_candles(symbol: str):
    candles = await candle_cache.get_candles(symbol)
    updated = await candle_cache.last_updated(symbol)
    return {
        "symbol": symbol,
        "last_updated": updated,
        "count": len(candles),
        "candles": [c.__dict__ for c in candles],
    }


@router.get("/structures/{symbol}")
async def get_structures(
    symbol: str,
    strategy: str = "both",       # "upside" | "downside" | "both"
    swing_lookback: int = 5,
    touch_mode: str = "wick",     # "wick" | "close" | "both"
    e_target: str = "A_OR_C",     # "A" | "C" | "A_OR_C"
):
    candles = await candle_cache.get_candles(symbol)
    if not candles:
        return {"symbol": symbol, "structures": []}

    results = build_structures_payload(
        candles,
        strategy=strategy,
        swing_lookback=swing_lookback,
        touch_mode=touch_mode,
        e_target=e_target,
    )

    return {"symbol": symbol, "count": len(results), "structures": results}
