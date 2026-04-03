"""
home.py — Endpoints for the Home/Discovery page and play history.

GET  /api/albums/recent?limit=12        — recently added albums
GET  /api/albums/random?limit=12        — random albums
GET  /api/genres                         — distinct genres with album counts
GET  /api/albums/recommended?limit=12   — least-played albums (or least recently added)
GET  /api/playback/history?limit=20     — recently played albums from play_history
POST /api/playback/history              — record a play event
"""

from __future__ import annotations

import sqlite3
import time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.dependencies import get_db
from app.models.album import AlbumSummary
from app.services.library_service import _album_row_to_dict, _ALBUM_SELECT

albums_router = APIRouter()
genres_router = APIRouter()
playback_router = APIRouter()


# ---------------------------------------------------------------------------
# Album discovery endpoints
# ---------------------------------------------------------------------------

@albums_router.get("/recent", response_model=list[AlbumSummary])
async def get_recent_albums(
    limit: int = Query(default=12, ge=1, le=50),
    db: sqlite3.Connection = Depends(get_db),
) -> list[AlbumSummary]:
    """Albums sorted by added DESC."""
    sql = f"""
        {_ALBUM_SELECT}
        GROUP BY a.id
        ORDER BY a.added DESC
        LIMIT ?
    """
    rows = db.execute(sql, [limit]).fetchall()
    return [AlbumSummary(**_album_row_to_dict(r)) for r in rows]


@albums_router.get("/random", response_model=list[AlbumSummary])
async def get_random_albums(
    limit: int = Query(default=12, ge=1, le=50),
    db: sqlite3.Connection = Depends(get_db),
) -> list[AlbumSummary]:
    """Random album selection."""
    sql = f"""
        {_ALBUM_SELECT}
        GROUP BY a.id
        ORDER BY RANDOM()
        LIMIT ?
    """
    rows = db.execute(sql, [limit]).fetchall()
    return [AlbumSummary(**_album_row_to_dict(r)) for r in rows]


