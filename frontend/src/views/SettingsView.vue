<template>
  <div class="settings-view">
    <h1 class="page-title">Tools</h1>

    <!-- Library Stats -->
    <section class="section">
      <h2 class="section-title">Library Overview</h2>
      <div v-if="statsLoading" class="stats-grid">
        <div v-for="i in 4" :key="i" class="stat-card skeleton-card"></div>
      </div>
      <div v-else-if="stats" class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_albums.toLocaleString() }}</div>
          <div class="stat-label">Albums</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_items.toLocaleString() }}</div>
          <div class="stat-label">Tracks</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.artists_count.toLocaleString() }}</div>
          <div class="stat-label">Artists</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ formattedDuration }}</div>
          <div class="stat-label">Total Duration</div>
        </div>
      </div>

      <div v-if="stats && Object.keys(stats.format_breakdown).length" class="format-table">
        <h3 class="sub-title">Format Breakdown</h3>
        <table class="formats">
          <tbody>
            <tr v-for="(count, fmt) in stats.format_breakdown" :key="fmt">
              <td class="fmt-name">{{ fmt }}</td>
              <td class="fmt-count">{{ count.toLocaleString() }}</td>
              <td class="fmt-bar-cell">
                <div class="fmt-bar" :style="{ width: barWidth(count) + '%' }"></div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Management Tasks -->
    <section class="section">
      <h2 class="section-title">Management Tasks</h2>
      <p class="section-desc">
        Run beets maintenance operations against the full library. Each task runs in the background —
        check the output below for progress.
      </p>

      <div class="tasks-grid">
        <div v-for="task in taskDefs" :key="task.id" class="task-card">
          <div class="task-header">
            <div class="task-icon-wrap">
              <component :is="task.icon" class="task-icon" />
            </div>
            <div class="task-meta">
              <div class="task-name">{{ task.name }}</div>
              <div class="task-desc">{{ task.desc }}</div>
            </div>
          </div>

          <div class="task-footer">
            <span class="status-badge" :class="statusClass(task.id)">
              {{ statusLabel(task.id) }}
            </span>
            <button
              class="run-btn"
              :disabled="isRunning(task.id)"
              @click="runTask(task.id)"
            >
              {{ isRunning(task.id) ? 'Running…' : 'Run' }}
            </button>
          </div>

          <div v-if="taskOutput(task.id)" class="task-output-wrap">
            <pre class="task-output">{{ taskOutput(task.id) }}</pre>
          </div>
        </div>
      </div>
    </section>

    <!-- Import Music -->
    <section class="section">
      <h2 class="section-title">Import Music</h2>
      <p class="section-desc">
        Point beets at a directory to scan for new music. Matched albums will be identified
        against MusicBrainz and you'll be able to review each match before it's imported.
      </p>
      <div class="import-embed">
        <ImportView />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import { fetchLibraryStats, runLibraryTask, getLibraryTask, type LibraryStats } from '@/api/library'
import ImportView from './ImportView.vue'

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

const stats = ref<LibraryStats | null>(null)
const statsLoading = ref(true)

const formattedDuration = computed(() => {
  const secs = stats.value?.total_duration ?? 0
  const days = Math.floor(secs / 86400)
  const hrs = Math.floor((secs % 86400) / 3600)
  const mins = Math.floor((secs % 3600) / 60)
  if (days > 0) return `${days}d ${hrs}h`
  if (hrs > 0) return `${hrs}h ${mins}m`
  return `${mins}m`
})

const maxFormatCount = computed(() => {
  if (!stats.value) return 1
  return Math.max(...Object.values(stats.value.format_breakdown))
})

function barWidth(count: number): number {
  return Math.round((count / maxFormatCount.value) * 100)
}

// ---------------------------------------------------------------------------
// Task definitions (using inline SVGs via render functions)
// ---------------------------------------------------------------------------

