<template>
  <div class="tracklist">
    <template v-if="disctotal > 1">
      <template v-for="discNum in discNumbers" :key="discNum">
        <div class="disc-header">Disc {{ discNum }}</div>
        <table class="track-table">
          <thead>
            <tr>
              <th class="col-num"></th>
              <th class="col-title">Title</th>
              <th v-if="showArtist" class="col-artist">Artist</th>
              <th class="col-length">Length</th>
              <th v-if="hasMixedFormats" class="col-format">Format</th>
              <th v-if="hasMixedFormats" class="col-bitrate">Bitrate</th>
              <th class="col-actions"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="track in tracksByDisc[discNum]"
              :key="track.id"
              class="track-row"
              :class="{ 'track-row-playing': isCurrentlyPlaying(track.id) }"
              @click="playFromTrack(track)"
            >
              <td class="col-num">
                <div class="num-cell">
                  <span class="track-num-text" :class="{ 'track-num-text-playing': isCurrentlyPlaying(track.id) }">{{ track.track || '—' }}</span>
                  <button
                    class="track-num-play play-btn"
                    :class="{ 'play-btn-active': isCurrentlyPlaying(track.id) }"
                    :title="isCurrentlyPlaying(track.id) ? 'Now playing' : 'Play'"
                    @click.stop="playFromTrack(track)"
                  >
                    <svg v-if="isCurrentlyPlaying(track.id) && playerStore.isPlaying" viewBox="0 0 24 24" fill="currentColor">
                      <rect x="6" y="4" width="4" height="16" rx="1"/>
                      <rect x="14" y="4" width="4" height="16" rx="1"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="currentColor">
                      <polygon points="5,3 19,12 5,21"/>
                    </svg>
                  </button>
                </div>
              </td>
              <td class="col-title track-title">{{ track.title }}</td>
              <td v-if="showArtist" class="col-artist track-artist">{{ track.artist }}</td>
              <td class="col-length track-length">{{ formatDuration(track.length) }}</td>
              <td v-if="hasMixedFormats" class="col-format">
                <span class="format-pill" :class="formatClass(track.format)">
                  {{ formatLabel(track.format) }}
                </span>
              </td>
              <td v-if="hasMixedFormats" class="col-bitrate track-bitrate">{{ formatBitrate(track.bitrate) }}</td>
              <td class="col-actions">
                <div class="row-actions">
                  <button class="row-action-btn" title="Add to queue" @click.stop="addToQueue(track)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                  </button>
                  <template v-if="showActions">
                    <button class="row-action-btn row-action-edit" title="Edit track" @click.stop="emit('edit-track', track)">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                      </svg>
                    </button>
                    <button class="row-action-btn row-action-delete" title="Remove from library" @click.stop="emit('delete-track', track)">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                        <path d="M10 11v6M14 11v6M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                      </svg>
                    </button>
                  </template>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </template>
    </template>

    <template v-else>
      <table class="track-table">
        <thead>
          <tr>
            <th class="col-num"></th>
            <th class="col-title">Title</th>
            <th v-if="showArtist" class="col-artist">Artist</th>
            <th class="col-length">Length</th>
            <th v-if="hasMixedFormats" class="col-format">Format</th>
            <th v-if="hasMixedFormats" class="col-bitrate">Bitrate</th>
            <th class="col-actions"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="track in tracks"
            :key="track.id"
            class="track-row"
            :class="{ 'track-row-playing': isCurrentlyPlaying(track.id) }"
            @click="playFromTrack(track)"
          >
            <td class="col-num">
              <div class="num-cell">
                <span class="track-num-text" :class="{ 'track-num-text-playing': isCurrentlyPlaying(track.id) }">{{ track.track || '—' }}</span>
                <button
                  class="track-num-play play-btn"
                  :class="{ 'play-btn-active': isCurrentlyPlaying(track.id) }"
                  :title="isCurrentlyPlaying(track.id) ? 'Now playing' : 'Play'"
                  @click.stop="playFromTrack(track)"
                >
                  <svg v-if="isCurrentlyPlaying(track.id) && playerStore.isPlaying" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="4" width="4" height="16" rx="1"/>
                    <rect x="14" y="4" width="4" height="16" rx="1"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="5,3 19,12 5,21"/>
                  </svg>
                </button>
              </div>
            </td>
            <td class="col-title track-title">{{ track.title }}</td>
            <td v-if="showArtist" class="col-artist track-artist">{{ track.artist }}</td>
            <td class="col-length track-length">{{ formatDuration(track.length) }}</td>
            <td v-if="hasMixedFormats" class="col-format">
              <span class="format-pill" :class="formatClass(track.format)">
                {{ formatLabel(track.format) }}
              </span>
            </td>
            <td v-if="hasMixedFormats" class="col-bitrate track-bitrate">{{ formatBitrate(track.bitrate) }}</td>
            <td class="col-actions">
              <div class="row-actions">
                <button class="row-action-btn" title="Add to queue" @click.stop="addToQueue(track)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                  </svg>
                </button>
                <template v-if="showActions">
                  <button class="row-action-btn row-action-edit" title="Edit track" @click.stop="emit('edit-track', track)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button class="row-action-btn row-action-delete" title="Remove from library" @click.stop="emit('delete-track', track)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                      <path d="M10 11v6M14 11v6M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                    </svg>
                  </button>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TrackInAlbum } from '@/types/album'
