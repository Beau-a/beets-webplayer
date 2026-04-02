import { onMounted, onBeforeUnmount } from 'vue'
import { usePlayerStore } from '@/stores/player'

const INPUT_TAGS = new Set(['INPUT', 'TEXTAREA', 'SELECT'])

function isTyping(): boolean {
  const el = document.activeElement as HTMLElement | null
  if (!el) return false
  if (INPUT_TAGS.has(el.tagName)) return true
  if (el.isContentEditable) return true
  // Inside an open modal
  if (el.closest('.modal-backdrop')) return true
  return false
}

export function useGlobalShortcuts() {
  const store = usePlayerStore()

  function handleKeydown(e: KeyboardEvent) {
    if (isTyping()) return

    switch (e.key) {
      case ' ':
        if (!store.currentTrack) return
        e.preventDefault()
        store.setIsPlaying(!store.isPlaying)
        break

      case 'ArrowLeft':
        e.preventDefault()
        if (store.currentTime > 3) {
          store.seek(Math.max(0, store.currentTime - 10))
        } else {
          store.previous()
        }
        break

      case 'ArrowRight':
        e.preventDefault()
        if (store.duration && store.currentTime < store.duration - 5) {
          store.seek(Math.min(store.duration, store.currentTime + 10))
        } else {
          store.next()
        }
        break

      case 'm':
      case 'M':
        e.preventDefault()
        store.toggleMute()
        break
    }
  }

  onMounted(() => window.addEventListener('keydown', handleKeydown))
  onBeforeUnmount(() => window.removeEventListener('keydown', handleKeydown))
}
