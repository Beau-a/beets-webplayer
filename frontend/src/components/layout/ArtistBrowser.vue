<template>
  <Transition name="flyout">
    <div
      v-if="visible"
      class="artist-browser"
      :style="{ left: sidebarCollapsed ? '56px' : '200px' }"
    >
      <!-- Header -->
      <div class="ab-header">
        <span class="ab-title">{{ activeLetter || 'Artists' }}</span>
        <button class="ab-close" @click="$emit('close')" title="Close" aria-label="Close artist browser">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="ab-close-icon">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <!-- Artist list -->
      <div class="ab-list" ref="listEl">
        <div v-if="loading" class="ab-loading">Loading…</div>
        <div v-else-if="artists.length === 0" class="ab-empty">No artists</div>
        <button
          v-for="artist in artists"
          :key="artist.name"
          class="ab-row"
          @click="onSelectArtist(artist.name)"
        >
          <span class="ab-artist-name">{{ artist.name }}</span>
          <span class="ab-album-count">{{ artist.album_count }}</span>
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { fetchArtists, type ArtistEntry } from '@/api/library'

const props = defineProps<{
  visible: boolean
  sidebarCollapsed: boolean
  activeLetter: string
}>()

const emit = defineEmits<{
  close: []
}>()

const router = useRouter()
const artists = ref<ArtistEntry[]>([])
const loading = ref(false)
const listEl = ref<HTMLElement | null>(null)

async function loadArtists(letter: string) {
  if (!letter) { artists.value = []; return }
  loading.value = true
  artists.value = []
  try {
    artists.value = await fetchArtists(letter)
  } finally {
    loading.value = false
    if (listEl.value) listEl.value.scrollTop = 0
  }
}

function onSelectArtist(name: string) {
  emit('close')
  router.push(`/artist/${encodeURIComponent(name)}`)
}

// Fetch when letter changes while visible
watch(() => props.activeLetter, (letter) => {
  if (props.visible) loadArtists(letter)
})

// Fetch when panel becomes visible
watch(() => props.visible, (val) => {
  if (val && props.activeLetter) loadArtists(props.activeLetter)
})
</script>

<style scoped>
.artist-browser {
  position: fixed;
  top: 0;
  bottom: 0;
  width: 220px;
  background: #0f0f11;
  border-right: 1px solid #27272a;
  z-index: 90;
  display: flex;
  flex-direction: column;
  transition: left 0.2s ease;
  overflow: hidden;
}

.flyout-enter-active,
.flyout-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.flyout-enter-from,
.flyout-leave-to {
  transform: translateX(-16px);
  opacity: 0;
}

.ab-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 12px 10px;
  border-bottom: 1px solid #27272a;
  flex-shrink: 0;
}

.ab-title {
  font-size: var(--text-sm);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #a78bfa;
}

.ab-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #52525b;
  padding: 2px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  transition: color 0.15s, background-color 0.15s;
}

.ab-close:hover {
  color: #a1a1aa;
  background-color: #27272a;
}

.ab-close-icon {
  width: 14px;
  height: 14px;
}

.ab-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.ab-list::-webkit-scrollbar { width: 4px; }
.ab-list::-webkit-scrollbar-track { background: transparent; }
.ab-list::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 2px; }

.ab-loading,
.ab-empty {
  font-size: var(--text-sm);
  color: #52525b;
  padding: 16px 12px;
  text-align: center;
}

.ab-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 7px 12px;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  gap: 8px;
  transition: background-color 0.12s;
}

.ab-row:hover {
  background-color: #27272a;
}

.ab-artist-name {
  font-size: var(--text-base);
  color: #d4d4d8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.ab-album-count {
  font-size: var(--text-xs);
  color: #52525b;
  background: #27272a;
  border-radius: 4px;
  padding: 1px 5px;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}
</style>
