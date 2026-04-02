<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @mousedown.self="$emit('close')">
      <div class="modal" ref="modalRef">

        <!-- REMOVE MODE -->
        <template v-if="activeMode === 'remove'">
          <h2 class="modal-title">Remove Artist from Library?</h2>
          <p class="modal-body">
            All albums by <strong>{{ artistName }}</strong> will be removed from the beets library.
            Audio files will <em>not</em> be deleted from disk.
          </p>
          <p v-if="error" class="modal-error">{{ error }}</p>
          <div class="modal-footer">
            <button class="btn-cancel" @click="$emit('close')" :disabled="saving">Cancel</button>
            <button class="btn-danger" @click="doRemove" :disabled="saving">
              {{ saving ? 'Removing…' : 'Remove All Albums' }}
            </button>
          </div>
        </template>

        <!-- RELOCATE MODE -->
        <template v-else-if="activeMode === 'relocate'">
          <h2 class="modal-title">Relocate Artist Files</h2>
          <p class="modal-body">
            Move all albums by <strong>{{ artistName }}</strong> into a new parent directory.
            Each album folder will be placed inside the destination.
          </p>
          <div class="field">
            <label class="field-label">Destination folder</label>
            <input
              class="field-input"
              v-model="destPath"
              placeholder="/mnt/nfs/ml/Artist"
              @keydown.enter="doRelocate"
            />
            <p class="field-hint">Each album folder will be moved inside this directory.</p>
          </div>
          <p v-if="error" class="modal-error">{{ error }}</p>
          <div class="modal-footer">
            <button class="btn-cancel" @click="$emit('close')" :disabled="saving">Cancel</button>
            <button class="btn-save" @click="doRelocate" :disabled="saving || !destPath.trim()">
              {{ saving ? 'Moving…' : 'Move Albums' }}
            </button>
          </div>
        </template>

        <!-- Result summary (after relocate completes with partial failures) -->
        <template v-else-if="activeMode === 'result'">
          <h2 class="modal-title">Relocation Complete</h2>
          <div class="result-stats">
            <div class="result-stat">
              <span class="stat-n stat-ok">{{ resultData.relocated }}</span>
              <span class="stat-label">Moved</span>
            </div>
            <div class="result-stat">
              <span class="stat-n stat-err">{{ resultData.failed }}</span>
              <span class="stat-label">Failed</span>
            </div>
          </div>
          <div v-if="resultData.errors.length > 0" class="result-errors">
            <p v-for="(e, i) in resultData.errors" :key="i" class="result-error-line">{{ e }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn-save" @click="emit('done', resultData)">Done</button>
          </div>
        </template>

      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, toRef, watch } from 'vue'
import { removeArtist, relocateArtist } from '@/api/library'
import { useFocusTrap } from '@/composables/useFocusTrap'

const props = defineProps<{
  open: boolean
  mode: 'remove' | 'relocate'
  artistName: string | null
}>()

const emit = defineEmits<{
  close: []
  removed: []
  done: [result: { relocated: number; failed: number; errors: string[] }]
}>()

const modalRef = ref<HTMLElement | null>(null)
useFocusTrap(modalRef, toRef(props, 'open'), () => emit('close'))

const saving = ref(false)
const error = ref('')
const destPath = ref('')
const activeMode = ref<'remove' | 'relocate' | 'result'>(props.mode)
const resultData = ref({ relocated: 0, failed: 0, errors: [] as string[] })

watch(() => props.open, (v) => {
  if (v) {
    saving.value = false
    error.value = ''
    destPath.value = ''
    activeMode.value = props.mode
  }
})

async function doRemove() {
  if (!props.artistName) return
  saving.value = true
  error.value = ''
  try {
    await removeArtist(props.artistName)
    emit('removed')
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    error.value = detail ?? 'Failed to remove artist.'
  } finally {
    saving.value = false
  }
}

async function doRelocate() {
  if (!props.artistName || !destPath.value.trim()) return
  saving.value = true
  error.value = ''
  try {
    const result = await relocateArtist(props.artistName, destPath.value.trim())
    resultData.value = result
    activeMode.value = 'result'
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    error.value = detail ?? 'Failed to move albums.'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9000;
  padding: 16px;
}

.modal {
  background: #18181b;
  border: 1px solid #3f3f46;
  border-radius: 12px;
  width: 100%;
  max-width: 460px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6);
  padding: 24px;
}

.modal-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: #f4f4f5;
  margin: 0 0 14px;
}

.modal-body {
  font-size: var(--text-md);
  color: #a1a1aa;
  line-height: 1.6;
  margin: 0 0 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 12px;
}

.field-label {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #71717a;
}

.field-input {
  background: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  padding: 7px 10px;
  color: #f4f4f5;
  font-size: var(--text-md);
  width: 100%;
  box-sizing: border-box;
  transition: border-color 0.15s;
  outline: none;
}
.field-input:focus { border-color: #7c3aed; }

.field-hint {
  font-size: var(--text-sm);
  color: #52525b;
  margin: 2px 0 0;
}

.modal-error {
  font-size: var(--text-base);
  color: #f87171;
  margin: 0 0 12px;
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #27272a;
}

.btn-cancel {
  background: none;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  padding: 8px 16px;
  color: #a1a1aa;
  font-size: var(--text-md);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}
.btn-cancel:hover:not(:disabled) { border-color: #71717a; color: #f4f4f5; }
.btn-cancel:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-save {
  background: #7c3aed;
  border: none;
  border-radius: 6px;
  padding: 8px 20px;
  color: white;
  font-size: var(--text-md);
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-save:hover:not(:disabled) { background: #6d28d9; }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-danger {
  background: #dc2626;
  border: none;
  border-radius: 6px;
  padding: 8px 20px;
  color: white;
  font-size: var(--text-md);
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-danger:hover:not(:disabled) { background: #b91c1c; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

/* Result summary */
.result-stats {
  display: flex;
  gap: 32px;
  margin-bottom: 16px;
}

.result-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-n {
  font-size: var(--text-3xl);
  font-weight: 700;
  line-height: 1;
}

.stat-ok { color: #4ade80; }
.stat-err { color: #f87171; }

.stat-label {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #71717a;
}

.result-errors {
  max-height: 160px;
  overflow-y: auto;
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 4px;
}

.result-error-line {
  font-size: var(--text-sm);
  font-family: ui-monospace, Consolas, monospace;
  color: #f87171;
  margin: 3px 0;
  line-height: 1.5;
}
</style>
