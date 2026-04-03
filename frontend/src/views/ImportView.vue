<template>
  <div class="import-view">
    <!-- Idle: start screen -->
    <ImportStart v-if="store.sessionState === 'idle'" />

    <!-- Connecting: spinner -->
    <div v-else-if="store.sessionState === 'connecting'" class="connecting-state">
      <div class="connecting-card">
        <div class="spinner">
          <svg viewBox="0 0 24 24" fill="none" class="spinner-svg">
            <circle cx="12" cy="12" r="10" stroke="#27272a" stroke-width="3"/>
            <path d="M12 2a10 10 0 0110 10" stroke="#7c3aed" stroke-width="3" stroke-linecap="round"/>
          </svg>
        </div>
        <p class="connecting-text">Connecting to import session…</p>
      </div>
    </div>

    <!-- Running: progress view -->
    <div v-else-if="store.sessionState === 'running'" class="session-layout">
      <ImportProgress />
    </div>

    <!-- Waiting for choice: progress in background + candidate list -->
    <div v-else-if="store.sessionState === 'waiting_choice'" class="session-layout">
      <ImportProgress />
      <div class="candidate-section">
        <CandidateList />
      </div>
    </div>

    <!-- No candidates found: ask user to search MB manually -->
    <div v-else-if="store.sessionState === 'waiting_no_candidates'" class="session-layout">
      <ImportProgress />
      <div class="candidate-section">
        <NoCandidatesPanel />
      </div>
    </div>

    <!-- Complete: summary -->
    <div v-else-if="store.sessionState === 'complete'" class="result-state">
      <div class="result-card">
        <div class="result-icon result-icon-success">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
          </svg>
        </div>
        <h2 class="result-title">Import Complete</h2>

        <div v-if="store.sessionSummary" class="summary-grid">
          <div class="summary-stat">
            <span class="stat-value stat-imported">{{ store.sessionSummary.total_imported }}</span>
            <span class="stat-label">Imported</span>
          </div>
          <div class="summary-stat">
            <span class="stat-value stat-skipped">{{ store.sessionSummary.total_skipped }}</span>
            <span class="stat-label">Skipped</span>
          </div>
          <div class="summary-stat">
            <span class="stat-value stat-errors">{{ store.sessionSummary.total_errors }}</span>
            <span class="stat-label">Errors</span>
          </div>
          <div class="summary-stat">
            <span class="stat-value stat-duration">{{ formatDuration(store.sessionSummary.duration_s) }}</span>
            <span class="stat-label">Duration</span>
          </div>
        </div>

        <!-- Log recap -->
        <div v-if="store.importLog.length > 0" class="result-log">
          <div
            v-for="(entry, i) in store.importLog"
            :key="i"
            class="result-log-entry"
            :class="`log-${entry.type}`"
          >
            <span class="log-icon">
              <template v-if="entry.type === 'imported'">✓</template>
              <template v-else-if="entry.type === 'skipped'">→</template>
              <template v-else>✗</template>
            </span>
            <span class="log-text">
              <template v-if="entry.type === 'imported'">
                {{ entry.artist }} — {{ entry.album }}
                <span v-if="entry.year" class="log-year">({{ entry.year }})</span>
              </template>
              <template v-else>
                {{ baseName(entry.path) }}
                <span v-if="entry.message" class="log-reason">— {{ entry.message }}</span>
              </template>
            </span>
          </div>
        </div>

        <!-- Post-import actions (only when albums were imported) -->
        <div v-if="store.importedAlbumIds.length > 0" class="post-import-actions">
          <p class="post-import-label">Run for imported albums:</p>
          <div class="post-import-btns">
            <button
              class="task-btn"
              :class="{ 'task-running': artTaskState === 'running', 'task-done': artTaskState === 'done', 'task-error': artTaskState === 'error' }"
              :disabled="artTaskState === 'running'"
              @click="runArt"
            >
              <span v-if="artTaskState === 'running'" class="task-spinner" />
              <span v-else-if="artTaskState === 'done'">✓</span>
              <span v-else-if="artTaskState === 'error'">✗</span>
              Get Art
            </button>
            <button
              class="task-btn"
              :class="{ 'task-running': lyricsTaskState === 'running', 'task-done': lyricsTaskState === 'done', 'task-error': lyricsTaskState === 'error' }"
              :disabled="lyricsTaskState === 'running'"
              @click="runLyrics"
            >
              <span v-if="lyricsTaskState === 'running'" class="task-spinner" />
              <span v-else-if="lyricsTaskState === 'done'">✓</span>
              <span v-else-if="lyricsTaskState === 'error'">✗</span>
              Get Lyrics
            </button>
          </div>
        </div>

        <div class="result-actions">
          <button class="result-btn btn-primary" @click="store.resetSession()">
            Import Another
          </button>
          <RouterLink to="/library" class="result-btn btn-secondary">
            Browse Library
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="store.sessionState === 'error'" class="result-state">
      <div class="result-card">
        <div class="result-icon result-icon-error">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <h2 class="result-title">Import Failed</h2>
        <p class="result-error-msg">{{ store.error || 'An unexpected error occurred.' }}</p>
        <div class="result-actions">
          <button class="result-btn btn-primary" @click="store.resetSession()">
            Try Again
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useImportStore } from '@/stores/import'
import ImportStart from '@/components/import/ImportStart.vue'
import ImportProgress from '@/components/import/ImportProgress.vue'
import CandidateList from '@/components/import/CandidateList.vue'
import NoCandidatesPanel from '@/components/import/NoCandidatesPanel.vue'
import { runLibraryTask, getLibraryTask } from '@/api/library'

