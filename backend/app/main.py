"""Rasa backend — FastAPI app entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import checkins, dashboard, debrief, recordings
from .store import store

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rasa")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    backend = await store.init()
    log.info("storage backend: %s", backend)
    log.info("emotion provider: %s", settings.emotion_provider)
    yield
    await store.close()


app = FastAPI(title="Rasa", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()
app.mount("/media", StaticFiles(directory=str(settings.media_path)), name="media")

app.include_router(checkins.router)
app.include_router(recordings.router)
app.include_router(dashboard.router)
app.include_router(debrief.router)


@app.get("/health")
async def health():
    return {"ok": True, "storage": store.backend, "emotion_provider": settings.emotion_provider}


WEB_DIR = Path(__file__).resolve().parent / "web"


@app.get("/", include_in_schema=False)
async def web_app():
    return FileResponse(WEB_DIR / "index.html")
