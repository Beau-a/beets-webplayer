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
from pathlib import Path

import beets.library

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
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
