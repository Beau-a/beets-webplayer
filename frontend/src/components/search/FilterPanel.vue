<template>
  <div class="filter-panel">
    <button class="filter-toggle" @click="open = !open">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="filter-icon">
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
      </svg>
      <span>Filters</span>
      <span v-if="activeCount > 0" class="active-badge">{{ activeCount }}</span>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="chevron-icon" :class="{ rotated: open }">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </button>

    <div v-if="open" class="filter-body">
      <div class="filter-grid">
        <!-- Genre -->
        <div class="filter-field">
          <label class="filter-label">Genre</label>
          <select class="filter-select" :value="filters.genre ?? ''" @change="onGenreChange">
            <option value="">All genres</option>
            <option v-for="g in genres" :key="g" :value="g">{{ g }}</option>
          </select>
        </div>

        <!-- Year from -->
        <div class="filter-field">
          <label class="filter-label">Year from</label>
          <input
            type="number"
            class="filter-input"
            placeholder="e.g. 1990"
            :value="filters.yearFrom ?? ''"
            @input="onYearFromInput"
            min="1900"
            max="2100"
          />
        </div>

        <!-- Year to -->
        <div class="filter-field">
          <label class="filter-label">Year to</label>
          <input
            type="number"
            class="filter-input"
            placeholder="e.g. 2010"
            :value="filters.yearTo ?? ''"
            @input="onYearToInput"
            min="1900"
            max="2100"
          />
        </div>

        <!-- Format -->
        <div class="filter-field">
          <label class="filter-label">Format</label>
          <select class="filter-select" :value="filters.format ?? ''" @change="onFormatChange">
            <option value="">All formats</option>
            <option v-for="f in formats" :key="f" :value="f">{{ f }}</option>
          </select>
        </div>

        <!-- Sort -->
        <div class="filter-field">
          <label class="filter-label">Sort by</label>
          <select class="filter-select" :value="filters.sort" @change="onSortChange">
            <option value="albumartist+">Artist A–Z</option>
            <option value="albumartist-">Artist Z–A</option>
            <option value="album+">Album A–Z</option>
            <option value="album-">Album Z–A</option>
            <option value="year-">Year (newest)</option>
            <option value="year+">Year (oldest)</option>
            <option value="added-">Recently Added</option>
          </select>
        </div>
      </div>

      <button v-if="activeCount > 0" class="clear-filters-btn" @click="$emit('clearFilters')">
        Clear filters
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface FilterState {
  genre: string | null
  yearFrom: number | null
  yearTo: number | null
  format: string | null
  sort: string
}

const props = defineProps<{
  filters: FilterState
  genres: string[]
  formats: string[]
}>()

const emit = defineEmits<{
  'update:genre': [value: string | null]
  'update:yearFrom': [value: number | null]
  'update:yearTo': [value: number | null]
  'update:format': [value: string | null]
  'update:sort': [value: string]
  clearFilters: []
}>()

const open = ref(false)

const activeCount = computed(() => {
  let count = 0
  if (props.filters.genre) count++
  if (props.filters.yearFrom != null) count++
  if (props.filters.yearTo != null) count++
  if (props.filters.format) count++
  return count
})

function onGenreChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  emit('update:genre', val || null)
}

function onFormatChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  emit('update:format', val || null)
}

function onSortChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  emit('update:sort', val)
}

function onYearFromInput(e: Event) {
  const val = (e.target as HTMLInputElement).value
  emit('update:yearFrom', val ? parseInt(val, 10) : null)
}

function onYearToInput(e: Event) {
  const val = (e.target as HTMLInputElement).value
  emit('update:yearTo', val ? parseInt(val, 10) : null)
}
</script>

<style scoped>
.filter-panel {
  width: 100%;
}

.filter-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: 1px solid #3f3f46; /* zinc-700 */
  border-radius: 8px;
  padding: 8px 14px;
  cursor: pointer;
  color: #a1a1aa; /* zinc-400 */
  font-size: var(--text-base);
  font-weight: 500;
  transition: background-color 0.15s, color 0.15s;
}

.filter-toggle:hover {
  background-color: #27272a;
  color: #d4d4d8;
}

.filter-icon {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.active-badge {
  background-color: #7c3aed; /* violet-700 */
  color: white;
  font-size: var(--text-xs);
  font-weight: 700;
  border-radius: 10px;
  padding: 1px 6px;
  line-height: 1.5;
}

.chevron-icon {
  width: 14px;
  height: 14px;
  margin-left: auto;
  transition: transform 0.2s;
}

.chevron-icon.rotated {
  transform: rotate(180deg);
}

.filter-body {
  margin-top: 12px;
  padding: 16px;
  background-color: #1c1c1f; /* between zinc-900 and zinc-800 */
  border-radius: 10px;
  border: 1px solid #27272a;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 14px;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-label {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #52525b; /* zinc-600 */
}

.filter-select,
.filter-input {
  background-color: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  padding: 7px 10px;
  font-size: var(--text-base);
  color: #d4d4d8;
  outline: none;
  transition: border-color 0.15s;
  appearance: none;
  -webkit-appearance: none;
  cursor: pointer;
}

.filter-select:focus,
.filter-input:focus {
  border-color: #7c3aed;
}

.filter-input[type='number']::-webkit-inner-spin-button,
.filter-input[type='number']::-webkit-outer-spin-button {
  opacity: 0.5;
}

.clear-filters-btn {
  margin-top: 14px;
  background: transparent;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: var(--text-sm);
  color: #a1a1aa;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.clear-filters-btn:hover {
  border-color: #7c3aed;
  color: #c084fc;
}
</style>
