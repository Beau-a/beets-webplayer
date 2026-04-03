# Architecture Review: Beets Web GUI

**Date**: 2026-04-02
**Scope**: Full-stack review of the current application with improvement recommendations inspired by Spotify, Plex, Jellyfin, Navidrome, iTunes, and MusicBrainz Picard.

---

## 1. What Is Working Well

### Strong foundations
- **Clean separation of concerns.** The backend has distinct routers, services, and models. The library_service.py is a proper data-access layer with parameterized SQL — no string interpolation. The frontend mirrors this with typed Pinia stores, composables, and API modules.
- **Streaming done right.** The playback router handles HTTP Range requests with async file chunking, path validation against `music_base_path`, and correct `206 Partial Content` responses. This is how Navidrome and Jellyfin do it.
- **Interactive import is genuinely impressive.** The WebSocket-based import pipeline that bridges beets' synchronous `threading.Event` to an async FastAPI WebSocket, letting the user pick MusicBrainz candidates in the browser, is the most technically ambitious part of the app and it works. No other beets GUI has this.
- **Thoughtful player store.** Shuffle with history (so "previous" works correctly during shuffle), repeat modes, buffering state tracking, and the `registerSeekFn` pattern to avoid circular dependencies — all solid.
- **Security basics covered.** Art and stream paths are resolved and validated against `music_base_path`. The `library_service.get_item` deliberately excludes `path` from its response.
- **Album detail view is rich.** Cover art with placeholder fallback, format badges color-coded by type, metadata pills, track list with disc grouping, edit/move/remove actions, file location display.

### Well-chosen patterns
- Using beets' own Library object for writes (tag changes, album removal) while using a read-only SQLite connection for fast queries — this avoids lock contention and is the correct approach for a single-user app.
- The artist browser's letter picker with dimmed letters for unused initials is a nice touch borrowed from physical media UIs.
- PrimeVue is installed but used sparingly — the app has its own consistent design language rather than looking like a component library demo.

---

## 2. Gaps Compared to Popular Music Software

### 2.1 Discovery and Browsing (High Impact)

**Problem:** The app is structured as a database browser, not a music experience. Every music app from Spotify to Jellyfin has a "Home" view that surfaces contextual, curated content. The current app drops you into a paginated album grid with 50 albums per page — there is no sense of "what should I listen to" or "what's new."

**What competitors do:**
- **Spotify/Apple Music**: Home page with recently played, recommended, new releases, jump-back-in cards
- **Plex/Jellyfin**: "Recently Added", "Recently Played", genre shelves, "On This Day" throwbacks
- **Navidrome**: Home with recently played, most played, recently added, random albums
- **iTunes**: "Recently Added" smart playlist as the default landing

**What's missing specifically:**
1. **No "Recently Added" anywhere.** The `added` column exists in the DB and the sort option exists (`added-`), but there's no dedicated section or landing page that shows it.
2. **No "Recently Played" tracking.** The player store doesn't persist play history anywhere. Every session starts from zero context.
3. **No random/discovery.** No "shuffle library" button, no random album picker, no "you might like" section.
4. **No genre browsing.** Genres exist as a filter facet in the library view, but there's no genre page or genre-based browsing experience.

#### Design Decisions (Confirmed 2026-04-02)