const SyncIcon = {
  render() {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('polyline', { points: '1 4 1 10 7 10' }),
      h('polyline', { points: '23 20 23 14 17 14' }),
      h('path', { d: 'M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15' }),
    ])
  },
}

const ArtIcon = {
  render() {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('rect', { x: '3', y: '3', width: '18', height: '18', rx: '2', ry: '2' }),
      h('circle', { cx: '8.5', cy: '8.5', r: '1.5' }),
      h('polyline', { points: '21 15 16 10 5 21' }),
    ])
  },
}

const LyricsIcon = {
  render() {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('path', { d: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' }),
      h('polyline', { points: '14 2 14 8 20 8' }),
      h('line', { x1: '16', y1: '13', x2: '8', y2: '13' }),
      h('line', { x1: '16', y1: '17', x2: '8', y2: '17' }),
      h('polyline', { points: '10 9 9 9 8 9' }),
    ])
  },
}

const taskDefs = [
  { id: 'mbsync', name: 'Sync MusicBrainz', desc: 'Re-fetch and update metadata for all albums from MusicBrainz.', icon: SyncIcon },
  { id: 'fetchart', name: 'Fetch Artwork', desc: 'Download missing album cover art from online sources.', icon: ArtIcon },
  { id: 'lyrics', name: 'Fetch Lyrics', desc: 'Find and embed lyrics for all tracks in the library.', icon: LyricsIcon },
]

// ---------------------------------------------------------------------------
// Task runner
// ---------------------------------------------------------------------------

interface TaskState {
  status: 'idle' | 'running' | 'complete' | 'error'
  output: string
  taskId: string | null
}

const taskStates = ref<Record<string, TaskState>>({
  mbsync: { status: 'idle', output: '', taskId: null },
  fetchart: { status: 'idle', output: '', taskId: null },
  lyrics: { status: 'idle', output: '', taskId: null },
})

const pollTimers: Record<string, ReturnType<typeof setInterval>> = {}

function isRunning(taskId: string): boolean {
  return taskStates.value[taskId]?.status === 'running'
}

function statusLabel(taskId: string): string {
  const s = taskStates.value[taskId]?.status ?? 'idle'
  return { idle: 'Idle', running: 'Running', complete: 'Complete', error: 'Error' }[s] ?? s
}

function statusClass(taskId: string): string {
  return taskStates.value[taskId]?.status ?? 'idle'
}

function taskOutput(taskId: string): string {
  return taskStates.value[taskId]?.output ?? ''
}

async function runTask(id: string) {
  const state = taskStates.value[id]
  if (!state || state.status === 'running') return

  state.status = 'running'
  state.output = ''
  state.taskId = null

  try {
    const res = await runLibraryTask(id)
    state.taskId = res.task_id
    startPolling(id, res.task_id)
  } catch {
    state.status = 'error'
    state.output = 'Failed to start task.'
  }
}

function startPolling(stateKey: string, taskId: string) {
  if (pollTimers[stateKey]) clearInterval(pollTimers[stateKey])

  pollTimers[stateKey] = setInterval(async () => {
    try {
      const result = await getLibraryTask(taskId)
      if (result.status === 'complete' || result.status === 'error') {
        taskStates.value[stateKey].status = result.status as 'complete' | 'error'
        taskStates.value[stateKey].output = result.output ?? ''
        clearInterval(pollTimers[stateKey])
        delete pollTimers[stateKey]
      }
    } catch {
      taskStates.value[stateKey].status = 'error'
      taskStates.value[stateKey].output = 'Lost contact with task.'
      clearInterval(pollTimers[stateKey])
      delete pollTimers[stateKey]
    }
  }, 2000)
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMounted(async () => {
  try {
    stats.value = await fetchLibraryStats()
  } finally {
    statsLoading.value = false
  }
})

onUnmounted(() => {
  Object.values(pollTimers).forEach(t => clearInterval(t))
})
</script>

<style scoped>
.settings-view {
  padding: 28px 32px 60px;
  background-color: #18181b;
  color: #f4f4f5;
  min-height: 100%;
}

.import-embed :deep(.import-view) {
  padding: 0;
  background: transparent;
  min-height: unset;
}

.import-embed :deep(.import-start) {
  display: block;
}

.import-embed :deep(.connecting-state),
.import-embed :deep(.result-state) {
  min-height: unset;
  padding: 0;
  align-items: flex-start;
  justify-content: flex-start;
}

.import-embed :deep(.result-card) {
  max-width: 100%;
}

.import-embed :deep(.session-layout) {
  padding: 0;
}

.import-embed :deep(.candidate-section) {
  padding: 0;
  padding-top: 16px;
}

.page-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: #f4f4f5;
  margin: 0 0 32px;
}

