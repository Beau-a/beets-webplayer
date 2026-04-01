<template>
  <div class="detail-view">
    <!-- Back button -->
    <button class="back-link" @click="router.back()">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="back-icon">
        <line x1="19" y1="12" x2="5" y2="12"/>
        <polyline points="12 19 5 12 12 5"/>
      </svg>
      Back
    </button>

    <!-- Loading state -->
    <div v-if="store.isLoading" class="loading-state">
      <div class="album-hero skeleton-hero">
        <div class="skeleton-cover"></div>
        <div class="skeleton-info">
          <div class="skeleton-bar tall"></div>
          <div class="skeleton-bar medium"></div>
          <div class="skeleton-bar short"></div>
        </div>
      </div>
    </div>

    <!-- Album content -->
    <template v-else-if="album">
      <div class="album-hero">
        <!-- Cover art -->
        <div class="cover-wrapper">
          <img
            v-if="!artError && album.has_art"
            :src="artUrl"
            :alt="`${album.album} cover`"
            class="cover-img"
            @error="artError = true"
          />
          <div v-else class="cover-placeholder" :style="placeholderStyle">
            <span class="cover-initial">{{ placeholderInitial }}</span>
          </div>
        </div>

        <!-- Album metadata -->
        <div class="album-info">
          <div class="album-type" v-if="album.albumtype">{{ album.albumtype }}</div>
          <h1 class="album-title">{{ album.album || 'Unknown Album' }}</h1>
          <div class="album-artist">{{ album.albumartist || 'Unknown Artist' }}</div>

          <div class="meta-pills">
            <span v-if="album.year" class="meta-pill">{{ album.year }}</span>
            <span v-if="album.format" class="meta-pill format-pill" :class="formatClass">{{ formatLabel }}</span>
            <span v-if="album.label" class="meta-pill">{{ album.label }}</span>
            <span v-if="album.country" class="meta-pill">{{ album.country }}</span>
          </div>

          <div class="meta-stats">
            <div class="meta-stat">
              <span class="stat-label">Tracks</span>
              <span class="stat-value">{{ album.track_count }}</span>
            </div>
            <div class="meta-stat">
              <span class="stat-label">Duration</span>
              <span class="stat-value">{{ totalDuration }}</span>
            </div>
            <div class="meta-stat" v-if="album.genres">
              <span class="stat-label">Genre</span>
              <span class="stat-value">{{ album.genres }}</span>
            </div>
            <div class="meta-stat" v-if="album.original_year && album.original_year !== album.year">
              <span class="stat-label">Original year</span>
              <span class="stat-value">{{ album.original_year }}</span>
            </div>
            <div class="meta-stat" v-if="album.catalognum">
              <span class="stat-label">Catalog</span>
              <span class="stat-value">{{ album.catalognum }}</span>
            </div>
          </div>

          <!-- Album actions -->
          <div class="album-actions">
            <button class="action-btn action-btn-play" @click="playAlbumNow">
              <svg viewBox="0 0 24 24" fill="currentColor" class="action-icon">
                <polygon points="5,3 19,12 5,21"/>
              </svg>
              Play Album
            </button>
            <button class="action-btn" @click="editAlbumOpen = true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="action-icon">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              Edit Album
            </button>
            <button class="action-btn" @click="albumActionsMode = 'relocate'">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="action-icon">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
              Move Files
            </button>
            <button class="action-btn action-btn-danger" @click="albumActionsMode = 'remove'">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="action-icon">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                <path d="M10 11v6M14 11v6"/>
                <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
              </svg>
              Remove
            </button>
          </div>

          <!-- File location -->
          <div v-if="albumFolder" class="album-location">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="location-icon">
              <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/>
            </svg>
            <span class="location-path" :title="albumFolder">{{ albumFolder }}</span>
          </div>
        </div>
      </div>

      <!-- Track list -->
      <div class="track-section">
        <AlbumTrackList
          :tracks="visibleTracks"
          :disctotal="album.disctotal"
          :albumartist="album.albumartist"
          :album-id="album.id"
          :album-name="album.album"
          :show-actions="true"
          @edit-track="openEditTrack"
          @delete-track="confirmDeleteTrack"
        />
      </div>
    </template>

    <!-- Error state -->
    <div v-else class="error-state">
      <p class="error-text">Album not found.</p>
      <RouterLink to="/library" class="back-link">Return to Library</RouterLink>
    </div>

    <!-- Delete confirmation dialog -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="confirm-backdrop" @mousedown.self="deleteTarget = null">
        <div class="confirm-dialog">
          <h3 class="confirm-title">Remove track from library?</h3>
          <p class="confirm-body">
            "<strong>{{ deleteTarget.title }}</strong>" will be removed from the beets library.
            The audio file will <em>not</em> be deleted from disk.
          </p>
          <div class="confirm-footer">
            <button class="btn-cancel" @click="deleteTarget = null">Cancel</button>
            <button class="btn-delete" :disabled="deleting" @click="executeDeleteTrack">
              {{ deleting ? 'Removing…' : 'Remove' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Edit modals -->
    <AlbumEditModal
      :album="album ?? null"
      :open="editAlbumOpen"
      @close="editAlbumOpen = false"
      @saved="onAlbumSaved"
    />
    <ItemEditModal
      :item="editTrack"
      :open="editTrackOpen"
      @close="editTrackOpen = false"
      @saved="onTrackSaved"
    />
    <AlbumActionsModal
      :open="albumActionsOpen"
      :mode="albumActionsMode ?? 'remove'"
      :album-id="album?.id ?? null"
      :album-name="album?.album ?? null"
      :current-folder="albumFolder"
      @close="albumActionsMode = null"
      @removed="onAlbumRemoved"
      @relocated="onAlbumRelocated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { getAlbumArtUrl } from '@/api/albums'
import { deleteItem } from '@/api/library'
import { usePlayerStore } from '@/stores/player'
import AlbumTrackList from '@/components/albums/AlbumTrackList.vue'
import AlbumEditModal from '@/components/library/AlbumEditModal.vue'
import AlbumActionsModal from '@/components/library/AlbumActionsModal.vue'
import ItemEditModal from '@/components/library/ItemEditModal.vue'
import type { TrackInAlbum } from '@/types/album'

const route = useRoute()
const router = useRouter()
const store = useLibraryStore()
const playerStore = usePlayerStore()

const artError = ref(false)
const albumId = computed(() => Number(route.params.albumId))
const album = computed(() => store.currentAlbum)

const artUrl = computed(() => getAlbumArtUrl(albumId.value))

// Edit album modal
const editAlbumOpen = ref(false)

// Album actions modal (remove / relocate)
const albumActionsMode = ref<'remove' | 'relocate' | null>(null)
const albumActionsOpen = computed(() => albumActionsMode.value !== null)

// Edit track modal
const editTrackOpen = ref(false)
const editTrack = ref<TrackInAlbum | null>(null)

// Delete confirmation
const deleteTarget = ref<TrackInAlbum | null>(null)
const deleting = ref(false)

// Track list — reactively derived so removals update the view
const visibleTracks = ref<TrackInAlbum[]>([])

const placeholderStyle = computed(() => {
  const title = album.value?.album ?? ''
  const c1 = (title.charCodeAt(0) || 0)
  const c2 = (title.charCodeAt(1) || 0)
  const hue = ((c1 * 37 + c2 * 13) % 360 + 360) % 360
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 60%, 25%), hsl(${(hue + 40) % 360}, 60%, 18%))`,
  }
})

const placeholderInitial = computed(() => {
  const title = album.value?.album ?? ''
  return title.charAt(0).toUpperCase() || '?'
})

const formatLabel = computed(() => {
  const f = (album.value?.format ?? '').toUpperCase()
  if (f.includes('FLAC')) return 'FLAC'
  if (f.includes('MP3')) return 'MP3'
  if (f.includes('OGG')) return 'OGG'
  if (f.includes('AAC') || f.includes('M4A')) return 'AAC'
  if (f.includes('OPUS')) return 'Opus'
  return f.slice(0, 6) || null
})

const formatClass = computed(() => {
  const f = (album.value?.format ?? '').toUpperCase()
  if (f.includes('FLAC')) return 'badge-flac'
  if (f.includes('MP3')) return 'badge-mp3'
  if (f.includes('OGG') || f.includes('OPUS')) return 'badge-ogg'
  return 'badge-other'
})

// Derive album folder from the first track's path
const albumFolder = computed(() => {
  // Derive from the store's current album so it updates reactively after a move.
  const p = album.value?.items[0]?.path ?? null
  if (!p) return null
  const lastSlash = p.lastIndexOf('/')
  return lastSlash > 0 ? p.slice(0, lastSlash) : p
})

const totalDuration = computed(() => {
  const secs = album.value?.total_length ?? 0
  if (!secs) return '—'
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  const s = Math.floor(secs % 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m ${String(s).padStart(2, '0')}s`
})

