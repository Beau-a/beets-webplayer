# Beets Web GUI — System Architecture

## 1. Overview

A web-based GUI for the beets music library manager, providing album/track browsing with cover art, full-text search using beets query syntax, in-browser audio playback with queue management, metadata editing, and — critically — an interactive browser-based import dialog that replaces beets' terminal-based candidate selection. The system wraps the beets Python API in a FastAPI backend, communicates with a Vue 3 SPA over REST and WebSockets, and introduces a custom beets plugin to intercept the import pipeline and delegate candidate selection to the browser.

**Design goals**: responsive browsing of a ~5,500-track library, real-time import interaction without deadlocks, gapless audio streaming via HTTP range requests, and a clean separation between beets internals and the web layer.

**Constraints**: single-user deployment on a LAN (no multi-tenancy), SQLite at `/mnt/nfs/musiclibrary.db`, audio files on the same NFS mount, beets v1.4.6.

---

## 2. Project Directory Structure

```
/mnt/nfs/beau/beets/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # FastAPI app factory
│   │   ├── config.py                # Settings (paths, CORS, beets config)
│   │   ├── dependencies.py          # Dependency injection (Library, DB session)
│   │   ├── main.py                  # Entrypoint: uvicorn target
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── album.py             # Pydantic response models for albums
│   │   │   ├── item.py              # Pydantic response models for items/tracks
│   │   │   ├── import_models.py     # Pydantic models for import WS messages
│   │   │   └── common.py            # Pagination, error, shared models
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── albums.py            # /api/albums endpoints
│   │   │   ├── items.py             # /api/items endpoints
│   │   │   ├── playback.py          # /api/stream/{item_id} audio endpoint
│   │   │   ├── library.py           # /api/library (stats, management ops)
│   │   │   ├── import_ws.py         # /ws/import WebSocket endpoint
│   │   │   └── metadata.py          # /api/metadata (edit, mbsync, lyrics)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── library_service.py   # Beets Library wrapper, query translation
│   │   │   ├── import_service.py    # Import session manager, plugin bridge
│   │   │   ├── stream_service.py    # File reading, range request logic
│   │   │   └── metadata_service.py  # Tag writing, mbsync, lyrics fetch
│   │   └── plugin/
│   │       ├── __init__.py
│   │       └── webimport.py         # The beets plugin: WebImportPlugin
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── tests/
│       ├── conftest.py
│       ├── test_albums.py
│       ├── test_items.py
│       ├── test_stream.py
│       └── test_import.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── env.d.ts
│   ├── src/
│   │   ├── main.ts                  # App bootstrap
│   │   ├── App.vue                  # Root: AppLayout + RouterView
│   │   ├── router/
│   │   │   └── index.ts             # Vue Router definitions
│   │   ├── stores/
│   │   │   ├── player.ts            # Pinia: playback state, queue
│   │   │   ├── library.ts           # Pinia: albums, items, search, filters
│   │   │   ├── import.ts            # Pinia: import session, WS state
│   │   │   └── ui.ts                # Pinia: sidebar, theme, layout prefs
│   │   ├── composables/
│   │   │   ├── useWebSocket.ts      # WebSocket connect/reconnect/message routing
│   │   │   ├── useAudioPlayer.ts    # HTML5 Audio wrapper, range-request aware
│   │   │   └── useBeetsQuery.ts     # Query string builder helper
│   │   ├── api/
│   │   │   ├── client.ts            # Axios instance, base URL, interceptors
│   │   │   ├── albums.ts            # Album API functions
│   │   │   ├── items.ts             # Item API functions
│   │   │   └── library.ts           # Library/metadata API functions
│   │   ├── views/
│   │   │   ├── LibraryView.vue      # Main browse view (album grid + filters)
│   │   │   ├── AlbumDetailView.vue  # Single album with track listing
│   │   │   ├── SearchView.vue       # Dedicated search results page
│   │   │   ├── ImportView.vue       # Import dashboard + interactive dialog
│   │   │   ├── QueueView.vue        # Current play queue management
│   │   │   └── SettingsView.vue     # Library stats, management actions
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppLayout.vue    # Shell: sidebar + main + player bar
│   │   │   │   ├── AppSidebar.vue   # Navigation sidebar
│   │   │   │   └── PlayerBar.vue    # Persistent bottom player
│   │   │   ├── albums/
│   │   │   │   ├── AlbumGrid.vue    # Responsive grid of AlbumCards
│   │   │   │   ├── AlbumCard.vue    # Cover art + artist + year
│   │   │   │   └── AlbumTrackList.vue # Track table for one album
│   │   │   ├── player/
│   │   │   │   ├── PlaybackControls.vue  # Play/pause/skip/shuffle/repeat
│   │   │   │   ├── ProgressBar.vue       # Seekable track progress
│   │   │   │   ├── VolumeControl.vue     # Volume slider + mute
│   │   │   │   └── QueueDrawer.vue       # Slide-out queue panel
│   │   │   ├── search/
│   │   │   │   ├── SearchBar.vue         # Top search input w/ query syntax hints
│   │   │   │   └── FilterPanel.vue       # Faceted filters (genre, year, format)
│   │   │   └── import/
│   │   │       ├── ImportStart.vue       # Directory picker + start button
│   │   │       ├── CandidateCard.vue     # One MusicBrainz match w/ score
│   │   │       ├── CandidateList.vue     # All candidates for current album
│   │   │       ├── TrackComparison.vue   # Side-by-side: file tags vs MB data
│   │   │       └── ImportProgress.vue    # Overall import session progress
│   │   ├── types/
│   │   │   ├── album.ts
│   │   │   ├── item.ts
│   │   │   ├── player.ts
│   │   │   └── import.ts
│   │   └── utils/
│   │       ├── formatters.ts        # Duration, bitrate, date formatting
│   │       └── constants.ts         # API base URL, WS URL, etc.
│   └── public/
│       └── favicon.ico
├── docs/
│   ├── beets-api-reference.md       # (existing)
│   └── architecture.md              # (this document)
├── docker-compose.yml               # Optional: backend + frontend containers
└── Makefile                         # dev shortcuts: run, lint, test
```