.section {
  margin-bottom: 48px;
}

.section-title {
  font-size: var(--text-base);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #71717a;
  margin: 0 0 16px;
}

.section-desc {
  font-size: var(--text-md);
  color: #71717a;
  margin: -8px 0 20px;
  line-height: 1.6;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.stat-card {
  background: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 10px;
  padding: 16px 18px;
}

.skeleton-card {
  height: 72px;
  background: linear-gradient(90deg, #27272a 25%, #3f3f46 50%, #27272a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #f4f4f5;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: var(--text-sm);
  color: #71717a;
}

/* Format table */
.format-table {
  margin-top: 8px;
}

.sub-title {
  font-size: var(--text-sm);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #52525b;
  margin: 0 0 10px;
}

.formats {
  width: 100%;
  border-collapse: collapse;
  max-width: 520px;
}

.formats tr { border-bottom: 1px solid #27272a; }
.formats tr:last-child { border-bottom: none; }

.fmt-name {
  font-size: var(--text-base);
  color: #a1a1aa;
  padding: 6px 0;
  width: 90px;
}

.fmt-count {
  font-size: var(--text-base);
  color: #71717a;
  padding: 6px 16px 6px 0;
  text-align: right;
  width: 60px;
  font-variant-numeric: tabular-nums;
}

.fmt-bar-cell {
  width: 100%;
  padding: 6px 0;
}

.fmt-bar {
  height: 6px;
  background: #7c3aed;
  border-radius: 3px;
  min-width: 4px;
  opacity: 0.7;
}

/* Tasks */
.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.task-card {
  background: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 10px;
  padding: 18px 20px;
}

.task-header {
  display: flex;
  gap: 14px;
  margin-bottom: 16px;
}

.task-icon-wrap {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  background: rgba(124, 58, 237, 0.15);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a78bfa;
}

.task-icon { width: 18px; height: 18px; }

.task-meta { flex: 1; min-width: 0; }

.task-name {
  font-size: 15px;
  font-weight: 600;
  color: #f4f4f5;
  margin-bottom: 4px;
}

.task-desc { font-size: var(--text-base); color: #71717a; line-height: 1.5; }

.task-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-badge {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 4px;
}

.status-badge.idle { background: rgba(113, 113, 122, 0.15); color: #71717a; }
.status-badge.running { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
.status-badge.complete { background: rgba(74, 222, 128, 0.15); color: #4ade80; }
.status-badge.error { background: rgba(248, 113, 113, 0.15); color: #f87171; }

.run-btn {
  background: #7c3aed;
  border: none;
  border-radius: 6px;
  padding: 7px 16px;
  color: white;
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.run-btn:hover:not(:disabled) { background: #6d28d9; }
.run-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.task-output-wrap {
  margin-top: 14px;
  border-top: 1px solid #3f3f46;
  padding-top: 12px;
}

.task-output {
  font-size: var(--text-xs);
  color: #71717a;
  background: #18181b;
  border-radius: 6px;
  padding: 10px 12px;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  font-family: ui-monospace, Consolas, monospace;
}
</style>