function playAlbumNow() {
  if (!album.value?.items.length) return
  const tracks = visibleTracks.value.map(t => ({
    id: t.id,
    title: t.title ?? '',
    artist: t.artist ?? album.value?.albumartist ?? '',
    album: album.value?.album ?? '',
    album_id: album.value?.id ?? 0,
    length: t.length ?? 0,
    format: t.format ?? '',
    bitrate: t.bitrate ?? 0,
  }))
  playerStore.playAlbum(tracks)
}

function openEditTrack(track: TrackInAlbum) {
  editTrack.value = track
  editTrackOpen.value = true
}

function confirmDeleteTrack(track: TrackInAlbum) {
  deleteTarget.value = track
}

async function executeDeleteTrack() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await deleteItem(deleteTarget.value.id)
    visibleTracks.value = visibleTracks.value.filter(t => t.id !== deleteTarget.value!.id)
    deleteTarget.value = null
  } catch {
    // ignore — stay open
  } finally {
    deleting.value = false
  }
}

function onAlbumSaved(_updated: unknown) {
  store.fetchAlbum(albumId.value)
}

function onAlbumRemoved() {
  albumActionsMode.value = null
  router.push('/library')
}

function onAlbumRelocated(updated: unknown) {
  albumActionsMode.value = null
  // The modal returns the updated AlbumDetail with new paths — apply it directly
  // so albumFolder updates instantly without a second network round-trip.
  if (updated && typeof updated === 'object') {
    store.currentAlbum = updated as typeof store.currentAlbum
  }
}

