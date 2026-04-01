<template>
  <div class="album-list-wrapper">
    <!-- Loading skeleton -->
    <div v-if="loading" class="album-list">
      <div v-for="n in 20" :key="n" class="skeleton-row">
        <div class="skeleton-thumb"></div>
        <div class="skeleton-col wide"></div>
        <div class="skeleton-col medium"></div>
        <div class="skeleton-col short"></div>
        <div class="skeleton-col short"></div>
      </div>
    </div>

    <!-- Populated list -->
    <table v-else-if="albums.length > 0" class="album-list">
      <thead>
        <tr class="list-header">
          <th class="col-art"></th>
          <th class="col-album">Album</th>
          <th class="col-artist">Artist</th>
          <th class="col-year">Year</th>
          <th class="col-tracks">Tracks</th>
          <th class="col-format">Format</th>
          <th class="col-genre">Genre</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="album in albums"
          :key="album.id"
          class="list-row"
          @click="goToAlbum(album.id)"
        >
          <td class="col-art">
            <div class="thumb-wrap">
              <img
                v-if="album.has_art"
                :src="getAlbumArtUrl(album.id)"
                class="thumb"
                loading="lazy"
                @error="(e) => ((e.target as HTMLImageElement).style.display = 'none')"
              />
              <div v-else class="thumb-placeholder">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="thumb-icon">
                  <circle cx="9" cy="18" r="3"/>
                  <circle cx="18" cy="15" r="3"/>
                  <polyline points="12 18 12 2 21 5 21 9"/>
                </svg>
              </div>
            </div>
          </td>
          <td class="col-album">
            <span class="album-name">{{ album.album || '—' }}</span>
          </td>
          <td class="col-artist">
            <span class="artist-name">{{ album.albumartist || '—' }}</span>
          </td>
          <td class="col-year">
            <span class="meta-text">{{ album.year || '—' }}</span>
          </td>
          <td class="col-tracks">
            <span class="meta-text">{{ album.track_count }}</span>
          </td>
          <td class="col-format">
            <span v-if="album.format" class="format-badge" :class="formatClass(album.format)">
              {{ formatLabel(album.format) }}
            </span>
            <span v-else class="meta-text">—</span>
          </td>
          <td class="col-genre">
            <span class="genre-text">{{ album.genres || '—' }}</span>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
        <circle cx="9" cy="18" r="3"/>
        <circle cx="18" cy="15" r="3"/>
        <polyline points="12 18 12 2 21 5 21 9"/>
        <line x1="12" y1="10" x2="12" y2="18"/>
      </svg>
      <p class="empty-text">No albums found</p>
      <p class="empty-subtext">Try adjusting your search or filters</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { getAlbumArtUrl } from '@/api/albums'
import type { AlbumSummary } from '@/types/album'

defineProps<{
  albums: AlbumSummary[]
  loading: boolean
}>()

const router = useRouter()

function goToAlbum(id: number) {
  router.push(`/library/${id}`)
}

function formatLabel(fmt: string): string {
  const f = fmt.toUpperCase()
  if (f.includes('FLAC')) return 'FLAC'
  if (f.includes('MP3')) return 'MP3'
  if (f.includes('OGG')) return 'OGG'
  if (f.includes('AAC') || f.includes('M4A')) return 'AAC'
  if (f.includes('OPUS')) return 'Opus'
  if (f.includes('WMA') || f.includes('WINDOWS')) return 'WMA'
  return fmt.slice(0, 6)
}

function formatClass(fmt: string): string {
  const f = fmt.toUpperCase()
  if (f.includes('FLAC')) return 'badge-flac'
  if (f.includes('MP3')) return 'badge-mp3'
  if (f.includes('OGG') || f.includes('OPUS')) return 'badge-ogg'
  if (f.includes('AAC')) return 'badge-aac'
  return 'badge-other'
}
</script>

<style scoped>
.album-list-wrapper {
  width: 100%;
}

.album-list {
  width: 100%;
  border-collapse: collapse;
}

/* Header */
.list-header th {
  padding: 8px 12px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: #52525b;
  text-align: left;
  border-bottom: 1px solid #27272a;
  white-space: nowrap;
}

/* Rows */
.list-row {
  border-bottom: 1px solid #27272a;
  cursor: pointer;
  transition: background 0.1s;
}

.list-row:hover {
  background: #27272a;
}

.list-row td {
  padding: 7px 12px;
  vertical-align: middle;
}

/* Columns */
.col-art { width: 44px; padding: 5px 8px 5px 4px !important; }
.col-album { min-width: 180px; }
.col-artist { min-width: 160px; }
.col-year { width: 60px; }
.col-tracks { width: 60px; }
.col-format { width: 70px; }
.col-genre { min-width: 120px; }

/* Thumbnail */
.thumb-wrap {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  overflow: hidden;
  background: #27272a;
  flex-shrink: 0;
}

.thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #27272a;
}

.thumb-icon {
  width: 16px;
  height: 16px;
  color: #3f3f46;
}

/* Text */
.album-name {
  font-size: var(--text-md);
  color: #f4f4f5;
  font-weight: 500;
}

.artist-name {
  font-size: var(--text-base);
  color: #a1a1aa;
}

.meta-text {
  font-size: var(--text-base);
  color: #71717a;
  font-variant-numeric: tabular-nums;
}

.genre-text {
  font-size: var(--text-sm);
  color: #52525b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 160px;
  display: block;
}

/* Format badges */
.format-badge {
  font-size: var(--text-xs);
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}

.badge-flac { background: rgba(74,222,128,0.15); color: #4ade80; }
.badge-mp3  { background: rgba(96,165,250,0.15);  color: #60a5fa; }
.badge-ogg  { background: rgba(251,191,36,0.15);  color: #fbbf24; }
.badge-aac  { background: rgba(251,146,60,0.15);  color: #fb923c; }
.badge-other { background: rgba(161,161,170,0.15); color: #a1a1aa; }

/* Skeleton */
.skeleton-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 4px;
  border-bottom: 1px solid #27272a;
}

.skeleton-thumb {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  flex-shrink: 0;
  background: linear-gradient(90deg, #27272a 25%, #3f3f46 50%, #27272a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-col {
  height: 12px;
  border-radius: 4px;
  background: linear-gradient(90deg, #27272a 25%, #3f3f46 50%, #27272a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-col.wide   { flex: 2; }
.skeleton-col.medium { flex: 1.5; }
.skeleton-col.short  { flex: 0.5; min-width: 40px; }

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 24px;
  gap: 12px;
}

.empty-icon { width: 56px; height: 56px; color: #3f3f46; }
.empty-text { font-size: var(--text-lg); font-weight: 500; color: #71717a; margin: 0; }
.empty-subtext { font-size: var(--text-base); color: #52525b; margin: 0; }
</style>
