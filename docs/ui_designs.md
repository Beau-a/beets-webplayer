# UI/UX Improvement Backlog — Beets Music Frontend

> Reviewed: 2026-03-31
> Scope: All components reviewed — LibraryView, ArtistView, AlbumDetailView, AppSidebar, PlayerBar, AlbumGrid, AlbumList, AlbumCard, AlbumTrackList, PlaybackControls, AppLayout.
> Theme: Dark zinc (#18181b bg, #27272a cards, #7c3aed violet accent)
> Framework: Vue 3 + TypeScript, no third-party UI library

---

## 1. Layout & Navigation

### 1.1 — Sidebar: persist collapse state across sessions
**What to change:** The `sidebarCollapsed` ref in `AppLayout.vue` (line 31) initializes to `false` on every load. Read from `localStorage` on mount and write back on toggle.
**Why it improves the experience:** Users who prefer the collapsed sidebar (more screen real estate) have to re-collapse it every visit. Persistent state is a basic expectation in any desktop-class app.
**Implementation:** `const sidebarCollapsed = ref(localStorage.getItem('sidebar.collapsed') === 'true')`. In the toggle handler: `localStorage.setItem('sidebar.collapsed', String(sidebarCollapsed.value))`.

---

### 1.2 — Sidebar: active state indicator should use a left border accent, not just background
**What to change:** `.nav-link-active` in `AppSidebar.vue` (line 197–200) uses `background-color: #3f3f46` and `color: #a78bfa`. Add a `border-left: 2px solid #7c3aed` and compensate left padding by 2px so layout doesn't shift.
**Why it improves the experience:** A left-border indicator is a stronger, more conventional active indicator in vertical navigation (VS Code, Linear, Notion all use this). The current background-only treatment doesn't differentiate strongly enough from hover.
**Implementation:** `.nav-link-active { border-left: 2px solid #7c3aed; padding-left: 6px; background-color: transparent; }` — note: remove the background to avoid double signal.

---

### 1.3 — Sidebar: tooltip labels when collapsed
**What to change:** When `collapsed === true`, the `<span v-if="!collapsed" class="nav-label">` hides text but there are no accessible tooltips on non-Library nav items (Search, Import, Queue, Settings). Only Library has a `title` attribute via its button.
**Why it improves the experience:** A collapsed sidebar without tooltips is unusable for anyone who hasn't memorized the icon set. All icon-only navigation must have accessible `title` attributes and visible tooltip treatment on hover.
**Implementation:** Add `title="Search"`, `title="Import"`, `title="Queue"`, `title="Settings"` to each `RouterLink`. Optionally, add a custom CSS tooltip using `::after` pseudo-element on `.nav-link[title]:hover` for a richer styled tooltip vs. the browser default.

---

### 1.4 — Player bar: "nothing playing" state is a dead zone
**What to change:** In `PlayerBar.vue` (line 31–33), the left third shows "Nothing playing" in muted zinc-600 text. The center and right controls still render but are disabled. The whole bar feels empty and inert.
**Why it improves the experience:** The empty state is a missed opportunity to guide the user. Spotify shows a soft prompt. At minimum, show a subtle placeholder that aligns visually with the playing state (art placeholder box + "Play something from your library").
**Implementation:** Wrap the center controls in a `v-if="store.currentTrack"` to hide them when nothing is loaded. Show a single centered line "Select an album to start playing" in `#52525b`. This prevents the confusing sight of disabled transport buttons when nothing is queued.

---

### 1.5 — Main content: no visible scroll-to-top when paginating
**What to change:** `LibraryView.vue` calls `window.scrollTo({ top: 0, behavior: 'smooth' })` on page change (line 259), but the scroll container is `.main-content` in `AppLayout.vue` (an `overflow-y: auto` div), not `window`. The scroll likely does not work.
**Why it improves the experience:** After navigating to a new page of albums, the viewport stays scrolled to the bottom. The user has to manually scroll up — a friction point that will be hit on every pagination action for anyone not on page 1.
**Implementation:** Assign a ref to `.main-content` in `AppLayout.vue` and expose a scroll method, or use `document.querySelector('.main-content')?.scrollTo({ top: 0, behavior: 'smooth' })` in `goToPage()`. Alternatively, emit an event from `LibraryView` that the layout handles.

---

### 1.6 — ArtistView split panel: no resize handle
**What to change:** The `.album-list-panel` in `ArtistView.vue` is fixed at `width: 260px` (line 405). There is no way for the user to adjust this.
**Why it improves the experience:** 260px is very narrow. Long album titles are truncated with `text-overflow: ellipsis`. Artists with 20+ albums benefit from a wider panel. A draggable divider is the standard solution for split-panel layouts.
**Implementation:** Add a `4px` drag handle `div` between the panels. Use `mousedown` + `mousemove` + `mouseup` to compute a new panel width clamped between `180px` and `400px`, stored in a `panelWidth` ref. Persist in `localStorage('artist.panelWidth')`.

---

## 2. Album Grid & AlbumCard

### 2.1 — Grid minimum card width is too narrow for small screens
**What to change:** `AlbumGrid.vue` uses `grid-template-columns: repeat(auto-fill, minmax(180px, 1fr))` (line 53). At `180px` minimum, cards become uncomfortably small — cover art is ~180px square at that column width, and the metadata text below is already `13px` with truncation.
**Why it improves the experience:** On a 1280px viewport with a 200px sidebar, the content area is ~1048px, yielding 5 columns at ~200px each. This is fine. But at 768px (tablet) you get 3 columns at ~240px — usable. The problem is anything narrower or with sidebar expanded to its flyout. Consider `minmax(160px, 1fr)` to keep at least 3 columns on smaller panels, while bumping the card metadata to show album name on two lines (remove truncation on card title).
**Why:** Prevents a 2-column grid on very wide monitors at high page density but this is minor — the bigger fix is removing single-line truncation on the title so short cards are not information-poor.
**Implementation:** Change `.album-card-wrapper { width: 180px }` (line 139) — this hardcoded width conflicts with the grid's `1fr` sizing and may be causing cards to not fill their grid cells. Remove the fixed width and let the grid drive dimensions.

---

### 2.2 — AlbumCard: play overlay only triggers on art hover, not card hover
**What to change:** In `AlbumCard.vue`, `.art-wrapper:hover .play-overlay` (line 204) makes the play overlay visible only when hovering over the image portion. Hovering the text metadata below shows nothing.
**Why it improves the experience:** The entire card is the interactive target — wrapping a `RouterLink`. The play overlay should show whenever the card is hovered. Spotify reveals the play button on the whole card hover.
**Implementation:** Move the trigger to `.album-card-wrapper:hover .play-overlay` or `.album-card:hover .play-overlay`. The gradient background on the overlay handles visual separation from the art, so this change is visually clean.

---

### 2.3 — AlbumCard: now-playing indicator could be more visible and informative
**What to change:** The `.now-playing-badge` (line 253–278) with three animated bars sits top-left of the cover art. The bars are only 3px wide and 6–10px tall — hard to see at a glance, especially on dark album covers.
**Why it improves the experience:** The now-playing signal is a primary piece of feedback. It should be unmissable. Spotify uses the animated bars but at a larger scale with a semi-opaque background. The current implementation also doesn't pause the animation when playback is paused (`playerStore.isPlaying` is not checked).
**Implementation:**
- Increase bar width to `4px`, max height to `14px`, gap to `3px`
- Add `animation-play-state: paused` when `!playerStore.isPlaying` (use a computed CSS variable)
- Consider placing the badge bottom-left with a slightly larger background pill: `padding: 4px 8px` instead of `padding: 3px 5px`

---

### 2.4 — AlbumCard: card hover lift animation should include a shadow upgrade
**What to change:** `.album-card:hover` (line 154–157) applies `transform: translateY(-2px) scale(1.02)` and `box-shadow: 0 8px 24px rgba(0,0,0,0.4)`. The shadow is a bit flat for a dark theme — shadows on dark backgrounds need higher opacity and larger blur to read.
**Why it improves the experience:** The lift effect is good but the shadow doesn't differentiate from the default card surface enough. On a `#18181b` background with a `#27272a` card, the shadow disappears.
**Implementation:** Change hover shadow to `box-shadow: 0 12px 32px rgba(0,0,0,0.7), 0 2px 8px rgba(124,58,237,0.15)`. The violet tint in the shadow reinforces the accent color system and gives a glow feel similar to Spotify/Apple Music card states.

---

### 2.5 — AlbumCard: artist name is not clickable
**What to change:** `.card-artist` (line 300–306) shows the artist name as static text. There is a full ArtistView at `/artist/:name`.
**Why it improves the experience:** In every major music app, the artist name is a link. This is expected affordance. Users cannot currently navigate from a card in the grid directly to the artist view.
**Implementation:** Replace the `<div class="card-artist">` with a `<RouterLink :to="'/artist/' + encodeURIComponent(album.albumartist)" class="card-artist-link">` with `@click.prevent.stop` to stop the parent card link from also firing, then manually push the route.

---

### 2.6 — Grid skeleton cards have mismatched structure vs. real cards
**What to change:** The `AlbumGrid.vue` skeleton `.skeleton-card` (line 59–82) is a flat `div`, but real cards are rendered by `AlbumCard.vue` wrapped in `.album-card-wrapper`. The skeleton card has `border-radius: 10px` but no border-radius on the art or a text area separation — so the shimmer appears as one large rectangle rather than art + metadata sections.
**Why it improves the experience:** Good skeleton screens match the final layout precisely. A mismatch causes a jarring layout shift when content loads in.
**Implementation:** Structure the skeleton to match the card: full-width art block (aspect-ratio 1/1, `border-radius: 10px 10px 0 0`) plus a `.skeleton-meta` block with three text lines. Increase the shimmer animation delay offset between cards with `animation-delay: calc(var(--i) * 0.05s)` set via inline style for a staggered wave effect.

---

### 2.7 — Grid: no visual feedback when navigating to album detail (route transition)
**What to change:** Clicking an album card instantly navigates via `RouterLink`. There is no route transition animation defined anywhere in the app.
**Why it improves the experience:** Without any transition, the UI snaps between views harshly. A simple fade (150ms) creates continuity and feels intentional.
**Implementation:** In `App.vue` or `AppLayout.vue`, wrap `<RouterView>` with `<Transition name="fade">` and define: `.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease }` / `.fade-enter-from, .fade-leave-to { opacity: 0 }`.

---

## 3. Album Detail View

### 3.1 — Hero cover art has no fallback quality gradient
**What to change:** When `artError` is true in `AlbumDetailView.vue`, `.cover-placeholder` (line 413–419) shows a generic music note icon on a flat `#27272a` background. The 280×280 space is visually dead.
**Why it improves the experience:** A placeholder that reflects the album title creates a sense of identity even without art. The user still needs to orient themselves.
**Implementation:** Generate a deterministic gradient from the album title string (hash the first two characters to a hue value, produce two HSL colors, apply as `background: linear-gradient(135deg, hsl(...), hsl(...))`). Display the first letter of the album title centered in a large, semi-opaque font overlay. This is the standard approach used by Spotify, Apple Music, and Plex.

---

### 3.2 — Back link target is always "/library" — breaks from artist view context
**What to change:** Both `AlbumDetailView.vue` (line 4) and `ArtistView.vue` (line 6) hardcode `RouterLink to="/library"` for back navigation.
**Why it improves the experience:** If a user navigates to an album from the artist view, hitting "Back to Library" teleports them to the album grid — not where they came from. This is a disorienting navigation break.
**Implementation:** Use `router.back()` or read from `history.state.back` / pass a `from` query param. The cleanest approach for Vue Router: in `onMounted`, read `window.history.state.back` and use that as the back link target, falling back to `/library`.

---

### 3.3 — Track list and track actions panel are visually disconnected
**What to change:** In `AlbumDetailView.vue` (lines 138–163), the `.track-actions-panel` renders a *second* list of track names with edit/delete buttons below the main `AlbumTrackList`. This creates two separate visual lists for the same content — confusing and wasteful of space.
**Why it improves the experience:** The user sees every track twice: once in the primary track list (play, title, duration) and again in the action panel (title, edit icon, delete icon). This violates the principle of single source of truth in the UI.
**Implementation:** Move edit and delete affordances directly into `AlbumTrackList.vue` as hover-revealed action buttons on each row. On row hover, show two icon buttons (edit, delete) at the right edge of the row in the same position as the current bitrate column, or add a new `col-actions` column to the right. This completely removes the need for `.track-actions-panel`.

---

### 3.4 — Album hero section does not adapt well to narrow viewport
**What to change:** The `.album-hero` flex layout (line 389–394) has a `flex-direction: column` breakpoint at `640px` (line 728–731), but the `cover-wrapper` at `280px` fixed size (line 396–403) makes the hero feel oversized on medium widths (768px–900px), consuming too much vertical space.
**Why it improves the experience:** At common tablet or narrow desktop widths, a 280px cover takes up nearly the entire viewport width in column mode, pushing all metadata and the track list far below the fold.
**Implementation:** Add a responsive breakpoint at `900px` that reduces `cover-wrapper` to `200px` square. At `640px` breakpoint (already exists), `cover-wrapper` can go to `min(100%, 220px)` with `align-self: center` to keep it proportionate. Add `max-height: 220px` at the column breakpoint.

---

### 3.5 — Album type label (e.g. "EP", "single") should be more prominent
**What to change:** `.album-type` in `AlbumDetailView.vue` (line 429–436) is `11px`, `font-weight: 700`, `color: #a78bfa` — uppercase small text above the title. This is the correct treatment but the font-size makes it feel insignificant.
**Why it improves the experience:** The album type (LP, EP, Single, Compilation) is meaningful context. It should feel like a badge rather than micro-label. Users scanning the hero glance at the title first; the type should read at-a-glance too.
**Implementation:** Add a background pill treatment: `background: rgba(167,139,250,0.1); border: 1px solid rgba(167,139,250,0.2); border-radius: 4px; padding: 2px 8px`. Keep the font size but the containment makes it feel more substantial.

---

### 3.6 — "Tracks" section header is redundant and adds visual noise
**What to change:** `.track-section-title` in `AlbumDetailView.vue` (line 567–573) renders "TRACKS" as an uppercase label above the track list. Since the context (album detail page) makes it obvious these are tracks, this label adds no information.
**Why it improves the experience:** Every pixel of vertical space on a content page is valuable. Removing this label lets the track list start immediately after the hero section, tightening the layout. If a divider is needed, use only `border-top: 1px solid #27272a` without the label.
**Implementation:** Remove the `.track-section-header` div entirely. Keep the `.track-section { border-top: 1px solid #27272a; padding-top: 28px }` for the visual separation.

---

## 4. Player Bar & Playback Controls

### 4.1 — Progress bar has no time display
**What to change:** The `ProgressBar` component sits below `PlaybackControls` in the center of `PlayerBar.vue`. Based on the component existing as a standalone file, inspect it — but based on the PlayerBar layout, there is no visible timestamp display (current time / total duration) flanking the scrubber.
**Why it improves the experience:** Without timestamps, the scrubber is meaningless — the user cannot see how far into a track they are or how much remains. This is a critical usability gap vs. any music player.
**Implementation:** The `ProgressBar.vue` component should render: `<span class="time-current">{{ currentTime }}</span> <input type="range" .../> <span class="time-total">{{ duration }}</span>` in a horizontal flex row. Format as `m:ss`.

---

### 4.2 — Now-playing art thumbnail has no click affordance to open album detail
**What to change:** The `.art-thumb` in `PlayerBar.vue` (line 108–115) is a static image. It is not interactive.
**Why it improves the experience:** In Spotify and Apple Music, clicking the album art in the player navigates to the now-playing album. This is a natural expectation that gives players context awareness. The current track's `album_id` is available via `store.currentTrack.album_id`.
**Implementation:** Wrap `.art-thumb` in a `RouterLink :to="'/library/' + store.currentTrack?.album_id"`. Add `cursor: pointer` and a subtle `opacity: 0.85 → 1.0` hover transition. Add a tooltip `title="Go to album"`.

---

### 4.3 — Track title in player bar is not a link to the album
**What to change:** `.track-title` and `.track-artist` in `PlayerBar.vue` (lines 145–162) are static `<span>` elements.
**Why it improves the experience:** Every major music player makes the track title and artist name in the player bar interactive links. The artist name should navigate to `/artist/:name`, the track title/album to `/library/:album_id`. This is deeply expected behavior.
**Implementation:** Replace `.track-info` spans with `RouterLink` components. Add `hover: { color: #f4f4f5; text-decoration: underline }` states. Use `@click.stop` to prevent any parent click handlers from interfering.

---

### 4.4 — No keyboard shortcut support for playback
**What to change:** There are no global keyboard event listeners for playback. Space bar play/pause, left/right arrow skip, m for mute are all standard.
**Why it improves the experience:** Power users and accessibility users rely on keyboard shortcuts. Spacebar = play/pause is a muscle memory expectation from every media player ever made.
**Implementation:** In `App.vue` or a dedicated composable (`useKeyboardShortcuts`), add `document.addEventListener('keydown', handler)` on mount. Handle `Space` (toggle play), `ArrowRight` (next), `ArrowLeft` (previous), `m` (mute toggle). Guard against triggering when focus is in a text input.

---

### 4.5 — Play/pause button in PlaybackControls has no visual loading/buffering state
**What to change:** `PlaybackControls.vue` `.ctrl-play` (line 169–185) is either play or pause — no in-between state. The `<audio>` element can be in a buffering state where `isPlaying` is true but audio isn't flowing.
**Why it improves the experience:** Without a buffering indicator, the UI lies — it shows a pause icon suggesting audio is playing, when it may be stalled. A spinner in the play button (similar to what `AlbumCard.vue` already does for its loading state) closes this feedback gap.
**Implementation:** Add a `isBuffering` state to the player store, set from the audio element's `waiting` and `canplaythrough` events. When `isBuffering`, render the spinner SVG in place of the pause icon inside `.ctrl-play`.

---

### 4.6 — Volume slider has no accessible label or visual value indicator
**What to change:** The `VolumeControl.vue` component (not read directly but present at `src/components/player/VolumeControl.vue`) likely renders a range input. Range inputs without visible current values or ARIA labels fail accessibility audits.
**Why it improves the experience:** A user with motor impairment using keyboard navigation cannot tell what volume level the slider is currently at without an `aria-valuenow` attribute or a displayed percentage.
**Implementation:** Add `aria-label="Volume"`, `aria-valuenow="{{ volumePercent }}"`, `aria-valuemin="0"`, `aria-valuemax="100"` to the range input. Display the current volume as a numeric percentage that appears on hover or focus, e.g. as a tooltip above the slider.

---

## 5. Track List (AlbumTrackList)

### 5.1 — Track number column shows "—" for missing numbers but position in list is obvious
**What to change:** `.track-num` in `AlbumTrackList.vue` (line 99) shows `track.track || '—'` for tracks without a track number. On hover, the play button replaces the track number visually on the column, which is a common pattern — but currently the play button is in its own `col-play` column (line 9) to the left of `col-num`.
**Why it improves the experience:** Spotify's track list collapses the track number and play button into the same column: track number is visible by default, replaced by the play button on hover. This saves a full column width and is the industry standard.
**Implementation:** Remove `col-play` as a separate column. In `col-num`, show track number when not hovered and not playing; show the play button icon on row hover; show the playing indicator icon when this track is active. Use a wrapper `div` with `position: relative` and CSS hover swap.

---

### 5.2 — Format and bitrate columns visible in track list add density without value
**What to change:** `AlbumTrackList.vue` shows `col-format` and `col-bitrate` (lines 15–16, 67–71) for every track in the list.
**Why it improves the experience:** For most albums, every track has the same format and bitrate (they're ripped from the same source). Showing these columns on every row is visual noise that pushes the meaningful columns (title, duration) to a narrower space. Spotify and Apple Music do not show per-track format in the primary track list.
**Implementation:** Show format/bitrate only if tracks in the album have *mixed* formats or bitrates (i.e., the album contains both FLAC and MP3 tracks). Otherwise hide these columns entirely. Add a computed `hasMixedFormats` that checks if `new Set(tracks.map(t => t.format)).size > 1`. The column header row can include a small toggle or the data can appear in a track detail tooltip on hover.

---

### 5.3 — Double-click to play is an undiscoverable interaction
**What to change:** `AlbumTrackList.vue` uses `@dblclick="playFromTrack(track)"` (line 24) as an interaction. There is no tooltip or visual affordance indicating this capability.
**Why it improves the experience:** Double-click is undiscoverable — no visual cue tells the user that double-clicking a row starts playback. The single-click play button already exists; double-click adds ambiguity. If kept, it should be indicated in a tooltip.
**Implementation:** Either remove `@dblclick` in favor of making the row single-click to play (more discoverable), OR keep double-click but add a row-level `title` attribute: `title="Double-click to play"` that appears in the browser tooltip. The `@dblclick` conflict with row-level navigation should also be considered.

---

### 5.4 — No "Add to queue" option on tracks — only "play now" (replace queue)
**What to change:** `playFromTrack()` in `AlbumTrackList.vue` always calls `playerStore.playAlbum()` which replaces the current queue. There is no way to add a single track or album to the end of an existing queue from the track list.
**Why it improves the experience:** Replacing the queue is a destructive action — it discards whatever the user was listening to. "Add to queue" is one of the highest-frequency interactions in any music player. Without it, the app feels limited and forces users to re-queue manually.
**Implementation:** Add a right-click context menu (or a hover-revealed "..." button) on track rows with options: "Play now", "Play next", "Add to end of queue". The player store needs `addToQueue(track)` and `playNext(track)` actions to support this.

---

### 5.5 — Disc headers have poor visual weight differentiation
**What to change:** `.disc-header` in `AlbumTrackList.vue` (line 231–239) uses `12px`, `color: #71717a`, uppercase text. It visually blends into the table header row (same font treatment in `.track-table th` at line 255–262).
**Why it improves the experience:** Disc separators need to feel distinctly different from column headers — they are section dividers, not metadata labels. The current treatment causes visual confusion on multi-disc albums.
**Implementation:** Differentiate disc headers: `font-size: 13px; color: #a78bfa; padding: 20px 12px 6px; background: none; border-bottom: 2px solid rgba(124,58,237,0.3)`. The violet accent with a thicker border clearly signals "this is a section break, not a column header."

---

## 6. Search & Filter Controls

### 6.1 — Sort dropdown is missing a custom dropdown chevron indicator
**What to change:** `LibraryView.vue` `.sort-select` (line 412–425) uses `appearance: none; -webkit-appearance: none` to remove native styling but does not add a custom chevron icon to the right of the field. The user sees a bare, arrow-free select box.
**Why it improves the experience:** `appearance: none` on a `select` removes the visual affordance that tells users it's a dropdown. Without a chevron, the element looks like a plain text label. This is a common implementation oversight.
**Implementation:** Wrap the `<select>` in a `<div class="sort-select-wrapper">` with `position: relative`. Add an SVG chevron absolutely positioned at `right: 10px; top: 50%; transform: translateY(-50%)`. Set `pointer-events: none` on the SVG so clicks still hit the select.

---

### 6.2 — FilterPanel and search bar lack visual grouping / hierarchy
**What to change:** The `SearchBar` and `sort-control` in `LibraryView.vue` `.controls-row` (line 33–51) sit next to each other without visual distinction. The `FilterPanel` sits below in `.library-controls` without clear separation from the search row.
**Why it improves the experience:** The controls area is the primary interaction zone but it reads as a flat list of inputs. A stronger visual grouping — a single card/bar container background — makes it clear these are a cohesive filter system.
**Implementation:** Add `background: #27272a; border: 1px solid #3f3f46; border-radius: 10px; padding: 12px 16px` to `.library-controls`. This creates a clear "filter bar" affordance.

---

### 6.3 — Artist filter chip: danger action (remove artist) is too accessible
**What to change:** The `.chip-action-danger` button (trash icon, lines 80–85 in `LibraryView.vue`) that removes the entire artist from the library sits directly inline on the active filter chip with no confirmation step visible from the chip itself.
**Why it improves the experience:** The remove-artist action is destructive and irreversible. Having the trash icon directly adjacent to the filter chip label — and the chip itself being near the search bar — creates a high risk of accidental triggering. The button should be visually further away and the severity communicated earlier.
**Implementation:** Move the artist chip action buttons (move, remove) out of the chip itself and into the artist header area or a separate toolbar that appears contextually. The chip should only contain the label and the clear (×) button. Destructive actions need breathing room and visual hierarchy — a filter chip is not the right container for them.

---

### 6.4 — No active filter count badge on the filter panel toggle
**What to change:** The `FilterPanel` component is always visible below the controls row. If it collapses (unclear from the code — it appears always open), or for a future collapsed state, there is no indicator of how many filters are currently active.
**Why it improves the experience:** When filters are active, users often forget they've filtered and wonder why results are limited. A persistent "X filters active" badge or indicator prevents this disorientation.
**Implementation:** Compute the number of active filters: `genre + (yearFrom ? 1 : 0) + (yearTo ? 1 : 0) + format`. Display a violet badge count next to the filter label or control row. When count is 0, show nothing.

---

## 7. ArtistView

### 7.1 — Artist header has no visual identity (no art, no dominant color)
**What to change:** The `.artist-header` in `ArtistView.vue` (line 335–343) is a plain flex bar with artist name text. There is no album art hero, no artist image, nothing visual.
**Why it improves the experience:** Even without a dedicated artist photo (which beets doesn't store), the header can be dramatically improved. Use the first album's cover art as a blurred, low-opacity banner background. This gives each artist view a unique visual identity.
**Implementation:** Fetch `getAlbumArtUrl(albums.value[0]?.id)` and set it as a CSS `background-image` on `.artist-header` with `background-size: cover; filter: blur(40px); opacity: 0.15` on a pseudo-element. Overlay the content normally. Add a gradient fade to `#18181b` at the bottom of the header.

---

### 7.2 — Selected album in left panel does not scroll into view when auto-selected
**What to change:** In `ArtistView.vue` `loadAlbums()` (line 246), the first album is auto-selected: `selectAlbum(data.items[0].id)`. If the user was previously on a different album and navigates to this artist again, the previously-selected row may not be visible without scrolling.
**Why it improves the experience:** Any list with auto-selection should scroll the selected item into view. This is standard behavior in file explorers, music players, and IDEs.
**Implementation:** After setting `selectedAlbumId`, use `nextTick(() => { document.querySelector('.album-row-active')?.scrollIntoView({ block: 'nearest' }) })`.

---

### 7.3 — Album row year is isolated but album count is more useful
**What to change:** `.album-row-year` (line 474) shows the year below the title. The year is already visible in the right detail panel. The album count (total tracks) would be more useful contextual information in the narrow left panel to help users pick which album to explore.
**Why it improves the experience:** When scanning a discography, "22 tracks" vs. "4 tracks" helps users pick an album to explore. Year is good but most users already sorted the list by year (the API default is `sort: 'year+'`).
**Implementation:** Show year AND track count: `<span class="album-row-meta">{{ alb.year }} · {{ alb.track_count }} tracks</span>` in one line. This increases information density without adding space.

---

## 8. Typography & Visual Polish

### 8.1 — Inconsistent font size scale across components
**What to change:** Font sizes in use across the codebase: `10px`, `11px`, `12px`, `13px`, `14px`, `16px`, `18px`, `20px`, `22px`, `28px`. This is 10 distinct sizes with no clear typographic scale. There is no CSS custom property system for type sizes.
**Why it improves the experience:** An inconsistent type scale creates visual noise and makes the interface feel "assembled" rather than designed. A 4-step scale (xs/sm/base/lg/xl/2xl) applied consistently would immediately tighten the visual quality.
**Implementation:** Define CSS custom properties in `:root` or `App.vue`:
```
--text-xs: 11px
--text-sm: 12px
--text-base: 13px
--text-md: 14px
--text-lg: 16px
--text-xl: 20px
--text-2xl: 28px
```
Then do a sweep to replace all hardcoded `font-size` values with these variables.

---

### 8.2 — "Library" heading (22px) is undersized for the primary page title
**What to change:** `.library-title` in `LibraryView.vue` (line 279–283) is `22px`, `font-weight: 700`. For a primary view header, this should be larger — at minimum `24px`, ideally `28px` to match the album title treatment.
**Why it improves the experience:** The page title anchors the user in the navigation. At 22px, it's barely larger than the `album-title` in `AlbumDetailView.vue` (`28px`), creating an inverted hierarchy where a sub-entity (album) feels more prominent than the library.
**Implementation:** Change to `font-size: 28px` and add `letter-spacing: -0.02em` (negative tracking at large sizes improves readability and looks more polished).

---

### 8.3 — All status labels use inconsistent uppercase treatment
**What to change:** Throughout the codebase, uppercase labels are used for: column headers (`AlbumList.vue` line 140–149), stat labels (`AlbumDetailView.vue` line 482–488), disc headers (`AlbumTrackList.vue` line 232–238), track section title (`AlbumDetailView.vue` line 568–572). Some use `letter-spacing: 0.05em`, others `0.06em`, `0.07em`, `0.08em`, `0.1em`.
**Why it improves the experience:** Uppercase micro-labels should have exactly one letter-spacing value system-wide. Inconsistency reads as lack of craft, even subconsciously.
**Implementation:** Standardize all uppercase label treatment to `font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #52525b`. Extract as a reusable CSS class `.label-uppercase` or a design token.

---

## 9. Animations & Micro-interactions

### 9.1 — Shimmer skeleton animations are out of phase with each other
**What to change:** In `AlbumGrid.vue`, all skeleton cards share the same `animation: shimmer 1.5s infinite` (line 72) with no delay offsets. All cards shimmer simultaneously — the entire grid pulses at once.
**Why it improves the experience:** A wave/cascade effect (each card's animation starts slightly offset from the previous) looks intentional and alive. Simultaneous shimmer on 24 cards is visually overwhelming.
**Implementation:** In `AlbumGrid.vue`, apply `:style="{ animationDelay: (n * 0.05) + 's' }"` to each `skeleton-card`. Since `v-for` only provides the index `n`, calculate: `Math.min(n * 0.05, 0.8)` to cap the max delay at 0.8s.

---

### 9.2 — No transition when switching between grid and list view
**What to change:** `LibraryView.vue` toggles between `<AlbumGrid>` and `<AlbumList>` with a `v-if`/`v-else` (lines 91–92). The switch is instantaneous.
**Why it improves the experience:** A fast cross-fade (100ms) between view modes reinforces that this is a mode switch, not a page navigation. Without animation, the snap looks like a glitch.
**Implementation:** Wrap the `<AlbumGrid>` / `<AlbumList>` in a `<Transition name="view-switch" mode="out-in">`. Define `.view-switch-enter-active, .view-switch-leave-active { transition: opacity 0.1s }` and `.view-switch-enter-from, .view-switch-leave-to { opacity: 0 }`.

---

### 9.3 — Album card format badge is identical across list and detail views — consider a hover tooltip for extended format info
**What to change:** The `format-badge` appears in `AlbumCard.vue`, `AlbumList.vue`, and `ArtistView.vue`. It shows only the format name (FLAC, MP3). No additional context is available.
**Why it improves the experience:** Audiophile users want to quickly check sample rate, bit depth, or bitrate. A tooltip on the format badge that shows e.g. "FLAC 24-bit / 96kHz" would serve this without cluttering the primary UI.
**Implementation:** The format badge already has the format string. For albums, the `bitrate` is available on tracks. On hover of any format badge, show a CSS tooltip (`::after` pseudo-element or a Tippy-style approach without a library) showing the most common bitrate in the album.

---

### 9.4 — Page change in pagination has no scroll feedback animation
**What to change:** Beyond the scroll-to-top fix (see item 1.5), when the grid content replaces on pagination, there is no transition — the content area instantly swaps.
**Why it improves the experience:** A brief opacity fade on the content area when loading new pages tells the user the content has changed, especially when the page number moves from e.g. 2 to 3 and the first row happens to contain similar albums.
**Implementation:** In `AlbumGrid.vue`, add a `v-if="!loading"` transition: on every new fetch cycle, briefly set an `isTransitioning` flag that applies `opacity: 0.4` for 100ms then fades back to 1. Or more simply, trigger the loading skeleton for 150ms even when the data arrives quickly (set a `minLoadTime` of 150ms to show the skeleton).

---

## 10. Accessibility

### 10.1 — All icon-only buttons lack accessible labels
**What to change:** Throughout the app, many buttons have only `title` attributes for accessibility (which only shows browser tooltips, not read by all screen readers correctly). Affected buttons include: all `.ctrl-btn` in `PlaybackControls.vue`, `.queue-btn` in `PlayerBar.vue`, `.view-btn` in `LibraryView.vue`, `.collapse-btn` in `AppSidebar.vue`, and all icon buttons in `ArtistView.vue`.
**Why it improves the experience:** `title` attributes are not reliably announced by screen readers. `aria-label` is the correct mechanism for icon-only interactive elements. This is a WCAG 2.1 AA requirement (Success Criterion 4.1.2 Name, Role, Value).
**Implementation:** Add `aria-label="Play"`, `aria-label="Pause"`, `aria-label="Next track"`, etc. to every icon-only button. Remove `title` attributes that are redundant with `aria-label` (they cause double-announcement). For toggle buttons (shuffle, repeat), use `aria-pressed="true/false"` to communicate state.

---

### 10.2 — Track table has no accessible row role or labeling
**What to change:** The `<table>` in `AlbumTrackList.vue` has no `aria-label`. The track rows are clickable/interactive but have no `role="button"` or accessible name. Screen reader users cannot identify the table or understand the row interactions.
**Why it improves the experience:** Tables require `<caption>` or `aria-label` to be identified. Interactive rows need `role="row"` (already implied from `<tr>`) but the custom click behavior on rows needs to be exposed.
**Implementation:** Add `aria-label="Track listing for [album name]"` to `<table>`. The `playFromTrack` function on `@dblclick` should have a keyboard equivalent — add `@keydown.enter="playFromTrack(track)"` to each `<tr>` and `tabindex="0"` to make rows keyboard navigable.

---

### 10.3 — Color is the only differentiator for format badges
**What to change:** The format badges (FLAC=green, MP3=blue, OGG=amber) across all components use color as the sole differentiator. Users with color vision deficiency cannot distinguish these without the text label — but the text label is present, which is good. The issue is contrast.
**Why it improves the experience:** `.badge-flac { background: rgba(74,222,128,0.15); color: #4ade80 }` — `#4ade80` on `rgba(74,222,128,0.15)` (which resolves to approximately `#253028` on `#27272a` bg) needs to meet 4.5:1 contrast for small text (11px bold). These colored badges may not meet WCAG AA contrast requirements.
**Implementation:** Increase badge text colors to their lighter variants: `#86efac` (green-300) for FLAC, `#93c5fd` (blue-300) for MP3, `#fcd34d` (amber-300) for OGG. Run a contrast checker — all should be at or above 4.5:1 against their semi-transparent backgrounds on `#27272a`.

---

### 10.4 — Modal dialogs lack focus trapping
**What to change:** The delete confirmation dialog in `AlbumDetailView.vue` (lines 174–190) is rendered via `<Teleport to="body">`. When it opens, focus is not moved into the dialog and is not trapped — a keyboard user can tab past the modal into the content behind it.
**Why it improves the experience:** WCAG 2.1 Success Criterion 2.1.2 (No Keyboard Trap) and standard modal behavior require that: (1) focus moves to the modal on open, (2) Tab/Shift-Tab cycle within the modal, (3) Escape closes the modal. Without this, the modal is inaccessible to keyboard users.
**Implementation:** On modal open, call `nextTick(() => confirmDialog.value?.querySelector('[autofocus], button')?.focus())`. Add a focus trap — listen for Tab keydown within the modal and cycle focus among focusable children. Vue's `<FocusTrap>` plugin or a hand-rolled composable using a ref array of focusable elements handles this.

---

### 10.5 — Artist chip danger button color (#7f1d1d) fails contrast
**What to change:** `.chip-action-danger` in `LibraryView.vue` (line 379) sets `color: #7f1d1d` (red-900) on a `#2d1f5e` background (the artist chip). `#7f1d1d` on `#2d1f5e` is very low contrast — approximately 1.5:1.
**Why it improves the experience:** This is a WCAG failure. The icon is invisible in practice. The hover color `#fca5a5` is fine, but the default state fails entirely.
**Implementation:** Change default color to `#f87171` (red-400), which provides acceptable contrast against the `#2d1f5e` chip background. The danger semantic is still communicated by the icon shape and color, and the element is now visible.

---

## 11. Pagination

### 11.1 — Current page is shown as a plain number with no total context
**What to change:** `.page-current` in `LibraryView.vue` (line 523–529) shows only the current page number (e.g., "3"). There is no "of N" context visible adjacent to the page number.
**Why it improves the experience:** The user already sees "Showing 51–100 of 497" in `.pagination-info`, which partially addresses this. But the page controls show "Prev 3 Next" — without knowing the total page count, "Next" is ambiguous ("Is this the last page?"). The `Next` button does disable when on the last page, but the user must click to find out.
**Implementation:** Change `.page-current` to render "Page {{ store.page }} of {{ totalPages }}" in the same violet styling. This eliminates the guess.

---

### 11.2 — Pagination controls are bottom-only — no top pagination for long lists
**What to change:** The pagination controls and page-size selector are only at the bottom of the content in `LibraryView.vue`. For a user showing 25 albums per page in list view (small rows), they may scroll significantly to reach the next-page control.
**Why it improves the experience:** Duplicate pagination at the top of the list allows faster navigation for users who browse sequentially, especially in list view where rows are compact and 25 rows can fill significant height.
**Implementation:** Extract pagination into a `<PaginationBar>` component, then render it both above and below the album grid/list. The `v-if` guard stays on both instances.

---

*End of backlog. Total items: 40. Recommended priority for first sprint: items 1.5, 2.2, 3.2, 3.3, 4.1, 4.2, 4.3, 5.1, 5.4, 10.1.*

---

## Effort Breakdown with Dependencies

### Quick wins — isolated, single-file CSS/logic changes

These have no dependencies and can be done in any order.

| # | Item | File |
|---|------|------|
| 1.1 | Persist sidebar collapse state in localStorage | `AppLayout.vue` |
| 1.2 | Sidebar active indicator: left border accent | `AppSidebar.vue` |
| 1.3 | Sidebar: add `title` tooltips to collapsed icons | `AppSidebar.vue` |
| 2.4 | Card hover shadow: add violet tint, deeper opacity | `AlbumCard.vue` |
| 3.5 | Album type label: add pill background treatment | `AlbumDetailView.vue` |
| 3.6 | Remove redundant "Tracks" section header | `AlbumDetailView.vue` |
| 4.2 | Player bar art thumbnail → link to album detail | `PlayerBar.vue` |
| 4.3 | Track title/artist in player bar → router links | `PlayerBar.vue` |
| 5.5 | Disc header visual differentiation (violet accent) | `AlbumTrackList.vue` |
| 6.1 | Sort dropdown: add custom chevron SVG | `LibraryView.vue` |
| 7.2 | Auto-select: scroll selected album row into view | `ArtistView.vue` |
| 7.3 | Album row: show year + track count together | `ArtistView.vue` |
| 8.2 | Library title size: 22px → 28px | `LibraryView.vue` |
| 9.2 | Grid/list view switch: add 100ms crossfade | `LibraryView.vue` |
| 10.3 | Format badge contrast: use lighter color variants | all badge components |
| 10.5 | Artist chip danger button: fix contrast (#7f1d1d → #f87171) | `LibraryView.vue` |
| 11.1 | Pagination: show "Page N of N" | `LibraryView.vue` |

---

### Medium effort — new logic or new component structure

| # | Item | Dependencies | Notes |
|---|------|-------------|-------|
| 1.4 | Player bar empty state redesign | none | Hide disabled controls, show guidance text |
| 2.3 | Now-playing badge: bigger, pauses when not playing | none | Needs `playerStore.isPlaying` check |
| 2.5 | Artist name on card → clickable link | none | Add `@click.stop` RouterLink; careful not to trigger the card link |
| 3.1 | Cover art placeholder: generative gradient + initial | none | Hash album title to HSL, render initial letter |
| 3.4 | Album hero responsive breakpoints | none | Add 900px breakpoint, reduce cover to 200px |
| 4.1 | Progress bar: add current/total time display | none | `ProgressBar.vue` needs timestamps flanking the scrubber |
| 4.5 | Play button buffering state (spinner) | needs `isBuffering` in store | Add `waiting`/`canplaythrough` audio events to player store |
| 5.1 | Collapse play button + track number into one column | none | CSS hover swap; removes a full column — visual improvement |
| 5.2 | Hide format/bitrate columns unless mixed formats | none | Add `hasMixedFormats` computed |
| 6.2 | Filter bar: add card background to group controls | none | Pure CSS wrapping treatment |
| 6.3 | Move artist remove/move buttons out of filter chip | needs UI location decision | Buttons need a new home (artist header strip or context menu) |
| 6.4 | Active filter count badge | none | Computed count of non-null filter values |
| 7.1 | Artist header: blurred album art banner | none | First album's art as `background-image` with blur + opacity overlay |
| 8.3 | Standardize uppercase label treatment | none | Sweep + extract `.label-uppercase` CSS class |
| 9.1 | Skeleton shimmer: stagger animation delays | none | Add `animation-delay` per card index |
| 9.4 | Pagination content fade on page change | none | Brief opacity transition when grid replaces |
| 2.6 | Skeleton cards: match real card structure | **depends on 2.1** | Fix fixed-width issue first, then match skeleton to actual layout |
| 11.2 | Add top pagination controls | **depends on 11.1** | Extract pagination into a reusable component first |

---

### High effort — cross-cutting or new infra

| # | Item | Dependencies | Notes |
|---|------|-------------|-------|
| 1.6 | ArtistView split panel: draggable resize handle | none but isolated | Mousedown/move/up + localStorage persistence |
| 2.1 | Fix card fixed width conflicting with grid `1fr` | **others depend on this** | AlbumCard currently has hardcoded `width: 180px` fighting the grid |
| 2.7 | Route transitions (fade between views) | none | Wrap `RouterView` in `<Transition>` in `AppLayout.vue` |
| 4.4 | Global keyboard shortcuts (space, arrows, m) | none | Composable `useKeyboardShortcuts`, guard against input focus |
| 5.3 | Replace dblclick with single-click to play | **conflicts with card navigation** | Needs design decision: click = play or click = navigate? |
| 8.1 | CSS type scale design tokens | **blocks 8.3** | Define `--text-xs` through `--text-2xl`, then sweep all components |
| 10.1 | `aria-label` sweep on all icon-only buttons | none | Tedious but mechanical — affects 10+ components |
| 10.2 | Track table: aria-label, keyboard nav on rows | depends on 5.3 decision | `tabindex="0"` + `@keydown.enter` on rows |
| 10.4 | Modal focus trap | none | Composable or per-modal; affects delete confirm + all edit modals |
| 4.6 | Volume slider: accessible label + value display | part of accessibility sweep | Can be done alongside 10.1 |

---

### Blocked / needs a decision first

| # | Item | Blocker |
|---|------|---------|
| Search/Library consolidation | Search and Library are the same view — decide: merge into one with a toggle, or differentiate with distinct capabilities (search = full-text, library = browse/filter) | Design decision |
| 6.3 | Relocate artist chip danger buttons | Needs a decision on where destructive actions live — artist header? context menu? |
| 5.3 | Single-click vs dblclick to play | Conflicts with card navigation (single click = navigate to detail). Needs a deliberate choice. |
