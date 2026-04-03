<template>
  <div class="now-playing-view">
    <!-- Blurred backdrop -->
    <div
      v-if="store.currentTrack"
      class="backdrop"
      :style="backdropStyle"
    ></div>

    <!-- Empty state -->
    <div v-if="!store.currentTrack" class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
        <circle cx="9" cy="18" r="3"/>
        <circle cx="18" cy="15" r="3"/>
        <polyline points="12 18 12 2 21 5 21 9"/>
        <line x1="12" y1="10" x2="12" y2="18"/>
      </svg>
      <p class="empty-text">Nothing playing</p>
      <RouterLink to="/library" class="empty-link">Browse your library</RouterLink>
    </div>

    <!-- Main now-playing layout -->
    <div v-else class="np-content">
      <!-- Left column: art + controls -->
      <div class="np-left">
        <!-- Album art -->
        <div class="art-container">
          <img
            v-if="!artError"
            :src="`/api/albums/${store.currentTrack.album_id}/art`"
            :alt="`${store.currentTrack.album} cover`"
            class="art-img"
            @error="artError = true"
          />
          <div v-else class="art-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="art-placeholder-icon">
              <circle cx="9" cy="18" r="3"/>
              <circle cx="18" cy="15" r="3"/>
              <polyline points="12 18 12 2 21 5 21 9"/>
              <line x1="12" y1="10" x2="12" y2="18"/>
            </svg>
          </div>
        </div>

        <!-- Track info -->
        <div class="track-info">
          <div class="track-title">{{ store.currentTrack.title }}</div>
          <RouterLink
            :to="`/artist/${encodeURIComponent(store.currentTrack.artist)}`"
            class="track-artist"
          >{{ store.currentTrack.artist }}</RouterLink>
          <RouterLink
            :to="`/library/${store.currentTrack.album_id}`"
            class="track-album"
          >{{ store.currentTrack.album }}</RouterLink>
        </div>

        <!-- Playback controls -->
        <div class="controls-section">
          <PlaybackControls />
        </div>

        <!-- Progress bar -->
        <div class="progress-section">
          <ProgressBar />
        </div>
      </div>

      <!-- Right column: lyrics + up next -->
      <div class="np-right">
        <!-- Lyrics panel -->
        <div class="panel lyrics-panel">
          <h3 class="panel-title">Lyrics</h3>
          <div v-if="lyricsLoading" class="panel-loading">Loading lyrics...</div>
          <div v-else-if="lyrics" class="lyrics-text">{{ lyrics }}</div>
          <div v-else class="panel-empty">No lyrics available</div>
        </div>

        <!-- Up Next -->
        <div class="panel up-next-panel">
          <h3 class="panel-title">Up Next</h3>
          <div v-if="upNext.length === 0" class="panel-empty">Nothing queued</div>
          <ul v-else class="up-next-list">
            <li
              v-for="(track, i) in upNext"
              :key="track.id"
              class="up-next-item"
              @click="store.jumpToIndex(store.queueIndex + 1 + i)"
            >
              <span class="up-next-num">{{ i + 1 }}</span>
              <div class="up-next-info">
                <span class="up-next-title">{{ track.title }}</span>
                <span class="up-next-artist">{{ track.artist }}</span>
              </div>
              <span class="up-next-dur">{{ formatTime(track.length) }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import PlaybackControls from '@/components/player/PlaybackControls.vue'
import ProgressBar from '@/components/player/ProgressBar.vue'
import { fetchItem } from '@/api/items'

const store = usePlayerStore()
const artError = ref(false)
const lyrics = ref<string | null>(null)
const lyricsLoading = ref(false)

// Reset art error when track changes
watch(
  () => store.currentTrack?.album_id,
  () => { artError.value = false },
)

// Blurred backdrop using album art
const backdropStyle = computed(() => {
  if (!store.currentTrack) return {}
  return {
    backgroundImage: `url(/api/albums/${store.currentTrack.album_id}/art)`,
  }
})

// Up next: next 5 tracks in queue
const upNext = computed(() => {
  const startIdx = store.queueIndex + 1
  return store.queue.slice(startIdx, startIdx + 5)
})

function formatTime(seconds: number | undefined): string {
  if (!seconds || isNaN(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

async function loadLyrics(itemId: number) {
  lyricsLoading.value = true
  lyrics.value = null
  try {
    const item = await fetchItem(itemId, true)
    lyrics.value = item.lyrics ?? null
  } catch {
    lyrics.value = null
  } finally {
    lyricsLoading.value = false
  }
}

// Load lyrics when current track changes
watch(
  () => store.currentTrack?.id,
  (id) => {
    if (id != null) loadLyrics(id)
    else lyrics.value = null
  },
  { immediate: true },
)

onMounted(() => {
  if (store.currentTrack?.id) loadLyrics(store.currentTrack.id)
})
</script>

<style scoped>
.now-playing-view {
  position: relative;
  min-height: calc(100vh - 44px - 72px);
  display: flex;
  align-items: stretch;
  overflow: hidden;
}

/* Blurred backdrop */
.backdrop {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  filter: blur(40px) brightness(0.3);
  transform: scale(1.1); /* prevent blur edge artifacts */
  pointer-events: none;
  z-index: 0;
}

/* Empty state */
.empty-state {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 16px;
  padding: 60px;
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: #52525b;
}

.empty-text {
  font-size: var(--text-xl, 1.25rem);
  color: #71717a;
  margin: 0;
}

.empty-link {
  color: #a78bfa;
  text-decoration: none;
  font-size: var(--text-base);
  transition: color 0.15s;
}

.empty-link:hover {
  color: #c4b5fd;
}

/* Main layout */
.np-content {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 40px;
  width: 100%;
  padding: 40px 40px 24px;
  align-items: flex-start;
}

/* Left column */
.np-left {
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.art-container {
  width: 320px;
  height: 320px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6);
  flex-shrink: 0;
}

.art-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.art-placeholder {
  width: 100%;
  height: 100%;
  background-color: #27272a;
  display: flex;
  align-items: center;
  justify-content: center;
}

.art-placeholder-icon {
  width: 80px;
  height: 80px;
  color: #52525b;
}

/* Track info */
.track-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  width: 100%;
  text-align: center;
}

.track-title {
  font-size: var(--text-xl, 1.25rem);
  font-weight: 700;
  color: #f4f4f5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

.track-artist {
  font-size: var(--text-base);
  color: #a78bfa;
  text-decoration: none;
  transition: color 0.15s;
}
.track-artist:hover { color: #c4b5fd; }

.track-album {
  font-size: var(--text-sm);
  color: #71717a;
  text-decoration: none;
  transition: color 0.15s;
}
.track-album:hover { color: #a1a1aa; }

.controls-section {
  width: 100%;
  display: flex;
  justify-content: center;
}

.progress-section {
  width: 100%;
}

/* Right column */
.np-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0;
}

.panel {
  background-color: rgba(24, 24, 27, 0.7);
  border: 1px solid rgba(39, 39, 42, 0.8);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(8px);
}

.panel-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: #a1a1aa;
  margin: 0 0 14px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 11px;
}

.panel-empty {
  color: #52525b;
  font-size: var(--text-sm);
}

.panel-loading {
  color: #71717a;
  font-size: var(--text-sm);
}

/* Lyrics panel */
.lyrics-panel {
  max-height: 260px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #3f3f46 transparent;
}

.lyrics-text {
  font-size: var(--text-sm, 0.875rem);
  color: #d4d4d8;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Up next */
.up-next-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.up-next-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.12s;
}

.up-next-item:hover {
  background-color: rgba(39, 39, 42, 0.8);
}

.up-next-num {
  font-size: var(--text-sm);
  color: #52525b;
  width: 18px;
  text-align: center;
  flex-shrink: 0;
}

.up-next-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.up-next-title {
  font-size: var(--text-sm);
  color: #e4e4e7;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.up-next-artist {
  font-size: var(--text-xs);
  color: #71717a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.up-next-dur {
  font-size: var(--text-xs);
  color: #52525b;
  flex-shrink: 0;
}
</style>
