import sqlite3
from contextlib import asynccontextmanager

import beets
import beets.library
import beets.ui
from beets import plugins
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.routers import albums, items, playback, library, import_ws
from app.routers.home import albums_router as home_albums_router, genres_router, playback_router as home_playback_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load beets config
    beets.config.read(user=True, defaults=True)

    # Ensure the musicbrainz metadata plugin is loaded so autotag lookups work.
    # In this version of beets, MusicBrainz is a plugin, not built-in core.
    plugins.load_plugins()
    loaded_names = {type(p).__name__.lower() for p in plugins.find_plugins()}
    if "musicbrainzplugin" not in loaded_names:
        from beets.plugins import _get_plugin, _instances
        mb_plugin = _get_plugin("musicbrainz")
        if mb_plugin is not None:
            _instances.append(mb_plugin)

    # Open beets Library (used for writes and complex queries).
    # Pass directory and path_formats explicitly from config so file operations
    # use the user's configured destination rather than the ~/Music default.
    lib = beets.library.Library(
        settings.beets_db_path,
        directory=beets.config["directory"].as_filename(),
        path_formats=beets.ui.get_path_formats(),
    )
    app.state.lib = lib

    # Open a separate read-only SQLite connection (used for fast read queries)
    db = sqlite3.connect(
        f"file:{settings.beets_db_path}?mode=ro",
        uri=True,
        check_same_thread=False,
    )
    db.row_factory = sqlite3.Row
    app.state.db = db

    # Ensure play_history table exists (write via rw connection)
    rw_db = sqlite3.connect(settings.beets_db_path, check_same_thread=False)
    try:
        rw_db.execute("""
            CREATE TABLE IF NOT EXISTS play_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                album_id INTEGER,
                played_at REAL NOT NULL,
                duration_played REAL NOT NULL
            )
        """)
        rw_db.commit()
    finally:
        rw_db.close()

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
        allow_origin_regex=r"https?://.*",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Home/discovery album endpoints must be registered BEFORE the main albums router
    # so /api/albums/recent etc. are matched before /api/albums/{album_id}
    app.include_router(home_albums_router, prefix="/api/albums", tags=["home"])
    app.include_router(albums.router, prefix="/api/albums", tags=["albums"])
    app.include_router(genres_router, prefix="/api/genres", tags=["home"])
    app.include_router(home_playback_router, prefix="/api/playback", tags=["home"])
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
            # Fall back to index.html for all SPA routes.
            # Must not be cached — Vite rebuilds produce new content-hashed chunk
            # filenames, so a stale cached index.html would reference non-existent
            # chunks and cause Vue Router lazy imports to silently fail.
            index = frontend_dist / "index.html"
            if index.exists():
                response = FileResponse(str(index))
                response.headers["Cache-Control"] = "no-cache, must-revalidate"
                return response
            raise HTTPException(status_code=404, detail="Frontend not built")

    return app


app = create_app()
