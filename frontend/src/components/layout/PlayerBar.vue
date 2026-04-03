<template>
  <div class="player-bar">
    <!-- Left: Now playing info -->
    <div class="now-playing">
      <template v-if="store.currentTrack">
        <!-- Album art thumbnail → link to now playing -->
        <RouterLink to="/now-playing" class="art-thumb" title="Now Playing">
          <img
            v-if="!artError"
            :src="`/api/albums/${store.currentTrack.album_id}/art`"
            :alt="store.currentTrack.album"
            class="art-img"
            @error="artError = true"
          />
          <div v-else class="art-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="9" cy="18" r="3"/>
              <circle cx="18" cy="15" r="3"/>
              <polyline points="12 18 12 2 21 5 21 9"/>
              <line x1="12" y1="10" x2="12" y2="18"/>
            </svg>
          </div>
        </RouterLink>
        <!-- Track info -->
        <div class="track-info">
          <RouterLink :to="`/library/${store.currentTrack.album_id}`" class="track-title track-link">{{ store.currentTrack.title }}</RouterLink>
          <RouterLink :to="`/artist/${encodeURIComponent(store.currentTrack.artist)}`" class="track-artist track-link">{{ store.currentTrack.artist }}</RouterLink>
        </div>
      </template>
      <template v-else>
        <div class="no-track">Play something from your library</div>
      </template>
    </div>

    <!-- Center: Playback controls + progress bar -->
    <div v-if="store.currentTrack" class="center-controls">
      <PlaybackControls />
      <ProgressBar />
    </div>

    <!-- Right: Volume + queue toggle -->
    <div class="right-controls">
      <VolumeControl />
      <button
        class="queue-btn"
        :class="{ 'queue-btn-active': queueOpen }"
        title="Queue"
        @click="$emit('toggle-queue')"
      >
        <!-- Queue / list icon -->
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="8" y1="6" x2="21" y2="6"/>
          <line x1="8" y1="12" x2="21" y2="12"/>
          <line x1="8" y1="18" x2="21" y2="18"/>
          <line x1="3" y1="6" x2="3.01" y2="6"/>
          <line x1="3" y1="12" x2="3.01" y2="12"/>
          <line x1="3" y1="18" x2="3.01" y2="18"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import PlaybackControls from '@/components/player/PlaybackControls.vue'
import ProgressBar from '@/components/player/ProgressBar.vue'
import VolumeControl from '@/components/player/VolumeControl.vue'

defineProps<{
  queueOpen?: boolean
}>()

defineEmits<{
  'toggle-queue': []
}>()

const store = usePlayerStore()
const artError = ref(false)

// Reset art error when track changes
watch(
  () => store.currentTrack?.album_id,
  () => { artError.value = false },
)
</script>

<style scoped>
.player-bar {
  display: flex;
  align-items: center;
  height: 72px;
  padding: 0 16px;
  gap: 16px;
}

/* Left section */
.now-playing {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 33.33%;
  min-width: 0;
  flex-shrink: 0;
}

.art-thumb {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  overflow: hidden;
  background-color: #27272a;
  flex-shrink: 0;
  display: block;
  transition: opacity 0.15s;
  cursor: pointer;
}

.art-thumb:hover {
  opacity: 0.8;
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
  width: 22px;
  height: 22px;
  color: #52525b;
}

.track-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.track-link {
  text-decoration: none;
  transition: color 0.15s;
}

.track-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: #f4f4f5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.track-title.track-link:hover { color: #a78bfa; }

.track-artist {
  font-size: var(--text-sm);
  color: #71717a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.track-artist.track-link:hover { color: #a1a1aa; }

.no-track {
  font-size: var(--text-base);
  color: #52525b;
}

/* Center section */
.center-controls {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 0;
  padding: 0 8px;
}

/* Right section */
.right-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  width: 33.33%;
  flex-shrink: 0;
}

.queue-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #71717a;
  border-radius: 6px;
  cursor: pointer;
  padding: 0;
  transition: color 0.15s;
  flex-shrink: 0;
}

.queue-btn svg {
  width: 16px;
  height: 16px;
}

.queue-btn:hover {
  color: #f4f4f5;
}

.queue-btn-active {
  color: #a78bfa;
}
</style>
