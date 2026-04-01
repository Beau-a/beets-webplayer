<template>
  <div class="progress-wrapper">
    <span class="time-label">{{ store.formattedCurrentTime }}</span>

    <div
      ref="barRef"
      class="bar-track"
      @mousedown="onMouseDown"
      @click="onBarClick"
    >
      <div class="bar-fill" :style="{ width: store.progress + '%' }"></div>
      <!-- Draggable thumb -->
      <div class="bar-thumb" :style="{ left: store.progress + '%' }"></div>
    </div>

    <span class="time-label time-label-right">{{ store.formattedDuration }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { usePlayerStore } from '@/stores/player'

const store = usePlayerStore()
const barRef = ref<HTMLDivElement | null>(null)
let isDragging = false

function getSeekSeconds(clientX: number): number {
  if (!barRef.value || !store.duration) return 0
  const rect = barRef.value.getBoundingClientRect()
  const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
  return ratio * store.duration
}

function onBarClick(e: MouseEvent) {
  if (isDragging) return
  store.seek(getSeekSeconds(e.clientX))
}

function onMouseDown(_e: MouseEvent) {
  isDragging = false
  let moved = false

  const onMove = (me: MouseEvent) => {
    moved = true
    isDragging = true
    store.seek(getSeekSeconds(me.clientX))
  }

  const onUp = (me: MouseEvent) => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
    if (moved) {
      store.seek(getSeekSeconds(me.clientX))
    }
    // Reset isDragging after a tick so the click handler doesn't fire
    requestAnimationFrame(() => { isDragging = false })
  }

  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}
</script>

<style scoped>
.progress-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.time-label {
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
  color: #71717a; /* zinc-500 */
  white-space: nowrap;
  min-width: 34px;
  text-align: right;
  flex-shrink: 0;
}

.time-label-right {
  text-align: left;
}

.bar-track {
  flex: 1;
  height: 4px;
  background-color: #3f3f46; /* zinc-700 */
  border-radius: 2px;
  cursor: pointer;
  position: relative;
  /* Expand hit area above/below without changing visual size */
  padding: 8px 0;
  margin: -8px 0;
}

.bar-fill {
  position: absolute;
  top: 8px;
  left: 0;
  height: 4px;
  background-color: #8b5cf6; /* violet-500 */
  border-radius: 2px;
  pointer-events: none;
  transition: width 0.1s linear;
}

.bar-thumb {
  position: absolute;
  top: 8px;
  width: 12px;
  height: 12px;
  background-color: #f4f4f5;
  border-radius: 50%;
  transform: translate(-50%, -4px);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
}

.bar-track:hover .bar-thumb {
  opacity: 1;
}

.bar-track:hover .bar-fill {
  background-color: #a78bfa; /* violet-400 on hover */
}
</style>