---

## 3. Backend Architecture

### 3.1 FastAPI App Initialization

**File**: `backend/app/__init__.py`

The app factory creates a FastAPI instance with:
- CORS middleware allowing the Vite dev server origin (`http://localhost:3000`)
- Router includes for each feature module
- A lifespan context manager that opens the beets `Library` on startup and closes it on shutdown
- The `Library` instance stored in `app.state.lib` and exposed via a FastAPI dependency (`get_library`)

```
def get_library(request: Request) -> Library:
    return request.app.state.lib
```

**Config** (`backend/app/config.py`): Pydantic `BaseSettings` class reading from environment or `.env`:
- `BEETS_DB_PATH` = `/mnt/nfs/musiclibrary.db`
- `BEETS_CONFIG_PATH` = path to beets config.yaml (needed for write operations and import)
- `MUSIC_BASE_PATH` = `/mnt/nfs/` (for resolving file paths)
- `CORS_ORIGINS` = `["http://localhost:3000"]`
- `HOST` / `PORT` = `0.0.0.0` / `5000`

### 3.2 Beets Library Initialization

The Library object is **initialized once** at app startup using beets' own `Library` constructor with the SQLite path. For operations that need the full beets config (import, mbsync), the `beets.util.confit` config system must also be loaded. This is done in the lifespan:

```
1. Load beets config from BEETS_CONFIG_PATH
2. Initialize Library(BEETS_DB_PATH, ...)
3. Register the WebImportPlugin (see section 6)
4. Store lib on app.state
```

**Thread safety**: beets Library uses SQLite underneath. Since FastAPI runs on asyncio, all beets Library calls that touch the DB must be dispatched to a thread pool via `asyncio.to_thread()` or `run_in_executor()`. This prevents blocking the event loop and avoids SQLite threading issues. Use a single-thread executor for all Library operations to serialize DB access.

### 3.3 Router Breakdown

| Router file | Prefix | Purpose |
|---|---|---|
| `albums.py` | `/api/albums` | Album CRUD, listing, search |
| `items.py` | `/api/items` | Track CRUD, listing, search |
| `playback.py` | `/api/stream` | Audio file streaming |
| `library.py` | `/api/library` | Stats, management operations |
| `metadata.py` | `/api/metadata` | Tag editing, mbsync, lyrics |
| `import_ws.py` | `/ws/import` | WebSocket for interactive import |

### 3.4 Audio Streaming Design

**Endpoint**: `GET /api/stream/{item_id}`

This must support **HTTP range requests** for seeking in audio players.

Logic:
1. Look up `item.path` from the library by `item_id`
2. Decode the bytes path to a filesystem string
3. Verify the file exists; return 404 if not
4. Read the `Range` header from the request
5. If no Range header: return the full file with `200 OK`, `Content-Type` based on format (audio/mpeg, audio/flac, audio/ogg, etc.), and `Accept-Ranges: bytes`
6. If Range header present: parse byte range, return `206 Partial Content` with correct `Content-Range` header, streaming the requested byte range
7. Use `StreamingResponse` with a file-reading generator (read in 64KB chunks)

A `Content-Length` header is required in both cases. Set `Cache-Control: public, max-age=86400` since audio files rarely change.

**Cover art endpoint**: `GET /api/albums/{album_id}/art`
- Read `album.artpath`, serve the image file
- If `artpath` is null/missing, return 404 (frontend shows a placeholder)

### 3.5 Background Task Handling

For long-running beets operations that are NOT the interactive import (e.g., mbsync on the whole library, lyrics fetch):

- Use FastAPI `BackgroundTasks` for fire-and-forget operations
- Track task status in an in-memory dict: `task_id -> {status, progress, error}`
- Expose `GET /api/library/tasks/{task_id}` for polling
- Optionally push progress updates via a separate general-purpose WebSocket at `/ws/tasks`

For the **interactive import**, see section 6 (the dedicated plugin design).

---

## 4. Frontend Architecture

### 4.1 Component Hierarchy

```
App.vue
└── AppLayout.vue
    ├── AppSidebar.vue                    # Fixed left sidebar
    │   └── Navigation links
    ├── <RouterView />                    # Main content area
    │   ├── LibraryView.vue
    │   │   ├── SearchBar.vue
    │   │   ├── FilterPanel.vue
    │   │   └── AlbumGrid.vue
    │   │       └── AlbumCard.vue (x N)
    │   ├── AlbumDetailView.vue
    │   │   ├── Album header (art, metadata)
    │   │   └── AlbumTrackList.vue
    │   ├── SearchView.vue
    │   │   ├── SearchBar.vue
    │   │   ├── FilterPanel.vue
    │   │   └── Results (albums + tracks mixed)
    │   ├── ImportView.vue
    │   │   ├── ImportStart.vue
    │   │   ├── ImportProgress.vue
    │   │   └── CandidateList.vue
    │   │       ├── CandidateCard.vue (x N)
    │   │       └── TrackComparison.vue
    │   ├── QueueView.vue
    │   └── SettingsView.vue
    └── PlayerBar.vue                     # Fixed bottom bar, always visible
        ├── Now-playing info (art thumbnail, title, artist)
        ├── PlaybackControls.vue
        ├── ProgressBar.vue
        ├── VolumeControl.vue
        └── QueueDrawer.vue (toggle)
```