import type { QueueTrack } from '@/types/player'
import { usePlayerStore } from '@/stores/player'

const props = defineProps<{
  tracks: TrackInAlbum[]
  disctotal: number
  albumartist?: string
  albumId: number
  albumName?: string
  showActions?: boolean
}>()

const emit = defineEmits<{
  'edit-track': [track: TrackInAlbum]
  'delete-track': [track: TrackInAlbum]
}>()

const playerStore = usePlayerStore()

// Show artist column if any track has a different artist than the albumartist
const showArtist = computed(() => {
  if (!props.albumartist) return false
  return props.tracks.some((t) => t.artist && t.artist !== props.albumartist)
})

const hasMixedFormats = computed(() => {
  return new Set(props.tracks.map((t) => t.format)).size > 1
})

const discNumbers = computed(() => {
  const nums = [...new Set(props.tracks.map((t) => t.disc || 1))].sort((a, b) => a - b)
  return nums
})

const tracksByDisc = computed(() => {
  const map: Record<number, TrackInAlbum[]> = {}
  for (const track of props.tracks) {
    const disc = track.disc || 1
    if (!map[disc]) map[disc] = []
    map[disc].push(track)
  }
  // Sort each disc's tracks by track number
  for (const disc in map) {
    map[disc].sort((a, b) => (a.track || 0) - (b.track || 0))
  }
  return map
})

// Sorted flat list matching the visual order (for playAlbum start index)
const sortedTracks = computed<TrackInAlbum[]>(() => {
  return [...props.tracks].sort((a, b) => {
    const discDiff = (a.disc || 1) - (b.disc || 1)
    if (discDiff !== 0) return discDiff
    return (a.track || 0) - (b.track || 0)
  })
})

function toQueueTrack(track: TrackInAlbum): QueueTrack {
  return {
    id: track.id,
    title: track.title,
    artist: track.artist || props.albumartist || 'Unknown Artist',
    album: props.albumName || 'Unknown Album',
    album_id: props.albumId,
    length: track.length,
    format: track.format,
    bitrate: track.bitrate,
  }
}

function addToQueue(track: TrackInAlbum) {
  playerStore.addToQueue(toQueueTrack(track))
}

function playFromTrack(track: TrackInAlbum) {
  // If already playing this track, toggle pause
  if (isCurrentlyPlaying(track.id)) {
    playerStore.setIsPlaying(!playerStore.isPlaying)
    return
  }
  const queueTracks = sortedTracks.value.map(toQueueTrack)
  const startIndex = sortedTracks.value.findIndex((t) => t.id === track.id)
  playerStore.playAlbum(queueTracks, Math.max(0, startIndex))
}

function isCurrentlyPlaying(trackId: number): boolean {
  return playerStore.currentTrack?.id === trackId
}

