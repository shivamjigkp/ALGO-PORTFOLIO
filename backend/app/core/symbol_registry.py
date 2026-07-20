"""
Tracks which symbols are currently active — this is what makes the platform
generic instead of hardcoded to Gold. Add/remove here, and the background
fetcher + detection engine pick it up automatically on the next cycle.
"""

import asyncio

from app.core.config import settings


class SymbolRegistry:
    def __init__(self):
        self._symbols: set[str] = set(settings.default_symbols)
        self._lock = asyncio.Lock()

    @staticmethod
    def _normalize(symbol: str) -> str:
        """Accepts 'XAUUSD', 'xauusd', or 'XAU/USD' and returns TwelveData's 'XAU/USD' format."""
        symbol = symbol.strip().upper()
        if "/" in symbol:
            return symbol
        if len(symbol) == 6:
            return f"{symbol[:3]}/{symbol[3:]}"
        return symbol

    async def add(self, symbol: str) -> None:
        symbol = self._normalize(symbol)
        async with self._lock:
            self._symbols.add(symbol)

    async def remove(self, symbol: str) -> None:
        async with self._lock:
            self._symbols.discard(symbol)

    async def list(self) -> list[str]:
        async with self._lock:
            return sorted(self._symbols)


symbol_registry = SymbolRegistry()
