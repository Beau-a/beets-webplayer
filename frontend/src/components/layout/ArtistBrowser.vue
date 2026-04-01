<template>
  <Transition name="flyout">
    <div
      v-if="visible"
      class="artist-browser"
      :style="{ left: sidebarCollapsed ? '56px' : '200px' }"
    >
      <!-- Header row -->
      <div class="ab-header">
        <span class="ab-title">Artists</span>
        <button class="ab-close" @click="$emit('close')" title="Close artist browser">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="ab-close-icon">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <!-- Letter picker -->
      <div class="ab-letters">
        <button
          v-for="l in LETTERS"
          :key="l"
          class="ab-letter-btn"
          :class="{
            'ab-letter-active': activeLetter === l,
            'ab-letter-dim': !activeLetters.includes(l),
          }"
          @click="selectLetter(l)"
        >
          {{ l }}
        </button>
      </div>

      <!-- Artist list -->
      <div class="ab-list" ref="listEl">
        <div v-if="loading" class="ab-loading">Loading…</div>
        <div v-else-if="artists.length === 0 && activeLetter" class="ab-empty">No artists</div>
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
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchArtists, fetchArtistLetters, type ArtistEntry } from '@/api/library'

const props = defineProps<{
  visible: boolean
  sidebarCollapsed: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const router = useRouter()

const LETTERS = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','#']

const activeLetter = ref('')
const activeLetters = ref<string[]>([])
const artists = ref<ArtistEntry[]>([])
const loading = ref(false)
const listEl = ref<HTMLElement | null>(null)

async function loadLetters() {
  try {
    activeLetters.value = await fetchArtistLetters()
  } catch {
    activeLetters.value = []
  }
}

async function selectLetter(letter: string) {
  if (activeLetter.value === letter) return
  activeLetter.value = letter
  loading.value = true
  artists.value = []
  try {
    artists.value = await fetchArtists(letter)
  } finally {
    loading.value = false
  }
  if (listEl.value) listEl.value.scrollTop = 0
}

function onSelectArtist(name: string) {
  emit('close')
  router.push(`/artist/${encodeURIComponent(name)}`)
}

onMounted(() => {
  loadLetters()
})

// When flyout becomes visible, reload letters in case library changed
watch(() => props.visible, (val) => {
  if (val) loadLetters()
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

/* Slide transition */
.flyout-enter-active,
.flyout-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.flyout-enter-from,
.flyout-leave-to {
  transform: translateX(-16px);
  opacity: 0;
}

/* Header */
.ab-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 12px 10px;
  border-bottom: 1px solid #27272a;
  flex-shrink: 0;
}

.ab-title {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #52525b;
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

/* Letter grid */
.ab-letters {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  padding: 10px 8px;
  border-bottom: 1px solid #27272a;
  flex-shrink: 0;
}

.ab-letter-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  border-radius: 5px;
  border: none;
  background: none;
  color: #71717a;
  cursor: pointer;
  transition: background-color 0.12s, color 0.12s;
}

.ab-letter-btn:hover:not(.ab-letter-dim) {
  background-color: #27272a;
  color: #d4d4d8;
}

.ab-letter-active {
  background-color: #5b21b6 !important;
  color: #ede9fe !important;
}

.ab-letter-dim {
  opacity: 0.3;
  cursor: default;
  pointer-events: none;
}

/* Artist list */
.ab-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.ab-list::-webkit-scrollbar {
  width: 4px;
}

.ab-list::-webkit-scrollbar-track {
  background: transparent;
}

.ab-list::-webkit-scrollbar-thumb {
  background: #3f3f46;
  border-radius: 2px;
}

.ab-loading,
.ab-empty {
  font-size: 12px;
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
  font-size: 13px;
  color: #d4d4d8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.ab-album-count {
  font-size: 11px;
  color: #52525b;
  background: #27272a;
  border-radius: 4px;
  padding: 1px 5px;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}
</style>
