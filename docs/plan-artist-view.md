# Plan: Artist Detail View

## Problem
Clicking an artist currently filters the library grid and forces the user to:
1. Click album → view tracks → back to library
2. Reopen artist filter → click next album → repeat

No way to browse all albums and tracks for one artist without repeated navigation.

## Solution
A dedicated `/artist/:artistName` route with a split-panel layout:
- **Left panel** (~280px): scrollable list of albums (cover, title, year)
- **Right panel**: selected album's tracks + play/edit/move/remove actions inline

## New Files
- `src/views/ArtistView.vue` — the split-panel view

## Changed Files
- `src/main.ts` — add route `/artist/:artistName`
- `src/components/layout/ArtistBrowser.vue` — `onSelectArtist` navigates to `/artist/:name` instead of emitting `select`
- `src/views/LibraryView.vue` — artist chip label links to `/artist/:name`; remove/relocate modals stay on the artist chip for quick access from search results

## Layout
```
┌──────────────────────────────────────────────────────────┐
│ ← Library   Artist Name              [Move] [Remove]     │
├────────────────┬─────────────────────────────────────────┤
│ Albums (N)     │ Selected Album Title · 2004             │
│                │ FLAC · 12 tracks · 48m 32s  [Play][Edit]│
│ ▶ Album 1 2004 │─────────────────────────────────────────│
│   Album 2 2001 │  1  Track Name                    3:45  │
│   Album 3 1999 │  2  Track Name                    4:12  │
│   ...          │  ...                                     │
└────────────────┴─────────────────────────────────────────┘
```

## Data Flow
- On mount: `GET /api/albums?q=albumartist:"Name"&page_size=200` → populate left panel
- On album select: `GET /api/albums/:id` → populate right panel (reuse `useLibraryStore.fetchAlbum`)
- Auto-select first album on load
- Reuse existing components: `AlbumTrackList`, `AlbumActionsModal`, `AlbumEditModal`, `ItemEditModal`

## Artist-level actions
- Move/Remove buttons in header call `ArtistActionsModal` (already built)
- On artist removed: navigate back to `/library`
- On artist relocated: refresh album list paths
