import sqlite3
from contextlib import asynccontextmanager

import beets
import beets.library
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.routers import albums, items, playback, library, import_ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load beets config
    beets.config.read(user=True, defaults=True)

    # Open beets Library (used for writes and complex queries)
    lib = beets.library.Library(settings.beets_db_path)
    app.state.lib = lib

    # Open a separate read-only SQLite connection (used for fast read queries)
    db = sqlite3.connect(
        f"file:{settings.beets_db_path}?mode=ro",
        uri=True,
        check_same_thread=False,
    )
    db.row_factory = sqlite3.Row
    app.state.db = db

    yield

    db.close()
    lib._close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Beets Web",
        description="Web GUI for the beets music library manager",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(albums.router, prefix="/api/albums", tags=["albums"])
    app.include_router(items.router, prefix="/api/items", tags=["items"])
    app.include_router(playback.router, prefix="/api/stream", tags=["playback"])
    app.include_router(library.router, prefix="/api/library", tags=["library"])
    # WebSocket endpoint lives at /ws/import — no prefix so the path is verbatim.
    app.include_router(import_ws.router, tags=["import"])

    # Serve built Vue SPA from frontend/dist in production.
    # Static assets (/assets/*) are served directly; everything else falls
    # through to index.html so Vue Router handles client-side navigation.
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str) -> FileResponse:
            # Serve any exact file that exists (favicon.ico, etc.)
            candidate = frontend_dist / full_path
            if candidate.exists() and candidate.is_file():
                return FileResponse(str(candidate))
            # Fall back to index.html for all SPA routes
            index = frontend_dist / "index.html"
            if index.exists():
                return FileResponse(str(index))
            raise HTTPException(status_code=404, detail="Frontend not built")

    return app


app = create_app()
