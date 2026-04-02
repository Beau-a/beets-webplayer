<template>
  <div class="import-start">
    <div class="start-card">
      <div class="start-form">
        <div class="field">
          <label class="field-label" for="import-dir">Directory path</label>
          <input
            id="import-dir"
            v-model="directory"
            type="text"
            class="field-input"
            placeholder="/mnt/nfs/incoming/NewAlbums"
            :disabled="isStarting"
            @keydown.enter="handleStart"
          />
        </div>

        <div class="options-grid">
          <label class="option-row">
            <input v-model="opts.autotag" type="checkbox" class="option-check" :disabled="isStarting" />
            <span class="option-label">Autotag (MusicBrainz lookup)</span>
          </label>
          <label class="option-row">
            <input v-model="opts.write_tags" type="checkbox" class="option-check" :disabled="isStarting" />
            <span class="option-label">Write tags to files</span>
          </label>
          <label class="option-row">
            <input v-model="opts.move" type="checkbox" class="option-check" :disabled="isStarting" />
            <span class="option-label">Move files into library</span>
          </label>
          <label class="option-row">
            <input v-model="opts.copy" type="checkbox" class="option-check" :disabled="isStarting" />
            <span class="option-label">Copy files (keep originals)</span>
          </label>
        </div>
        <p class="options-hint" v-if="!opts.move && !opts.copy">
          Neither move nor copy selected — files will be imported in-place and tracked at their current location.
        </p>

        <div v-if="errorMessage" class="error-banner">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="error-icon">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {{ errorMessage }}
        </div>

        <button
          class="start-btn"
          :disabled="!directory.trim() || isStarting"
          @click="handleStart"
        >
          <svg v-if="isStarting" class="spinner-icon" viewBox="0 0 24 24" fill="none">
            <circle class="spinner-track" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"/>
            <path class="spinner-arc" d="M12 2a10 10 0 0110 10" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          {{ isStarting ? 'Connecting…' : 'Start Import' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useImportStore } from '@/stores/import'

const importStore = useImportStore()

const directory = ref('')
const opts = reactive({
  autotag: true,
  write_tags: true,
  copy: false,
  move: true,
})

const isStarting = computed(() => importStore.sessionState === 'connecting')
const errorMessage = computed(() => importStore.error)

async function handleStart() {
  if (!directory.value.trim() || isStarting.value) return
  await importStore.startImport(directory.value.trim(), {
    autotag: opts.autotag,
    write_tags: opts.write_tags,
    copy: opts.copy,
    move: opts.move,
  })
}
</script>

<style scoped>
.import-start {
  display: block;
}

.start-card {
  background: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 10px;
  padding: 18px 20px;
}

.start-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: var(--text-base);
  font-weight: 500;
  color: #a1a1aa;
}

.field-input {
  background-color: #09090b;
  border: 1px solid #27272a;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: var(--text-md);
  color: #f4f4f5;
  font-family: ui-monospace, Consolas, monospace;
  transition: border-color 0.15s;
  outline: none;
  width: 100%;
  box-sizing: border-box;
}

.field-input::placeholder {
  color: #52525b;
}

.field-input:focus {
  border-color: #7c3aed;
}

.field-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 16px;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.option-check {
  width: 15px;
  height: 15px;
  accent-color: #7c3aed;
  flex-shrink: 0;
  cursor: pointer;
}

.option-check:disabled {
  cursor: not-allowed;
}

.option-label {
  font-size: var(--text-base);
  color: #a1a1aa;
  user-select: none;
}

.options-hint {
  font-size: var(--text-sm);
  color: #a16207;
  background: rgba(161, 98, 7, 0.1);
  border: 1px solid rgba(161, 98, 7, 0.3);
  border-radius: 6px;
  padding: 8px 12px;
  margin: 0;
  line-height: 1.5;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  padding: 10px 14px;
  font-size: var(--text-base);
  color: #fca5a5;
}

.error-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.start-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background-color: #7c3aed;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 12px 20px;
  font-size: var(--text-md);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s;
}

.start-btn:hover:not(:disabled) {
  background-color: #6d28d9;
}

.start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.spinner-icon {
  width: 16px;
  height: 16px;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

.spinner-track {
  opacity: 0.2;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
