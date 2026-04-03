"""
import_ws.py — WebSocket endpoint for the interactive beets import dialog.

Routes:
  POST /api/library/import   — start an import session (in library.py via this router)
  GET  /ws/import            — WebSocket for real-time import interaction

The POST endpoint is defined here but mounted on the library router from library.py
(see app/routers/library.py).  The WS endpoint lives at the root path /ws/import
and is included in main.py without a prefix.
"""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

import beets.library

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.config import settings
from app.dependencies import get_library
from app.models.import_models import ImportStartRequest, ImportStartResponse
from app.services.import_service import import_service

log = logging.getLogger(__name__)

# Router for the WebSocket endpoint (mounted without a prefix in main.py).
router = APIRouter()

# Router for the REST endpoint (included with prefix=/api/library in library.py).
library_router = APIRouter()


_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def _serialize_album_info(info) -> dict:
    """Convert a beets AlbumInfo object to a JSON-safe dict for the MB search response."""
    tracks = []
    for t in (info.tracks or []):
        tracks.append({
            "title": getattr(t, "title", "") or "",
            "artist": getattr(t, "artist", "") or "",
            "track": getattr(t, "index", 0) or 0,
            "length": float(getattr(t, "length", 0) or 0),
            "mb_trackid": getattr(t, "track_id", "") or "",
        })
    return {
        "artist": getattr(info, "albumartist", "") or "",
        "album": getattr(info, "album", "") or "",
        "year": getattr(info, "year", 0) or 0,
        "label": getattr(info, "label", "") or "",
        "country": getattr(info, "country", "") or "",
        "mb_albumid": getattr(info, "album_id", "") or "",
        "track_count": len(info.tracks) if info.tracks else 0,
        "tracks": tracks,
    }


# ---------------------------------------------------------------------------
# GET /api/library/import/mb-search
# ---------------------------------------------------------------------------

@library_router.get("/import/mb-search")
async def mb_search(q: str = Query(..., min_length=1)):
    """
    Search MusicBrainz for album releases matching a query string.

    If q contains a UUID (raw or embedded in a MB release URL), performs a
    direct ID lookup via metadata_plugins.albums_for_ids().

    Otherwise, attempts a text search: split on ' - ' to extract artist and
    album name, then call metadata_plugins.candidates() (up to 5 results).

    Both calls are blocking network I/O; dispatched via run_in_executor to
    avoid blocking the asyncio event loop.

    Returns: {"results": [{artist, album, year, label, country, mb_albumid, track_count, tracks}]}
    """
    loop = asyncio.get_event_loop()

    uuid_match = _UUID_RE.search(q)

    if uuid_match:
        # Direct ID or URL lookup — pass the raw query; the MB plugin's
        # _extract_id will parse out the UUID from URLs automatically.
        raw_q = q.strip()
        def _lookup_by_id():
            from beets import metadata_plugins
            return [i for i in metadata_plugins.albums_for_ids([raw_q]) if i is not None]

        raw_results = await loop.run_in_executor(None, _lookup_by_id)
    else:
        # Text search — split on ' - ' for artist / album.
        parts = q.split(" - ", 1)
        if len(parts) == 2:
            artist = parts[0].strip()
            album = parts[1].strip()
        else:
            artist = ""
            album = q.strip()

        def _search_by_text():
            # Bypass metadata_plugins.candidates() entirely to avoid the
            # extra_tags / plurality issue (extra_tags like 'tracks' need
            # real Item objects to compute values; we have none here).
            # Instead, call each metadata source plugin's search API
            # directly with only the criteria we actually know: release
            # name and artist. Distance scoring happens later in the import
            # thread when _fetch_mb_release calls tag_album() with real items.
            from beets.metadata_plugins import find_metadata_source_plugins, SearchParams
            results = []
            criteria = {"release": album}
            if artist:
                criteria["artist"] = artist
            for plugin in find_metadata_source_plugins():
                if not hasattr(plugin, "get_search_response"):
                    continue
                try:
                    params = SearchParams("album", "", criteria, 5)
                    ids = plugin.get_search_response(params)
                    infos = list(filter(None, plugin.albums_for_ids(
                        r["id"] for r in ids
                    )))
                    results.extend(infos)
                    if results:
                        break  # stop after first plugin returns results
                except Exception as exc:
                    log.debug("mb_search text search failed for plugin %s: %s", plugin, exc)
            return results[:5]

        raw_results = await loop.run_in_executor(None, _search_by_text)

    results = [_serialize_album_info(info) for info in raw_results if info is not None]
    return {"results": results}


