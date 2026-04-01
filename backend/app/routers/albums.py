"""
albums.py — /api/albums endpoints.

GET    /api/albums           — paginated album list (AlbumSummary)
GET    /api/albums/{id}/art  — serve cover art image
GET    /api/albums/{id}      — single album with tracks (AlbumDetail)
PATCH  /api/albums/{id}      — update album metadata
DELETE /api/albums/{id}      — remove album from library (does not delete files)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

import beets.library
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response

from app.config import settings
from app.dependencies import get_db, get_library
from app.models.album import AlbumDetail, AlbumRelocateRequest, AlbumSummary, AlbumUpdateRequest
from app.models.common import PaginatedResponse
from app.services import library_service, relocate_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[AlbumSummary])
async def list_albums(
    q: Optional[str] = Query(default=None, description="Beets-style query string"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    sort: str = Query(default="albumartist+"),
    db: sqlite3.Connection = Depends(get_db),
) -> PaginatedResponse[AlbumSummary]:
    rows, total = library_service.get_albums(db, q=q, page=page, page_size=page_size, sort=sort)
    albums = [AlbumSummary(**row) for row in rows]
    return PaginatedResponse(items=albums, total=total, page=page, page_size=page_size)


@router.get("/{album_id}/art")
async def get_album_art(
    album_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> FileResponse:
    """
    Serve the cover art file for an album.

    Security: validates that artpath is within settings.music_base_path
    before serving to prevent arbitrary file reads.
    """
    row = library_service.get_album(db, album_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Album not found")

    artpath_raw = row.get("artpath")
    if not artpath_raw:
        raise HTTPException(status_code=404, detail="No cover art for this album")

    if isinstance(artpath_raw, (bytes, bytearray)):
        artpath_str = artpath_raw.decode("utf-8", errors="replace")
    else:
        artpath_str = str(artpath_raw)

    try:
        art_path = Path(artpath_str).resolve()
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid art path")

    base = Path(settings.music_base_path).resolve()
    try:
        art_path.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=403, detail="Art path is outside permitted directory")

    if not art_path.exists() or not art_path.is_file():
        raise HTTPException(status_code=404, detail="Cover art file not found")

    suffix = art_path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    media_type = media_type_map.get(suffix, "application/octet-stream")

    return FileResponse(str(art_path), media_type=media_type)


@router.get("/{album_id}", response_model=AlbumDetail)
async def get_album(
    album_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> AlbumDetail:
    row = library_service.get_album(db, album_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Album not found")
    return AlbumDetail(**row)


@router.patch("/{album_id}", response_model=AlbumDetail)
async def update_album(
    album_id: int,
    body: AlbumUpdateRequest,
    lib: beets.library.Library = Depends(get_library),
    db: sqlite3.Connection = Depends(get_db),
) -> AlbumDetail:
    """
    Update album-level metadata.  Changes are stored in the beets DB.
    Tag writing happens at the item level (use PATCH /api/items/{id} for that).
    """
    album = lib.get_album(album_id)
    if album is None:
        raise HTTPException(status_code=404, detail="Album not found")

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="No fields provided for update")

    for field, value in updates.items():
        setattr(album, field, value)

    try:
        album.store()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save album: {exc}") from exc

    row = library_service.get_album(db, album_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Album not found after update")
    return AlbumDetail(**row)


@router.delete("/{album_id}", status_code=204)
async def delete_album(
    album_id: int,
    lib: beets.library.Library = Depends(get_library),
) -> Response:
    """
    Remove an album and all its tracks from the beets library.
    Audio files are NOT deleted from disk.
    """
    album = lib.get_album(album_id)
    if album is None:
        raise HTTPException(status_code=404, detail="Album not found")

    try:
        album.remove(delete=False)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to remove album: {exc}") from exc

    return Response(status_code=204)


@router.post("/{album_id}/relocate")
async def relocate_album_files(
    album_id: int,
    body: AlbumRelocateRequest,
    lib: beets.library.Library = Depends(get_library),
    db: sqlite3.Connection = Depends(get_db),
) -> AlbumDetail:
    """
    Move an album's files to a new parent directory and update beets DB paths.
    The album folder is moved into `destination`; the folder name is preserved.
    """
    try:
        relocate_service.relocate_album(
            lib=lib,
            album_id=album_id,
            destination=body.destination,
            music_base_path=settings.music_base_path,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=msg)
        if "outside the permitted" in msg:
            raise HTTPException(status_code=403, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to move files: {exc}")

    row = library_service.get_album(db, album_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Album not found after relocation")
    return AlbumDetail(**row)
