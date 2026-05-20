from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from deepreflect.api.routes import analyze, flashcards, graph, ingest, settings, summary
from deepreflect.api.routes import notifications
from deepreflect.config import ensure_dirs, load_config

log = logging.getLogger(__name__)

_FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"


async def _warn_if_notifications_image_deps_missing() -> None:
    """Log once at startup if Playwright Chromium is not installed."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log.warning(
            "Notifications: playwright not installed — run: uv run deepreflect setup-notifications"
        )
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
    except Exception:
        log.warning(
            "Notifications: Chromium not found — run: uv run deepreflect setup-notifications"
        )


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Start APScheduler on startup, shut it down on exit."""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from deepreflect.notifications.scheduler import setup_notification_jobs

        cfg = load_config()
        scheduler = AsyncIOScheduler()
        setup_notification_jobs(scheduler, cfg)
        scheduler.start()
        app.state.scheduler = scheduler
        log.info("Scheduler started.")
        await _warn_if_notifications_image_deps_missing()
    except ImportError:
        log.warning("apscheduler not installed — notifications disabled.")
        app.state.scheduler = None

    yield

    scheduler = getattr(app.state, "scheduler", None)
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        log.info("Scheduler stopped.")


def create_app() -> FastAPI:
    cfg = load_config()
    ensure_dirs(cfg)

    app = FastAPI(
        title="DeepReflect",
        description="Local AI learning memory agent",
        version="0.1.0",
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:7733"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(ingest.router, prefix="/api")
    app.include_router(analyze.router, prefix="/api")
    app.include_router(graph.router, prefix="/api")
    app.include_router(summary.router, prefix="/api")
    app.include_router(flashcards.router, prefix="/api")
    app.include_router(settings.router, prefix="/api")
    app.include_router(notifications.router, prefix="/api")

    # Serve compiled React build if it exists
    if _FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")

    return app


app = create_app()
