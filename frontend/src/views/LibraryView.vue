<template>
  <div class="library-view">
    <!-- Header bar -->
    <div class="library-header">
      <h1 class="library-title">Library</h1>
      <div class="library-count" v-if="!store.isLoading">
        {{ store.totalAlbums }} album{{ store.totalAlbums !== 1 ? 's' : '' }}
      </div>
      <div class="view-toggle">
        <button class="view-btn" :class="{ active: viewMode === 'grid' }" title="Grid view" @click="setViewMode('grid')">
          <svg viewBox="0 0 24 24" fill="currentColor" class="view-icon">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
        </button>
        <button class="view-btn" :class="{ active: viewMode === 'list' }" title="List view" @click="setViewMode('list')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="view-icon">
            <line x1="8" y1="6" x2="21" y2="6"/>
            <line x1="8" y1="12" x2="21" y2="12"/>
            <line x1="8" y1="18" x2="21" y2="18"/>
            <circle cx="3" cy="6" r="1" fill="currentColor"/>
            <circle cx="3" cy="12" r="1" fill="currentColor"/>
            <circle cx="3" cy="18" r="1" fill="currentColor"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Search + Sort + Filters -->
    <div class="library-controls">
      <div class="controls-row">
        <SearchBar
          :model-value="store.filters.query"
          @update:model-value="store.filters.query = $event"
          @search="onSearch"
        />
        <div class="sort-control">
          <label class="sort-label">Sort</label>
          <div class="sort-select-wrapper">
            <select class="sort-select" :value="store.filters.sort" @change="onSortSelectChange">
              <option value="albumartist+">Artist A–Z</option>
              <option value="albumartist-">Artist Z–A</option>
              <option value="album+">Album A–Z</option>
              <option value="album-">Album Z–A</option>
              <option value="year-">Year (newest)</option>
              <option value="year+">Year (oldest)</option>
              <option value="added-">Recently Added</option>
            </select>
            <svg class="sort-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>
        </div>
        <span v-if="activeFilterCount > 0" class="filter-count-badge">{{ activeFilterCount }} active</span>
      </div>
      <FilterPanel
        :filters="store.filters"
        :genres="facetGenres"
        :formats="facetFormats"
        @update:genre="store.setFilter('genre', $event)"
        @update:year-from="store.setFilter('yearFrom', $event)"
        @update:year-to="store.setFilter('yearTo', $event)"
        @update:format="store.setFilter('format', $event)"
        @update:sort="onSortChange"
        @clear-filters="onClearFilters"
      />
    </div>

    <!-- Artist filter chip + action strip -->
    <div v-if="activeArtistFilter" class="artist-filter-section">
      <div class="artist-chip-row">
        <div class="artist-chip">
          <span class="artist-chip-label">Artist: {{ activeArtistFilter }}</span>
          <button class="artist-chip-clear" @click="clearArtistFilter" title="Clear artist filter">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="chip-x-icon">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </div>
      <div class="artist-action-strip">
        <button class="artist-action-btn" @click="artistModalMode = 'relocate'">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="action-btn-icon">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
          Move Files
        </button>
        <button class="artist-action-btn artist-action-btn-danger" @click="artistModalMode = 'remove'">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="action-btn-icon">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
            <path d="M10 11v6M14 11v6M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
          </svg>
          Remove from Library
        </button>
      </div>
    </div>

    <!-- Album grid / list -->
    <div class="library-content" :style="{ opacity: store.isLoading ? 0.4 : 1, transition: 'opacity 0.15s' }">
      <!-- Top pagination (no page-size selector) -->
      <div class="pagination pagination-top" v-if="!store.isLoading && store.totalAlbums > 0">
        <div class="pagination-controls">
          <button
            class="page-btn"
            :disabled="store.page <= 1"
            @click="goToPage(store.page - 1)"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="page-icon">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            Prev
          </button>
          <span class="page-current">{{ store.page }} / {{ totalPages }}</span>
          <button
            class="page-btn"
            :disabled="store.page >= totalPages"
            @click="goToPage(store.page + 1)"
          >
            Next
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="page-icon">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </button>
        </div>
      </div>
      <Transition name="view-switch" mode="out-in">
        <AlbumGrid v-if="viewMode === 'grid'" key="grid" :albums="store.albums" :loading="store.isLoading" />
        <AlbumList v-else key="list" :albums="store.albums" :loading="store.isLoading" />
      </Transition>
    </div>

    <!-- Artist actions modal -->
    <ArtistActionsModal
      :open="artistModalOpen"
      :mode="artistModalMode ?? 'remove'"
      :artist-name="activeArtistFilter || null"
      @close="artistModalMode = null"
      @removed="onArtistRemoved"
      @done="onArtistActionDone"
    />

    <!-- Pagination -->
    <div class="pagination" v-if="!store.isLoading && store.totalAlbums > 0">
      <div class="pagination-left">
        <span class="pagination-info">
          Showing {{ pageStart }}–{{ pageEnd }} of {{ store.totalAlbums }}
        </span>
        <label class="page-size-label">
          Per page
          <select class="page-size-select" :value="store.pageSize" @change="onPageSizeChange">
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
            <option value="200">200</option>
          </select>
        </label>
      </div>
      <div class="pagination-controls">
        <button
          class="page-btn"
          :disabled="store.page <= 1"
          @click="goToPage(store.page - 1)"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="page-icon">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Prev
        </button>
        <span class="page-current">{{ store.page }} / {{ totalPages }}</span>
        <button
          class="page-btn"
          :disabled="store.page >= totalPages"
          @click="goToPage(store.page + 1)"
        >
          Next
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="page-icon">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import SearchBar from '@/components/search/SearchBar.vue'
import FilterPanel from '@/components/search/FilterPanel.vue'
import AlbumGrid from '@/components/albums/AlbumGrid.vue'
import AlbumList from '@/components/albums/AlbumList.vue'
import ArtistActionsModal from '@/components/library/ArtistActionsModal.vue'

