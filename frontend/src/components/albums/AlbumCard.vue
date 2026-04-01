<template>
  <div class="album-card-wrapper">
    <RouterLink :to="`/library/${album.id}`" class="album-card">
      <!-- Cover art -->
      <div class="art-wrapper">
        <img
          v-if="!artError && album.has_art"
          :src="artUrl"
          :alt="`${album.album} cover`"
          class="art-img"
          @error="artError = true"
        />
        <div v-else class="art-placeholder">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="placeholder-icon">
            <circle cx="9" cy="18" r="3"/>
            <circle cx="18" cy="15" r="3"/>
            <polyline points="12 18 12 2 21 5 21 9"/>
            <line x1="12" y1="10" x2="12" y2="18"/>
          </svg>
        </div>

        <!-- Play button overlay -->
        <div class="play-overlay" @click.prevent="onPlayClick">
          <button class="play-circle" :class="{ 'play-circle-loading': isLoading }" :title="`Play ${album.album}`">
            <svg v-if="!isLoading" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5,3 19,12 5,21"/>
            </svg>
            <!-- Spinner -->
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="spinner">
              <circle cx="12" cy="12" r="10" stroke-dasharray="40 22"/>
            </svg>
          </button>
        </div>

        <!-- Now-playing indicator badge -->
        <div v-if="isCurrentAlbum" class="now-playing-badge">
          <span class="badge-dot" :style="{ animationPlayState: playerStore.isPlaying ? 'running' : 'paused' }"></span>
          <span class="badge-dot" :style="{ animationPlayState: playerStore.isPlaying ? 'running' : 'paused' }"></span>
          <span class="badge-dot" :style="{ animationPlayState: playerStore.isPlaying ? 'running' : 'paused' }"></span>
        </div>
      </div>

      <!-- Metadata -->
      <div class="card-meta">
        <div class="card-title">{{ album.album || 'Unknown Album' }}</div>
        <RouterLink
          :to="`/artist/${encodeURIComponent(album.albumartist || 'Unknown Artist')}`"
          class="card-artist card-artist-link"
          @click.stop
        >{{ album.albumartist || 'Unknown Artist' }}</RouterLink>
        <div class="card-footer">
          <span class="card-year">{{ album.year || '—' }}</span>
          <span v-if="album.format" class="format-badge" :class="formatClass">
            {{ formatLabel }}
          </span>
        </div>
      </div>
    </RouterLink>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { getAlbumArtUrl, fetchAlbum } from '@/api/albums'
import { usePlayerStore } from '@/stores/player'
import type { AlbumSummary } from '@/types/album'
import type { QueueTrack } from '@/types/player'

const props = defineProps<{
  album: AlbumSummary
}>()

const playerStore = usePlayerStore()
const artError = ref(false)
const isLoading = ref(false)
const artUrl = computed(() => getAlbumArtUrl(props.album.id))

const isCurrentAlbum = computed(() => {
  return playerStore.currentTrack?.album_id === props.album.id
})

const formatLabel = computed(() => {
  const f = props.album.format?.toUpperCase() ?? ''
  if (f.includes('FLAC')) return 'FLAC'
  if (f.includes('MP3')) return 'MP3'
  if (f.includes('OGG')) return 'OGG'
  if (f.includes('AAC') || f.includes('M4A')) return 'AAC'
  if (f.includes('OPUS')) return 'Opus'
  return f.slice(0, 6) || '—'
})

const formatClass = computed(() => {
  const f = props.album.format?.toUpperCase() ?? ''
  if (f.includes('FLAC')) return 'badge-flac'
  if (f.includes('MP3')) return 'badge-mp3'
  if (f.includes('OGG') || f.includes('OPUS')) return 'badge-ogg'
  return 'badge-other'
})

