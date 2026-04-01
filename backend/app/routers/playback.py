"""
playback.py — /api/stream endpoints.

GET /api/stream/{item_id}       — stream audio file with HTTP range request support
GET /api/stream/{item_id}/info  — lightweight track metadata for the player UI
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import AsyncGenerator, Optional

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.config import settings
from app.dependencies import get_db

router = APIRouter()

# ---------------------------------------------------------------------------
# Format → Content-Type map
# ---------------------------------------------------------------------------

FORMAT_CONTENT_TYPES: dict[str, str] = {
    "MP3": "audio/mpeg",
    "FLAC": "audio/flac",
    "OGG": "audio/ogg",
    "AAC": "audio/aac",
    "ALAC": "audio/mp4",
    "WMA": "audio/x-ms-wma",
    "Windows Media": "audio/x-ms-wma",
    "AIFF": "audio/aiff",
    "WAV": "audio/wav",
    "Opus": "audio/opus",
}

_CHUNK_SIZE = 64 * 1024  # 64 KB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_and_validate_path(raw_path: bytes | str) -> Path:
    """
    Decode the raw path from the DB, resolve it to an absolute canonical path,
    and verify it sits within settings.music_base_path.

    Raises HTTPException(403) if the path escapes the music root.
    Raises HTTPException(404) if the path is malformed.
    """
    if isinstance(raw_path, (bytes, bytearray)):
        path_str = raw_path.decode("utf-8", errors="replace")
    else:
        path_str = str(raw_path)

    try:
        resolved = Path(path_str).resolve()
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid file path")

    base = Path(settings.music_base_path).resolve()
    try:
        resolved.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=403, detail="File path is outside permitted directory")

    return resolved


def _parse_range(range_header: str, file_size: int) -> tuple[int, int]:
    """
    Parse a Range header value such as 'bytes=0-65535' or 'bytes=1048576-'.

    Returns (start, end) as inclusive byte offsets clamped to [0, file_size-1].
    Raises HTTPException(416) for unparseable or unsatisfiable ranges.
    """
    try:
        unit, _, spec = range_header.partition("=")
        if unit.strip().lower() != "bytes":
            raise ValueError("Only bytes ranges are supported")

        # Take only the first range spec (no multi-range support needed)
        first_spec = spec.split(",")[0].strip()
        start_str, _, end_str = first_spec.partition("-")

        start = int(start_str) if start_str.strip() else 0
        end = int(end_str) if end_str.strip() else file_size - 1

        # Clamp end to last valid byte
        end = min(end, file_size - 1)

        if start > end or start < 0:
            raise ValueError("Unsatisfiable range")

    except (ValueError, AttributeError) as exc:
        raise HTTPException(
            status_code=416,
            detail="Range Not Satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        ) from exc

    return start, end


async def _file_chunk_generator(
    path: str, start: int, end: int
) -> AsyncGenerator[bytes, None]:
    """
    Async generator that yields up to _CHUNK_SIZE bytes at a time
    from [start, end] (inclusive) of the given file.
    """
    remaining = end - start + 1
    async with aiofiles.open(path, "rb") as f:
        await f.seek(start)
        while remaining > 0:
            read_size = min(_CHUNK_SIZE, remaining)
            chunk = await f.read(read_size)
            if not chunk:
                break
            yield chunk
            remaining -= len(chunk)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/{item_id}/info")
async def stream_item_info(
    item_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    """
    Return lightweight track metadata for the player UI.

    Fields: id, title, artist, album, length, format, bitrate.
    Path is never included.
    """
    row = db.execute(
        "SELECT id, title, artist, album, length, format, bitrate "
        "FROM items WHERE id = ?",
        [item_id],
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return dict(row)


@router.get("/{item_id}")
async def stream_item(
    item_id: int,
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
) -> StreamingResponse:
    """
    Stream an audio file with HTTP range request support.

    Security: the resolved file path is validated against music_base_path
    before any file operation is performed.
    """
    # 1. Fetch path and format directly — library_service.get_item omits path
    row = db.execute(
        "SELECT path, format FROM items WHERE id = ?",
        [item_id],
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")

    # 2. Decode path bytes and validate against music_base_path
    audio_path = _resolve_and_validate_path(row["path"])

    # 3. Check the file exists on disk
    if not audio_path.exists() or not audio_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    # 4. Determine Content-Type from format
    fmt: str = row["format"] or ""
    content_type = FORMAT_CONTENT_TYPES.get(fmt, "application/octet-stream")

    file_size = os.path.getsize(str(audio_path))

    # 5. Common headers present on every response
    common_headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "public, max-age=86400",
    }

    # 6. Handle Range header
    range_header: Optional[str] = request.headers.get("range")

    if range_header is None:
        # Full file — 200 OK
        headers = {
            **common_headers,
            "Content-Length": str(file_size),
        }
        return StreamingResponse(
            _file_chunk_generator(str(audio_path), 0, file_size - 1),
            status_code=200,
            media_type=content_type,
            headers=headers,
        )
    else:
        # Partial content — 206
        start, end = _parse_range(range_header, file_size)
        chunk_size = end - start + 1
        headers = {
            **common_headers,
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(chunk_size),
        }
        return StreamingResponse(
            _file_chunk_generator(str(audio_path), start, end),
            status_code=206,
            media_type=content_type,
            headers=headers,
        )