### 4.2 Vue Router

```
/                    → redirect to /library
/library             → LibraryView.vue
/library/:albumId    → AlbumDetailView.vue
/search              → SearchView.vue (query in ?q= param)
/import              → ImportView.vue
/queue               → QueueView.vue
/settings            → SettingsView.vue
```

All routes render inside `AppLayout.vue`'s `<RouterView />`. The `PlayerBar` is outside the router — it persists across all navigation.

### 4.3 Pinia Stores

#### `player.ts` — Player Store

```
State:
  currentTrack: Item | null        // Currently playing track
  queue: Item[]                    // Ordered play queue
  queueIndex: number               // Position in queue (-1 = nothing)
  isPlaying: boolean
  currentTime: number              // Seconds into current track
  duration: number                 // Total length of current track
  volume: number                   // 0.0 - 1.0
  isMuted: boolean
  repeatMode: 'off' | 'all' | 'one'
  shuffleEnabled: boolean

Actions:
  play(track: Item)                // Clear queue, play this track
  playAlbum(albumId, startTrack?)  // Queue all album tracks, start playing
  addToQueue(track: Item)          // Append to queue
  addToQueueNext(track: Item)      // Insert after current
  removeFromQueue(index: number)
  clearQueue()
  next()                           // Advance (respect shuffle/repeat)
  previous()                       // Go back
  seek(seconds: number)
  setVolume(v: number)
  toggleMute()
  toggleShuffle()
  cycleRepeat()

Getters:
  hasNext: boolean
  hasPrevious: boolean
  streamUrl: string                // Computed: /api/stream/{currentTrack.id}
  progress: number                 // 0-100 percentage
```

The store does NOT hold the Audio element. The `useAudioPlayer` composable owns the `HTMLAudioElement` and syncs its state into this store. This separation allows the store to be purely reactive data while the composable manages the imperative Audio API.

#### `library.ts` — Library Store

```
State:
  albums: Album[]
  totalAlbums: number
  currentAlbum: Album | null
  currentAlbumTracks: Item[]
  searchResults: { albums: Album[], items: Item[] }
  filters: {
    query: string                  // Raw beets query string
    genre: string | null
    yearFrom: number | null
    yearTo: number | null
    format: string | null
    sort: string                   // e.g. 'albumartist+' 'year-'
  }
  pagination: { page: number, pageSize: number }
  isLoading: boolean

Actions:
  fetchAlbums()                    // Paginated, filtered
  fetchAlbum(id: number)           // Single album + tracks
  searchLibrary(query: string)     // Beets query syntax search
  updateFilters(partial)
  resetFilters()
  editItemMetadata(itemId, fields) // PATCH /api/items/:id
  editAlbumMetadata(albumId, fields)
  removeItem(itemId)
  removeAlbum(albumId)

Getters:
  genreList: string[]              // Distinct genres for filter panel
  formatList: string[]             // Distinct formats
  yearRange: [number, number]      // Min/max year
```

#### `import.ts` — Import Store

```
State:
  sessionActive: boolean
  sessionId: string | null
  wsConnected: boolean
  currentAlbumPath: string | null      // Directory being imported right now
  candidates: ImportCandidate[]        // MB candidates for current album
  currentTrackMapping: TrackMapping[]  // File↔MB track comparison
  selectedCandidateIndex: number | null
  importLog: ImportLogEntry[]          // History of all decisions this session
  progress: { completed: number, total: number, currentDir: string }
  error: string | null

Actions:
  startImport(directory: string)       // POST /api/library/import, then open WS
  connectWebSocket()
  sendChoice(choice: ImportChoice)     // Send user's decision to backend via WS
  skipAlbum()
  abortImport()
  applyAsIs()                          // Import without changes
  disconnectWebSocket()

The store subscribes to WS messages and updates its state reactively.
```

#### `ui.ts` — UI Store

```
State:
  sidebarCollapsed: boolean
  queueDrawerOpen: boolean
  theme: 'light' | 'dark'
  albumViewMode: 'grid' | 'list'
  gridSize: 'small' | 'medium' | 'large'

Persisted to localStorage via a Pinia plugin.
```

### 4.4 Composables

#### `useAudioPlayer.ts`

- Creates and manages a single `HTMLAudioElement` instance (module-level singleton)
- Sets `audio.src` to the player store's `streamUrl` whenever `currentTrack` changes
- Listens to `timeupdate`, `ended`, `loadedmetadata`, `error` events and syncs into the player store
- On `ended`: calls `playerStore.next()`
- Exposes: `play()`, `pause()`, `seek(seconds)`, `setVolume(v)` — these manipulate the Audio element and the store updates reactively
- Initialized once in `App.vue` setup, never destroyed

#### `useWebSocket.ts`

- Manages a WebSocket connection to a given URL
- Auto-reconnects with exponential backoff (1s, 2s, 4s, max 30s)
- Accepts a `messageHandlers: Record<string, (payload) => void>` map
- Incoming messages are JSON with shape `{ type: string, payload: any }`
- Provides `send(type, payload)`, `connect()`, `disconnect()`, `isConnected` ref
- Used by the import store to connect to `/ws/import`

