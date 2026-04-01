<template>
  <div class="candidate-list">
    <!-- Header -->
    <div class="list-header">
      <div class="list-header-left">
        <h3 class="list-title">Choose a match</h3>
        <p class="album-path" :title="store.candidatesPayload?.album_path">
          {{ store.candidatesPayload?.album_path ? truncatePath(store.candidatesPayload.album_path) : '' }}
        </p>
      </div>
      <div v-if="store.candidatesPayload?.rec" class="rec-badge" :class="`rec-${store.candidatesPayload.rec}`">
        {{ recLabel }}
      </div>
    </div>

    <!-- No candidates -->
    <div v-if="store.candidates.length === 0" class="no-candidates">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="no-match-icon">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        <line x1="8" y1="11" x2="14" y2="11"/>
      </svg>
      <p>No MusicBrainz matches found for this album.</p>
      <div class="no-candidate-actions">
        <button class="action-btn btn-secondary" @click="doAsIs">Import As-Is</button>
        <button class="action-btn btn-ghost" @click="doSkip">Skip</button>
      </div>
    </div>

    <!-- Two-column layout -->
    <div v-else class="candidate-columns">
      <!-- Left: candidate cards -->
      <div class="cards-col">
        <div class="cards-scroll">
          <CandidateCard
            v-for="candidate in store.candidates"
            :key="candidate.index"
            :candidate="candidate"
            :is-selected="store.selectedCandidateIndex === candidate.index"
            :file-track-count="store.candidatesPayload?.file_tracks.length ?? 0"
            @select="store.selectCandidate(candidate.index)"
          />
        </div>
      </div>

      <!-- Right: track comparison -->
      <div class="comparison-col">
        <div v-if="selectedCandidate" class="comparison-wrapper">
          <TrackComparison
            :file-tracks="store.candidatesPayload?.file_tracks ?? []"
            :candidate-tracks="selectedCandidate.tracks"
          />
        </div>
        <div v-else class="comparison-placeholder">
          Select a candidate to see track comparison.
        </div>
      </div>
    </div>

    <!-- Action bar -->
    <div v-if="store.candidates.length > 0" class="action-bar">
      <button
        class="action-btn btn-primary"
        @click="doApply"
      >
        Apply Selected
      </button>
      <button class="action-btn btn-secondary" @click="doAsIs">Import As-Is</button>
      <div class="action-spacer" />
      <button
        v-if="(store.candidatesPayload?.file_tracks.length ?? 0) > 1"
        class="action-btn btn-ghost"
        @click="doSingleton"
      >
        As Tracks
      </button>
      <button class="action-btn btn-ghost" @click="doSkip">Skip</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useImportStore } from '@/stores/import'
import CandidateCard from './CandidateCard.vue'
import TrackComparison from './TrackComparison.vue'

const store = useImportStore()

const selectedCandidate = computed(() =>
  store.candidates.find((c) => c.index === store.selectedCandidateIndex) ?? null,
)

const recLabel = computed(() => {
  switch (store.candidatesPayload?.rec) {
    case 'strong': return 'Strong match'
    case 'medium': return 'Decent match'
    case 'low': return 'Weak match'
    case 'none': return 'No recommendation'
    default: return ''
  }
})

function truncatePath(path: string): string {
  if (path.length <= 70) return path
  const parts = path.split('/')
  if (parts.length > 3) {
    return '…/' + parts.slice(-2).join('/')
  }
  return path
}

function doApply() {
  store.submitChoice({ action: 'apply', candidate_index: store.selectedCandidateIndex })
}

function doAsIs() {
  store.submitChoice({ action: 'as_is' })
}

function doSkip() {
  store.submitChoice({ action: 'skip' })
}

function doSingleton() {
  store.submitChoice({ action: 'singleton' })
}
</script>

<style scoped>
.candidate-list {
  background-color: #18181b;
  border: 1px solid #27272a;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Header */
.list-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 20px 14px;
  border-bottom: 1px solid #27272a;
  gap: 12px;
}

.list-header-left {
  min-width: 0;
}

.list-title {
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
  max-width: 500px;
}

/* Recommendation badge */
.rec-badge {
  flex-shrink: 0;
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 3px 9px;
  border-radius: 99px;
}

.rec-strong {
  background-color: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.rec-medium {
  background-color: rgba(250, 204, 21, 0.15);
  color: #facc15;
}

.rec-low {
  background-color: rgba(251, 146, 60, 0.15);
  color: #fb923c;
}

.rec-none {
  background-color: rgba(248, 113, 113, 0.15);
  color: #f87171;
}

/* No candidates */
.no-candidates {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  gap: 12px;
}

.no-match-icon {
  width: 40px;
  height: 40px;
  color: #3f3f46;
}

.no-candidates p {
  font-size: var(--text-md);
  color: #71717a;
  margin: 0;
  text-align: center;
}

.no-candidate-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

/* Two-column layout */
.candidate-columns {
  display: grid;
  grid-template-columns: 40% 60%;
  flex: 1;
  min-height: 0;
  border-bottom: 1px solid #27272a;
}

.cards-col {
  border-right: 1px solid #27272a;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.cards-scroll {
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 440px;
}

.comparison-col {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.comparison-wrapper {
  overflow-y: auto;
  padding: 12px;
  max-height: 440px;
}

.comparison-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 120px;
  color: #3f3f46;
  font-size: var(--text-base);
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

.btn-primary {
  background-color: #7c3aed;
  color: #fff;
}

.btn-primary:hover {
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
