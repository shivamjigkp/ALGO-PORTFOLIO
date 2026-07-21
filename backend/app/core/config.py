"""
Central configuration for the QuantX backend.
Reads all secrets and tunables from environment variables (.env in local dev,
Render's "Environment" tab in production) — nothing sensitive is hardcoded.
"""

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    # --- TwelveData ---
    twelvedata_api_key: str = field(
        default_factory=lambda: os.environ.get("TWELVEDATA_API_KEY", "")
    )
    twelvedata_base_url: str = "https://api.twelvedata.com"

    # Free (Basic) plan limits — see docs/strategy-guide.md for rationale.
    # We stay comfortably under these so requests never get throttled.
    max_requests_per_minute: int = 7          # actual cap is 8/min
    max_requests_per_day: int = 750           # actual cap is 800/day

    # --- Default symbol universe (Forex + Metals) ---
    default_symbols: tuple = (
        "XAU/USD",   # Gold
        "XAG/USD",   # Silver
        "EUR/USD",   # Euro
        "GBP/USD",   # British Pound
       
    )

    # --- Candle fetch settings ---
    default_interval: str = "15min"           # matches Pine Script default feel
    candles_per_fetch: int = 200               # enough history for swing detection
    poll_interval_seconds: int = 60            # how often the background worker refreshes each symbol

    # --- Swing/structure defaults (mirrors Pine Script inputs) ---
    default_swing_lookback: int = 5


settings = Settings()


def validate_settings() -> None:
    """Call this once on startup — fails loudly instead of silently returning empty data."""
    if not settings.twelvedata_api_key:
        raise RuntimeError(
            "TWELVEDATA_API_KEY is not set. "
            "Add it to your .env file locally, or to Render's Environment tab in production."
        )