async function onPlayClick() {
  if (isLoading.value) return

  // If this album is already playing, just toggle play/pause
  if (isCurrentAlbum.value) {
    playerStore.setIsPlaying(!playerStore.isPlaying)
    return
  }

  isLoading.value = true
  try {
    const detail = await fetchAlbum(props.album.id)
    const queueTracks: QueueTrack[] = detail.items
      .slice()
      .sort((a, b) => {
        const discDiff = (a.disc || 1) - (b.disc || 1)
        if (discDiff !== 0) return discDiff
        return (a.track || 0) - (b.track || 0)
      })
      .map((t) => ({
        id: t.id,
        title: t.title,
        artist: t.artist || detail.albumartist || 'Unknown Artist',
        album: detail.album || 'Unknown Album',
        album_id: detail.id,
        length: t.length,
        format: t.format,
        bitrate: t.bitrate,
      }))
    playerStore.playAlbum(queueTracks, 0)
  } catch (err) {
    console.error('[AlbumCard] Failed to load album tracks:', err)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.album-card-wrapper {
  position: relative;
}

.album-card {
  display: flex;
  flex-direction: column;
  width: 100%;
  background-color: #27272a; /* zinc-800 */
  border-radius: 10px;
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  cursor: pointer;
}

.album-card:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.7), 0 2px 8px rgba(124, 58, 237, 0.15);
}

.art-wrapper {
  width: 100%;
  aspect-ratio: 1 / 1;
  height: auto;
  flex-shrink: 0;
  background-color: #18181b; /* zinc-900 */
  overflow: hidden;
  position: relative;
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
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #18181b;
}

.placeholder-icon {
  width: 48px;
  height: 48px;
  color: #52525b; /* zinc-600 */
}

/* Play overlay */
.play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  padding: 10px;
  opacity: 0;
  transition: opacity 0.15s;
  background: linear-gradient(to top, rgba(0,0,0,0.6) 0%, transparent 60%);
}

.album-card:hover .play-overlay {
  opacity: 1;
}

.play-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #8b5cf6; /* violet-500 */
  border: none;
  cursor: pointer;
  padding: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  transition: background-color 0.15s, transform 0.1s;
}

.play-circle svg {
  width: 16px;
  height: 16px;
  color: #fff;
  margin-left: 2px; /* optical center for play triangle */
}

.play-circle:hover {
  background-color: #7c3aed;
  transform: scale(1.08);
}

.play-circle-loading {
  background-color: #6d28d9;
  cursor: wait;
}

/* Spinner animation */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner {
  animation: spin 0.8s linear infinite;
}

/* Now playing animated bars */
.now-playing-badge {
  position: absolute;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 14px;
  background-color: rgba(0,0,0,0.6);
  border-radius: 4px;
  padding: 4px 8px;
}

.badge-dot {
  display: block;
  width: 4px;
  max-height: 14px;
  border-radius: 1px;
  background-color: #a78bfa;
  animation: bar-bounce 0.8s ease infinite alternate;
}

.badge-dot:nth-child(1) { height: 6px; animation-delay: 0s; }
.badge-dot:nth-child(2) { height: 10px; animation-delay: 0.2s; }
.badge-dot:nth-child(3) { height: 6px; animation-delay: 0.4s; }

@keyframes bar-bounce {
  from { transform: scaleY(0.4); }
  to { transform: scaleY(1); }
}

/* Card metadata */
.card-meta {
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-height: 0;
}

.card-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: #f4f4f5; /* zinc-100 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.card-artist {
  font-size: var(--text-sm);
  color: #71717a; /* zinc-500 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.card-artist-link {
  text-decoration: none;
  transition: color 0.15s;
}

.card-artist-link:hover {
  color: #a78bfa;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}

.card-year {
  font-size: var(--text-sm);
  color: #52525b; /* zinc-600 */
}

.format-badge {
  font-size: var(--text-2xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 2px 6px;
  border-radius: 4px;
  line-height: 1.5;
}

.badge-flac {
  background-color: rgba(74, 222, 128, 0.15);
  color: #4ade80; /* green-400 */
}

.badge-mp3 {
  background-color: rgba(96, 165, 250, 0.15);
  color: #60a5fa; /* blue-400 */
}

.badge-ogg {
  background-color: rgba(251, 191, 36, 0.15);
  color: #fbbf24; /* amber-400 */
}

.badge-other {
  background-color: rgba(161, 161, 170, 0.15);
  color: #a1a1aa; /* zinc-400 */
}
</style>
