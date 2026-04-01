import { watch } from 'vue'
import { usePlayerStore, registerSeekFn } from '@/stores/player'

// Module-level singleton — created once, never recreated
const audio = new Audio()
audio.preload = 'metadata'

// Export so the store can call it directly after registerSeekFn registers it
export function seekTo(seconds: number) {
  audio.currentTime = seconds
}

export function useAudioPlayer() {
  const playerStore = usePlayerStore()

  // Register our seek function into the store
  registerSeekFn(seekTo)

  // ── Audio event listeners ─────────────────────────────────────────────
  audio.addEventListener('timeupdate', () => {
    playerStore.setCurrentTime(audio.currentTime)
  })

  audio.addEventListener('loadedmetadata', () => {
    playerStore.setDuration(audio.duration)
  })

  audio.addEventListener('ended', () => {
    playerStore.next()
  })

  audio.addEventListener('play', () => {
    playerStore.setIsPlaying(true)
  })

  audio.addEventListener('pause', () => {
    playerStore.setIsPlaying(false)
  })

  audio.addEventListener('error', () => {
    console.error('[useAudioPlayer] audio error for src:', audio.src, audio.error)
    playerStore.next()
  })

  audio.addEventListener('waiting', () => {
    playerStore.setIsBuffering(true)
  })

  audio.addEventListener('canplaythrough', () => {
    playerStore.setIsBuffering(false)
  })

  // ── Watch streamUrl — load and play when it changes ───────────────────
  watch(
    () => playerStore.streamUrl,
    (url) => {
      if (!url) {
        audio.pause()
        audio.src = ''
        playerStore.setIsBuffering(false)
        return
      }
      audio.src = url
      audio.load()
      audio.play().catch((err) => {
        // Autoplay may be blocked by browser policy; user interaction will resume it
        console.warn('[useAudioPlayer] play() promise rejected:', err)
      })
    },
  )

  // ── Watch isPlaying — sync play/pause to audio element ───────────────
  watch(
    () => playerStore.isPlaying,
    (playing) => {
      if (playing) {
        if (audio.paused && audio.src) {
          audio.play().catch((err) => {
            console.warn('[useAudioPlayer] play() rejected:', err)
          })
        }
      } else {
        if (!audio.paused) {
          audio.pause()
        }
      }
    },
  )

  // ── Watch volume and muted ────────────────────────────────────────────
  watch(
    () => playerStore.volume,
    (v) => {
      audio.volume = v
    },
    { immediate: true },
  )

  watch(
    () => playerStore.isMuted,
    (muted) => {
      audio.muted = muted
    },
    { immediate: true },
  )
}
