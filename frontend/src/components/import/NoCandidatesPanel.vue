<template>
  <div class="no-candidates-panel">
    <!-- Header -->
    <div class="panel-header">
      <div class="header-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          <line x1="8" y1="11" x2="14" y2="11"/>
        </svg>
      </div>
      <div class="header-text">
        <h3 class="panel-title">No MusicBrainz matches found</h3>
        <p class="album-path" :title="store.noCandidatesPayload?.album_path">
          {{ truncatePath(store.noCandidatesPayload?.album_path ?? '') }}
        </p>
      </div>
    </div>

    <!-- File track list -->
    <div v-if="store.noCandidatesPayload?.file_tracks.length" class="file-tracks">
      <div class="file-tracks-label">Files in this folder</div>
      <div class="file-track-list">
        <div
          v-for="(t, i) in store.noCandidatesPayload.file_tracks"
          :key="i"
          class="file-track"
        >
          <span class="file-track-num">{{ t.track || i + 1 }}</span>
          <span class="file-track-title">{{ t.title || t.filename }}</span>
          <span class="file-track-length">{{ formatLength(t.length) }}</span>
        </div>
      </div>
    </div>

    <!-- MB Search section -->
    <div class="mb-search-section">
      <p class="mb-search-hint">
        Find this album on MusicBrainz. Paste a release URL or search for artist / album.
      </p>
      <div class="mb-search-input-row">
        <input
          v-model="mbQuery"
          class="mb-search-input"
          placeholder="e.g. musicbrainz.org/release/… or Pink Floyd - The Wall"
          @keydown.enter="doMBSearch"
        />
        <button
          class="search-btn"
          :disabled="mbSearching || !mbQuery.trim()"
          @click="doMBSearch"
        >
          <span v-if="mbSearching" class="btn-spinner" />
          <span v-else>Search</span>
        </button>
      </div>

      <div v-if="mbSearchError" class="mb-search-error">{{ mbSearchError }}</div>

      <!-- Search results -->
      <div v-if="mbResults.length > 0" class="mb-results">
        <div
          v-for="result in mbResults"
          :key="result.mb_albumid"
          class="mb-result-card"
          :class="{ 'is-selected': selectedMBResult?.mb_albumid === result.mb_albumid }"
          @click="selectedMBResult = result"
        >
          <div class="mb-result-main">
            <span class="mb-result-album">{{ result.album }}</span>
            <span class="mb-result-artist">{{ result.artist }}</span>
          </div>
          <div class="mb-result-meta">
            <span v-if="result.year">{{ result.year }}</span>
            <span v-if="result.country"> · {{ result.country }}</span>
            <span v-if="result.label"> · {{ result.label }}</span>
            <span> · {{ result.track_count }} tracks</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Action bar -->
    <div class="action-bar">
      <button
        class="action-btn btn-primary"
        :disabled="!selectedMBResult"
        @click="doApplyMB"
      >
        Apply Selected Release
      </button>
      <button class="action-btn btn-secondary" @click="doAsIs">Import As-Is</button>
      <div class="action-spacer" />
      <button class="action-btn btn-ghost" @click="doSkip">Skip</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useImportStore } from '@/stores/import'
import { searchMusicBrainz } from '@/api/library'
import type { MBSearchResult } from '@/types/import'

const store = useImportStore()

const mbQuery = ref('')
const mbSearching = ref(false)
const mbSearchError = ref('')
const mbResults = ref<MBSearchResult[]>([])
const selectedMBResult = ref<MBSearchResult | null>(null)

async function doMBSearch() {
  if (!mbQuery.value.trim()) return
  mbSearching.value = true
  mbSearchError.value = ''
  mbResults.value = []
  selectedMBResult.value = null
  try {
    mbResults.value = await searchMusicBrainz(mbQuery.value.trim())
    if (mbResults.value.length === 0) {
      mbSearchError.value = 'No results found. Try a different search or URL.'
    }
  } catch {
    mbSearchError.value = 'Search failed. Check the server connection.'
  } finally {
    mbSearching.value = false
  }
}

function doApplyMB() {
  if (!selectedMBResult.value) return
  store.submitChoice({ action: 'apply', mb_id: selectedMBResult.value.mb_albumid })
}

function doAsIs() {
  store.submitChoice({ action: 'as_is' })
}

