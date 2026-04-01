<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @mousedown.self="$emit('close')">
      <div class="modal">

        <!-- REMOVE MODE -->
        <template v-if="mode === 'remove'">
          <h2 class="modal-title">Remove Album from Library?</h2>
          <p class="modal-body">
            <strong>{{ albumName }}</strong> will be removed from the beets library.
            The audio files will <em>not</em> be deleted from disk.
          </p>
          <div class="modal-footer">
            <button class="btn-cancel" @click="$emit('close')" :disabled="saving">Cancel</button>
            <button class="btn-danger" @click="doRemove" :disabled="saving">
              {{ saving ? 'Removing…' : 'Remove' }}
            </button>
          </div>
        </template>

        <!-- RELOCATE MODE -->
        <template v-else-if="mode === 'relocate'">
          <h2 class="modal-title">Relocate Album Files</h2>
          <p class="modal-body">Move this album's folder into a new parent directory.</p>
          <div class="field">
            <label class="field-label">Destination folder</label>
            <input
              class="field-input"
              v-model="destPath"
              placeholder="/mnt/nfs/ml/Artist"
              @keydown.enter="doRelocate"
            />
            <p class="field-hint">The album folder will be moved inside this directory.</p>
          </div>
          <p v-if="error" class="modal-error">{{ error }}</p>
          <div class="modal-footer">
            <button class="btn-cancel" @click="$emit('close')" :disabled="saving">Cancel</button>
            <button class="btn-save" @click="doRelocate" :disabled="saving || !destPath.trim()">
              {{ saving ? 'Moving…' : 'Move Files' }}
            </button>
          </div>
        </template>

      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { deleteAlbum, relocateAlbum } from '@/api/library'
import type { AlbumDetail } from '@/types/album'

const props = defineProps<{
  open: boolean
  mode: 'remove' | 'relocate'
  albumId: number | null
  albumName: string | null
  currentFolder: string | null
}>()

const emit = defineEmits<{
  close: []
  removed: []
  relocated: [album: AlbumDetail]
}>()

const saving = ref(false)
const error = ref('')
const destPath = ref('')

// Pre-fill destination with the parent of the current folder
watch(() => props.open, (v) => {
  if (v) {
    error.value = ''
    saving.value = false
    if (props.currentFolder) {
      const lastSlash = props.currentFolder.lastIndexOf('/')
      destPath.value = lastSlash > 0 ? props.currentFolder.slice(0, lastSlash) : ''
    } else {
      destPath.value = ''
    }
  }
})

async function doRemove() {
  if (!props.albumId) return
  saving.value = true
  try {
    await deleteAlbum(props.albumId)
    emit('removed')
  } catch {
    // let the parent handle navigation
    emit('removed')
  } finally {
    saving.value = false
  }
}

async function doRelocate() {
  if (!props.albumId || !destPath.value.trim()) return
  saving.value = true
  error.value = ''
  try {
    const updated = await relocateAlbum(props.albumId, destPath.value.trim())
    emit('relocated', updated)
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    error.value = detail ?? 'Failed to move files.'
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
</style>
