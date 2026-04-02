import { watch, nextTick } from 'vue'
import type { Ref } from 'vue'

const FOCUSABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

export function useFocusTrap(
  containerRef: Ref<HTMLElement | null>,
  open: Ref<boolean>,
  onEscape: () => void,
) {
  function getFocusable(): HTMLElement[] {
    return Array.from(containerRef.value?.querySelectorAll<HTMLElement>(FOCUSABLE) ?? [])
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      e.preventDefault()
      onEscape()
      return
    }
    if (e.key !== 'Tab') return
    const focusable = getFocusable()
    if (!focusable.length) { e.preventDefault(); return }
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (e.shiftKey) {
      if (document.activeElement === first) { e.preventDefault(); last.focus() }
    } else {
      if (document.activeElement === last) { e.preventDefault(); first.focus() }
    }
  }

  watch(open, (isOpen) => {
    if (isOpen) {
      nextTick(() => {
        const focusable = getFocusable()
        focusable[0]?.focus()
        document.addEventListener('keydown', handleKeydown)
      })
    } else {
      document.removeEventListener('keydown', handleKeydown)
    }
  })
}
