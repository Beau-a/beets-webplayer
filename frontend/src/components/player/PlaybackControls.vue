<template>
  <div class="controls">
    <!-- Shuffle -->
    <button
      class="ctrl-btn"
      :class="{ 'ctrl-active': store.shuffleEnabled }"
      title="Shuffle"
      aria-label="Shuffle"
      @click="store.toggleShuffle()"
    >
      <!-- Shuffle icon -->
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="16 3 21 3 21 8"/>
        <line x1="4" y1="20" x2="21" y2="3"/>
        <polyline points="21 16 21 21 16 21"/>
        <line x1="15" y1="15" x2="21" y2="21"/>
      </svg>
    </button>

    <!-- Previous -->
    <button
      class="ctrl-btn ctrl-skip"
      :disabled="!store.hasPrevious"
      title="Previous"
      aria-label="Previous"
      @click="store.previous()"
    >
      <!-- Skip-back icon -->
      <svg viewBox="0 0 24 24" fill="currentColor">
        <polygon points="19,20 9,12 19,4"/>
        <rect x="5" y="4" width="3" height="16" rx="1"/>
      </svg>
    </button>

    <!-- Play / Pause -->
    <button
      class="ctrl-btn ctrl-play"
      :disabled="!store.currentTrack"
      :title="store.isPlaying ? 'Pause' : 'Play'"
      :aria-label="store.isPlaying ? 'Pause' : 'Play'"
      @click="togglePlay"
    >
      <!-- Buffering spinner -->
      <svg v-if="store.isBuffering" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="ctrl-spinner">
        <circle cx="12" cy="12" r="10" stroke-dasharray="40 22"/>
      </svg>
      <!-- Pause icon -->
      <svg v-else-if="store.isPlaying" viewBox="0 0 24 24" fill="currentColor">
        <rect x="6" y="4" width="4" height="16" rx="1"/>
        <rect x="14" y="4" width="4" height="16" rx="1"/>
      </svg>
      <!-- Play icon -->
      <svg v-else viewBox="0 0 24 24" fill="currentColor">
        <polygon points="5,3 19,12 5,21"/>
      </svg>
    </button>

    <!-- Next -->
    <button
      class="ctrl-btn ctrl-skip"
      :disabled="!store.hasNext"
      title="Next"
      aria-label="Next"
      @click="store.next()"
    >
      <!-- Skip-forward icon -->
      <svg viewBox="0 0 24 24" fill="currentColor">
        <polygon points="5,4 15,12 5,20"/>
        <rect x="16" y="4" width="3" height="16" rx="1"/>
      </svg>
    </button>

    <!-- Repeat -->
    <button
      class="ctrl-btn"
      :class="repeatClass"
      :title="repeatTitle"
      :aria-label="repeatTitle"
      @click="store.cycleRepeat()"
    >
      <!-- Repeat-one icon -->
      <svg v-if="store.repeatMode === 'one'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="17 1 21 5 17 9"/>
        <path d="M3 11V9a4 4 0 0 1 4-4h14"/>
        <polyline points="7 23 3 19 7 15"/>
        <path d="M21 13v2a4 4 0 0 1-4 4H3"/>
        <line x1="12" y1="11" x2="12" y2="17"/>
        <line x1="9.5" y1="13.5" x2="12" y2="11"/>
      </svg>
      <!-- Repeat-all icon -->
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="17 1 21 5 17 9"/>
        <path d="M3 11V9a4 4 0 0 1 4-4h14"/>
        <polyline points="7 23 3 19 7 15"/>
        <path d="M21 13v2a4 4 0 0 1-4 4H3"/>
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { usePlayerStore } from '@/stores/player'

const store = usePlayerStore()

function togglePlay() {
  if (!store.currentTrack) return
  store.setIsPlaying(!store.isPlaying)
}

const repeatClass = computed(() => {
  if (store.repeatMode === 'off') return ''
  return 'ctrl-active'
})

const repeatTitle = computed(() => {
  if (store.repeatMode === 'off') return 'Repeat: off'
  if (store.repeatMode === 'all') return 'Repeat: all'
  return 'Repeat: one'
})
</script>

<style scoped>
.controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.ctrl-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: #a1a1aa; /* zinc-400 */
  border-radius: 50%;
  cursor: pointer;
  transition: color 0.15s, background-color 0.15s;
  padding: 0;
  flex-shrink: 0;
}

.ctrl-btn svg {
  width: 16px;
  height: 16px;
}

.ctrl-btn:hover:not(:disabled) {
  color: #f4f4f5;
  background-color: #27272a;
}

.ctrl-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.ctrl-active {
  color: #a78bfa; /* violet-400 */
}

.ctrl-active:hover:not(:disabled) {
  color: #c4b5fd;
}

/* Slightly larger skip buttons */
.ctrl-skip svg {
  width: 18px;
  height: 18px;
}

/* Play/pause button — larger, filled circle */
.ctrl-play {
  width: 42px;
  height: 42px;
  background-color: #f4f4f5;
  color: #09090b;
  border-radius: 50%;
}

.ctrl-play svg {
  width: 18px;
  height: 18px;
}

.ctrl-play:hover:not(:disabled) {
  background-color: #ffffff;
  color: #09090b;
}

.ctrl-play:disabled {
  background-color: #3f3f46;
  color: #71717a;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.ctrl-spinner {
  animation: spin 0.8s linear infinite;
}
</style>
