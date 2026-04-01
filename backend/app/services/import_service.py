"""
import_service.py — ImportBridge and ImportService.

The ImportBridge is the thread-safety layer between the synchronous beets import
pipeline (running in a background thread) and the async FastAPI WebSocket handler.

Flow:
  1. FastAPI POST /api/library/import creates an ImportBridge and launches a thread.
  2. The thread runs WebImportSession.run() (blocking).
  3. For each album, the session calls bridge.send_candidates(), which blocks the
     import thread until the browser sends a choice.
  4. The FastAPI WebSocket handler reads events from bridge.get_next_event() and
     forwards them to the browser. When the browser responds, it calls
     bridge.submit_choice(), which unblocks the import thread.
"""

from __future__ import annotations

import asyncio
import threading
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from beets.importer import ImportTask


def _serialize_candidates(task: "ImportTask", candidates: list) -> dict:
    """Convert a beets ImportTask and its candidates into a JSON-safe dict."""
    file_tracks = []
    for item in (task.items or []):
        try:
            path_name = Path(item.path).name if item.path else ""
        except Exception:
            path_name = ""
        file_tracks.append({
            "filename": path_name,
            "title": item.title or "",
            "artist": item.artist or "",
            "track": item.track or 0,
            "length": float(item.length or 0),
        })

    serialized_candidates = []
    for i, match in enumerate(candidates):
        info = match.info
        tracks = []
        for t in (info.tracks or []):
            tracks.append({
                "title": t.title or "",
                "artist": t.artist or "",
                "track": t.index or 0,
                "length": float(t.length or 0),
                "mb_trackid": t.mb_trackid or "",
            })
        serialized_candidates.append({
            "index": i,
            "distance": float(match.distance),
            "artist": info.albumartist or "",
            "album": info.album or "",
            "year": info.year or 0,
            "label": getattr(info, "label", "") or "",
            "country": getattr(info, "country", "") or "",
            "mb_albumid": info.mb_albumid or "",
            "track_count": len(info.tracks) if info.tracks else 0,
            "tracks": tracks,
            "extra_items": len(match.extra_items) if hasattr(match, "extra_items") else 0,
            "missing_tracks": len(match.extra_tracks) if hasattr(match, "extra_tracks") else 0,
        })

    album_path = ""
    if task.paths:
        try:
            album_path = str(task.paths[0])
        except Exception:
            pass

    rec_name = "none"
    if task.rec is not None:
        try:
            rec_name = task.rec.name
        except Exception:
            rec_name = str(task.rec)

    return {
        "album_path": album_path,
        "file_tracks": file_tracks,
        "candidates": serialized_candidates,
        "rec": rec_name,
    }


class ImportBridge:
    """
    Thread-safe bridge between the synchronous beets import thread
    and the async FastAPI WebSocket handler.

    The import thread calls send_candidates() which blocks until the
    browser sends back a choice.  FastAPI's async side reads from
    _event_queue and writes choices back.
    """

    def __init__(self, session_id: str, loop: asyncio.AbstractEventLoop):
        self.session_id: str = session_id
        self._loop: asyncio.AbstractEventLoop = loop
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._choice_event: threading.Event = threading.Event()
        self._user_choice: dict | None = None
        self._cancel_event: threading.Event = threading.Event()
        self._choice_lock: threading.Lock = threading.Lock()

    # ------------------------------------------------------------------
    # Import-thread side (called from the background beets thread)
    # ------------------------------------------------------------------

    def send_candidates(self, task: "ImportTask", candidates: list) -> dict:
        """
        Called from the import THREAD.  Blocks until the user responds
        (or a 300-second timeout / cancel).

        Returns a choice dict:
            {"action": "apply", "candidate_index": 0}
            {"action": "skip"}
            {"action": "as_is"}
            {"action": "singleton"}
            {"action": "abort"}
        """
        payload = _serialize_candidates(task, candidates)

        # Push the candidates event onto the async queue (thread-safe).
        self._loop.call_soon_threadsafe(
            self._event_queue.put_nowait,
            {"type": "candidates", "payload": payload},
        )

        # Block the import thread, waiting for the user's response.
        self._choice_event.clear()
        signalled = self._choice_event.wait(timeout=300)

        if not signalled or self._cancel_event.is_set():
            return {"action": "skip"}

        with self._choice_lock:
            choice = self._user_choice
            self._user_choice = None

        return choice or {"action": "skip"}

    def send_progress(self, event_type: str, payload: dict) -> None:
        """
        Called from the import thread.  Fire-and-forget progress event.
        """
        self._loop.call_soon_threadsafe(
            self._event_queue.put_nowait,
            {"type": event_type, "payload": payload},
        )

    def is_cancelled(self) -> bool:
        """Allow the plugin to poll for cancellation between stages."""
        return self._cancel_event.is_set()

    # ------------------------------------------------------------------
    # FastAPI async side (called from the asyncio event loop)
    # ------------------------------------------------------------------

    async def get_next_event(self) -> dict:
        """Await the next event produced by the import thread."""
        return await self._event_queue.get()

    async def submit_choice(self, choice: dict) -> None:
        """Called when the browser sends back a choice for the current album."""
        with self._choice_lock:
            self._user_choice = choice
        self._choice_event.set()

    def cancel(self) -> None:
        """Abort the import session.  Unblocks any waiting import thread."""
        self._cancel_event.set()
        self._choice_event.set()  # wake up the blocked import thread immediately


