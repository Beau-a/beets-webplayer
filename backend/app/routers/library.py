"""
library.py — /api/library endpoints.

GET  /api/library/stats              — aggregate library statistics
GET  /api/library/facets             — distinct filter values for the UI
POST /api/library/import             — start an interactive import session
POST /api/library/tasks              — run a management task (mbsync/fetchart/lyrics)
GET  /api/library/tasks/{task_id}    — poll task status + output
"""

from __future__ import annotations

import sqlite3
import subprocess
import threading
import uuid
from pathlib import Path
from typing import Optional

import beets.library
from beets import dbcore
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from app.config import settings
from app.dependencies import get_db, get_library
from app.services import relocate_service
from app.routers.import_ws import library_router as _import_router
from app.services import library_service

router = APIRouter()

# Mount import endpoints onto this router so they're served under /api/library.
router.include_router(_import_router)

# ---------------------------------------------------------------------------
# In-process task registry (simple; one process, no Redis needed)
# ---------------------------------------------------------------------------

_tasks: dict[str, dict] = {}
_tasks_lock = threading.Lock()

_SUPPORTED_TASKS = {"mbsync", "fetchart", "lyrics"}


class LibraryTaskRequest(BaseModel):
    task: str
    album_ids: list[int] = []
    item_ids: list[int] = []


class LibraryTaskResponse(BaseModel):
    task_id: str
    status: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/artists/letters")
async def get_artist_letters(db: sqlite3.Connection = Depends(get_db)) -> list[str]:
    """Return sorted list of first characters (uppercased) that albumartists start with.

    Also includes '#' if any non-alpha artists exist.
    """
    cur = db.execute(
        "SELECT DISTINCT albumartist FROM albums WHERE albumartist IS NOT NULL AND albumartist != ''"
    )
    rows = cur.fetchall()

    letters: set[str] = set()
    has_non_alpha = False
    for (name,) in rows:
        first = name[0].upper() if name else ""
        if first and first.isalpha():
            letters.add(first)
        elif first:
            has_non_alpha = True

    result = sorted(letters)
    if has_non_alpha:
        result.append("#")
    return result


@router.get("/artists")
async def get_artists(
    letter: str = Query(default=""),
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    """Return distinct albumartist values with album counts.

    If letter is provided (A-Z), filter to artists starting with that letter.
    If letter is '#', filter to artists not starting with A-Z.
    """
    if letter == "#":
        cur = db.execute(
            """
            SELECT albumartist, COUNT(*) AS album_count
            FROM albums
            WHERE albumartist IS NOT NULL
              AND albumartist != ''
              AND albumartist GLOB '[^A-Za-z]*'
            GROUP BY albumartist
            ORDER BY albumartist COLLATE NOCASE
            """
        )
    elif letter and len(letter) == 1 and letter.isalpha():
        param = letter.upper() + "%"
        cur = db.execute(
            """
            SELECT albumartist, COUNT(*) AS album_count
            FROM albums
            WHERE albumartist IS NOT NULL
              AND albumartist != ''
              AND albumartist LIKE ? COLLATE NOCASE
            GROUP BY albumartist
            ORDER BY albumartist COLLATE NOCASE
            """,
            (param,),
        )
    else:
        cur = db.execute(
            """
            SELECT albumartist, COUNT(*) AS album_count
            FROM albums
            WHERE albumartist IS NOT NULL
              AND albumartist != ''
            GROUP BY albumartist
            ORDER BY albumartist COLLATE NOCASE
            """
        )

    rows = cur.fetchall()
    return [{"name": row[0], "album_count": row[1]} for row in rows]


class ArtistRelocateRequest(BaseModel):
    destination: str


class ArtistRelocateResponse(BaseModel):
    relocated: int
    failed: int
    errors: list[str]


@router.delete("/artists/{artist_name:path}", status_code=204)
async def remove_artist(
    artist_name: str,
    lib: beets.library.Library = Depends(get_library),
) -> Response:
    """Remove all albums by an artist from the library (files are NOT deleted)."""
    albums = lib.albums(dbcore.query.SubstringQuery("albumartist", artist_name))
    album_list = list(albums)
    if not album_list:
        raise HTTPException(status_code=404, detail=f"No albums found for artist: {artist_name}")
    for album in album_list:
        album.remove(delete=False)
    return Response(status_code=204)


@router.post("/artists/{artist_name:path}/relocate", response_model=ArtistRelocateResponse)
async def relocate_artist_files(
    artist_name: str,
    body: ArtistRelocateRequest,
    lib: beets.library.Library = Depends(get_library),
) -> ArtistRelocateResponse:
    """Move all albums by an artist to a new parent directory."""
    albums = lib.albums(dbcore.query.SubstringQuery("albumartist", artist_name))
    album_list = list(albums)
    if not album_list:
        raise HTTPException(status_code=404, detail=f"No albums found for artist: {artist_name}")

    # Validate destination once up front
    dest = Path(body.destination).resolve()
    base = Path(settings.music_base_path).resolve()
    try:
        dest.relative_to(base)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail=f"Destination is outside the permitted base path ({settings.music_base_path})",
        )

    relocated = 0
    errors = []
    for album in album_list:
        try:
            relocate_service.relocate_album(
                lib=lib,
                album_id=album.id,
                destination=body.destination,
                music_base_path=settings.music_base_path,
            )
            relocated += 1
        except Exception as exc:
            errors.append(f"Album {album.id} ({album.album!r}): {exc}")

    return ArtistRelocateResponse(
        relocated=relocated,
        failed=len(errors),
        errors=errors,
    )