@albums_router.get("/recommended", response_model=list[AlbumSummary])
async def get_recommended_albums(
    limit: int = Query(default=12, ge=1, le=50),
    db: sqlite3.Connection = Depends(get_db),
) -> list[AlbumSummary]:
    """
    Least-played albums. If play_history table exists, uses actual play counts.
    Falls back to least recently added as a proxy for unplayed.
    """
    # Check whether play_history table exists
    table_exists = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='play_history'"
    ).fetchone()

    if table_exists:
        sql = f"""
            {_ALBUM_SELECT}
            LEFT JOIN play_history ph ON ph.album_id = a.id
            GROUP BY a.id
            ORDER BY COUNT(ph.id) ASC, a.added ASC
            LIMIT ?
        """
    else:
        # Fallback: least recently added (never-played proxy)
        sql = f"""
            {_ALBUM_SELECT}
            GROUP BY a.id
            ORDER BY a.added ASC
            LIMIT ?
        """

    rows = db.execute(sql, [limit]).fetchall()
    return [AlbumSummary(**_album_row_to_dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Genres endpoint
# ---------------------------------------------------------------------------

class GenreWithCount(BaseModel):
    genre: str
    album_count: int


@genres_router.get("", response_model=list[GenreWithCount])
async def get_genres(
    db: sqlite3.Connection = Depends(get_db),
) -> list[GenreWithCount]:
    """
    Distinct genres with album counts, sorted by count DESC.
    Genres are split on comma since beets stores them as "Rock, Alternative".
    """
    rows = db.execute(
        "SELECT genres FROM albums WHERE genres IS NOT NULL AND genres != ''"
    ).fetchall()

    counts: dict[str, int] = {}
    for row in rows:
        for g in row["genres"].split(","):
            g = g.strip()
            if g:
                counts[g] = counts.get(g, 0) + 1

    result = [GenreWithCount(genre=g, album_count=c) for g, c in counts.items()]
    result.sort(key=lambda x: x.album_count, reverse=True)
    return result


# ---------------------------------------------------------------------------
# Play history endpoints
# ---------------------------------------------------------------------------

class PlayHistoryEntry(BaseModel):
    item_id: int
    duration_played: float


class PlayHistoryRecord(BaseModel):
    id: int
    item_id: int
    album_id: Optional[int] = None
    played_at: float
    duration_played: float
    # joined album fields
    album: Optional[str] = None
    albumartist: Optional[str] = None
    year: Optional[int] = None
    genres: Optional[str] = None
    label: Optional[str] = None
    country: Optional[str] = None
    albumtype: Optional[str] = None
    track_count: int = 0
    total_length: Optional[float] = None
    has_art: bool = False
    added: Optional[float] = None
    format: Optional[str] = None


@playback_router.get("/history", response_model=list[PlayHistoryRecord])
async def get_play_history(
    limit: int = Query(default=20, ge=1, le=100),
    db: sqlite3.Connection = Depends(get_db),
) -> list[PlayHistoryRecord]:
    """Recently played albums (distinct album_ids, most recent first, with album detail)."""
    # Check whether play_history table exists
    table_exists = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='play_history'"
    ).fetchone()
    if not table_exists:
        return []

    sql = """
        SELECT
            ph.id,
            ph.item_id,
            ph.album_id,
            ph.played_at,
            ph.duration_played,
            a.album,
            a.albumartist,
            a.year,
            a.genres,
            a.label,
            a.country,
            a.albumtype,
            a.added,
            a.artpath,
            COUNT(i.id) AS track_count,
            SUM(i.length) AS total_length,
            (a.artpath IS NOT NULL AND a.artpath != '') AS has_art,
            (
                SELECT i2.format
                FROM items i2
                WHERE i2.album_id = a.id
                GROUP BY i2.format
                ORDER BY COUNT(*) DESC
                LIMIT 1
            ) AS format
        FROM play_history ph
        LEFT JOIN albums a ON a.id = ph.album_id
        LEFT JOIN items i ON i.album_id = a.id
        GROUP BY ph.album_id
        ORDER BY ph.played_at DESC
        LIMIT ?
    """
    rows = db.execute(sql, [limit]).fetchall()

    result = []
    for row in rows:
        d = dict(row)
        artpath = d.get("artpath")
        if isinstance(artpath, (bytes, bytearray)):
            d["artpath"] = artpath.decode("utf-8", errors="replace")
        d["has_art"] = bool(d.get("has_art", 0))
        result.append(PlayHistoryRecord(**d))
    return result


@playback_router.post("/history", status_code=201)
async def record_play(
    body: PlayHistoryEntry,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    """
    Record a play event. Looks up album_id from item_id.
    Creates play_history table if it doesn't exist yet.
    """
    # Ensure table exists (idempotent)
    db.execute("""
        CREATE TABLE IF NOT EXISTS play_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            album_id INTEGER,
            played_at REAL NOT NULL,
            duration_played REAL NOT NULL
        )
    """)
    db.commit()

    # Look up album_id from items table (read-only connection, but CREATE TABLE
    # needs write — we open a separate rw connection for writes)
    # Actually: our db is read-only. We need a writable connection.
    # We'll open one inline here using the same path.
    import sqlite3 as _sqlite3
    from app.config import settings

    rw_db = _sqlite3.connect(settings.beets_db_path, check_same_thread=False)
    rw_db.row_factory = _sqlite3.Row
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

        # Look up album_id
        item_row = rw_db.execute(
            "SELECT album_id FROM items WHERE id = ?", [body.item_id]
        ).fetchone()
        album_id = item_row["album_id"] if item_row else None

        rw_db.execute(
            "INSERT INTO play_history (item_id, album_id, played_at, duration_played) VALUES (?, ?, ?, ?)",
            [body.item_id, album_id, time.time(), body.duration_played],
        )
        rw_db.commit()
    finally:
        rw_db.close()

    return {"ok": True}
