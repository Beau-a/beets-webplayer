<template>
  <div class="import-progress">
    <!-- Header -->
    <div class="progress-header">
      <div class="progress-header-left">
        <h2 class="progress-title">
          <span class="pulse-dot" />
          Importing…
        </h2>
        <p v-if="store.progress.currentPath" class="current-path" :title="store.progress.currentPath">
          {{ truncatePath(store.progress.currentPath) }}
        </p>
      </div>
      <button class="abort-btn" @click="confirmAbort">Abort</button>
    </div>

    <!-- Progress bar -->
    <div class="progress-track">
      <div
        class="progress-fill"
        :style="{ width: progressPercent + '%' }"
      />
    </div>
    <div class="progress-counts">
      <span class="progress-fraction">
        {{ store.progress.completed }}
        <template v-if="store.progress.total > 0"> / {{ store.progress.total }}</template>
        albums
      </span>
      <span class="progress-pct" v-if="store.progress.total > 0">{{ progressPercent }}%</span>
    </div>

    <!-- Log -->
    <div class="log-container" ref="logEl">
      <div v-if="store.importLog.length === 0" class="log-empty">
        Waiting for results…
      </div>
      <div
        v-for="(entry, i) in store.importLog"
        :key="i"
        class="log-entry"
        :class="[`log-${entry.type}`]"
      >
        <span class="log-icon">
          <template v-if="entry.type === 'imported'">✓</template>
          <template v-else-if="entry.type === 'skipped'">→</template>
          <template v-else>✗</template>
        </span>
        <span class="log-text">
          <template v-if="entry.type === 'imported'">
            Imported:
            <strong>{{ entry.artist }}</strong> — {{ entry.album }}
            <span v-if="entry.year" class="log-year">({{ entry.year }})</span>
          </template>
          <template v-else-if="entry.type === 'skipped'">
            Skipped: {{ baseName(entry.path) }}
            <span v-if="entry.message" class="log-reason">— {{ entry.message }}</span>
          </template>
          <template v-else>
            Error: {{ baseName(entry.path) }}
            <span v-if="entry.message" class="log-reason">— {{ entry.message }}</span>
          </template>
        </span>
      </div>
    </div>

    <!-- Abort confirmation dialog -->
    <div v-if="showAbortConfirm" class="abort-overlay">
      <div class="abort-dialog">
        <h3 class="abort-title">Abort import?</h3>
        <p class="abort-body">
          The current album will be skipped. Albums already imported will be kept.
        </p>
        <div class="abort-actions">
          <button class="abort-cancel" @click="showAbortConfirm = false">Continue importing</button>
          <button class="abort-confirm" @click="doAbort">Abort</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useImportStore } from '@/stores/import'

const store = useImportStore()
const logEl = ref<HTMLElement | null>(null)
const showAbortConfirm = ref(false)

const progressPercent = computed(() => {
  if (store.progress.total <= 0) return 0
  return Math.min(100, Math.round((store.progress.completed / store.progress.total) * 100))
})

// Auto-scroll log to bottom when new entries arrive
watch(
  () => store.importLog.length,
  async () => {
    await nextTick()
    if (logEl.value) {
      logEl.value.scrollTop = logEl.value.scrollHeight
    }
  },
)

function truncatePath(path: string): string {
  if (path.length <= 60) return path
  const parts = path.split('/')
  if (parts.length > 3) {
    return '…/' + parts.slice(-2).join('/')
  }
  return path
}

function baseName(path: string): string {
  return path.split('/').pop() || path
}

function confirmAbort() {
  showAbortConfirm.value = true
}

function doAbort() {
  showAbortConfirm.value = false
  store.abortImport()
}
</script>

<style scoped>
.import-progress {
  padding: 28px 32px;
  position: relative;
}

.progress-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.progress-header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.progress-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 700;
  color: #f4f4f5;
  margin: 0;
}

.pulse-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #8b5cf6;
  animation: pulse 1.8s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.75); }
}

.current-path {
  font-size: var(--text-sm);
  color: #52525b;
  font-family: ui-monospace, Consolas, monospace;
  max-width: 500px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
}

.abort-btn {
  background-color: transparent;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: var(--text-base);
  color: #a1a1aa;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  flex-shrink: 0;
}

.abort-btn:hover {
  border-color: #ef4444;
  color: #fca5a5;
}

.progress-track {
  height: 6px;
  background-color: #27272a;
  border-radius: 99px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #7c3aed, #8b5cf6);
  border-radius: 99px;
  transition: width 0.4s ease;
  min-width: 4px;
}

.progress-counts {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.progress-fraction,
.progress-pct {
  font-size: var(--text-sm);
  color: #71717a;
}

.progress-pct {
  color: #8b5cf6;
  font-weight: 600;
}

.log-container {
  background-color: #09090b;
  border: 1px solid #27272a;
  border-radius: 8px;
  max-height: 320px;
  overflow-y: auto;
  font-family: ui-monospace, Consolas, monospace;
  font-size: var(--text-sm);
  scroll-behavior: smooth;
}

.log-empty {
  padding: 20px;
  color: #52525b;
  text-align: center;
  font-family: inherit;
}

.log-entry {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 5px 14px;
  border-bottom: 1px solid #18181b;
  line-height: 1.5;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-icon {
  flex-shrink: 0;
  width: 14px;
  font-weight: 700;
}

.log-imported .log-icon { color: #4ade80; }
.log-skipped .log-icon { color: #71717a; }
.log-error .log-icon { color: #f87171; }

.log-text {
  color: #a1a1aa;
  flex: 1;
  min-width: 0;
  word-break: break-all;
}

.log-imported .log-text { color: #d4d4d8; }
.log-imported strong { color: #e4e4e7; }

.log-error .log-text { color: #fca5a5; }

.log-year {
  color: #71717a;
  font-size: var(--text-xs);
}

.log-reason {
  color: #71717a;
}

/* Abort confirmation */
.abort-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.abort-dialog {
  background-color: #18181b;
  border: 1px solid #3f3f46;
  border-radius: 12px;
  padding: 28px 32px;
  max-width: 380px;
  width: 100%;
}

.abort-title {
  font-size: 17px;
  font-weight: 700;
  color: #f4f4f5;
  margin: 0 0 8px;
}

.abort-body {
  font-size: var(--text-md);
  color: #71717a;
  line-height: 1.5;
  margin: 0 0 24px;
}

.abort-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.abort-cancel {
  background-color: #27272a;
  border: none;
  border-radius: 7px;
  padding: 9px 16px;
  font-size: var(--text-base);
  color: #a1a1aa;
  cursor: pointer;
  transition: background-color 0.15s;
}

.abort-cancel:hover {
  background-color: #3f3f46;
}

.abort-confirm {
  background-color: #dc2626;
  border: none;
  border-radius: 7px;
  padding: 9px 16px;
  font-size: var(--text-base);
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  transition: background-color 0.15s;
}

.abort-confirm:hover {
  background-color: #b91c1c;
}
</style>