#### `useBeetsQuery.ts`

- Helper to build beets query strings from structured filter state
- Converts `{ genre: "Rock", yearFrom: 2000, yearTo: 2010, sort: "year+" }` into `"genre:Rock year:2000..2010 year+"`
- Used by the library store and search components

---

## 5. REST API Contracts

### 5.1 Albums

**`GET /api/albums`** — List albums (paginated, filterable)

Query params:
| Param | Type | Default | Description |
|---|---|---|---|
| `q` | string | `""` | Beets query string |
| `page` | int | `1` | Page number |
| `page_size` | int | `50` | Items per page (max 200) |
| `sort` | string | `"albumartist+"` | Sort field+direction |

Response `200`:
```json
{
  "items": [
    {
      "id": 1,
      "album": "OK Computer",
      "albumartist": "Radiohead",
      "year": 1997,
      "genre": "Alternative Rock",
      "format": "FLAC",
      "disctotal": 1,
      "label": "Parlophone",
      "country": "UK",
      "mb_albumid": "...",
      "track_count": 12,
      "total_length": 3215.4,
      "has_art": true,
      "added": 1700000000
    }
  ],
  "total": 497,
  "page": 1,
  "page_size": 50
}
```

Note: `format` is not a native album field in beets. It must be derived by querying the album's items and returning the most common format (or a comma-separated list if mixed). Compute this in `library_service.py` with a SQL query: `SELECT format, COUNT(*) FROM items WHERE album_id = ? GROUP BY format ORDER BY COUNT(*) DESC LIMIT 1`. Similarly, `track_count` and `total_length` are aggregated from items.

`has_art` is derived from `artpath IS NOT NULL` on the album row.

---

**`GET /api/albums/{album_id}`** — Single album with full metadata

Response `200`:
```json
{
  "id": 1,
  "album": "OK Computer",
  "albumartist": "Radiohead",
  "year": 1997,
  "genre": "Alternative Rock",
  "label": "Parlophone",
  "country": "UK",
  "catalognum": "...",
  "mb_albumid": "...",
  "mb_releasegroupid": "...",
  "albumtype": "album",
  "albumstatus": "Official",
  "disctotal": 1,
  "added": 1700000000,
  "has_art": true,
  "items": [
    {
      "id": 101,
      "title": "Airbag",
      "artist": "Radiohead",
      "track": 1,
      "disc": 1,
      "length": 284.5,
      "format": "FLAC",
      "bitrate": 1024000,
      "samplerate": 44100,
      "bitdepth": 16
    }
  ]
}
```

---

**`GET /api/albums/{album_id}/art`** — Album cover art

Response: raw image bytes with appropriate `Content-Type` (image/jpeg, image/png).
Returns `404` if no art.

---

**`PATCH /api/albums/{album_id}`** — Edit album metadata

Request body:
```json
{
  "album": "OK Computer",
  "year": 1997,
  "genre": "Alternative Rock",
  "label": "Parlophone"
}
```
Only fields present in the body are updated. Valid field names are the album fields from the beets schema. The service calls `album[field] = value` then `album.store()` for each field, inside a beets transaction. This writes to the database. To also write tags to files, the service must then call `album.try_sync(True)` to propagate changes to embedded tags.

Response `200`: updated album object (same shape as GET single album)

---

**`DELETE /api/albums/{album_id}`** — Remove album from library

Query param: `delete_files=false` (if true, also delete audio files from disk)

Calls `album.remove(delete=delete_files)` which removes the album and its items from the beets DB and optionally the filesystem.

Response `204` No Content

---

### 5.2 Items (Tracks)

**`GET /api/items`** — List/search items

Query params: same as albums (`q`, `page`, `page_size`, `sort`)

Response `200`:
```json
{
  "items": [
    {
      "id": 101,
      "title": "Airbag",
      "artist": "Radiohead",
      "album": "OK Computer",
      "album_id": 1,
      "track": 1,
      "disc": 1,
      "year": 1997,
      "genre": "Alternative Rock",
      "length": 284.5,
      "format": "FLAC",
      "bitrate": 1024000,
      "samplerate": 44100,
      "bitdepth": 16,
      "added": 1700000000
    }
  ],
  "total": 5565,
  "page": 1,
  "page_size": 50
}
```

---

**`GET /api/items/{item_id}`** — Single item, full metadata

Returns all item fields from the beets schema (the full ~91 field set, minus `path` and `acoustid_fingerprint` which are large/sensitive).

---

**`PATCH /api/items/{item_id}`** — Edit item metadata

Same pattern as album PATCH. Calls `item[field] = value`, `item.store()`, then `item.try_sync(True)` to write tags.

Request body: partial field object
Response `200`: updated item

---

**`DELETE /api/items/{item_id}`** — Remove item from library

Query param: `delete_file=false`
Response `204`

---

### 5.3 Audio Streaming

**`GET /api/stream/{item_id}`** — Stream audio file

Request headers:
- `Range: bytes=0-` (optional)

Response `200` (no Range) or `206` (with Range):
- `Content-Type: audio/flac` | `audio/mpeg` | `audio/ogg` | etc.
- `Accept-Ranges: bytes`
- `Content-Length: <total or partial length>`
- `Content-Range: bytes 0-999999/1000000` (only for 206)
- Body: raw audio bytes

---

### 5.4 Library Management

**`GET /api/library/stats`** — Library statistics

