# Plan: Manual MusicBrainz Lookup During Import

**Date**: 2026-04-02  
**Status**: In progress

---

## Problem

Two gaps in the interactive import flow:

1. **No candidates → silent as-is.** When beets finds zero MB matches for an album, `webimport.py` returns `Action.ASIS` immediately. The browser never sees the album and the user cannot intervene.

2. **Wrong candidates → no override.** When beets finds candidates but none match the actual album, the user can only skip or import as-is. There is no way to say "use this specific MusicBrainz release."

---

## Solution

- Fix no-candidates to block and ask the user (send `no_candidates` WS event, wait for choice)
- Add a "Search MusicBrainz" panel to both the normal candidates UI and the no-candidates UI
- New REST endpoint `GET /api/library/import/mb-search?q=...` for MB lookup/search
- When user picks a result: send `{"action": "apply", "mb_id": "..."}` over WS
- Backend calls `tag_album(task.items, search_ids=[mb_id])` to build a proper AlbumMatch with item→track mapping

---

## Files Changed

| File | Change |
|---|---|
| `backend/app/services/import_service.py` | Add `send_no_candidates()` to `ImportBridge` |
| `backend/app/plugin/webimport.py` | Route no-candidates through bridge; handle `mb_id` in apply; add `_fetch_mb_release` |
| `backend/app/routers/import_ws.py` | Add `GET /api/library/import/mb-search` |
| `frontend/src/types/import.ts` | Add `waiting_no_candidates` state, `NoCandidatesPayload`, `mb_id` on `ImportChoice` |
| `frontend/src/stores/import.ts` | Handle `no_candidates` WS message, expose `noCandidatesPayload` |
| `frontend/src/views/ImportView.vue` | Add `waiting_no_candidates` branch |
| `frontend/src/components/import/CandidateList.vue` | Add collapsible MB search section |
| `frontend/src/components/import/NoCandidatesPanel.vue` | New component (no-candidates waiting state) |

---

## Backend Implementation

### `import_service.py` — Add `send_no_candidates`

Same blocking pattern as `send_candidates`. Sends `no_candidates` event with `album_path` and `file_tracks`.

```python
def send_no_candidates(self, task) -> dict:
    file_tracks = [...]  # same serialization as in _serialize_candidates
    album_path = str(task.paths[0]) if task.paths else ""
    self._loop.call_soon_threadsafe(
        self._event_queue.put_nowait,
        {"type": "no_candidates", "payload": {"album_path": album_path, "file_tracks": file_tracks}},
    )
    self._choice_event.clear()
    signalled = self._choice_event.wait(timeout=300)
    if not signalled:
        return {"action": "skip", "reason": "timeout"}
    if self._cancel_event.is_set():
        return {"action": "skip", "reason": "cancelled"}
    with self._choice_lock:
        choice = self._user_choice
        self._user_choice = None
    return choice or {"action": "skip"}
```

### `webimport.py` — Route no-candidates; handle `mb_id`

Change the `if not candidates:` branch to call `send_no_candidates`. Refactor so both paths (candidates/no-candidates) share one action-dispatch block. Add `mb_id` handling before `candidate_index`:

```python
if action == "apply":
    mb_id = choice.get("mb_id")
    if mb_id:
        match = self._fetch_mb_release(mb_id, task)
        if match is not None:
            return match
        self._send_skipped(task, "MusicBrainz ID lookup failed")
        return Action.SKIP
    idx = choice.get("candidate_index", 0)
    ...  # existing path
```

`_fetch_mb_release` calls `beets.autotag.match.tag_album(task.items, search_ids=[mb_id])` — this runs the full distance computation against task items so the mapping is correct. Runs on the import background thread, not the event loop, so no executor needed.

### `import_ws.py` — Add MB search endpoint

```
GET /api/library/import/mb-search?q=<query>
```

- If `q` contains a UUID or looks like a MB URL: `metadata_plugins.albums_for_ids([q])` (returns ≤1 result)
- If text: `metadata_plugins.candidates([], artist, album, False)`, limit 5 results
  - Split on ` - ` for artist/album; if no ` - `, use full string as album with empty artist
- Both calls are sync network I/O → wrap in `run_in_executor`
- Returns `{"results": [{artist, album, year, label, country, mb_albumid, track_count, tracks}]}`

Note: `album_for_id` in the MB plugin already handles URL extraction via `_extract_id`, so MB URLs passed directly to `albums_for_ids` work correctly.

---

## Frontend Implementation

### Types

```typescript
type ImportSessionState = '...' | 'waiting_no_candidates'  // add new state

interface NoCandidatesPayload {
  album_path: string
  file_tracks: FileTrack[]
}

interface ImportChoice {
  action: 'apply' | 'as_is' | 'skip' | 'singleton' | 'abort'
  candidate_index?: number
  mb_id?: string  // add optional field
}
```

### Store changes

- Add `noCandidatesPayload = ref<NoCandidatesPayload | null>(null)`
- Handle `no_candidates` WS event: set state to `waiting_no_candidates`, store payload
- Clear `noCandidatesPayload` in `submitChoice` and `resetSession`

### `CandidateList.vue` — MB search section

Collapsible section below the action bar. Always visible when the component is shown (works for both "wrong candidates" and "no candidates" use cases).

- Text input: "Paste MB URL or search Artist - Album"
- Search button → `GET /api/library/import/mb-search?q=...` → shows mini result cards
- User clicks a result card to select it
- "Apply This Release" button → `store.submitChoice({ action: 'apply', mb_id: result.mb_albumid })`

### `NoCandidatesPanel.vue` — New component

Shown when state is `waiting_no_candidates`. Contains:
- Header with album path and folder name
- File track list from `noCandidatesPayload.file_tracks`
- Embedded MB search section (same as CandidateList's section)
- Action buttons: Apply Selected, Import As-Is, Skip

### `ImportView.vue`

Add `v-else-if="store.sessionState === 'waiting_no_candidates'"` branch showing `NoCandidatesPanel` (same layout as `waiting_choice` — progress at top, panel below).

---

## Gotchas

1. **`run_in_executor` required** in the REST endpoint — `musicbrainzngs` is synchronous. NOT needed inside `webimport.py` (runs on background thread).

2. **`tag_album` is a network call** (~1–3s). The import thread blocks during `_fetch_mb_release`. Consider sending a fire-and-forget progress event before the call so the browser shows something is happening.

3. **MB rate limiting** — MusicBrainz enforces 1 req/s. Beets' MB module handles this internally. Still, debounce the search input on the frontend (~400ms) to avoid rapid-fire requests.

4. **`send_no_candidates` shares `_choice_event`** with `send_candidates` — this is correct because the two paths are mutually exclusive per task. No race condition possible.

5. **Existing dead-code branch** in `CandidateList.vue` — the `v-if="store.candidates.length === 0"` no-candidates block will no longer be reached from the normal import flow after this change (the backend emits `no_candidates` instead of `candidates` with empty list). Harmless to leave; remove in a follow-up cleanup.

---

## Implementation Order

1. Backend: `send_no_candidates` in `import_service.py`
2. Backend: `webimport.py` routing + `_fetch_mb_release`
3. Backend: `mb-search` REST endpoint (testable with curl)
4. Frontend: types
5. Frontend: store
6. Frontend: `NoCandidatesPanel.vue`
7. Frontend: `CandidateList.vue` search section
8. Frontend: `ImportView.vue` branch