@router.get("/stats")
async def get_stats(db: sqlite3.Connection = Depends(get_db)) -> dict:
    """Return aggregate library statistics (counts, duration, format breakdown, etc.)."""
    return library_service.get_stats(db)


@router.get("/facets")
async def get_facets(db: sqlite3.Connection = Depends(get_db)) -> dict:
    """Return distinct facet values for filter UI (genres, formats, labels, year range)."""
    return library_service.get_facets(db)


@router.post("/tasks", response_model=LibraryTaskResponse, status_code=202)
async def run_task(body: LibraryTaskRequest) -> LibraryTaskResponse:
    """
    Launch a beets management task in the background.

    Returns immediately with a task_id; poll GET /api/library/tasks/{task_id}
    for status and output.

    Supported tasks:
      - mbsync   — re-sync MusicBrainz metadata
      - fetchart — download missing album art
      - lyrics   — fetch song lyrics
    """
    if body.task not in _SUPPORTED_TASKS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported task '{body.task}'. Must be one of: {', '.join(sorted(_SUPPORTED_TASKS))}",
        )

    task_id = str(uuid.uuid4())
    with _tasks_lock:
        _tasks[task_id] = {"task_id": task_id, "status": "running", "output": ""}

    def _run() -> None:
        cmd = ["/usr/bin/beet", "-c", settings.beets_config_path, body.task]

        # Append ID filters when specific IDs were requested.
        # beets query syntax: "id:123" matches a single item/album by id.
        if body.task in ("mbsync", "fetchart") and body.album_ids:
            for aid in body.album_ids:
                cmd.append(f"id:{aid}")
        elif body.task == "lyrics" and body.item_ids:
            for iid in body.item_ids:
                cmd.append(f"id:{iid}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10-minute hard limit per task
            )
            combined = result.stdout
            if result.stderr:
                combined += "\n" + result.stderr
            status = "complete" if result.returncode == 0 else "error"
        except subprocess.TimeoutExpired:
            combined = "Task timed out after 600 seconds."
            status = "error"
        except Exception as exc:
            combined = str(exc)
            status = "error"

        with _tasks_lock:
            if task_id in _tasks:
                _tasks[task_id]["status"] = status
                _tasks[task_id]["output"] = combined.strip()

    thread = threading.Thread(target=_run, daemon=True, name=f"beets-task-{task_id[:8]}")
    thread.start()

    return LibraryTaskResponse(task_id=task_id, status="running")


@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    """Poll the status and output of a management task."""
    with _tasks_lock:
        task = _tasks.get(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task