Response `200`:
```json
{
  "total_albums": 497,
  "total_items": 5565,
  "total_duration": 1234567.8,
  "total_size_bytes": 98765432100,
  "format_breakdown": { "FLAC": 3200, "MP3": 2365 },
  "genre_breakdown": { "Rock": 1500, "Electronic": 800, ... },
  "year_range": [1960, 2025],
  "artists_count": 245
}
```

These stats are computed via direct SQL for performance:
```sql
SELECT format, COUNT(*) FROM items GROUP BY format;
SELECT MIN(year), MAX(year) FROM albums WHERE year > 0;
SELECT COUNT(DISTINCT albumartist) FROM albums;
SELECT SUM(length) FROM items;
-- total_size_bytes via SUM(filesize) if available, or estimate from bitrate*length
```

---

**`POST /api/library/import`** — Start an import session

Request body:
```json
{
  "directory": "/mnt/nfs/incoming/NewAlbum",
  "options": {
    "copy": true,
    "move": false,
    "write_tags": true,
    "autotag": true
  }
}
```

Response `202`:
```json
{
  "session_id": "uuid-string",
  "ws_url": "/ws/import?session_id=uuid-string"
}
```

This starts the import in a background thread. The client must connect to the WebSocket to interact with it.

---

**`POST /api/library/tasks`** — Run a management task

Request body:
```json
{
  "task": "mbsync",
  "options": { "pretend": false }
}
```

Supported tasks: `mbsync`, `lyrics`, `fetchart`, `replaygain`

Response `202`:
```json
{
  "task_id": "uuid-string",
  "status": "running"
}
```

**`GET /api/library/tasks/{task_id}`** — Check task status

Response `200`:
```json
{
  "task_id": "...",
  "task": "mbsync",
  "status": "running" | "completed" | "failed",
  "progress": { "completed": 150, "total": 497 },
  "error": null,
  "started_at": "2026-03-29T10:00:00Z"
}
```

---

### 5.5 Metadata Operations

**`POST /api/metadata/items/{item_id}/lyrics`** — Fetch lyrics for a single track

Response `200`:
```json
{
  "item_id": 101,
  "lyrics": "I am born in a crossfire hurricane...",
  "source": "Genius"
}
```

---

### 5.6 Facets / Filter Options

**`GET /api/library/facets`** — Distinct values for filter UI

Response `200`:
```json
{
  "genres": ["Alternative Rock", "Electronic", "Jazz", ...],
  "formats": ["FLAC", "MP3", "AAC"],
  "labels": ["Parlophone", "Warp Records", ...],
  "year_range": [1960, 2025]
}
```

Computed via SQL `SELECT DISTINCT` queries. Cache this in memory and invalidate on `database_change` events from beets.

---

## 6. The Beets Import Plugin — `WebImportPlugin`

This is the most architecturally complex piece. The beets import pipeline is a synchronous, blocking process that expects a human at a terminal. We must intercept it and redirect the UI to the browser.

### 6.1 Architecture Overview

```
┌─────────────┐      ┌──────────────────────┐      ┌──────────────┐
│   Browser    │◄────►│   FastAPI (asyncio)   │◄────►│ Import Thread │
│  (Vue SPA)  │  WS  │                      │      │  (beets)     │
│             │      │  /ws/import endpoint  │      │              │
│ CandidateList│◄────│  import_ws.py router  │◄────│ WebImport    │
│ user clicks │────►│                      │────►│  Plugin       │
│  "Apply"    │      │  import_service.py    │      │              │
└─────────────┘      └──────────────────────┘      └──────────────┘
                              ▲                           │
                              │      threading.Event      │
                              └───────────────────────────┘
```

### 6.2 Communication Bridge

The plugin runs in a **background thread** (the import process is blocking). The FastAPI WebSocket handler runs in the **asyncio event loop**. They communicate via a **shared bridge object**:

**`ImportBridge`** (in `import_service.py`):

```
class ImportBridge:
    Attributes:
        session_id: str
        _candidate_queue: asyncio.Queue    # Plugin → FastAPI: candidate data
        _choice_event: threading.Event     # Signal: user has made a choice
        _user_choice: ImportChoice | None  # The choice itself
        _progress_queue: asyncio.Queue     # Plugin → FastAPI: progress events
        _cancel_event: threading.Event     # FastAPI → Plugin: abort import

    Methods:
        # Called from the beets plugin thread (blocking side):
        send_candidates(task, candidates) → blocks until user responds
        send_progress(event_type, data)
        check_cancelled() → bool

        # Called from the FastAPI async side:
        async get_next_event() → dict       # Awaits from candidate/progress queues
        async submit_choice(choice)          # Sets user_choice, signals event
        cancel()
```

The critical flow for `send_candidates()`:

1. Plugin calls `bridge.send_candidates(task, candidates)` from the import thread
2. This method puts the candidate data onto `_candidate_queue` (thread-safe with `asyncio.Queue` via `loop.call_soon_threadsafe`)
3. It then calls `_choice_event.wait()` — this **blocks the import thread** until the user responds
4. When the user clicks a choice in the browser, FastAPI calls `bridge.submit_choice(choice)` which sets `_user_choice` and calls `_choice_event.set()`
5. `send_candidates()` unblocks, reads `_user_choice`, clears the event, and returns the choice to the plugin
6. The plugin returns the choice to beets, and the import pipeline continues

### 6.3 Plugin Implementation Design

**File**: `backend/app/plugin/webimport.py`

The plugin is a `BeetsPlugin` subclass. It does NOT use the standard `before_choose_candidate` event because that event in beets v1.4.6 doesn't cleanly allow intercepting the candidate selection flow. Instead, the plugin provides a **custom import session** that replaces the interactive prompt.