function onTrackSaved(_updated: unknown) {
  store.fetchAlbum(albumId.value)
}

onMounted(async () => {
  store.currentAlbum = null
  await store.fetchAlbum(albumId.value)
  visibleTracks.value = [...(album.value?.items ?? [])]
})
</script>

<style scoped>
.detail-view {
  padding: 24px 32px 60px;
  min-height: 100%;
  background-color: #18181b;
  color: #f4f4f5;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #71717a;
  text-decoration: none;
  font-size: var(--text-base);
  margin-bottom: 24px;
  transition: color 0.15s;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.back-link:hover { color: #a78bfa; }

.back-icon { width: 16px; height: 16px; }

/* Hero layout */
.album-hero {
  display: flex;
  gap: 32px;
  margin-bottom: 40px;
  align-items: flex-start;
}

.cover-wrapper {
  flex-shrink: 0;
  width: 280px;
  height: 280px;
  border-radius: 12px;
  overflow: hidden;
  background-color: #27272a;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
}

@media (max-width: 900px) {
  .cover-wrapper {
    width: 200px;
    height: 200px;
  }
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #27272a;
  position: relative;
}

.cover-initial {
  font-size: 96px;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.15);
  line-height: 1;
  user-select: none;
}

.album-info {
  flex: 1;
  min-width: 0;
  padding-top: 8px;
}

.album-type {
  display: inline-block;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #a78bfa;
  background: rgba(167, 139, 250, 0.1);
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 4px;
  padding: 2px 8px;
  margin-bottom: 8px;
}

.album-title {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: #f4f4f5;
  margin: 0 0 8px;
  line-height: 1.2;
}

.album-artist {
  font-size: var(--text-lg);
  color: #a1a1aa;
  margin-bottom: 18px;
}

.meta-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
}

.meta-pill {
  font-size: var(--text-sm);
  padding: 4px 10px;
  background-color: #27272a;
  border-radius: 20px;
  color: #a1a1aa;
}

