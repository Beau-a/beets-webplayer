<template>
  <div class="artist-view">

    <!-- Artist header -->
    <div class="artist-header">
      <div
        v-if="albums.length > 0 && albums[0].has_art"
        class="artist-header-bg"
        :style="{ backgroundImage: `url(${getAlbumArtUrl(albums[0].id)})` }"
      ></div>
      <div class="artist-header-fg">
        <RouterLink to="/library" class="back-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="back-icon">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Library
        </RouterLink>
        <h1 class="artist-name">{{ artistName }}</h1>
        <span class="artist-meta" v-if="albums.length">
          {{ albums.length }} album{{ albums.length !== 1 ? 's' : '' }}
        </span>
        <div class="header-spacer" />
        <button class="header-btn" title="Move artist files" @click="artistModalMode = 'relocate'">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="header-btn-icon">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
          Move Artist
        </button>
        <button class="header-btn header-btn-danger" title="Remove artist from library" @click="artistModalMode = 'remove'">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="header-btn-icon">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
            <path d="M10 11v6M14 11v6"/>
            <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
          </svg>
          Remove Artist
        </button>
      </div>
    </div>

    <!-- Split panel -->
    <div class="split-panel">

      <!-- Left: album list -->
      <div class="album-list-panel">
        <div v-if="loadingAlbums" class="panel-loading">Loading albums…</div>
        <button
          v-for="alb in albums"
          :key="alb.id"
          class="album-row"
          :class="{ 'album-row-active': selectedAlbumId === alb.id }"
          @click="selectAlbum(alb.id)"
        >
          <div class="album-thumb">
            <img
              v-if="alb.has_art"
              :src="getAlbumArtUrl(alb.id)"
              class="album-thumb-img"
              loading="lazy"
              @error="(e) => ((e.target as HTMLImageElement).style.display = 'none')"
            />
            <div v-else class="album-thumb-placeholder">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="thumb-icon">
                <circle cx="9" cy="18" r="3"/><circle cx="18" cy="15" r="3"/>
                <polyline points="12 18 12 2 21 5 21 9"/>
              </svg>
            </div>
          </div>
          <div class="album-row-info">
            <span class="album-row-title">{{ alb.album || 'Unknown Album' }}</span>
            <span class="album-row-year" v-if="alb.year || alb.track_count">
              {{ [alb.year, alb.track_count ? `${alb.track_count} tracks` : null].filter(Boolean).join(' · ') }}
            </span>
          </div>
        </button>
      </div>

      <!-- Right: selected album detail -->
      <div class="album-detail-panel">
        <!-- Loading skeleton -->
        <div v-if="loadingDetail" class="detail-loading">
          <div class="skeleton-bar" style="width:55%;height:22px;margin-bottom:8px"></div>
          <div class="skeleton-bar" style="width:35%;height:14px;margin-bottom:20px"></div>
          <div v-for="i in 8" :key="i" class="skeleton-bar" style="height:14px;margin-bottom:8px"></div>
        </div>

        <template v-else-if="currentAlbum">
          <!-- Album sub-header -->
          <div class="detail-header">
            <div class="detail-header-info">
              <h2 class="detail-title">{{ currentAlbum.album || 'Unknown Album' }}</h2>
              <div class="detail-meta">
                <span v-if="currentAlbum.year" class="detail-meta-item">{{ currentAlbum.year }}</span>
                <span v-if="formatLabel" class="detail-meta-item format-badge" :class="formatClass">{{ formatLabel }}</span>
                <span class="detail-meta-item">{{ currentAlbum.track_count }} tracks</span>
                <span class="detail-meta-item">{{ totalDuration }}</span>
                <span v-if="currentAlbum.genres" class="detail-meta-item">{{ currentAlbum.genres }}</span>
              </div>
              <div v-if="albumFolder" class="detail-location">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="location-icon">
                  <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/>
                </svg>
                <span class="location-path" :title="albumFolder">{{ albumFolder }}</span>
              </div>
            </div>
            <div class="detail-actions">
              <button class="action-btn action-btn-play" @click="playAlbum">
                <svg viewBox="0 0 24 24" fill="currentColor" class="action-icon"><polygon points="5,3 19,12 5,21"/></svg>
                Play
              </button>
              <button class="action-btn" @click="editAlbumOpen = true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="action-icon">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
                Edit
              </button>
              <button class="action-btn" @click="albumActionsMode = 'relocate'">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="action-icon">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
                Move
              </button>
              <button class="action-btn action-btn-danger" @click="albumActionsMode = 'remove'">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="action-icon">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                </svg>
                Remove
              </button>
            </div>
          </div>

          <!-- Track list -->
          <div class="detail-tracks">
            <AlbumTrackList
              :tracks="currentAlbum.items"
              :disctotal="currentAlbum.disctotal"
              :albumartist="currentAlbum.albumartist"
              :album-id="currentAlbum.id"
              :album-name="currentAlbum.album"
            />
          </div>
        </template>

        <div v-else class="detail-empty">
          Select an album to view its tracks.
        </div>
      </div>
    </div>

    <!-- Album-level modals -->
    <AlbumActionsModal
      :open="albumActionsMode !== null"
      :mode="albumActionsMode ?? 'remove'"
      :album-id="currentAlbum?.id ?? null"
      :album-name="currentAlbum?.album ?? null"
      :current-folder="albumFolder"
      @close="albumActionsMode = null"
      @removed="onAlbumRemoved"
      @relocated="onAlbumRelocated"
    />
    <AlbumEditModal
      :album="currentAlbum ?? null"
      :open="editAlbumOpen"
      @close="editAlbumOpen = false"
      @saved="onAlbumSaved"
    />

    <!-- Artist-level modals -->
    <ArtistActionsModal
      :open="artistModalMode !== null"
      :mode="artistModalMode ?? 'remove'"
      :artist-name="artistName"
      @close="artistModalMode = null"
      @removed="onArtistRemoved"
      @done="onArtistDone"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { fetchAlbums as apiFetchAlbums, fetchAlbum as apiFetchAlbum, getAlbumArtUrl } from '@/api/albums'