The approach:

1. The plugin subclasses or monkey-patches `beets.ui.commands.PromptChoice` / the `choose_match` function that the importer calls when it needs user input
2. Specifically, beets' `importer.py` calls `choose_match(task)` during album import and `choose_item(task)` during singleton import. These are the interception points.
3. The plugin replaces these functions with versions that:
   a. Serialize the `task` object's candidates into JSON-safe dicts
   b. Send them to the browser via the bridge
   c. Block waiting for the user's response
   d. Return the appropriate beets action/selection

**What the plugin sends for each candidate set** (the `ImportCandidateSet` message):

```
{
  "type": "candidates",
  "payload": {
    "album_path": "/mnt/nfs/incoming/Radiohead - OK Computer",
    "file_tracks": [
      {
        "filename": "01 - Airbag.flac",
        "title": "Airbag",
        "artist": "Radiohead",
        "track": 1,
        "length": 284.5
      }
    ],
    "candidates": [
      {
        "index": 0,
        "distance": 0.02,
        "artist": "Radiohead",
        "album": "OK Computer",
        "year": 1997,
        "label": "Parlophone",
        "country": "UK",
        "mb_albumid": "a1b2c3...",
        "media": "CD",
        "track_count": 12,
        "tracks": [
          {
            "title": "Airbag",
            "artist": "Radiohead",
            "track": 1,
            "length": 284.0,
            "mb_trackid": "..."
          }
        ],
        "extra_tracks": [],
        "missing_tracks": []
      }
    ],
    "rec": "strong"
  }
}
```

`distance` is beets' match distance (0.0 = perfect, 1.0 = no match). `rec` is beets' recommendation level: `"strong"`, `"medium"`, `"low"`, or `"none"`.

**What the browser sends back** (`ImportChoice` message):

```
{
  "type": "choice",
  "payload": {
    "action": "apply",
    "candidate_index": 0
  }
}
```

Supported actions:
| Action | Description |
|---|---|
| `apply` | Accept candidate at `candidate_index` |
| `as_is` | Import with existing tags, no changes |
| `skip` | Skip this album entirely |
| `singleton` | Import tracks as individual singletons |
| `abort` | Cancel the entire import session |

### 6.4 Deadlock Prevention

Deadlocks can occur if:

1. **The import thread blocks but the WS disconnects**: The bridge must have a timeout on `_choice_event.wait(timeout=300)`. If it times out (5 minutes of no response), treat as "skip". Also check `_cancel_event` periodically.

2. **The asyncio loop is blocked**: Never. All beets operations run in the import thread, not the event loop. The FastAPI side only does async queue reads and WS sends.

3. **Multiple imports simultaneously**: Disallow this. The `ImportService` tracks a single active session. `POST /api/library/import` returns `409 Conflict` if a session is already running.

4. **WS disconnects mid-import**: The bridge detects this (FastAPI side sets a disconnect flag). The import thread checks on next candidate and either pauses (waits for reconnect for 60s) or aborts.

### 6.5 Import Progress Events

Besides candidate selection, the plugin also streams these events via the bridge:

| Event type | When | Payload |
|---|---|---|
| `session_start` | Import begins | `{ directory, estimated_albums }` |
| `album_start` | Starting to process an album dir | `{ path }` |
| `candidates` | MB lookup complete, need user choice | (see above) |
| `album_imported` | Album successfully imported | `{ album, artist, year, track_count }` |
| `album_skipped` | User skipped | `{ path }` |
| `item_moved` | File moved/copied | `{ from, to }` |
| `error` | Error processing an album | `{ path, message }` |
| `session_complete` | Import finished | `{ total_imported, total_skipped, total_errors }` |

---

## 7. WebSocket Message Schema

All WebSocket messages use a uniform envelope:

```json
{
  "type": "string",
  "payload": { ... },
  "timestamp": "ISO-8601"
}
```

### 7.1 Server-to-Client Messages (import WS)

| type | payload | description |
|---|---|---|
| `session_start` | `{ directory: str, estimated_albums: int }` | Import session begun |
| `album_start` | `{ path: str }` | Processing new album directory |
| `candidates` | `ImportCandidateSet` (see section 6.3) | Candidates ready, awaiting choice |
| `album_imported` | `{ album: str, artist: str, year: int, track_count: int }` | Successfully imported |
| `album_skipped` | `{ path: str, reason: str }` | Skipped |
| `item_moved` | `{ from_path: str, to_path: str }` | File moved/copied |
| `error` | `{ path: str, message: str }` | Error on one album |
| `session_complete` | `{ total_imported: int, total_skipped: int, total_errors: int, duration_s: float }` | Done |
| `heartbeat` | `{}` | Keepalive every 30s |

### 7.2 Client-to-Server Messages (import WS)

| type | payload | description |
|---|---|---|
| `choice` | `{ action: str, candidate_index?: int }` | User's import decision |
| `abort` | `{}` | Cancel entire import |

---

## 8. Technology Decisions

### 8.1 WebSocket Library

**Decision**: Use FastAPI/Starlette's built-in WebSocket support.

Rationale: FastAPI's `WebSocket` class (from Starlette) is production-grade, supports the patterns we need (accept, send_json, receive_json, close), and requires no additional dependency. No need for the standalone `websockets` library or Socket.IO — we have a single WS endpoint with simple JSON messages.

### 8.2 Vue Component Library

**Decision**: **PrimeVue** (v4+)

