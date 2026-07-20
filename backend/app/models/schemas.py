"""Shared data models used across the fetcher, cache, and detection engine."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Candle:
    """A single OHLC candle. Timestamp is Unix epoch seconds (UTC)."""
    timestamp: int
    open: float
    high: float
    low: float
    close: float

    @staticmethod
    def from_twelvedata_row(row: dict) -> "Candle":
        """Parses one row from TwelveData's /time_series response into a Candle."""
        import datetime

        dt = datetime.datetime.strptime(row["datetime"], "%Y-%m-%d %H:%M:%S")
        return Candle(
            timestamp=int(dt.replace(tzinfo=datetime.timezone.utc).timestamp()),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
        )