import AlbumTrackList from '@/components/albums/AlbumTrackList.vue'
import AlbumActionsModal from '@/components/library/AlbumActionsModal.vue'
import AlbumEditModal from '@/components/library/AlbumEditModal.vue'
import ArtistActionsModal from '@/components/library/ArtistActionsModal.vue'
import type { AlbumSummary, AlbumDetail } from '@/types/album'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()

const artistName = computed(() => decodeURIComponent(route.params.artistName as string))

const albums = ref<AlbumSummary[]>([])
const loadingAlbums = ref(false)
const selectedAlbumId = ref<number | null>(null)
const loadingDetail = ref(false)
const currentAlbum = ref<AlbumDetail | null>(null)

const editAlbumOpen = ref(false)
const albumActionsMode = ref<'remove' | 'relocate' | null>(null)
const artistModalMode = ref<'remove' | 'relocate' | null>(null)

// ---------- derived ----------

const albumFolder = computed(() => {
  const p = currentAlbum.value?.items[0]?.path ?? null
  if (!p) return null
  const i = p.lastIndexOf('/')
  return i > 0 ? p.slice(0, i) : p
})

const formatLabel = computed(() => {
  const f = (currentAlbum.value?.format ?? '').toUpperCase()
  if (f.includes('FLAC')) return 'FLAC'
  if (f.includes('MP3')) return 'MP3'
  if (f.includes('OGG')) return 'OGG'
  if (f.includes('AAC') || f.includes('M4A')) return 'AAC'
  if (f.includes('OPUS')) return 'Opus'
  return f.slice(0, 6) || null
})

