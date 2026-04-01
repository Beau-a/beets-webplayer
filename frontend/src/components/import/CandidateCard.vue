<template>
  <div
    class="candidate-card"
    :class="{ 'is-selected': isSelected }"
    @click="$emit('select')"
    role="button"
    :aria-pressed="isSelected"
    tabindex="0"
    @keydown.enter="$emit('select')"
    @keydown.space.prevent="$emit('select')"
  >
    <!-- Match quality badge -->
    <div class="quality-row">
      <span class="quality-dot" :class="qualityClass" />
      <span class="quality-label" :class="qualityClass">{{ qualityLabel }}</span>
      <span class="distance-score">{{ (candidate.distance * 100).toFixed(0) }}% distance</span>
    </div>

    <!-- Artist / Album / Year -->
    <div class="candidate-title">{{ candidate.album }}</div>
    <div class="candidate-artist">{{ candidate.artist }}</div>

    <div class="candidate-meta">
      <span v-if="candidate.year" class="meta-chip">{{ candidate.year }}</span>
      <span v-if="candidate.label" class="meta-chip">{{ candidate.label }}</span>
      <span v-if="candidate.country" class="meta-chip">{{ candidate.country }}</span>
    </div>

    <!-- Track count + warnings -->
    <div class="track-info">
      <span class="track-count">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="track-icon">
          <line x1="8" y1="6" x2="21" y2="6"/>
          <line x1="8" y1="12" x2="21" y2="12"/>
          <line x1="8" y1="18" x2="21" y2="18"/>
          <line x1="3" y1="6" x2="3.01" y2="6"/>
          <line x1="3" y1="12" x2="3.01" y2="12"/>
          <line x1="3" y1="18" x2="3.01" y2="18"/>
        </svg>
        {{ candidate.track_count }} tracks
        <template v-if="fileTrackCount > 0 && fileTrackCount !== candidate.track_count">
          <span class="file-vs-mb">({{ fileTrackCount }} files)</span>
        </template>
      </span>
      <span
        v-if="candidate.missing_tracks > 0"
        class="warn-chip warn-missing"
        :title="`${candidate.missing_tracks} track(s) in MusicBrainz not found in your files`"
      >
        −{{ candidate.missing_tracks }} missing
      </span>
      <span
        v-if="candidate.extra_items > 0"
        class="warn-chip warn-extra"
        :title="`${candidate.extra_items} file(s) not matched to any MusicBrainz track`"
      >
        +{{ candidate.extra_items }} extra
      </span>
    </div>

    <!-- MusicBrainz link -->
    <a
      v-if="candidate.mb_albumid"
      :href="`https://musicbrainz.org/release/${candidate.mb_albumid}`"
      target="_blank"
      rel="noopener noreferrer"
      class="mb-link"
      @click.stop
    >
      MusicBrainz ↗
    </a>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ImportCandidate } from '@/types/import'

const props = defineProps<{
  candidate: ImportCandidate
  isSelected: boolean
  fileTrackCount: number
}>()

defineEmits<{
  select: []
}>()

const qualityClass = computed(() => {
  const d = props.candidate.distance
  if (d < 0.1) return 'quality-excellent'
  if (d < 0.3) return 'quality-good'
  if (d < 0.5) return 'quality-possible'
  return 'quality-poor'
})

const qualityLabel = computed(() => {
  const d = props.candidate.distance
  if (d < 0.1) return 'Excellent match'
  if (d < 0.3) return 'Good match'
  if (d < 0.5) return 'Possible match'
  return 'Poor match'
})
</script>

<style scoped>
.candidate-card {
  background-color: #18181b;
  border: 1.5px solid #27272a;
  border-radius: 10px;
  padding: 14px 16px;
  cursor: pointer;
  transition: border-color 0.15s, background-color 0.15s;
  user-select: none;
}

.candidate-card:hover {
  border-color: #3f3f46;
  background-color: #1f1f23;
}

.candidate-card.is-selected {
  border-color: #7c3aed;
  background-color: rgba(124, 58, 237, 0.08);
}

.candidate-card:focus-visible {
  outline: 2px solid #7c3aed;
  outline-offset: 2px;
}

/* Quality */
.quality-row {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 10px;
}

.quality-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.quality-excellent .quality-dot,
.quality-excellent { color: #4ade80; }
.quality-excellent.quality-dot { background-color: #4ade80; }

.quality-good .quality-dot,
.quality-good { color: #facc15; }
.quality-good.quality-dot { background-color: #facc15; }

.quality-possible .quality-dot,
.quality-possible { color: #fb923c; }
.quality-possible.quality-dot { background-color: #fb923c; }

.quality-poor .quality-dot,
.quality-poor { color: #f87171; }
.quality-poor.quality-dot { background-color: #f87171; }

.quality-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.distance-score {
  font-size: var(--text-xs);
  color: #52525b;
  margin-left: auto;
}

/* Title / artist */
.candidate-title {
  font-size: var(--text-md);
  font-weight: 600;
  color: #f4f4f5;
  margin-bottom: 2px;
  line-height: 1.3;
}

.candidate-artist {
  font-size: var(--text-base);
  color: #a1a1aa;
  margin-bottom: 10px;
}

/* Meta chips */
.candidate-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 10px;
}

.meta-chip {
  font-size: var(--text-xs);
  background-color: #27272a;
  color: #71717a;
  border-radius: 4px;
  padding: 2px 7px;
}

/* Track info */
.track-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.track-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-sm);
  color: #71717a;
}

.file-vs-mb {
  color: #52525b;
  font-size: var(--text-xs);
}

.track-icon {
  width: 12px;
  height: 12px;
}

.warn-chip {
  font-size: var(--text-xs);
  font-weight: 500;
  border-radius: 4px;
  padding: 2px 7px;
}

.warn-missing {
  background-color: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.warn-extra {
  background-color: rgba(251, 146, 60, 0.15);
  color: #fb923c;
}

/* MB link */
.mb-link {
  font-size: var(--text-xs);
  color: #7c3aed;
  text-decoration: none;
  display: inline-block;
}

.mb-link:hover {
  color: #8b5cf6;
  text-decoration: underline;
}
</style>
