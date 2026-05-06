from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from deepreflect.api.routes import analyze, flashcards, graph, ingest, summary
from deepreflect.config import ensure_dirs, load_config

_FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    cfg = load_config()
    ensure_dirs(cfg)

    app = FastAPI(
        title="DeepReflect",
        description="Local AI learning memory agent",
        version="0.1.0",
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

    # Serve compiled React build if it exists
    if _FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")

    return app


app = create_app()
