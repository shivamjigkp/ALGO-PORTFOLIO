"""
Symbol management routes — list active symbols, add a new one to track.
"""

from fastapi import APIRouter

from app.core.symbol_registry import symbol_registry

router = APIRouter(tags=["symbols"])


@router.get("/symbols")
async def list_symbols():
    return {"symbols": await symbol_registry.list()}


@router.post("/symbols/{symbol}")
async def add_symbol(symbol: str):
    await symbol_registry.add(symbol)
    return {"symbols": await symbol_registry.list()}
