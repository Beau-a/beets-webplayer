<template>
  <Teleport to="body">
    <div v-if="open && album" class="modal-backdrop" @mousedown.self="$emit('close')">
      <div class="modal" ref="modalRef">
        <div class="modal-header">
          <h2 class="modal-title">Edit Album</h2>
          <button class="close-btn" aria-label="Close" @click="$emit('close')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <form class="modal-body" @submit.prevent="handleSave">
          <div class="field-grid">
            <div class="field">
              <label class="field-label">Album</label>
              <input v-model="form.album" type="text" class="field-input" />
            </div>
            <div class="field">
              <label class="field-label">Album Artist</label>
              <input v-model="form.albumartist" type="text" class="field-input" />
            </div>
            <div class="field">
              <label class="field-label">Year</label>
              <input v-model.number="form.year" type="number" class="field-input" min="0" max="9999" />
            </div>
            <div class="field">
              <label class="field-label">Original Year</label>
              <input v-model.number="form.original_year" type="number" class="field-input" min="0" max="9999" />
            </div>
            <div class="field">
              <label class="field-label">Genre</label>
              <input v-model="form.genres" type="text" class="field-input" />
            </div>
            <div class="field">
              <label class="field-label">Label</label>
              <input v-model="form.label" type="text" class="field-input" />
            </div>
            <div class="field">
              <label class="field-label">Country</label>
              <input v-model="form.country" type="text" class="field-input" />
            </div>
            <div class="field">
              <label class="field-label">Album Type</label>
              <input v-model="form.albumtype" type="text" class="field-input" placeholder="album, single, ep…" />
            </div>
            <div class="field">
              <label class="field-label">Catalog #</label>
              <input v-model="form.catalognum" type="text" class="field-input" />
            </div>
            <div class="field">
              <label class="field-label">Barcode</label>
              <input v-model="form.barcode" type="text" class="field-input" />
            </div>
            <div class="field">
              <label class="field-label">ASIN</label>
              <input v-model="form.asin" type="text" class="field-input" />
            </div>
            <div class="field field-checkbox">
              <label class="checkbox-row">
                <input v-model="form.comp" type="checkbox" class="check-input" />
                <span class="field-label" style="text-transform: none; letter-spacing: 0; font-size: var(--text-base);">Compilation</span>
              </label>
            </div>
          </div>

          <div v-if="error" class="error-msg">{{ error }}</div>

          <div class="modal-footer">
            <button type="button" class="btn-cancel" @click="$emit('close')">Cancel</button>
            <button type="submit" class="btn-save" :disabled="saving">
              {{ saving ? 'Saving…' : 'Save Changes' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, toRef, watch } from 'vue'
import { updateAlbum, type AlbumUpdatePayload } from '@/api/library'
import type { AlbumDetail } from '@/types/album'
import { useFocusTrap } from '@/composables/useFocusTrap'

const props = defineProps<{
  album: AlbumDetail | null
  open: boolean
}>()

const emit = defineEmits<{
  close: []
  saved: [updated: unknown]
}>()

const modalRef = ref<HTMLElement | null>(null)
useFocusTrap(modalRef, toRef(props, 'open'), () => emit('close'))

interface AlbumFormState {
  album: string
  albumartist: string
  year: number | null
  original_year: number | null
  genres: string
  label: string
  country: string
  albumtype: string
  catalognum: string
  barcode: string
  asin: string
  comp: boolean
}

const form = ref<AlbumFormState>({
  album: '',
  albumartist: '',
  year: null,
  original_year: null,
  genres: '',
  label: '',
  country: '',
  albumtype: '',
  catalognum: '',
  barcode: '',
  asin: '',
  comp: false,
})

const saving = ref(false)
const error = ref('')

watch(
  () => props.album,
  (a) => {
    if (!a) return
    form.value = {
      album: a.album ?? '',
      albumartist: a.albumartist ?? '',
      year: a.year ?? null,
      original_year: a.original_year ?? null,
      genres: a.genres ?? '',
      label: a.label ?? '',
      country: a.country ?? '',
      albumtype: a.albumtype ?? '',
      catalognum: a.catalognum ?? '',
      barcode: a.barcode ?? '',
      asin: a.asin ?? '',
      comp: Boolean(a.comp),
    }
    error.value = ''
  },
  { immediate: true },
)

async function handleSave() {
  if (!props.album) return
  saving.value = true
  error.value = ''

  const a = props.album
  const payload: AlbumUpdatePayload = {}
  if (form.value.album !== (a.album ?? '')) payload.album = form.value.album
  if (form.value.albumartist !== (a.albumartist ?? '')) payload.albumartist = form.value.albumartist
  if (form.value.year !== (a.year ?? null)) payload.year = form.value.year ?? undefined
  if (form.value.original_year !== (a.original_year ?? null)) payload.original_year = form.value.original_year ?? undefined
  if (form.value.genres !== (a.genres ?? '')) payload.genres = form.value.genres
  if (form.value.label !== (a.label ?? '')) payload.label = form.value.label
  if (form.value.country !== (a.country ?? '')) payload.country = form.value.country
  if (form.value.albumtype !== (a.albumtype ?? '')) payload.albumtype = form.value.albumtype
  if (form.value.catalognum !== (a.catalognum ?? '')) payload.catalognum = form.value.catalognum
  if (form.value.barcode !== (a.barcode ?? '')) payload.barcode = form.value.barcode
  if (form.value.asin !== (a.asin ?? '')) payload.asin = form.value.asin
  if (form.value.comp !== Boolean(a.comp)) payload.comp = form.value.comp ? 1 : 0

  if (Object.keys(payload).length === 0) {
    emit('close')
    return
  }

  try {
    const updated = await updateAlbum(props.album.id, payload)
    emit('saved', updated)
    emit('close')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to save changes'
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
  max-width: 640px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #27272a;
}

.modal-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: #f4f4f5;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #71717a;
  cursor: pointer;
  padding: 4px;
  display: flex;
  border-radius: 4px;
  transition: color 0.15s;
}
.close-btn:hover { color: #f4f4f5; }

.icon { width: 18px; height: 18px; }

.modal-body {
  padding: 20px 24px;
}

.field-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field-checkbox {
  justify-content: flex-end;
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding-bottom: 6px;
}

.check-input {
  width: 16px;
  height: 16px;
  accent-color: #7c3aed;
  cursor: pointer;
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

.error-msg {
  margin-top: 12px;
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  font-size: var(--text-base);
  color: #f87171;
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
.btn-cancel:hover { border-color: #71717a; color: #f4f4f5; }

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
</style>
