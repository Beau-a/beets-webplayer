# Feature: Differentiate Search vs Library Views

## Decision

Search and Library are currently the same view. They will be split into two distinct views with different purposes.

## Library View (current: `/library`)

Standard music app browse experience:
- Grid/list of albums, sorted by artist/album/year/recently added
- Faceted filtering: genre, format, year range
- Artist filter chip (navigate from artist page → filter library by artist)
- Pagination
- No full-text search — discovery is through browsing and filtering

## Search View (new: `/search`)

Modelled after the default beets web plugin search page — a DB query tool:
- Single prominent search input
- Searches across tracks, albums, and artists simultaneously
- Results grouped by type: Tracks | Albums | Artists
- Supports beets query syntax (e.g. `artist:Radiohead year:2000..2010 format:FLAC`)
- No pagination needed for typical queries — show top N results per category with a "show more" expansion
- Each result is clickable: track → album detail, album → album detail, artist → artist view

## Implementation Notes

- Create `src/views/SearchView.vue` as a new top-level route at `/search`
- Add Search to the sidebar nav (already has a placeholder icon)
- Backend: `/api/search?q=...` endpoint that queries beets across items and albums
- The existing `SearchBar` component in LibraryView can be repurposed or simplified — Library's text filter can remain as a quick title/artist filter, while Search is the full-text beets query tool
- Remove the text query input from LibraryView filters once SearchView exists, or keep it as a lightweight filter-within-results input
