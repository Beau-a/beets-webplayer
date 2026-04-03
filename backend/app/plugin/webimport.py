"""
webimport.py — WebImportSession

A beets ImportSession subclass that delegates candidate selection to the
browser via an ImportBridge instead of prompting at the terminal.

Usage (from import_service.py):
    counters = {"imported": 0, "skipped": 0, "errors": 0}
    session = WebImportSession(lib, loghandler=None, paths=[dir], query=None,
                               bridge=bridge, counters=counters)
    session.run()
    session.cleanup()

IMPORTANT: beets calls task.choose_match(session) which does:
    choice = session.choose_match(task)   # expects a RETURN VALUE
    task.set_choice(choice)
So choose_match (and choose_item) must RETURN the action/match — they must
NOT call task.set_choice() themselves.

resolve_duplicate is called directly by beets and IS expected to call
task.set_choice() itself.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from beets.importer import ImportSession, ImportTask, Action
from beets.plugins import BeetsPlugin

if TYPE_CHECKING:
    from app.services.import_service import ImportBridge

log = logging.getLogger(__name__)


class WebImportSession(ImportSession):
    """
    Beets ImportSession subclass that drives the import pipeline via a
    browser WebSocket connection rather than the terminal.
    """

    def __init__(self, lib, loghandler, paths, query, bridge: "ImportBridge", counters: dict):
        super().__init__(lib, loghandler, paths, query)
        self.bridge = bridge
        self.counters = counters

        # Register a class-level listener for the album_imported event so we
        # get notified after beets has actually written the album to the library.
        # BeetsPlugin.listeners is a class-level defaultdict(list) shared by all
        # plugins — we can append directly and remove it in cleanup().
        self._album_imported_listener = self._on_album_imported
        BeetsPlugin.listeners["album_imported"].append(self._album_imported_listener)

    def cleanup(self) -> None:
        """Unregister listeners. Call this after session.run() completes."""
        try:
            BeetsPlugin.listeners["album_imported"].remove(self._album_imported_listener)
        except ValueError:
            pass  # already removed

    # ------------------------------------------------------------------
    # Event listener — called by plugins.send("album_imported", ...)
    # ------------------------------------------------------------------

    def _on_album_imported(self, lib, album) -> None:
        """Called by beets after an album is successfully written to the library."""
        log.info("album_imported event: album=%s artist=%s", getattr(album, 'album', '?'), getattr(album, 'albumartist', '?'))
        self.counters["imported"] += 1
        try:
            self.bridge.send_progress("album_imported", {
                "album_id": album.id,
                "album": album.album or "",
                "artist": album.albumartist or "",
                "year": album.year or 0,
                "track_count": 0,
            })
        except Exception as exc:
            log.debug("WebImportSession: error sending album_imported event: %s", exc)

    # ------------------------------------------------------------------
    # Required abstract method overrides
    # ------------------------------------------------------------------

    def should_resume(self, path) -> bool:
        """Never resume a partial import — always start fresh."""
        return False

    # ------------------------------------------------------------------
    # Core interception points — called by the beets import pipeline
    #
    # NOTE: beets calls task.choose_match(session) which does:
    #   choice = session.choose_match(task)
    #   task.set_choice(choice)
    # So these methods MUST RETURN the action/match, NOT call task.set_choice().
    # ------------------------------------------------------------------

    def choose_match(self, task: ImportTask):
        """
        Called by the beets importer for each album candidate set.
        Returns an Action constant or an AlbumMatch object.
        Blocks until the browser sends back a choice when candidates exist.
        """
        if self.bridge.is_cancelled():
            self._send_skipped(task, "import cancelled")
            return Action.SKIP

        candidates = task.candidates or []

        # Notify the browser that we've started processing this album.
        album_path = _task_path(task)
        log.info("choose_match called: path=%s candidates=%d", album_path, len(candidates))
        self.bridge.send_progress("album_start", {"path": album_path})

        if not candidates:
            log.info("choose_match: no candidates, asking user for %s", album_path)
            choice = self.bridge.send_no_candidates(task)
        else:
            # Block the import thread until the browser responds.
            choice = self.bridge.send_candidates(task, candidates)

        action = choice.get("action", "skip")

        if action == "apply":
            # User may supply a MusicBrainz release ID directly (from the
            # manual search panel) instead of picking from the candidate list.
            mb_id = choice.get("mb_id")
            if mb_id:
                self.bridge.send_progress("mb_lookup_start", {"mb_id": mb_id})
                match = self._fetch_mb_release(mb_id, task)
                if match is not None:
                    return match
                self._send_skipped(task, "MusicBrainz ID lookup failed")
                return Action.SKIP
            idx = choice.get("candidate_index", 0)
            if isinstance(idx, int) and 0 <= idx < len(candidates):
                return candidates[idx]
            log.warning(
                "WebImportSession: invalid candidate_index %r (have %d); skipping.",
                idx, len(candidates),
            )
            self._send_skipped(task, "invalid candidate selection")
            return Action.SKIP

        if action == "as_is":
            return Action.ASIS

        if action == "singleton":
            return Action.TRACKS

        if action == "abort":
            self.bridge.cancel()
            self._send_skipped(task, "import aborted")
            return Action.SKIP

        # "skip" or any unrecognised value
        reason = choice.get("reason", "")
        if reason == "timeout":
            self._send_skipped(task, "timed out waiting for response")
        else:
            self._send_skipped(task, "skipped by user")
        return Action.SKIP

    def choose_item(self, task: ImportTask):
        """
        Called by the beets importer for singleton (non-album) imports.
        Returns an Action constant or a TrackMatch object.
        Auto-applies the best candidate when the recommendation is strong;
        otherwise imports as-is.
        """
        if self.bridge.is_cancelled():
            return Action.ASIS

        candidates = task.candidates or []

        if candidates:
            rec_name = ""
            try:
                rec_name = task.rec.name if task.rec is not None else ""
            except Exception:
                pass
            if rec_name == "strong":
                return candidates[0]

        return Action.ASIS

    def resolve_duplicate(self, task, found_duplicates):
        """
        Called when an import would create a duplicate in the library.
        This method IS expected to call task.set_choice() directly.
        Default policy: skip the duplicate.
        """
        task.set_choice(Action.SKIP)
        self.counters["skipped"] += 1
        try:
            self.bridge.send_progress("album_skipped", {
                "path": _task_path(task),
                "reason": "already in library",
            })
        except Exception as exc:
            log.debug("WebImportSession: error sending album_skipped (duplicate): %s", exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_mb_release(self, mb_id: str, task: ImportTask):
        """
        Look up a specific MusicBrainz release by ID and return the best
        AlbumMatch (with item→track mapping computed against task.items),
        or None if the lookup fails or returns no usable match.

        Runs on the import background thread — blocking network I/O is fine here.
        """
        try:
            from beets.autotag import match as autotag_match
            _artist, _album, proposal = autotag_match.tag_album(
                task.items or [], search_ids=[mb_id]
            )
            if proposal and proposal.candidates:
                return proposal.candidates[0]
            log.warning("_fetch_mb_release: no match returned for mb_id=%s", mb_id)
        except Exception as exc:
            log.warning("_fetch_mb_release failed for mb_id=%s: %s", mb_id, exc)
        return None

    def _send_skipped(self, task: ImportTask, reason: str) -> None:
        """Increment skip counter and notify the browser."""
        self.counters["skipped"] += 1
        try:
            self.bridge.send_progress("album_skipped", {
                "path": _task_path(task),
                "reason": reason,
            })
        except Exception as exc:
            log.debug("WebImportSession: error sending album_skipped: %s", exc)


def _task_path(task: ImportTask) -> str:
    """Return a clean string path from a task, handling bytes paths."""
    try:
        p = task.paths[0] if task.paths else b""
        if isinstance(p, bytes):
            return p.decode("utf-8", errors="replace")
        return str(p)
    except Exception:
        return ""
