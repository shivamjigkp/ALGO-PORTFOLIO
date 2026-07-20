# ABCDE Reversal Structure — Live Trading Platform

A pure price-action liquidity-sweep reversal detection system for Forex & Metals, running as a full-stack web platform — real-time data, structure detection, and a live dashboard.

Originally built and validated as a TradingView Pine Script v5 indicator (now ported to Python), it identifies a 5-point **A–B–C–D–E** liquidity sweep pattern that precedes trend reversals, and marks a defined entry zone once the pattern completes. No oscillators, no moving averages — purely swing-point and liquidity based.

📖 **Full strategy mechanics, rules, and edge cases:** [`docs/strategy-guide.md`](docs/strategy-guide.md)

---

## What It Does

- Detects the ABCDE structure independently in two directions:
  - **Upside** — SELL reversal signal in a downtrend
  - **Downside** — BUY reversal signal in an uptrend
- Tracks unlimited symbols in parallel (any Forex pair or Metal — e.g., XAUUSD, XAGUSD, EURUSD)
- Tracks multiple structures per symbol simultaneously, each independently validated/invalidated
- Renders live on a web dashboard — chart with A/B/C/D/E markings, entry zone, and the optional E2 extension point
- Broadcasts live updates to unlimited users via WebSocket, backed by a single cached data feed

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python (FastAPI), deployed on Render |
| Frontend | Next.js (React), deployed on Vercel |
| Market Data | TwelveData (free tier — Forex & Metals) |
| Realtime | WebSocket |
| Charting | TradingView Lightweight Charts |

## Repository Structure

```
backend/     → FastAPI service: data fetching, ABCDE detection engine, WebSocket API
frontend/    → Next.js dashboard: live charts, symbol selector, signal list
docs/        → Full strategy guide + reference images
```

See [`docs/strategy-guide.md`](docs/strategy-guide.md) for complete pattern rules, and the `backend/` and `frontend/` folders for setup instructions.

## Disclaimer

This project is a technical pattern-recognition and charting tool. It does not constitute financial advice and does not guarantee profitable outcomes. Use appropriate risk management, and consult a licensed financial advisor before trading live capital.

## License

MIT — see [`LICENSE`](LICENSE).