const store = useLibraryStore()
const route = useRoute()
const router = useRouter()

const viewMode = ref<'grid' | 'list'>(
  (localStorage.getItem('library.viewMode') as 'grid' | 'list') ?? 'grid'
)

const facetGenres = computed(() => store.facets?.genres ?? [])
const facetFormats = computed(() => store.facets?.formats ?? [])

const activeFilterCount = computed(() => {
  const f = store.filters
  return [f.genre, f.yearFrom, f.yearTo, f.format].filter(Boolean).length
})

const totalPages = computed(() => Math.ceil(store.totalAlbums / store.pageSize))

const pageStart = computed(() => (store.page - 1) * store.pageSize + 1)
const pageEnd = computed(() => Math.min(store.page * store.pageSize, store.totalAlbums))

// The artist name currently being filtered from the URL param (not the raw query string)
const activeArtistFilter = ref<string>('')

// Artist actions modal (remove / relocate)
const artistModalMode = ref<'remove' | 'relocate' | null>(null)
const artistModalOpen = computed(() => artistModalMode.value !== null)

function applyArtistFromRoute() {
  const artistParam = route.query.artist
  if (artistParam && typeof artistParam === 'string') {
    activeArtistFilter.value = artistParam
    store.filters.query = `albumartist:"${artistParam}"`
    store.fetchAlbums()
  } else {
    activeArtistFilter.value = ''
  }
}

function clearArtistFilter() {
  activeArtistFilter.value = ''
  store.filters.query = ''
  router.replace({ path: '/library' })
  store.fetchAlbums()
}

function onArtistRemoved() {
  artistModalMode.value = null
  clearArtistFilter()
}

function onArtistActionDone() {
  artistModalMode.value = null
  store.fetchAlbums()
}

onMounted(async () => {
  const savedSize = localStorage.getItem('library.pageSize')
  if (savedSize) store.setPageSize(Number(savedSize))

  if (route.query.artist) {
    applyArtistFromRoute()
    await store.fetchFacets()
  } else {
    await Promise.all([store.fetchAlbums(), store.fetchFacets()])
  }
})

watch(() => route.query.artist, () => {
  applyArtistFromRoute()
})

function onSearch(query: string) {
  store.setFilter('query', query)
  store.fetchAlbums()
}

function onSortChange(sort: string) {
  store.setFilter('sort', sort)
  store.fetchAlbums()
}

function onSortSelectChange(e: Event) {
  onSortChange((e.target as HTMLSelectElement).value)
}

function onClearFilters() {
  store.resetFilters()
  store.fetchAlbums()
}

function setViewMode(mode: 'grid' | 'list') {
  viewMode.value = mode
  localStorage.setItem('library.viewMode', mode)
}

function onPageSizeChange(e: Event) {
  const n = Number((e.target as HTMLSelectElement).value)
  store.setPageSize(n)
  localStorage.setItem('library.pageSize', String(n))
  store.fetchAlbums()
}