const formatClass = computed(() => {
  const f = (currentAlbum.value?.format ?? '').toUpperCase()
  if (f.includes('FLAC')) return 'badge-flac'
  if (f.includes('MP3')) return 'badge-mp3'
  if (f.includes('OGG') || f.includes('OPUS')) return 'badge-ogg'
  return 'badge-other'
})

const totalDuration = computed(() => {
  const secs = currentAlbum.value?.total_length ?? 0
  if (!secs) return ''
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  const s = Math.floor(secs % 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m ${String(s).padStart(2, '0')}s`
})

// ---------- data loading ----------

async function loadAlbums() {
  loadingAlbums.value = true
  try {
    const q = `albumartist:"${artistName.value}"`
    const data = await apiFetchAlbums({ q, page: 1, page_size: 200, sort: 'year+' })
    albums.value = data.items
    if (data.items.length > 0 && selectedAlbumId.value === null) {
      selectAlbum(data.items[0].id)
    }
  } finally {
    loadingAlbums.value = false
  }
}

async function selectAlbum(id: number) {
  if (selectedAlbumId.value === id && currentAlbum.value) return
  selectedAlbumId.value = id
  loadingDetail.value = true
  currentAlbum.value = null
  nextTick(() => {
    document.querySelector('.album-row-active')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  })
  try {
    currentAlbum.value = await apiFetchAlbum(id)
  } finally {
    loadingDetail.value = false
  }
}

// ---------- actions ----------

function playAlbum() {
  if (!currentAlbum.value?.items.length) return
  playerStore.playAlbum(
    currentAlbum.value.items.map(t => ({
      id: t.id,
      title: t.title ?? '',
      artist: t.artist ?? currentAlbum.value?.albumartist ?? '',
      album: currentAlbum.value?.album ?? '',
      album_id: currentAlbum.value?.id ?? 0,
      length: t.length ?? 0,
      format: t.format ?? '',
      bitrate: t.bitrate ?? 0,
    }))
  )
}

function onAlbumRemoved() {
  albumActionsMode.value = null
  albums.value = albums.value.filter(a => a.id !== selectedAlbumId.value)
  currentAlbum.value = null
  selectedAlbumId.value = null
  if (albums.value.length > 0) selectAlbum(albums.value[0].id)
}

function onAlbumRelocated(updated: unknown) {
  albumActionsMode.value = null
  if (updated && typeof updated === 'object') {
    currentAlbum.value = updated as AlbumDetail
  }
}

function onAlbumSaved() {
  if (selectedAlbumId.value !== null) selectAlbum(selectedAlbumId.value)
}

function onArtistRemoved() {
  artistModalMode.value = null
  router.push('/library')
}

function onArtistDone() {
  artistModalMode.value = null
  loadAlbums()
}

// ---------- lifecycle ----------

onMounted(loadAlbums)

watch(artistName, () => {
  albums.value = []
  currentAlbum.value = null
  selectedAlbumId.value = null
  loadAlbums()
})
</script>

<style scoped>
.artist-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #18181b;
  color: #f4f4f5;
  overflow: hidden;
}

/* Header */
.artist-header {
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid #27272a;
  flex-shrink: 0;
}

.artist-header-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background-size: cover;
  background-position: center;
  filter: blur(40px);
  opacity: 0.12;
  transform: scale(1.1);
}

.artist-header-fg {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 24px;
  flex-wrap: wrap;
  width: 100%;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #71717a;
  text-decoration: none;
  font-size: 13px;
  transition: color 0.15s;
  flex-shrink: 0;
}
.back-link:hover { color: #a78bfa; }
.back-icon { width: 15px; height: 15px; }

.artist-name {
  font-size: 18px;
  font-weight: 700;
  color: #f4f4f5;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.artist-meta {
  font-size: 13px;
  color: #71717a;
  flex-shrink: 0;
}

.header-spacer { flex: 1; }

.header-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  padding: 6px 11px;
  color: #a1a1aa;
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  flex-shrink: 0;
}
.header-btn:hover { border-color: #7c3aed; color: #f4f4f5; }
.header-btn-danger { border-color: #7f1d1d; color: #fca5a5; }
.header-btn-danger:hover { background: #7f1d1d; border-color: #dc2626; color: #fff; }
.header-btn-icon { width: 13px; height: 13px; }

/* Split panel */
.split-panel {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Left: album list */
.album-list-panel {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid #27272a;
  overflow-y: auto;
  padding: 6px 0;
}

.album-list-panel::-webkit-scrollbar { width: 4px; }
.album-list-panel::-webkit-scrollbar-track { background: transparent; }
.album-list-panel::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 2px; }

.panel-loading {
  font-size: 12px;
  color: #52525b;
  padding: 20px;
  text-align: center;
}

.album-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 6px 10px;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background-color 0.12s;
  border-left: 2px solid transparent;
}
.album-row:hover { background-color: #27272a; }
.album-row-active {
  background-color: #27272a;
  border-left-color: #7c3aed;
}

.album-thumb {
  width: 44px;
  height: 44px;
  border-radius: 5px;
  overflow: hidden;
  flex-shrink: 0;
  background: #27272a;
}
.album-thumb-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.album-thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.thumb-icon { width: 20px; height: 20px; color: #3f3f46; }

.album-row-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.album-row-title {
  font-size: 13px;
  color: #d4d4d8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.album-row-active .album-row-title { color: #f4f4f5; }
.album-row-year { font-size: 11px; color: #71717a; }

/* Right: album detail */
.album-detail-panel {
  flex: 1;
  overflow-y: auto;
  min-width: 0;
}

.album-detail-panel::-webkit-scrollbar { width: 6px; }
.album-detail-panel::-webkit-scrollbar-track { background: transparent; }
.album-detail-panel::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 3px; }

.detail-loading {
  padding: 24px 28px;
}
.skeleton-bar {
  border-radius: 5px;
  background: linear-gradient(90deg, #27272a 25%, #3f3f46 50%, #27272a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  width: 100%;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.detail-empty {
  padding: 60px 28px;
  text-align: center;
  font-size: 14px;
  color: #52525b;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #27272a;
  flex-wrap: wrap;
}

.detail-header-info { flex: 1; min-width: 0; }

.detail-title {
  font-size: 20px;
  font-weight: 700;
  color: #f4f4f5;
  margin: 0 0 8px;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.detail-meta-item {
  font-size: 12px;
  color: #71717a;
}
.detail-meta-item + .detail-meta-item::before {
  content: '·';
  margin-right: 8px;
}

.format-badge {
  padding: 2px 7px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
}
.badge-flac { background: rgba(74,222,128,0.15); color: #86efac; }
.badge-mp3  { background: rgba(96,165,250,0.15); color: #93c5fd; }
.badge-ogg  { background: rgba(251,191,36,0.15); color: #fcd34d; }
.badge-other { background: rgba(161,161,170,0.15); color: #a1a1aa; }

.detail-location {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 4px;
}
.location-icon { width: 13px; height: 13px; color: #52525b; flex-shrink: 0; }
.location-path {
  font-size: 11px;
  font-family: ui-monospace, Consolas, monospace;
  color: #52525b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.detail-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  padding: 6px 10px;
  color: #a1a1aa;
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  white-space: nowrap;
}
.action-btn:hover { border-color: #7c3aed; color: #f4f4f5; }
.action-btn-play { background: #7c3aed; border-color: #7c3aed; color: white; }
.action-btn-play:hover { background: #6d28d9; border-color: #6d28d9; }
.action-btn-danger { border-color: #7f1d1d; color: #fca5a5; }
.action-btn-danger:hover { background: #7f1d1d; border-color: #dc2626; color: #fff; }
.action-icon { width: 13px; height: 13px; }

.detail-tracks { padding: 8px 0 32px; }
</style>
