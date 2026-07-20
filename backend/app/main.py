"""
FastAPI entrypoint. Starts the background data-fetcher on boot and wires
up the route modules from app/api/. Route logic itself lives in
app/api/routes_symbols.py and app/api/routes_structures.py — this file
only handles app setup, lifespan, and middleware.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_structures import router as structures_router
from app.api.routes_symbols import router as symbols_router
from app.api.ws_live import router as ws_router
from app.core.config import validate_settings
from app.data.fetcher_worker import run_fetcher_loop

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

app.include_router(symbols_router)
app.include_router(structures_router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