function formatDuration(seconds: number): string {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

function formatBitrate(bitrate: number): string {
  if (!bitrate) return '—'
  return `${Math.round(bitrate / 1000)} kbps`
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
  if (f.includes('FLAC')) return 'pill-flac'
  if (f.includes('MP3')) return 'pill-mp3'
  if (f.includes('OGG') || f.includes('OPUS')) return 'pill-ogg'
  return 'pill-other'
}
</script>

<style scoped>
.tracklist {
  width: 100%;
}

.disc-header {
  font-size: var(--text-base);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #a78bfa;
  padding: 20px 12px 6px;
  border-bottom: 2px solid rgba(124, 58, 237, 0.3);
  margin-bottom: 4px;
}

.disc-header:first-child {
  padding-top: 0;
}

.track-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-base);
}

.track-table thead tr {
  border-bottom: 1px solid #27272a;
}

.track-table th {
  text-align: left;
  padding: 8px 12px;
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #52525b; /* zinc-600 */
}

.track-row {
  border-radius: 6px;
  transition: background-color 0.1s;
  cursor: pointer;
}

.track-row:hover {
  background-color: #27272a; /* zinc-800 */
}

.track-row-playing {
  background-color: rgba(139, 92, 246, 0.08);
}

.track-row-playing:hover {
  background-color: rgba(139, 92, 246, 0.14);
}

.track-table td {
  padding: 9px 12px;
  color: #d4d4d8; /* zinc-300 */
}

/* Collapsed num+play column */
.col-num {
  width: 44px;
  padding: 0 4px 0 8px !important;
  text-align: center;
}

.num-cell {
  position: relative;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.track-num-text {
  display: block;
  color: #71717a;
  font-size: var(--text-sm);
  line-height: 1;
  user-select: none;
}

.track-num-text-playing {
  color: #a78bfa;
}

.track-num-play {
  display: none;
  position: absolute;
  inset: 0;
  align-items: center;
  justify-content: center;
}

.track-row:hover .track-num-text {
  display: none;
}

.track-row:hover .track-num-play {
  display: flex;
}

.play-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: none;
  background: transparent;
  color: #a1a1aa;
  border-radius: 50%;
  cursor: pointer;
  padding: 0;
  transition: color 0.15s, background-color 0.15s;
}

.play-btn svg {
  width: 12px;
  height: 12px;
}

.play-btn:hover {
  color: #f4f4f5;
  background-color: #3f3f46;
}

/* Always show for active track */
.play-btn-active {
  color: #a78bfa !important;
}

.col-title {
  min-width: 180px;
}

.track-title {
  font-weight: 500;
  color: #f4f4f5;
}

.track-row-playing .track-title {
  color: #c4b5fd;
}

.col-artist {
  min-width: 140px;
}

.track-artist {
  color: #a1a1aa; /* zinc-400 */
}

.col-length {
  width: 70px;
  text-align: right;
}

.track-length {
  font-variant-numeric: tabular-nums;
  color: #71717a;
  text-align: right;
}

.col-format {
  width: 80px;
}

.col-bitrate {
  width: 90px;
  text-align: right;
}

.track-bitrate {
  color: #71717a;
  font-size: var(--text-sm);
  text-align: right;
}

.format-pill {
  font-size: var(--text-2xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 2px 6px;
  border-radius: 4px;
  line-height: 1.6;
}

.pill-flac {
  background-color: rgba(74, 222, 128, 0.15);
  color: #86efac;
}

.pill-mp3 {
  background-color: rgba(96, 165, 250, 0.15);
  color: #93c5fd;
}

.pill-ogg {
  background-color: rgba(251, 191, 36, 0.15);
  color: #fcd34d;
}

.pill-other {
  background-color: rgba(161, 161, 170, 0.15);
  color: #a1a1aa;
}

/* Row action buttons */
.col-actions {
  width: 1px;
  padding: 0 8px 0 4px !important;
  white-space: nowrap;
}

.row-actions {
  display: flex;
  gap: 2px;
  align-items: center;
  opacity: 0;
  transition: opacity 0.12s;
}

.track-row:hover .row-actions {
  opacity: 1;
}

.row-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #52525b;
  border-radius: 4px;
  cursor: pointer;
  padding: 0;
  transition: color 0.12s, background-color 0.12s;
}

.row-action-btn svg {
  width: 13px;
  height: 13px;
}

.row-action-btn:hover {
  background-color: #3f3f46;
  color: #a1a1aa;
}

.row-action-edit:hover { color: #a78bfa; }
.row-action-delete:hover { color: #f87171; }
</style>