const store = useImportStore()

type TaskState = 'idle' | 'running' | 'done' | 'error'
const artTaskState = ref<TaskState>('idle')
const lyricsTaskState = ref<TaskState>('idle')

async function pollTask(taskId: string, stateRef: typeof artTaskState) {
  while (true) {
    await new Promise(r => setTimeout(r, 1500))
    const result = await getLibraryTask(taskId)
    if (result.status === 'complete') { stateRef.value = 'done'; return }
    if (result.status === 'error') { stateRef.value = 'error'; return }
  }
}

async function runArt() {
  artTaskState.value = 'running'
  try {
    const result = await runLibraryTask('fetchart', store.importedAlbumIds)
    pollTask(result.task_id, artTaskState)
  } catch {
    artTaskState.value = 'error'
  }
}

async function runLyrics() {
  lyricsTaskState.value = 'running'
  try {
    const result = await runLibraryTask('lyrics', store.importedAlbumIds)
    pollTask(result.task_id, lyricsTaskState)
  } catch {
    lyricsTaskState.value = 'error'
  }
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return `${m}m ${s}s`
}

function baseName(path: string): string {
  return path.split('/').pop() || path
}
</script>

<style scoped>
.import-view {
  min-height: 100%;
  background-color: #18181b;
  color: #f4f4f5;
}

/* Connecting */
.connecting-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  padding: 40px;
}

.connecting-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.spinner {
  width: 48px;
  height: 48px;
}

.spinner-svg {
  width: 100%;
  height: 100%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.connecting-text {
  font-size: var(--text-md);
  color: #71717a;
  margin: 0;
}

/* Session layout (running / waiting_choice) */
.session-layout {
  padding: 0;
}

.candidate-section {
  padding: 0 32px 32px;
}

/* Result states */
.result-state {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 40px 24px;
  min-height: 100%;
}

.result-card {
  width: 100%;
  max-width: 560px;
  background-color: #09090b;
  border: 1px solid #27272a;
  border-radius: 12px;
  padding: 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.result-icon {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.result-icon svg {
  width: 26px;
  height: 26px;
}

.result-icon-success {
  background-color: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.result-icon-error {
  background-color: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.result-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: #f4f4f5;
  margin: 0 0 20px;
  text-align: center;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background-color: #27272a;
  border-radius: 10px;
  overflow: hidden;
  width: 100%;
  margin-bottom: 24px;
}

.summary-stat {
  background-color: #18181b;
  padding: 14px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 700;
}

.stat-imported { color: #4ade80; }
.stat-skipped { color: #71717a; }
.stat-errors { color: #f87171; }
.stat-duration { color: #a78bfa; }

.stat-label {
  font-size: var(--text-xs);
  color: #52525b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Compact log in result card */
.result-log {
  width: 100%;
  max-height: 220px;
  overflow-y: auto;
  background-color: #09090b;
  border: 1px solid #1f1f23;
  border-radius: 8px;
  font-family: ui-monospace, Consolas, monospace;
  font-size: var(--text-xs);
  margin-bottom: 24px;
}

.result-log-entry {
  display: flex;
  align-items: baseline;
  gap: 7px;
  padding: 4px 12px;
  border-bottom: 1px solid #18181b;
}

.result-log-entry:last-child {
  border-bottom: none;
}

.log-imported .log-icon { color: #4ade80; }
.log-skipped .log-icon { color: #71717a; }
.log-error .log-icon { color: #f87171; }

.log-icon {
  flex-shrink: 0;
  width: 14px;
  font-weight: 700;
}

.log-text {
  color: #a1a1aa;
  word-break: break-all;
}

.log-imported .log-text { color: #d4d4d8; }
.log-error .log-text { color: #fca5a5; }

.log-year {
  color: #71717a;
}

.log-reason {
  color: #71717a;
}

.result-error-msg {
  font-size: var(--text-md);
  color: #71717a;
  text-align: center;
  margin: 0 0 24px;
  line-height: 1.5;
}

.post-import-actions {
  width: 100%;
  margin-bottom: 20px;
  padding: 16px;
  background-color: #18181b;
  border: 1px solid #27272a;
  border-radius: 8px;
}

.post-import-label {
  font-size: var(--text-xs);
  color: #71717a;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 10px;
}

.post-import-btns {
  display: flex;
  gap: 8px;
}

.task-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  border: 1px solid #3f3f46;
  background-color: #27272a;
  color: #d4d4d8;
  transition: background-color 0.15s, border-color 0.15s;
}

.task-btn:hover:not(:disabled) {
  background-color: #3f3f46;
  border-color: #52525b;
}

.task-btn:disabled {
  opacity: 0.6;
  cursor: default;
}

.task-btn.task-done {
  border-color: #166534;
  color: #4ade80;
}

.task-btn.task-error {
  border-color: #7f1d1d;
  color: #f87171;
}

.task-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid #52525b;
  border-top-color: #a78bfa;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.result-actions {
  display: flex;
  gap: 10px;
}

.result-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: var(--text-md);
  font-weight: 500;
  cursor: pointer;
  border: none;
  text-decoration: none;
  transition: background-color 0.15s;
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
</style>
