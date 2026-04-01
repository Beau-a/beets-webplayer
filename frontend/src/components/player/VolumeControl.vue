<template>
  <div class="volume-control">
    <!-- Mute toggle button with volume icon -->
    <button class="vol-icon-btn" :title="store.isMuted ? 'Unmute' : 'Mute'" @click="store.toggleMute()">
      <!-- Muted -->
      <svg v-if="store.isMuted || store.volume === 0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
        <line x1="23" y1="9" x2="17" y2="15"/>
        <line x1="17" y1="9" x2="23" y2="15"/>
      </svg>
      <!-- Low volume -->
      <svg v-else-if="store.volume < 0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
        <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
      </svg>
      <!-- High volume -->
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
        <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
      </svg>
    </button>

    <!-- Volume slider -->
    <input
      type="range"
      class="vol-slider"
      min="0"
      max="1"
      step="0.02"
      :value="store.isMuted ? 0 : store.volume"
      @input="onInput"
    />
  </div>
</template>

<script setup lang="ts">
import { usePlayerStore } from '@/stores/player'

const store = usePlayerStore()

function onInput(e: Event) {
  const v = parseFloat((e.target as HTMLInputElement).value)
  store.setVolume(v)
  if (store.isMuted && v > 0) {
    store.toggleMute()
  }
}
</script>

<style scoped>
.volume-control {
  display: flex;
  align-items: center;
  gap: 6px;
}

.vol-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #a1a1aa;
  border-radius: 6px;
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
  transition: color 0.15s;
}

.vol-icon-btn svg {
  width: 16px;
  height: 16px;
}

.vol-icon-btn:hover {
  color: #f4f4f5;
}

.vol-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 80px;
  height: 4px;
  border-radius: 2px;
  background: #3f3f46;
  outline: none;
  cursor: pointer;
}

.vol-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #f4f4f5;
  cursor: pointer;
  transition: background-color 0.15s;
}

.vol-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #f4f4f5;
  cursor: pointer;
  border: none;
}

.vol-slider:hover::-webkit-slider-thumb {
  background: #a78bfa;
}

.vol-slider:hover::-moz-range-thumb {
  background: #a78bfa;
}
</style>