function doSkip() {
  store.submitChoice({ action: 'skip' })
}

function truncatePath(path: string): string {
  if (!path) return ''
  if (path.length <= 70) return path
  const parts = path.split('/')
  if (parts.length > 3) return '…/' + parts.slice(-2).join('/')
  return path
}

function formatLength(seconds: number): string {
  if (!seconds) return ''
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}
</script>

<style scoped>
.no-candidates-panel {
  background-color: #18181b;
  border: 1px solid #27272a;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Header */
.panel-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid #27272a;
}

.header-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  color: #52525b;
  margin-top: 2px;
}

.header-icon svg {
  width: 100%;
  height: 100%;
}

.header-text {
  min-width: 0;
}

.panel-title {
  font-size: 15px;
  font-weight: 700;
  color: #f4f4f5;
  margin: 0 0 3px;
}

.album-path {
  font-size: var(--text-sm);
  color: #52525b;
  font-family: ui-monospace, Consolas, monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
  max-width: 600px;
}

/* File track list */
.file-tracks {
  padding: 14px 20px;
  border-bottom: 1px solid #27272a;
  max-height: 200px;
  overflow-y: auto;
}

.file-tracks-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #52525b;
  margin-bottom: 8px;
}

.file-track-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.file-track {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: var(--text-sm);
}

.file-track-num {
  flex-shrink: 0;
  width: 20px;
  text-align: right;
  color: #52525b;
  font-family: ui-monospace, Consolas, monospace;
}

.file-track-title {
  flex: 1;
  color: #a1a1aa;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-track-length {
  flex-shrink: 0;
  color: #52525b;
  font-family: ui-monospace, Consolas, monospace;
  font-size: var(--text-xs);
}

/* MB Search section */
.mb-search-section {
  padding: 18px 20px;
  border-bottom: 1px solid #27272a;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mb-search-hint {
  font-size: var(--text-sm);
  color: #71717a;
  margin: 0;
}

.mb-search-input-row {
  display: flex;
  gap: 8px;
}

.mb-search-input {
  flex: 1;
  background-color: #09090b;
  border: 1px solid #3f3f46;
  border-radius: 7px;
  padding: 9px 12px;
  font-size: var(--text-base);
  color: #f4f4f5;
  outline: none;
  transition: border-color 0.15s;
}

.mb-search-input:focus {
  border-color: #7c3aed;
}

.mb-search-input::placeholder {
  color: #52525b;
}

.search-btn {
  flex-shrink: 0;
  padding: 9px 18px;
  background-color: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 7px;
  color: #d4d4d8;
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.15s;
}

.search-btn:hover:not(:disabled) {
  background-color: #3f3f46;
}

.search-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.btn-spinner {
  display: inline-block;
  width: 13px;
  height: 13px;
  border: 2px solid #52525b;
  border-top-color: #a78bfa;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.mb-search-error {
  font-size: var(--text-sm);
  color: #f87171;
}

/* Search results */
.mb-results {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mb-result-card {
  padding: 10px 14px;
  background-color: #09090b;
  border: 1px solid #27272a;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.15s, background-color 0.15s;
}

.mb-result-card:hover {
  border-color: #3f3f46;
  background-color: #111113;
}

.mb-result-card.is-selected {
  border-color: #7c3aed;
  background-color: rgba(124, 58, 237, 0.08);
}

.mb-result-main {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 3px;
}

.mb-result-album {
  font-size: var(--text-base);
  font-weight: 600;
  color: #f4f4f5;
}

.mb-result-artist {
  font-size: var(--text-sm);
  color: #a1a1aa;
}

.mb-result-meta {
  font-size: var(--text-xs);
  color: #52525b;
}

/* Action bar */
.action-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background-color: #09090b;
}

.action-spacer {
  flex: 1;
}

.action-btn {
  padding: 8px 16px;
  border-radius: 7px;
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: background-color 0.15s, color 0.15s;
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.btn-primary {
  background-color: #7c3aed;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background-color: #6d28d9;
}

.btn-secondary {
  background-color: #27272a;
  color: #d4d4d8;
}

.btn-secondary:hover {
  background-color: #3f3f46;
}

.btn-ghost {
  background-color: transparent;
  color: #71717a;
  border: 1px solid #27272a;
}

.btn-ghost:hover {
  background-color: #27272a;
  color: #a1a1aa;
}
</style>