function goToPage(n: number) {
  store.setPage(n)
  store.fetchAlbums()
  document.querySelector('.main-content')?.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<style scoped>
.library-view {
  padding: 28px 32px 40px;
  min-height: 100%;
  background-color: #18181b; /* zinc-900 */
  color: #f4f4f5;
}

.library-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.library-title {
  font-size: var(--text-3xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #f4f4f5;
  margin: 0;
}

.library-count {
  font-size: var(--text-base);
  color: #71717a;
  flex: 1;
}

.view-toggle {
  display: flex;
  gap: 2px;
  background: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 8px;
  padding: 3px;
}

.view-btn {
  background: none;
  border: none;
  border-radius: 5px;
  padding: 5px 7px;
  cursor: pointer;
  color: #71717a;
  display: flex;
  align-items: center;
  transition: background 0.15s, color 0.15s;
}

.view-btn:hover {
  color: #d4d4d8;
}

.view-btn.active {
  background: #3f3f46;
  color: #f4f4f5;
}

.view-icon {
  width: 16px;
  height: 16px;
}

/* Artist filter chip + action strip */
.artist-filter-section {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.artist-chip-row {
  display: flex;
  align-items: center;
}

.artist-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #2d1f5e;
  border: 1px solid #5b21b6;
  border-radius: 20px;
  padding: 4px 10px 4px 12px;
}

.artist-chip-label {
  font-size: var(--text-base);
  color: #c4b5fd;
}

.artist-chip-clear {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  cursor: pointer;
  color: #7c3aed;
  padding: 0;
  border-radius: 50%;
  transition: color 0.15s;
}

.artist-chip-clear:hover {
  color: #c4b5fd;
}

.chip-x-icon {
  width: 13px;
  height: 13px;
}

.artist-action-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 4px;
}

.artist-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 7px;
  padding: 6px 12px;
  font-size: var(--text-sm);
  font-weight: 500;
  color: #a1a1aa;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.artist-action-btn:hover {
  background: #3f3f46;
  color: #f4f4f5;
  border-color: #52525b;
}

.artist-action-btn-danger {
  color: #f87171;
  border-color: rgba(248, 113, 113, 0.3);
  background: rgba(239, 68, 68, 0.06);
}

.artist-action-btn-danger:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(248, 113, 113, 0.6);
  color: #fca5a5;
}

.action-btn-icon {
  width: 13px;
  height: 13px;
  flex-shrink: 0;
}

.library-controls {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 24px;
  background: #1f1f23;
  border: 1px solid #3f3f46;
  border-radius: 10px;
  padding: 12px 16px;
}

.filter-count-badge {
  background: #7c3aed;
  color: white;
  font-size: var(--text-xs);
  font-weight: 700;
  border-radius: 10px;
  padding: 2px 8px;
  white-space: nowrap;
  flex-shrink: 0;
}

.controls-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.sort-control {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.sort-label {
  font-size: var(--text-sm);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #52525b;
  white-space: nowrap;
}

.sort-select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.sort-select {
  background-color: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 7px;
  padding: 8px 32px 8px 12px;
  font-size: var(--text-base);
  color: #d4d4d8;
  outline: none;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  transition: border-color 0.15s;
}

.sort-select:focus {
  border-color: #7c3aed;
}

.sort-chevron {
  position: absolute;
  right: 10px;
  width: 12px;
  height: 12px;
  color: #71717a;
  pointer-events: none;
}

.library-content {
  width: 100%;
}

.view-switch-enter-active,
.view-switch-leave-active { transition: opacity 0.1s ease; }
.view-switch-enter-from,
.view-switch-leave-to { opacity: 0; }

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #27272a;
  gap: 16px;
  flex-wrap: wrap;
}

.pagination-top {
  margin-top: 0;
  margin-bottom: 16px;
  padding-top: 0;
  border-top: none;
  justify-content: flex-end;
}

.pagination-left {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.pagination-info {
  font-size: var(--text-base);
  color: #71717a;
}

.page-size-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-sm);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #52525b;
  cursor: pointer;
}

.page-size-select {
  background-color: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: var(--text-base);
  color: #d4d4d8;
  outline: none;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  transition: border-color 0.15s;
}

.page-size-select:focus {
  border-color: #7c3aed;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: #27272a;
  border: none;
  border-radius: 7px;
  padding: 8px 14px;
  font-size: var(--text-base);
  color: #a1a1aa;
  cursor: pointer;
  transition: background-color 0.15s, color 0.15s;
}

.page-btn:hover:not(:disabled) {
  background-color: #3f3f46;
  color: #f4f4f5;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-icon {
  width: 14px;
  height: 14px;
}

.page-current {
  font-size: var(--text-base);
  color: #a78bfa; /* violet-400 */
  font-weight: 600;
  min-width: 24px;
  text-align: center;
}
</style>
