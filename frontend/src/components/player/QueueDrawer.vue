<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="modelValue" class="drawer-overlay" @click.self="$emit('update:modelValue', false)">
        <div class="drawer-panel" role="dialog" aria-label="Play Queue">
          <!-- Header -->
          <div class="drawer-header">
            <h2 class="drawer-title">Queue</h2>
            <div class="drawer-header-actions">
              <button
                v-if="store.queue.length > 0"
                class="clear-btn"
                @click="store.clearQueue()"
              >
                Clear all
              </button>
              <button class="close-btn" title="Close" @click="$emit('update:modelValue', false)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Queue list -->
          <div class="drawer-body">
            <template v-if="store.queue.length > 0">
              <div
                v-for="(track, index) in store.queue"
                :key="`${track.id}-${index}`"
                class="queue-item"
                :class="{ 'queue-item-active': index === store.queueIndex }"
                @click="store.jumpToIndex(index)"
              >
                <span class="queue-index">{{ index + 1 }}</span>
                <div class="queue-track-info">
                  <span class="queue-track-title">{{ track.title }}</span>
                  <span class="queue-track-artist">{{ track.artist }}</span>
                </div>
                <span class="queue-track-duration">{{ formatTime(track.length) }}</span>
                <button
                  class="queue-remove-btn"
                  title="Remove from queue"
                  @click.stop="store.removeFromQueue(index)"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </template>
            <div v-else class="queue-empty">
              <p>The queue is empty.</p>
              <p class="queue-empty-hint">Play an album or track to get started.</p>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { usePlayerStore } from '@/stores/player'

defineProps<{
  modelValue: boolean
}>()

defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const store = usePlayerStore()

function formatTime(seconds: number): string {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}
</script>

<style scoped>
.drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background-color: rgba(0, 0, 0, 0.5);
}

.drawer-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 360px;
  max-width: 100vw;
  background-color: #18181b; /* zinc-900 */
  border-left: 1px solid #27272a;
  display: flex;
  flex-direction: column;
  z-index: 201;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #27272a;
  flex-shrink: 0;
}

.drawer-title {
  font-size: 15px;
  font-weight: 700;
  color: #f4f4f5;
  margin: 0;
}

.drawer-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.clear-btn {
  font-size: 12px;
  color: #71717a;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: color 0.15s;
}

.clear-btn:hover {
  color: #ef4444;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: #71717a;
  border-radius: 6px;
  cursor: pointer;
  padding: 0;
  transition: color 0.15s;
}

.close-btn svg {
  width: 16px;
  height: 16px;
}

.close-btn:hover {
  color: #f4f4f5;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.1s;
  border-radius: 0;
}

.queue-item:hover {
  background-color: #27272a;
}

.queue-item-active {
  background-color: rgba(139, 92, 246, 0.1);
  border-left: 2px solid #8b5cf6;
  padding-left: 14px;
}

.queue-index {
  font-size: 11px;
  color: #52525b;
  min-width: 20px;
  text-align: right;
  flex-shrink: 0;
}

.queue-item-active .queue-index {
  color: #a78bfa;
}

.queue-track-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.queue-track-title {
  font-size: 13px;
  font-weight: 500;
  color: #f4f4f5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-item-active .queue-track-title {
  color: #a78bfa;
}

.queue-track-artist {
  font-size: 11px;
  color: #71717a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-track-duration {
  font-size: 12px;
  color: #71717a;
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.queue-remove-btn {
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

.queue-remove-btn svg {
  width: 13px;
  height: 13px;
}

.queue-item:hover .queue-remove-btn {
  color: #71717a;
}

.queue-remove-btn:hover {
  color: #ef4444 !important;
}

.queue-empty {
  padding: 48px 24px;
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

/* Transition */
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.2s ease;
}

.drawer-enter-active .drawer-panel,
.drawer-leave-active .drawer-panel {
  transition: transform 0.25s ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.drawer-enter-from .drawer-panel,
.drawer-leave-to .drawer-panel {
  transform: translateX(100%);
}
</style>
