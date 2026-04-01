<template>
  <div class="search-view">
    <div class="search-header">
      <h1 class="search-title">Search</h1>
    </div>

    <div class="search-bar-wrapper">
      <SearchBar
        v-model="queryValue"
        @search="onSearch"
        placeholder="Search your library... (try artist:radiohead year:2000..2010)"
      />
    </div>

    <!-- Initial / no query state -->
    <div v-if="!hasSearched" class="hint-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="hint-icon">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <p class="hint-text">Search across albums and tracks</p>
      <p class="hint-subtext">Supports beets query syntax: <code>artist:radiohead</code>, <code>year:2000..2010</code>, <code>genre:jazz</code></p>
    </div>

    <!-- Loading -->
    <div v-else-if="store.isLoading" class="loading-section">
      <div class="skeleton-results">
        <div v-for="n in 6" :key="n" class="skeleton-result-row"></div>
      </div>
    </div>

    <!-- Results -->
    <template v-else>
      <!-- Albums -->
      <section class="result-section" v-if="store.searchResults.albums.length > 0">
        <h2 class="result-section-title">
          Albums
          <span class="result-count">{{ store.searchResults.albums.length }}</span>
        </h2>
        <AlbumGrid :albums="store.searchResults.albums" :loading="false" />
      </section>

      <!-- Tracks -->
      <section class="result-section" v-if="store.searchResults.items.length > 0">
        <h2 class="result-section-title">
          Tracks
          <span class="result-count">{{ store.searchResults.items.length }}</span>
        </h2>
        <table class="tracks-table">
          <thead>
            <tr>
              <th class="col-title">Title</th>
              <th class="col-artist">Artist</th>
              <th class="col-album">Album</th>
              <th class="col-year">Year</th>
              <th class="col-length">Length</th>
              <th class="col-format">Format</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in store.searchResults.items"
              :key="item.id"
              class="track-row"
              @click="goToAlbum(item.album_id)"
            >
              <td class="col-title track-title">{{ item.title }}</td>
              <td class="col-artist">{{ item.artist }}</td>
              <td class="col-album">{{ item.album }}</td>
              <td class="col-year">{{ item.year || '—' }}</td>
              <td class="col-length track-length">{{ formatDuration(item.length) }}</td>
              <td class="col-format">
                <span class="format-badge" :class="formatClass(item.format)">
                  {{ formatLabel(item.format) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- No results -->
      <div
        v-if="store.searchResults.albums.length === 0 && store.searchResults.items.length === 0"
        class="no-results"
      >
        <p class="no-results-text">No results for <strong>"{{ lastQuery }}"</strong></p>
        <p class="no-results-sub">Try different keywords or query syntax</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import SearchBar from '@/components/search/SearchBar.vue'
import AlbumGrid from '@/components/albums/AlbumGrid.vue'

const route = useRoute()
const router = useRouter()
const store = useLibraryStore()

const queryValue = ref('')
const hasSearched = ref(false)
const lastQuery = ref('')

onMounted(() => {
  const q = route.query.q as string | undefined
  if (q) {
    queryValue.value = q
    doSearch(q)
  }
})

function onSearch(query: string) {
  lastQuery.value = query
  router.replace({ query: query ? { q: query } : {} })
  if (query.trim()) {
    doSearch(query)
  }
}

async function doSearch(query: string) {
  hasSearched.value = true
  await store.searchLibrary(query)
}

function goToAlbum(albumId: number) {
  router.push(`/library/${albumId}`)
}

function formatDuration(seconds: number): string {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

function formatLabel(format: string): string {
  const f = (format ?? '').toUpperCase()
  if (f.includes('FLAC')) return 'FLAC'
  if (f.includes('MP3')) return 'MP3'
  if (f.includes('OGG')) return 'OGG'
  if (f.includes('AAC') || f.includes('M4A')) return 'AAC'
  if (f.includes('OPUS')) return 'Opus'
  return f.slice(0, 6) || '—'
}

function formatClass(format: string): string {
  const f = (format ?? '').toUpperCase()
  if (f.includes('FLAC')) return 'badge-flac'
  if (f.includes('MP3')) return 'badge-mp3'
  if (f.includes('OGG') || f.includes('OPUS')) return 'badge-ogg'
  return 'badge-other'
}
</script>

<style scoped>
.search-view {
  padding: 28px 32px 60px;
  min-height: 100%;
  background-color: #18181b;
  color: #f4f4f5;
}

.search-header {
  margin-bottom: 20px;
}

.search-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: #f4f4f5;
  margin: 0;
}

.search-bar-wrapper {
  margin-bottom: 28px;
}

/* Hint state */
.hint-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 24px;
  gap: 12px;
  text-align: center;
}

.hint-icon {
  width: 48px;
  height: 48px;
  color: #3f3f46;
}

.hint-text {
  font-size: 15px;
  color: #71717a;
  margin: 0;
}

.hint-subtext {
  font-size: var(--text-base);
  color: #52525b;
  margin: 0;
}

.hint-subtext code {
  background-color: #27272a;
  border-radius: 4px;
  padding: 2px 6px;
  font-family: ui-monospace, Consolas, monospace;
  font-size: var(--text-sm);
  color: #a78bfa;
}

/* Result sections */
.result-section {
  margin-bottom: 40px;
}

.result-section-title {
  font-size: var(--text-md);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #71717a;
  margin: 0 0 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.result-count {
  background-color: #27272a;
  color: #a1a1aa;
  font-size: var(--text-xs);
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
}

/* Tracks table */
.tracks-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-base);
}

.tracks-table thead tr {
  border-bottom: 1px solid #27272a;
}

.tracks-table th {
  text-align: left;
  padding: 8px 12px;
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #52525b;
}

.track-row {
  cursor: pointer;
  border-radius: 6px;
  transition: background-color 0.1s;
}

.track-row:hover {
  background-color: #27272a;
}

.tracks-table td {
  padding: 9px 12px;
  color: #d4d4d8;
}

.track-title {
  font-weight: 500;
  color: #f4f4f5;
}

.track-length {
  font-variant-numeric: tabular-nums;
  color: #71717a;
}

.col-title { min-width: 180px; }
.col-artist { min-width: 140px; }
.col-album { min-width: 140px; }
.col-year { width: 60px; }
.col-length { width: 70px; text-align: right; }
.col-format { width: 80px; }

.format-badge {
  font-size: var(--text-2xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 2px 6px;
  border-radius: 4px;
  line-height: 1.5;
}

.badge-flac { background-color: rgba(74, 222, 128, 0.15); color: #4ade80; }
.badge-mp3  { background-color: rgba(96, 165, 250, 0.15);  color: #60a5fa; }
.badge-ogg  { background-color: rgba(251, 191, 36, 0.15);  color: #fbbf24; }
.badge-other { background-color: rgba(161, 161, 170, 0.15); color: #a1a1aa; }

/* No results */
.no-results {
  text-align: center;
  padding: 60px 24px;
}

.no-results-text {
  font-size: 15px;
  color: #71717a;
  margin: 0 0 8px;
}

.no-results-sub {
  font-size: var(--text-base);
  color: #52525b;
  margin: 0;
}

/* Loading skeleton */
.loading-section {
  padding: 12px 0;
}

.skeleton-results {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-result-row {
  height: 44px;
  border-radius: 6px;
  background: linear-gradient(90deg, #27272a 25%, #3f3f46 50%, #27272a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
