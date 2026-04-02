<template>
  <Teleport to="body">
    <div v-if="open && item" class="modal-backdrop" @mousedown.self="$emit('close')">
      <div class="modal" ref="modalRef">
        <div class="modal-header">
          <h2 class="modal-title">Edit Track</h2>
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
              <label class="field-label">Title</label>
              <input v-model="form.title" type="text" class="field-input" />
            </div>
            <div class="field">
              <label class="field-label">Artist</label>
              <input v-model="form.artist" type="text" class="field-input" />
            </div>
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
              <label class="field-label">Track #</label>
              <input v-model.number="form.track" type="number" class="field-input" min="0" />
            </div>
            <div class="field">
              <label class="field-label">Disc #</label>
              <input v-model.number="form.disc" type="number" class="field-input" min="0" />
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
              <label class="field-label">BPM</label>
              <input v-model.number="form.bpm" type="number" class="field-input" min="0" />
            </div>
            <div class="field">
              <label class="field-label">Media</label>
              <input v-model="form.media" type="text" class="field-input" placeholder="CD, Vinyl, Digital…" />
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
import { updateItem, type ItemUpdatePayload } from '@/api/library'
import type { TrackInAlbum } from '@/types/album'
import { useFocusTrap } from '@/composables/useFocusTrap'

const props = defineProps<{
  item: TrackInAlbum | null
  open: boolean
}>()

const emit = defineEmits<{
  close: []
  saved: [updated: unknown]
}>()

const modalRef = ref<HTMLElement | null>(null)
useFocusTrap(modalRef, toRef(props, 'open'), () => emit('close'))

interface FormState {
  title: string
  artist: string
  album: string
  albumartist: string
  year: number | null
  track: number | null
  disc: number | null
  genres: string
  label: string
  country: string
  bpm: number | null
  media: string
}

const form = ref<FormState>({
  title: '',
  artist: '',
  album: '',
  albumartist: '',
  year: null,
  track: null,
  disc: null,
  genres: '',
  label: '',
  country: '',
  bpm: null,
  media: '',
})

const saving = ref(false)
const error = ref('')

watch(
  () => props.item,
  (item) => {
    if (!item) return
    form.value = {
      title: item.title ?? '',
      artist: item.artist ?? '',
      album: (item as unknown as Record<string, unknown>).album as string ?? '',
      albumartist: '',
      year: (item as unknown as Record<string, unknown>).year as number | null ?? null,
      track: item.track ?? null,
      disc: item.disc ?? null,
      genres: (item as unknown as Record<string, unknown>).genres as string ?? '',
      label: (item as unknown as Record<string, unknown>).label as string ?? '',
      country: (item as unknown as Record<string, unknown>).country as string ?? '',
      bpm: (item as unknown as Record<string, unknown>).bpm as number | null ?? null,
      media: (item as unknown as Record<string, unknown>).media as string ?? '',
    }
    error.value = ''
  },
  { immediate: true },
)

async function handleSave() {
  if (!props.item) return
  saving.value = true
  error.value = ''

  const payload: ItemUpdatePayload = {}
  if (form.value.title !== (props.item.title ?? '')) payload.title = form.value.title
  if (form.value.artist !== (props.item.artist ?? '')) payload.artist = form.value.artist
  const origAlbum = (props.item as unknown as Record<string, unknown>).album as string ?? ''
  if (form.value.album !== origAlbum) payload.album = form.value.album
  if (form.value.track !== (props.item.track ?? null)) payload.track = form.value.track ?? undefined
  if (form.value.disc !== (props.item.disc ?? null)) payload.disc = form.value.disc ?? undefined
  if (form.value.year !== null) payload.year = form.value.year
  if (form.value.genres) payload.genres = form.value.genres
  if (form.value.label) payload.label = form.value.label
  if (form.value.country) payload.country = form.value.country
  if (form.value.bpm) payload.bpm = form.value.bpm
  if (form.value.media) payload.media = form.value.media

  if (Object.keys(payload).length === 0) {
    emit('close')
    return
  }

  try {
    const updated = await updateItem(props.item.id, payload)
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