.format-pill.badge-flac { background-color: rgba(74, 222, 128, 0.15); color: #86efac; }
.format-pill.badge-mp3 { background-color: rgba(96, 165, 250, 0.15); color: #93c5fd; }
.format-pill.badge-ogg { background-color: rgba(251, 191, 36, 0.15); color: #fcd34d; }
.format-pill.badge-other { background-color: rgba(161, 161, 170, 0.15); color: #a1a1aa; }

.meta-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 20px 32px;
  margin-bottom: 24px;
}

.meta-stat { display: flex; flex-direction: column; gap: 2px; }

.stat-label {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #52525b;
}

.stat-value { font-size: var(--text-md); color: #d4d4d8; }

/* Album actions */
.album-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  padding: 6px 12px;
  color: #a1a1aa;
  font-size: var(--text-base);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}
.action-btn:hover { border-color: #7c3aed; color: #f4f4f5; }

.action-btn-play {
  background: #7c3aed;
  border-color: #7c3aed;
  color: white;
}
.action-btn-play:hover { background: #6d28d9; border-color: #6d28d9; color: white; }

.action-btn-danger {
  border-color: #7f1d1d;
  color: #fca5a5;
}
.action-btn-danger:hover {
  background: #7f1d1d;
  border-color: #dc2626;
  color: #fff;
}

.action-icon { width: 14px; height: 14px; }

/* File location */
.album-location {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 14px;
}

.location-icon {
  width: 14px;
  height: 14px;
  color: #52525b;
  flex-shrink: 0;
}

.location-path {
  font-size: var(--text-sm);
  font-family: ui-monospace, Consolas, monospace;
  color: #52525b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

/* Track section */
.track-section { border-top: 1px solid #27272a; padding-top: 28px; }

.track-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.track-section-title {
  font-size: var(--text-md);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #71717a;
  margin: 0;
}


/* Delete confirm */
.confirm-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9000;
  padding: 16px;
}

.confirm-dialog {
  background: #18181b;
  border: 1px solid #3f3f46;
  border-radius: 12px;
  padding: 24px;
  max-width: 420px;
  width: 100%;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6);
}

.confirm-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: #f4f4f5;
  margin: 0 0 12px;
}

.confirm-body {
  font-size: var(--text-md);
  color: #a1a1aa;
  line-height: 1.6;
  margin: 0 0 20px;
}

.confirm-footer { display: flex; justify-content: flex-end; gap: 10px; }

.btn-cancel {
  background: none;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  padding: 8px 16px;
  color: #a1a1aa;
  font-size: var(--text-md);
  cursor: pointer;
}
.btn-cancel:hover { border-color: #71717a; color: #f4f4f5; }

.btn-delete {
  background: #dc2626;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  color: white;
  font-size: var(--text-md);
  cursor: pointer;
}
.btn-delete:hover:not(:disabled) { background: #b91c1c; }
.btn-delete:disabled { opacity: 0.5; cursor: not-allowed; }

/* Loading skeletons */
.loading-state { width: 100%; }

.skeleton-hero {
  display: flex;
  gap: 32px;
  margin-bottom: 40px;
}

.skeleton-cover {
  width: 280px;
  height: 280px;
  border-radius: 12px;
  background: linear-gradient(90deg, #27272a 25%, #3f3f46 50%, #27272a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  flex-shrink: 0;
}

.skeleton-info {
  flex: 1;
  padding-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-bar {
  border-radius: 6px;
  background: linear-gradient(90deg, #27272a 25%, #3f3f46 50%, #27272a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-bar.tall { height: 32px; width: 70%; }
.skeleton-bar.medium { height: 18px; width: 45%; }
.skeleton-bar.short { height: 14px; width: 30%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Error */
.error-state { text-align: center; padding: 80px 24px; }
.error-text { font-size: var(--text-lg); color: #71717a; margin-bottom: 16px; }

@media (max-width: 640px) {
  .album-hero { flex-direction: column; }
  .cover-wrapper {
    width: min(100%, 220px);
    height: auto;
    max-height: 220px;
    aspect-ratio: 1 / 1;
    align-self: center;
  }
}
</style>