# ---------------------------------------------------------------------------
# POST /api/library/import
# ---------------------------------------------------------------------------

@library_router.post("/import", response_model=ImportStartResponse, status_code=202)
async def start_import(
    body: ImportStartRequest,
    lib: beets.library.Library = Depends(get_library),
):
    """
    Start an interactive import session.

    - Validates the directory is within settings.import_base_path.
    - Returns 409 if a session is already running.
    - Launches a background thread running the beets import pipeline.
    - Returns a session_id and the WebSocket URL to connect to.
    """
    # Security: resolve the target directory and ensure it's within the allowed base.
    try:
        target = Path(body.directory).resolve()
        base = Path(settings.import_base_path).resolve()
        target.relative_to(base)  # raises ValueError if outside base
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={
                "detail": (
                    f"Directory must be within the allowed import base path "
                    f"({settings.import_base_path})."
                )
            },
        )

    if not target.exists():
        return JSONResponse(
            status_code=400,
            content={"detail": f"Directory does not exist: {body.directory}"},
        )

    if not target.is_dir():
        return JSONResponse(
            status_code=400,
            content={"detail": f"Path is not a directory: {body.directory}"},
        )

    loop = asyncio.get_event_loop()

    try:
        bridge = import_service.start_session(
            lib=lib,
            directory=str(target),
            options=body.options.model_dump(),
            loop=loop,
        )
    except ValueError:
        return JSONResponse(
            status_code=409,
            content={"detail": "An import session is already running."},
        )

    return ImportStartResponse(
        session_id=bridge.session_id,
        ws_url=f"/ws/import?session_id={bridge.session_id}",
    )


# ---------------------------------------------------------------------------
# GET /ws/import  (WebSocket)
# ---------------------------------------------------------------------------

@router.websocket("/ws/import")
async def import_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for the interactive import dialog.

    The client connects here after receiving a session_id from POST /api/library/import.
    Messages flow:
      Server → Client: candidates, progress events, session_complete
      Client → Server: {"type": "choice", "payload": {...}}
                       {"type": "abort", "payload": {}}
    """
    bridge = import_service.get_active_bridge()

    if bridge is None or bridge.session_id != session_id:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    await websocket.send_json({"type": "connected", "payload": {"session_id": session_id}})

    # Two concurrent tasks:
    #   relay_task  — reads from the bridge queue and forwards to the browser
    #   receive_task — reads from the browser and dispatches to the bridge

    async def relay_events():
        """Read events from the import thread and forward them to the browser."""
        try:
            while True:
                event = await bridge.get_next_event()
                await websocket.send_json(event)
                if event.get("type") == "session_complete":
                    # Import is done — close the connection cleanly.
                    await websocket.close(code=1000)
                    return
        except WebSocketDisconnect:
            pass
        except Exception as exc:
            log.debug("import_websocket relay_events error: %s", exc)

    async def receive_choices():
        """Read messages from the browser and dispatch to the bridge."""
        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type", "")
                payload = data.get("payload", {})

                if msg_type == "choice":
                    await bridge.submit_choice(payload)
                elif msg_type == "abort":
                    bridge.cancel()
                else:
                    log.debug("import_websocket: unknown message type %r", msg_type)
        except WebSocketDisconnect:
            # Client disconnected — the import thread will time out after 300 s.
            log.debug("import_websocket: client disconnected (session %s)", session_id)
        except Exception as exc:
            log.debug("import_websocket receive_choices error: %s", exc)

    relay_task = asyncio.create_task(relay_events())
    receive_task = asyncio.create_task(receive_choices())

    # Wait for either task to finish (relay ends on session_complete or disconnect;
    # receive ends on disconnect).
    done, pending = await asyncio.wait(
        {relay_task, receive_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # Clear the session now that the WS is done.  The import thread also
    # schedules a delayed clear as a safety net; calling it twice is harmless.
    import_service.clear_session()
