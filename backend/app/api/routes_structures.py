"""
Candle and structure-detection routes — raw candle data plus the ABCDE
structure detection results for a given symbol.
"""

from fastapi import APIRouter

from app.data.cache_store import candle_cache
from app.engine.entry_zone import calculate_entry_zone
from app.engine.structure_manager import DetectionConfig, detect_structures, to_dict

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
