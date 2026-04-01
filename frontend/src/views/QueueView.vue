<template>
  <div class="queue-view">
    <div class="queue-header">
      <h1 class="queue-heading">Play Queue</h1>
      <button
        v-if="store.queue.length > 0"
        class="clear-all-btn"
        @click="store.clearQueue()"
      >
        Clear all
      </button>
    </div>

    <!-- Currently playing -->
    <template v-if="store.currentTrack">
      <section class="queue-section">
        <h2 class="section-label">Now Playing</h2>
        <div class="current-track-card">
          <div class="current-art">
            <img
              v-if="!nowArtError"
              :src="`/api/albums/${store.currentTrack.album_id}/art`"
              :alt="store.currentTrack.album"
              class="art-img"
              @error="nowArtError = true"
            />
            <div v-else class="art-placeholder">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="9" cy="18" r="3"/>
                <circle cx="18" cy="15" r="3"/>
                <polyline points="12 18 12 2 21 5 21 9"/>
                <line x1="12" y1="10" x2="12" y2="18"/>
              </svg>
            </div>
          </div>
          <div class="current-info">
            <div class="current-title">{{ store.currentTrack.title }}</div>
            <div class="current-artist">{{ store.currentTrack.artist }}</div>
            <div class="current-album">{{ store.currentTrack.album }}</div>
          </div>
          <!-- Mini playback controls -->
          <div class="current-controls">
            <PlaybackControls />
          </div>
        </div>
      </section>
    </template>

    <!-- Up next -->
    <section class="queue-section">
      <h2 class="section-label">
        Up Next
        <span v-if="upNextTracks.length" class="section-count">{{ upNextTracks.length }} tracks</span>
      </h2>

      <template v-if="upNextTracks.length > 0">
        <div
          v-for="(item) in upNextTracks"
          :key="`${item.track.id}-${item.index}`"
          class="queue-row"
          @click="store.jumpToIndex(item.index)"
        >
          <span class="row-index">{{ item.index + 1 }}</span>
          <div class="row-info">
            <span class="row-title">{{ item.track.title }}</span>
            <span class="row-artist">{{ item.track.artist }}</span>
          </div>
          <span class="row-album">{{ item.track.album }}</span>
          <span class="row-duration">{{ formatTime(item.track.length) }}</span>
          <button
            class="row-remove"
            title="Remove"
            @click.stop="store.removeFromQueue(item.index)"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </template>
      <div v-else class="queue-empty">
        <p>Nothing up next.</p>
        <p class="queue-empty-hint">Play an album or track to build a queue.</p>
      </div>
    </section>

    <!-- Previously played (tracks before current) -->
    <section v-if="previousTracks.length > 0" class="queue-section queue-section-dim">
      <h2 class="section-label">Previously Played</h2>
      <div
        v-for="(item) in previousTracks"
        :key="`${item.track.id}-${item.index}`"
        class="queue-row queue-row-dim"
        @click="store.jumpToIndex(item.index)"
      >
        <span class="row-index">{{ item.index + 1 }}</span>
        <div class="row-info">
          <span class="row-title">{{ item.track.title }}</span>
          <span class="row-artist">{{ item.track.artist }}</span>
        </div>
        <span class="row-album">{{ item.track.album }}</span>
        <span class="row-duration">{{ formatTime(item.track.length) }}</span>
        <button
          class="row-remove"
          title="Remove"
          @click.stop="store.removeFromQueue(item.index)"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { usePlayerStore } from '@/stores/player'
import PlaybackControls from '@/components/player/PlaybackControls.vue'
import type { QueueTrack } from '@/types/player'

const store = usePlayerStore()
const nowArtError = ref(false)

interface IndexedTrack {
  track: QueueTrack
  index: number
}

const upNextTracks = computed<IndexedTrack[]>(() => {
  return store.queue
    .map((t, i) => ({ track: t, index: i }))
    .filter((item) => item.index > store.queueIndex)
})

const previousTracks = computed<IndexedTrack[]>(() => {
  return store.queue
    .map((t, i) => ({ track: t, index: i }))
    .filter((item) => item.index < store.queueIndex)
})

function formatTime(seconds: number): string {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}
</script>

<style scoped>
.queue-view {
  padding: 24px 32px 60px;
  min-height: 100%;
  background-color: #18181b;
  color: #f4f4f5;
  max-width: 900px;
}

.queue-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.queue-heading {
  font-size: 24px;
  font-weight: 700;
  color: #f4f4f5;
  margin: 0;
}

.clear-all-btn {
  font-size: 13px;
  color: #71717a;
  background: transparent;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  padding: 6px 14px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.clear-all-btn:hover {
  color: #ef4444;
  border-color: #ef4444;
}

.queue-section {
  margin-bottom: 36px;
}

.section-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #52525b;
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-count {
  font-size: 11px;
  font-weight: 500;
  color: #3f3f46;
  letter-spacing: 0;
  text-transform: none;
}

/* Currently playing card */
.current-track-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background-color: #27272a;
  border: 1px solid #3f3f46;
  border-left: 3px solid #8b5cf6;
  border-radius: 10px;
  padding: 16px;
}

.current-art {
  width: 64px;
  height: 64px;
  border-radius: 6px;
  overflow: hidden;
  background-color: #18181b;
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
  display: flex;
  align-items: center;
  justify-content: center;
}

.art-placeholder svg {
  width: 28px;
  height: 28px;
  color: #52525b;
}

.current-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.current-title {
  font-size: 15px;
  font-weight: 600;
  color: #f4f4f5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.current-artist {
  font-size: 13px;
  color: #a1a1aa;
}

.current-album {
  font-size: 12px;
  color: #71717a;
}

.current-controls {
  flex-shrink: 0;
}

/* Queue rows */
.queue-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.1s;
}

.queue-row:hover {
  background-color: #27272a;
}

.queue-row-dim {
  opacity: 0.5;
}

.row-index {
  font-size: 12px;
  color: #52525b;
  min-width: 24px;
  text-align: right;
  flex-shrink: 0;
}

.row-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.row-title {
  font-size: 13px;
  font-weight: 500;
  color: #f4f4f5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-artist {
  font-size: 12px;
  color: #71717a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-album {
  font-size: 12px;
  color: #52525b;
  min-width: 120px;
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 0;
}

.row-duration {
  font-size: 12px;
  color: #71717a;
  font-variant-numeric: tabular-nums;
  min-width: 36px;
  text-align: right;
  flex-shrink: 0;
}

.row-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: transparent;
  border-radius: 4px;
  cursor: pointer;
  padding: 0;
  transition: color 0.15s;
  flex-shrink: 0;
}

.row-remove svg {
  width: 13px;
  height: 13px;
}

.queue-row:hover .row-remove {
  color: #71717a;
}

.row-remove:hover {
  color: #ef4444 !important;
}

.queue-empty {
  padding: 40px 0;
  text-align: center;
}

.queue-empty p {
  font-size: 14px;
  color: #52525b;
  margin: 0 0 6px;
}

.queue-empty-hint {
  font-size: 12px;
  color: #3f3f46 !important;
}
</style>
