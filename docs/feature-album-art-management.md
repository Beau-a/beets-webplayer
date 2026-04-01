# Feature: Per-Album Art Management

## Overview

On the album detail page (`/library/:id`), add the ability to view, replace, or import album art — mirroring the image management tools currently available in Settings, but scoped to the specific album.

## User-Facing Capabilities

1. **Fetch from image DB** — trigger a beets `fetchart` operation for just this album, pulling the best match from the configured image sources (MusicBrainz, Cover Art Archive, etc.)
2. **Import from file** — upload a local image (JPG/PNG) to replace the current art
3. **Clear art** — remove the current embedded/fetched art

## Placement

- Add an "Edit Art" button or icon in the album detail header, near the cover art image.
- Opens a small modal or inline panel with the three options above.
- Should feel consistent with the existing Settings art management UI.

## Backend Requirements

- `POST /api/albums/{id}/art/fetch` — runs `beet fetchart id:{id}` for the single album, returns success/failure and the new art URL
- `POST /api/albums/{id}/art/upload` — accepts multipart file upload, writes to beets art path, returns new art URL
- `DELETE /api/albums/{id}/art` — clears embedded art

## Notes

- After any art operation, the frontend should bust the art image cache (force re-fetch of `getAlbumArtUrl(id)`) so the new art appears immediately without a page reload.
- The Settings page already has a working `fetchart` flow — reuse that backend logic, just parameterize by album ID.
- Consider showing a "last fetched" timestamp or source name (e.g. "Cover Art Archive") if beets exposes it.