Rationale:
- Provides a `DataTable` (for track listings with sorting), `DataView` (for album grid/list toggle), `Dialog`, `ProgressBar`, `Slider` (volume, seek), `Button`, `InputText`, `Chip`, `Tag` — all needed for this UI
- Unstyled mode available — lets us apply custom dark-themed music-player styling without fighting the framework
- Lighter than Vuetify, more components than Headless UI
- Tree-shakeable: only import what we use
- Good Vue 3 + TypeScript support

Alternative considered: Vuetify 3 — heavier, Material Design look harder to customize for a music player aesthetic. Rejected.
Alternative considered: No component library — too much work building DataTable, Slider, Dialog from scratch. Rejected.

### 8.3 Audio Player Approach

**Decision**: Native `HTMLAudioElement` wrapped in the `useAudioPlayer` composable.

Rationale:
- `HTMLAudioElement` natively supports HTTP range requests (required for seeking in streaming audio)
- Setting `audio.src = "/api/stream/123"` just works — the browser handles range negotiation automatically
- No library needed; `howler.js` or similar would add complexity with no benefit for our single-stream use case
- We are NOT doing gapless playback or complex audio routing — if that becomes a requirement later, we'd consider the Web Audio API

The `audio.preload` attribute should be set to `"auto"` so the browser buffers ahead. For `next()`, we can preload the next track by creating a second `Audio` object.

### 8.4 HTTP Client (Frontend)

**Decision**: **Axios**

Rationale: familiar API, interceptors for error handling, good TypeScript support. `fetch` would also work but Axios's interceptor pattern is cleaner for centralized error toasts.

### 8.5 CSS Strategy

**Decision**: **Tailwind CSS** with PrimeVue unstyled mode + custom Tailwind-based theme.

Rationale: rapid styling, dark mode support built in (`dark:` variant), pairs naturally with PrimeVue's unstyled/passthrough mode. The music player UI benefits from a custom dark theme that Tailwind makes easy to build.