**Visual approach:** Plex/Jellyfin-style Home page. Horizontal scrollable shelves per section, album art cards. This matches the existing `AlbumCard` component and is the most natural fit for a personal media library (as opposed to Spotify's playlist-centric approach).

**Home page sections in priority order:**

1. **Recently Added** — albums sorted by `added DESC`. Data already exists in the DB.
2. **Recently Played** — albums/tracks sorted by last play timestamp. Requires the play history table from recommendation 1.2.
3. **Genres** — browsable genre shelves, similar to Plex's genre rows. Each genre gets a horizontal shelf of album cards. Top genres by album count, each showing a scrollable row of albums in that genre.
4. **Recommended** — surfaces forgotten/under-listened content.

**Recommendation algorithm — explicit design decision:**
The "Recommended" shelf deliberately surfaces the **least-played artist** and the **least-played track** in the library, not the most-played. The rationale: in a personal library where the user already owns and chose every album, the goal of recommendations is to resurface forgotten or under-listened content — music the user added but never got around to exploring. This is the opposite of streaming-service recommendations that optimize for engagement with familiar content. Implementation: query `play_history` for artists/tracks with the lowest play counts (including zero plays), then pull albums from those artists. Albums with zero plays are the strongest signal for "you added this but never listened to it."

### 2.2 Artist Experience (Medium-High Impact)

**Problem:** The artist "view" is really just a filtered library query (`?artist=Name`). There's no dedicated artist page with biography, discography grouped by type, or aggregate stats.

**What competitors do:**
- **Spotify**: Artist page with hero image, popular tracks, discography split by Albums/Singles/Compilations, "Fans Also Like"
- **Plex**: Artist page with biography (from Last.fm/MusicBrainz), albums sorted chronologically, track popularity
- **MusicBrainz Picard**: Links to MusicBrainz artist page with rich metadata

**What exists now:**
- `/artist/:artistName` route exists (ArtistView.vue) but was not visible in the sidebar nav. The sidebar only has Library, Player, Tools.
- The library view handles `?artist=Name` from the artist browser flyout and shows a chip filter + action strip (Move Files, Remove from Library).

### 2.3 Now Playing Experience (Medium Impact)

**Problem:** The player bar is functional but minimal. There is no expanded "Now Playing" view — the kind of full-screen album art experience that Spotify, Apple Music, and every serious music player provides.

**What competitors do:**
- **Spotify**: Click the album art in the player bar to expand to a full "Now Playing" view with large art, lyrics, canvas, queue
- **Apple Music/iTunes**: MiniPlayer expands to full window with album art, Up Next, lyrics panel
- **Jellyfin**: Full-screen now playing with background blur of album art

**Current state:**
- The QueueView (`/player`) shows a "Now Playing" card at the top, but it's just text metadata + small art + playback controls. No immersive experience.
- No lyrics display (lyrics are fetched as a background task but never rendered in the UI).

#### Design Decisions (Confirmed 2026-04-02)

**Confirmed approach: Plex-style Now Playing.** The expanded Now Playing view will use:
- **Large album art** (centered, prominent)
- **Blurred album art backdrop** — the album art rendered full-bleed behind the content with heavy blur and a dark overlay, creating an immersive color-tinted background
- **Lyrics panel** — displayed alongside or below the playback controls when lyrics data exists for the current track
- **Up Next queue** — scrollable list showing the upcoming tracks in the queue

This matches the Plex/Jellyfin visual language rather than Spotify's more minimal approach, which suits a self-hosted media library aesthetic.

### 2.4 Playlist/Queue Persistence (Medium Impact)

**Problem:** The queue is entirely ephemeral. Close the tab, lose everything. No playlists. No saved queues.

**What competitors do:**
- **Every single music app**: Persists queue state across sessions
- **Spotify/Apple Music/Plex/Jellyfin/Navidrome**: Full playlist CRUD
- **Navidrome**: Smart playlists based on queries

**Recommendation priority:** Queue persistence via localStorage is trivially achievable and should be done first. Full playlists require a new DB table and are a separate feature.

### 2.5 Search Experience (Medium Impact)

**Problem:** There are two separate search experiences (Library header search bar and `/search` page) that behave differently, creating confusion. The Library search filters albums in-place; the Search page runs a parallel album+track query. Neither has type-ahead, recent searches, or search suggestions.

**What competitors do:**
- **Spotify**: Single search bar, unified results with sections (Top Result, Songs, Albums, Artists), type-ahead
- **Plex**: Search bar with instant results dropdown, then a full results page
- **Navidrome**: Single search with artist/album/track tabs

### 2.6 Mobile/Responsive (Low-Medium Impact)

**Problem:** The `AlbumDetailView` has a single `@media (max-width: 640px)` breakpoint for the hero layout, and `@media (max-width: 900px)` for cover size. The sidebar, player bar, and library grid have no responsive breakpoints. The app will be barely usable on a phone.

**What competitors do:** All of them have mobile-first or at minimum responsive layouts with hamburger menus, bottom navigation bars, and touch-friendly hit targets.

---

## 3. Prioritized Improvement Recommendations

### Tier 1: High Impact, Low-Medium Effort

#### 1.1 Home Page / Dashboard View
**What:** Replace the `/` redirect to `/library` with a proper Home view.
**Content sections (confirmed priority order):**
1. **Recently Added** (top 10-20 albums, sorted by `added DESC`) -- data already in DB
2. **Recently Played** (requires new play tracking, see 1.2)
3. **Genres** (browsable genre shelves -- each genre as a horizontal row of album cards, similar to Plex genre rows)
4. **Recommended** (least-played artists and tracks -- see design decision in section 2.1)

**Visual approach:** Plex/Jellyfin-style horizontal scrollable shelves, one per section, with album art cards. Reuses the existing `AlbumCard` component.

**Backend:** New endpoint `GET /api/albums/recent?limit=10` (trivial query on existing `added` column). New endpoint `GET /api/genres` returning genres with album counts and sample albums. New endpoint `GET /api/albums/recommended?limit=10` querying least-played content from play history.

**Frontend:** New `HomeView.vue` with four shelf sections.

**Effort:** 2-3 days (increased from original estimate due to genres shelf and recommendation logic).

#### 1.2 Play History & Queue Persistence
**What:** Two separate but related improvements.

**Queue persistence (frontend only):**
- On every queue mutation, serialize `queue`, `queueIndex`, `currentTrack`, `volume`, `shuffleEnabled`, `repeatMode` to `localStorage`.
- On app init, hydrate the player store from localStorage.
- Do NOT auto-resume playback -- just restore the queue state so the user sees where they left off.

**Play history (requires backend):**
- New SQLite table `play_history(id INTEGER PRIMARY KEY, item_id INTEGER, played_at REAL, duration_played REAL)`.
- New endpoint `POST /api/playback/history` called when a track plays past 30 seconds (or to completion).
- New endpoint `GET /api/playback/history?limit=50` for the Recently Played shelf.
- This is also the foundation for future "most played" and smart playlists.

**Effort:** Queue persistence: 2 hours. Play history: 1 day.

#### 1.3 Unified Search with Inline Results
**What:** Collapse the two search experiences into one.

**Approach:**
- Remove the `/search` route as a standalone page.
- Add a global search bar to the top of AppLayout (or make the sidebar search global).
- On typing, show an inline dropdown with sections: Top Albums (3), Top Tracks (3), Top Artists (3).
- Pressing Enter or "See all results" navigates to `/search?q=...` which becomes a full results page.
- Remove the duplicate search bar from LibraryView; the library view's existing FilterPanel handles faceted filtering, which is distinct from global search.

**Backend:** New endpoint `GET /api/search?q=...&limit=3` that returns `{albums: [], items: [], artists: []}` in a single call (more efficient than the current two parallel calls).

**Effort:** 1-2 days.

### Tier 2: Medium Impact, Medium Effort

#### 2.1 Proper Artist Page
**What:** The ArtistView exists but needs enrichment.

**Content:**
- Hero section with artist name (and optionally first letter/color placeholder if no image)
- Discography grouped by `albumtype` (Album, Single, EP, Compilation) with horizontal shelves or vertical sections
- "All Tracks" section with the most popular (or all) tracks listed
- Total albums, total tracks, total duration stats
- Link to MusicBrainz artist page (using `mb_albumartistid` which is already in the DB)

**Backend:** New endpoint `GET /api/artists/{name}` returning `{name, album_count, track_count, total_duration, mb_id, albums_by_type: {album: [...], single: [...], ...}}`.

**Frontend:** Redesign `ArtistView.vue` to be a rich page rather than a filtered library query.

**Effort:** 2-3 days.

#### 2.2 Now Playing Expanded View
**What:** Clicking the album art in the player bar opens a full-page "Now Playing" experience.

**Content:**
- Large album art (centered, ~400px)
- Track title, artist, album (linked)
- Full playback controls + progress bar
- Up Next queue (scrollable list below or in a side panel)
- Lyrics panel (if lyrics exist -- beets' lyrics plugin stores them in the `lyrics` field on items)
- Background: blurred album art as a subtle backdrop (CSS `backdrop-filter` on a dimmed art image)

**Navigation:** This could be a route (`/now-playing`) or a modal/overlay triggered from the player bar. A route is simpler and more shareable.

**Backend:** Modify the items query to optionally include the `lyrics` field: `GET /api/items/{id}?include=lyrics`.

**Effort:** 2-3 days.

#### 2.3 Genre Browsing
**What:** A genre page accessible from the sidebar or home page.

**Content:**
- Grid of genre cards with album counts
- Clicking a genre shows albums in that genre (reuse library view with pre-applied genre filter)

**Backend:** The facets endpoint already returns genres. A dedicated `GET /api/genres` with album counts would be cleaner.

**Effort:** 1 day.

### Tier 3: Lower Priority / Larger Effort

#### 3.1 Playlists
- New `playlists` and `playlist_items` tables
- CRUD API endpoints
- Frontend playlist management view
- "Add to Playlist" context menu on tracks/albums
- **Effort:** 3-5 days

#### 3.2 Mobile Layout
- Responsive breakpoints for sidebar (collapse to bottom tab bar)
- Touch-friendly album grid (larger tap targets)
- Swipe gestures on queue items
- **Effort:** 3-5 days

#### 3.3 Keyboard Shortcuts / Accessibility
- The `useGlobalShortcuts` composable exists but I didn't examine its contents. This should cover: Space (play/pause), Left/Right arrows (seek), Up/Down (volume), N (next), P (previous), / (focus search).
- **Effort:** 1 day to audit and fill gaps

#### 3.4 Gapless Playback
- Pre-buffer the next track's first chunk before the current track ends
- Use Web Audio API or dual `<audio>` elements with crossfade
- **Effort:** 2-3 days, technically complex

---

## 4. Architectural Concerns

### 4.1 Backend: Task Registry Is Process-Local and Leaks Memory

**File:** `backend/app/routers/library.py`, lines 40-44.

```python
_tasks: dict[str, dict] = {}
_tasks_lock = threading.Lock()
```

Completed tasks are never cleaned up from `_tasks`. Over time this dict grows without bound. Each task stores its full stdout/stderr output as a string.

#### Design Decisions (Confirmed 2026-04-02)

**Clarification on what `_tasks` stores:** The `_tasks` dict stores management task *runs* — e.g., one `mbsync` run, one `fetchart` run, one `lyrics` run. These are NOT per-album entries. A single `fetchart` run that processes 500 newly imported albums is still one entry in `_tasks`. Therefore, a cap of 50 entries would mean 50 separate task invocations, not 50 albums. A large album import does not risk eviction under any reasonable cap.

**Recommended approach: TTL eviction (not count cap).** Remove completed or errored tasks from `_tasks` 30 minutes after they finish. This is simpler and more predictable than a count-based cap:
- No confusion about whether a cap could affect large imports (it cannot, but TTL removes the question entirely).
- Completed tasks are only useful for polling their result shortly after they finish — 30 minutes is generous.
- In-progress tasks are never evicted (TTL only starts on completion/error).
- Implementation: when a task transitions to `completed` or `errored` state, record a `finished_at` timestamp. On each new task creation or status poll, sweep `_tasks` and remove entries where `now - finished_at > 1800` seconds.

**Future consideration — per-album task granularity:** If the system evolves to spawn per-album tasks (e.g., one `fetchart` task per album rather than one batched run), the TTL eviction approach still works cleanly — each task expires independently 30 minutes after completion. However, the frontend polling strategy would need to change: instead of polling individual task IDs, the UI should use a batch status endpoint (e.g., `GET /api/tasks?batch_id=...` or `GET /api/tasks?status=running`) to avoid N individual polling requests for N albums. This is not needed now but is recorded here as a design constraint for any future task-per-album refactor.

### 4.2 Backend: Read-Only DB Connection Might See Stale Data After Writes

When a write happens through the beets Library object (e.g., `album.store()`), the read-only `sqlite3.Connection` obtained via `get_db()` may not see the change immediately because SQLite's WAL mode has reader isolation.

**Current mitigation:** The code re-queries the read connection right after a write (`library_service.get_album(db, album_id)` after `album.store()`). This works because the write commits before the read query executes, and SQLite WAL readers see committed data.

**Risk:** This is fine for single-user, single-process deployment. If you ever run multiple uvicorn workers, the shared `Library` object's mutex won't protect across processes.

**Recommendation:** No action needed now. If scaling to multiple workers, switch to a write-through connection pool or WAL2 mode.

### 4.3 Frontend: Duplicate Utility Functions

`formatTime()` is defined independently in:
- `QueueDrawer.vue` (line 79)
- `QueueView.vue` (inline)
- `SearchView.vue` (line 134, as `formatDuration`)

`formatLabel()` / `formatClass()` for audio format badges is duplicated in:
- `AlbumDetailView.vue` (lines 242-258)
- `SearchView.vue` (lines 141-157)

**Fix:** Extract to `src/utils/format.ts` and import.

### 4.4 Frontend: Player Store Does Not Persist

Already covered in recommendation 1.2, but worth flagging as an architectural concern: every page refresh loses the entire playback queue. This is the single most user-visible gap.

### 4.5 Frontend: No Error Boundaries

API call failures are caught and logged to console (`console.error`) but never surfaced to the user. The library store silently swallows fetch failures.

**Fix:** Add a toast/notification system. PrimeVue's `Toast` component is already available since PrimeVue is installed. Wire API error interceptors in `api/client.ts` to show error toasts.

### 4.6 Backend: CORS Allow-All

The architecture doc mentions "CORS middleware with broad allow-all for dev convenience." This is fine for a LAN-only personal server, but if the app is ever exposed to the internet, this should be locked down.

### 4.7 Frontend: Router Configuration in main.ts

Routes are defined inline in `main.ts` rather than in a dedicated router file. The architecture doc shows `src/router/index.ts` but the actual code has routes in `main.ts`. This is a minor organizational issue but makes routes harder to find and manage as the app grows.

---

## 5. Navigation / Information Architecture Recommendations

### Current Navigation
```
Sidebar:
  Library  (with A-Z artist browser flyout)
  Player   (queue view)
  Tools    (stats + tasks + import)
```

### Proposed Navigation
```
Sidebar:
  Home        (NEW: dashboard with recently added, recently played, random picks)
  Library     (existing album grid/list, keep A-Z artist flyout)
  Search      (promoted to sidebar; currently only accessible via /search route)
  Player      (renamed from "Player" to "Queue" or keep as-is)
  Tools       (existing: tasks + import -- move stats to Home)
```

**Rationale:**
- **Home** becomes the default landing page. Users open the app and immediately see actionable content rather than a flat paginated list.
- **Search** in the sidebar makes it discoverable. Currently it's only reachable by URL or from the library search bar, which behaves differently.
- **Stats** move from Tools to the Home page. They're informational/discovery content, not maintenance tools. The Tools page becomes purely operational (import, mbsync, fetchart, lyrics).
- The artist browser flyout stays on Library -- it's a library browsing tool.

### Route Structure
```
/                    -> HomeView (dashboard)
/library             -> LibraryView (existing)
/library/:albumId    -> AlbumDetailView (existing)
/artist/:name        -> ArtistView (enriched, see 2.1)
/search              -> SearchView (unified, see 1.3)
/now-playing         -> NowPlayingView (new, see 2.2)
/player              -> QueueView (existing)
/tools               -> ToolsView (existing, minus stats)
```

---

## 6. Implementation Sequence

Ordered by impact and dependency. Items within a phase can be parallelized.

### Phase 1: Foundation (1 week)
1. **Queue persistence via localStorage** -- immediate user impact, no backend changes
2. **Extract duplicate utility functions** to `src/utils/format.ts`
3. **Add toast notifications** for API errors (use PrimeVue Toast)
4. **Task registry cleanup** -- add TTL eviction to `_tasks` dict
5. **Move routes to dedicated `src/router/index.ts`**

### Phase 2: Home & Discovery (1-2 weeks)
1. **Backend**: `GET /api/albums/recent`, `GET /api/genres` (with album counts and sample albums per genre) endpoints
2. **Backend**: Play history table + `POST /api/playback/history` + `GET /api/playback/history`
3. **Backend**: `GET /api/albums/recommended` endpoint — query for least-played artists and least-played/never-played tracks, return albums from those artists
4. **Frontend**: `HomeView.vue` with four horizontal scrollable shelves: Recently Added, Recently Played, Genres, Recommended
5. **Frontend**: Wire player composable to POST play history after 30s of playback
6. **Update navigation**: Add Home to sidebar, change `/` redirect to Home view

### Phase 3: Search & Artist (1 week)
1. **Backend**: Unified `GET /api/search` endpoint
2. **Frontend**: Global search bar in AppLayout with inline dropdown results
3. **Backend**: `GET /api/artists/{name}` enriched endpoint
4. **Frontend**: Redesign ArtistView with discography sections, MusicBrainz link, stats

### Phase 4: Now Playing & Polish (1 week)
1. **Frontend**: NowPlayingView with large art, lyrics, blurred backdrop
2. **Backend**: Include lyrics field in item detail response
3. **Frontend**: Genre browsing page
4. **Frontend**: Mobile responsive breakpoints (sidebar collapse, grid adjustments)

---

## 7. Summary

The beets web GUI has a remarkably solid technical foundation. The import system, streaming infrastructure, and data layer are well-engineered. The main gaps are in the *music experience* layer -- the features that make users want to open the app to listen, not just to manage. A Home page with contextual content, queue persistence, and a richer artist/now-playing experience would transform this from a competent library manager into something that feels like a personal Spotify built on your own collection. The good news is that most of these improvements are additive -- they build on existing data and components rather than requiring rewrites.
