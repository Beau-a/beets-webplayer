<template>
  <div class="track-comparison">
    <div class="comparison-header">
      <div class="col-header">Your Files</div>
      <div class="col-header">MusicBrainz Match</div>
    </div>

    <div class="comparison-body">
      <template v-for="(row, i) in rows" :key="i">
        <div
          class="track-row"
          :class="{
            'row-mismatch': row.mismatch,
            'row-extra': row.extra,
            'row-missing': row.missing,
          }"
        >
          <!-- File side -->
          <div class="track-cell file-cell">
            <template v-if="row.file">
              <span class="track-num">{{ row.file.track || '—' }}</span>
              <div class="track-details">
                <span class="track-title" :class="{ 'title-mismatch': row.mismatch }">
                  {{ row.file.title || row.file.filename || '(untitled)' }}
                </span>
                <span class="track-sub">
                  {{ row.file.artist }}
                  <span v-if="row.file.length" class="track-dur">{{ formatDuration(row.file.length) }}</span>
                </span>
              </div>
            </template>
            <div v-else class="track-absent">—</div>
          </div>

          <!-- MB side -->
          <div class="track-cell mb-cell">
            <template v-if="row.candidate">
              <span class="track-num">{{ row.candidate.track || '—' }}</span>
              <div class="track-details">
                <span class="track-title" :class="{ 'title-mismatch': row.mismatch }">
                  {{ row.candidate.title || '(untitled)' }}
                </span>
                <span class="track-sub">
                  {{ row.candidate.artist }}
                  <span v-if="row.candidate.length" class="track-dur">{{ formatDuration(row.candidate.length) }}</span>
                </span>
              </div>
            </template>
            <div v-else class="track-absent track-absent-missing">Missing in files</div>
          </div>
        </div>
      </template>

      <div v-if="rows.length === 0" class="no-tracks">
        No track data available.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FileTrack, CandidateTrack } from '@/types/import'

const props = defineProps<{
  fileTracks: FileTrack[]
  candidateTracks: CandidateTrack[]
}>()

interface ComparisonRow {
  file: FileTrack | null
  candidate: CandidateTrack | null
  mismatch: boolean   // both present but titles differ
  extra: boolean      // file has no MB match
  missing: boolean    // MB has no file match
}

const rows = computed((): ComparisonRow[] => {
  const result: ComparisonRow[] = []
  const maxLen = Math.max(props.fileTracks.length, props.candidateTracks.length)

  for (let i = 0; i < maxLen; i++) {
    const file = props.fileTracks[i] ?? null
    const candidate = props.candidateTracks[i] ?? null

    const extra = file !== null && candidate === null
    const missing = file === null && candidate !== null

    let mismatch = false
    if (file && candidate) {
      const ft = (file.title ?? '').toLowerCase().trim()
      const ct = (candidate.title ?? '').toLowerCase().trim()
      mismatch = ft !== ct && ft !== '' && ct !== ''
    }

    result.push({ file, candidate, mismatch, extra, missing })
  }

  return result
})

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.track-comparison {
  font-size: 12px;
  font-family: ui-monospace, Consolas, monospace;
}

.comparison-header {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background-color: #27272a;
  border-radius: 8px 8px 0 0;
  overflow: hidden;
}

.col-header {
  background-color: #27272a;
  padding: 8px 12px;
  font-size: 11px;
  font-weight: 600;
  color: #71717a;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.comparison-body {
  border: 1px solid #27272a;
  border-top: none;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
  max-height: 400px;
  overflow-y: auto;
}

.track-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  border-bottom: 1px solid #1f1f23;
}

.track-row:last-child {
  border-bottom: none;
}

.track-row.row-mismatch {
  background-color: rgba(251, 146, 60, 0.04);
}

.track-row.row-extra .file-cell {
  background-color: rgba(251, 146, 60, 0.06);
}

.track-row.row-missing .mb-cell {
  background-color: rgba(239, 68, 68, 0.06);
}

.track-cell {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 7px 12px;
  border-right: 1px solid #1f1f23;
  min-width: 0;
}

.mb-cell {
  border-right: none;
}

.track-num {
  flex-shrink: 0;
  width: 20px;
  color: #52525b;
  text-align: right;
  padding-top: 1px;
}

.track-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.track-title {
  color: #d4d4d8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-title.title-mismatch {
  color: #fb923c;
}

.track-sub {
  color: #71717a;
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.track-dur {
  color: #52525b;
}

.track-absent {
  color: #3f3f46;
  font-style: italic;
  padding: 4px 0;
  flex: 1;
}

.track-absent-missing {
  color: #7f1d1d;
}

.no-tracks {
  padding: 20px;
  color: #52525b;
  text-align: center;
}
</style>