### 8.6 Python Dependencies (Backend)

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn[standard]` | ASGI server (with uvloop, httptools) |
| `beets` | Music library manager |
| `pydantic>=2` | Request/response models (bundled with FastAPI) |
| `python-multipart` | File upload support (if needed for art) |
| `aiofiles` | Async file I/O for streaming responses |

No ORM needed — beets owns the SQLite database. Direct SQLite access (via `sqlite3` module) for read-heavy endpoints; beets API for write operations.

### 8.7 Hybrid Data Access Strategy

**Decision**: Use **direct SQLite** for read-only list/search/stats endpoints. Use the **beets Library API** for write operations (metadata editing, imports, removals).

Rationale: The beets Library API is synchronous and loads full model objects. For listing 50 albums with aggregated track counts, a single SQL query is orders of magnitude faster than iterating beets Album objects. However, writes must go through beets to ensure tags are synced to files and plugins are notified.

Implementation: `library_service.py` holds both a `sqlite3` connection (for reads) and the beets `Library` object (for writes). Read methods use raw SQL. Write methods use `lib.get_item()` / `lib.get_album()` then mutate and store.

---

## 9. Implementation Sequence

This is ordered for a single developer. Steps marked [parallel] can overlap.

### Phase 1: Project Scaffolding (1-2 days)

1. Initialize the project directory structure at `/mnt/nfs/beau/beets/`
2. Set up Python venv at `backend/venv`, install FastAPI + uvicorn + beets
3. Create `backend/app/main.py` with hello-world FastAPI app
4. Scaffold Vue 3 project with `npm create vite@latest frontend -- --template vue-ts`
5. Install PrimeVue, Pinia, Vue Router, Axios, Tailwind CSS
6. Configure Vite proxy: `/api` and `/ws` forward to `localhost:5000`
7. Verify both servers start and the frontend can hit the backend

### Phase 2: Read-Only Library Browsing (3-4 days) [Backend + Frontend parallelizable]

8. **Backend**: Implement `config.py`, `dependencies.py`, beets Library initialization in lifespan
9. **Backend**: Implement `library_service.py` with SQLite read methods
10. **Backend**: Implement `GET /api/albums` (paginated, with beets query support)
11. **Backend**: Implement `GET /api/albums/{id}` (single album + tracks)
12. **Backend**: Implement `GET /api/albums/{id}/art` (cover art serving)
13. **Backend**: Implement `GET /api/items` (paginated, searchable)
14. **Backend**: Implement `GET /api/library/stats` and `GET /api/library/facets`
15. **Frontend**: Build `AppLayout`, `AppSidebar`, routing shell
16. **Frontend**: Build `library.ts` Pinia store with fetch actions
17. **Frontend**: Build `AlbumGrid`, `AlbumCard` components
18. **Frontend**: Build `LibraryView` with album grid, pagination
19. **Frontend**: Build `AlbumDetailView` with `AlbumTrackList`
20. **Frontend**: Build `SearchBar`, `FilterPanel`, `SearchView`
21. **Frontend**: Build `useBeetsQuery` composable
22. Wire frontend to backend; test browsing the real library

### Phase 3: Audio Playback (2-3 days)

23. **Backend**: Implement `GET /api/stream/{item_id}` with range request support
24. **Frontend**: Build `player.ts` Pinia store
25. **Frontend**: Build `useAudioPlayer` composable
26. **Frontend**: Build `PlayerBar` with `PlaybackControls`, `ProgressBar`, `VolumeControl`
27. **Frontend**: Build `QueueDrawer` and `QueueView`
28. **Frontend**: Add "play" buttons to `AlbumTrackList` and `AlbumCard`
29. Test: play tracks, seek, queue management, album playback, next/previous

### Phase 4: Interactive Import (3-5 days)

30. **Backend**: Implement `ImportBridge` class in `import_service.py`
31. **Backend**: Implement `WebImportPlugin` in `plugin/webimport.py`
32. **Backend**: Implement `POST /api/library/import` endpoint
33. **Backend**: Implement `/ws/import` WebSocket endpoint in `import_ws.py`
34. **Backend**: Test plugin integration — run an import, verify candidates are serialized
35. **Frontend**: Build `import.ts` Pinia store
36. **Frontend**: Build `useWebSocket` composable
37. **Frontend**: Build `ImportStart` (directory input + start button)
38. **Frontend**: Build `CandidateCard`, `CandidateList`, `TrackComparison`
39. **Frontend**: Build `ImportProgress`
40. **Frontend**: Build `ImportView` assembling all import components
41. End-to-end test: import a real album directory, select candidate in browser, verify it imports

### Phase 5: Metadata Editing & Management (2-3 days)

42. **Backend**: Implement `PATCH /api/items/{id}` and `PATCH /api/albums/{id}` with tag writing
43. **Backend**: Implement `DELETE` endpoints for items and albums
44. **Backend**: Implement `POST /api/library/tasks` for mbsync/lyrics/fetchart
45. **Backend**: Implement `GET /api/library/tasks/{id}` for task polling
46. **Frontend**: Add inline edit UI to `AlbumDetailView` and track lists
47. **Frontend**: Build `SettingsView` with stats display and management action buttons
48. Test: edit a track title, verify it writes to file tags; run mbsync

### Phase 6: Polish & Hardening (2-3 days)

49. Error handling: toast notifications for API errors, WS disconnect handling
50. Loading states: skeleton loaders for album grid, spinner for search
51. Keyboard shortcuts: space=play/pause, left/right=seek, up/down=volume
52. Responsive design: mobile-friendly layout adjustments
53. Performance: virtual scrolling for large result sets (if needed)
54. Dark theme refinement
55. Write integration tests for critical flows

---

## 10. Risks & Decisions Log

### Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **beets import interception is fragile** — beets' internal import flow may change between versions, and monkey-patching `choose_match` is not a stable API | High | Pin beets to v1.4.6. Write integration tests that exercise the import flow. Isolate the patching to a single module (`webimport.py`) for easy updates. |
| **SQLite concurrent access** — FastAPI serves async requests, but SQLite does not handle concurrent writers well | Medium | All writes go through a single-threaded executor. Reads use `sqlite3` in read-only mode with WAL journal mode. Only one import can run at a time. |
| **NFS latency for audio streaming** — audio files are on NFS, which may have variable latency | Medium | Use buffered streaming (64KB chunks). Set `audio.preload = "auto"` in the browser. Consider adding a `Content-Length` header so the browser can show accurate progress. |
| **Large album art files** — some artpath images could be very large BMPs or TIFFs | Low | Serve art through a resizing middleware or cache thumbnails. For v1, just serve the raw file and rely on browser scaling. |
| **WebSocket drops during import** — network hiccup kills the WS mid-import | Medium | Import thread pauses (60s timeout) waiting for reconnect. Frontend auto-reconnects. If timeout expires, import skips remaining albums rather than losing data. |

### Decisions Made

| Decision | Rationale | Alternative Rejected |
|---|---|---|
| Direct SQLite for reads, beets API for writes | Performance for listing 500 albums; correctness for tag writing | Pure beets API (too slow for pagination) |
| Single import session at a time | Avoids SQLite write contention and simplifies bridge | Queued imports (unnecessary complexity for single-user) |
| PrimeVue over Vuetify | Lighter, unstyled mode pairs with Tailwind, sufficient component set | Vuetify (heavy, hard to customize away from Material) |
| Native HTMLAudioElement over Howler.js | Simpler, range requests work natively, no extra dependency | Howler.js (adds abstraction layer we don't need) |
| Monkey-patch `choose_match` over `before_choose_candidate` event | The event in v1.4.6 doesn't provide a mechanism to return a choice; `choose_match` is the actual decision point | Event-based (insufficient API surface) |
| `threading.Event` for plugin-to-async bridge | Simple, proven pattern for thread↔asyncio communication | `asyncio.Queue` alone (doesn't solve blocking in the thread side) |

### Open Questions

1. **Directory browsing for import**: Should the frontend let users browse the server filesystem to pick an import directory, or just type/paste a path? A file browser endpoint (`GET /api/filesystem?path=/mnt/nfs/incoming/`) would be convenient but has security implications. **Recommendation**: Implement a simple directory listing endpoint restricted to a configurable `IMPORT_BASE_PATH` (e.g., `/mnt/nfs/incoming/`), so the user can browse within that directory only.

2. **Album art management**: Should users be able to upload new cover art via the UI? This requires a file upload endpoint and calling `album.set_art(path)`. **Recommendation**: Defer to Phase 6 or later. For v1, art is read-only.

3. **Playlist persistence**: The current design treats the play queue as ephemeral (in-memory Pinia state, lost on page refresh). Should playlists be persisted server-side? **Recommendation**: For v1, persist the queue to `localStorage` via a Pinia persistence plugin. Server-side playlists are a future feature.

4. **Authentication**: The design assumes a trusted LAN with no auth. If the app will be exposed beyond the LAN, add token-based auth. **Recommendation**: Defer auth. If needed later, add a simple shared secret / bearer token.