class ImportService:
    """Manages the single active import session (one at a time)."""

    def __init__(self) -> None:
        self._active_bridge: ImportBridge | None = None
        self._lock: threading.Lock = threading.Lock()

    def start_session(
        self,
        lib,
        directory: str,
        options: dict,
        loop: asyncio.AbstractEventLoop,
    ) -> ImportBridge:
        """
        Create a new ImportBridge and launch the beets import in a background
        thread.  Raises ValueError if a session is already active.

        The thread:
          1. Builds a WebImportSession with the bridge.
          2. Applies import options to beets config.
          3. Calls session.run() (blocking).
          4. Sends a session_complete event, then clears the active session.
        """
        with self._lock:
            if self._active_bridge is not None:
                raise ValueError("An import session is already running.")

            session_id = str(uuid.uuid4())
            bridge = ImportBridge(session_id=session_id, loop=loop)
            self._active_bridge = bridge

        # Import here to avoid circular imports at module load time.
        from app.plugin.webimport import WebImportSession

        def _run_import() -> None:
            import time
            import beets

            start_time = time.monotonic()
            counters = {"imported": 0, "skipped": 0, "errors": 0}
            session = None

            try:
                # Apply per-session import options to beets config.
                beets.config["import"]["copy"].set(options.get("copy", True))
                beets.config["import"]["move"].set(options.get("move", False))
                beets.config["import"]["write"].set(options.get("write_tags", True))
                beets.config["import"]["autotag"].set(options.get("autotag", True))
                beets.config["import"]["timid"].set(options.get("timid", False))
                # Non-interactive: we drive decisions via the bridge.
                beets.config["import"]["quiet"].set(False)

                session = WebImportSession(
                    lib=lib,
                    loghandler=None,
                    paths=[directory],
                    query=None,
                    bridge=bridge,
                    counters=counters,
                )

                bridge.send_progress("session_start", {
                    "directory": directory,
                    "estimated_albums": 0,  # beets doesn't know ahead of time
                })

                session.run()

            except Exception as exc:
                bridge.send_progress("error", {
                    "path": directory,
                    "message": str(exc),
                })
            finally:
                if session is not None:
                    session.cleanup()
                elapsed = time.monotonic() - start_time
                bridge.send_progress("session_complete", {
                    "total_imported": counters["imported"],
                    "total_skipped": counters["skipped"],
                    "total_errors": counters["errors"],
                    "duration_s": round(elapsed, 2),
                })
                self.clear_session()

        thread = threading.Thread(target=_run_import, daemon=True, name=f"beets-import-{session_id}")
        thread.start()

        return bridge

    def get_active_bridge(self) -> ImportBridge | None:
        with self._lock:
            return self._active_bridge

    def clear_session(self) -> None:
        with self._lock:
            self._active_bridge = None


# Module-level singleton used by the router.
import_service = ImportService()
