import { watch } from 'vue'
import { usePlayerStore, registerSeekFn } from '@/stores/player'
import { recordPlay } from '@/api/playback'

// Module-level singleton — created once, never recreated
const audio = new Audio()
audio.preload = 'metadata'

// Export so the store can call it directly after registerSeekFn registers it
export function seekTo(seconds: number) {
  audio.currentTime = seconds
}

// Track play duration for the current track
let _playStartTime: number | null = null
let _accumulatedTime = 0
let _currentItemId: number | null = null
let _historyPosted = false

function resetPlayTracking(itemId: number | null) {
  _playStartTime = null
  _accumulatedTime = 0
  _currentItemId = itemId
  _historyPosted = false
}

function onAudioPlay() {
  _playStartTime = Date.now()
}

function onAudioPause() {
  if (_playStartTime !== null) {
    _accumulatedTime += (Date.now() - _playStartTime) / 1000
    _playStartTime = null
  }
}

async function maybeRecordPlay() {
  // Accumulate any remaining time
  if (_playStartTime !== null) {
    _accumulatedTime += (Date.now() - _playStartTime) / 1000
    _playStartTime = null
  }

  if (_historyPosted || _currentItemId === null) return
  if (_accumulatedTime >= 30) {
    _historyPosted = true
    try {
      await recordPlay(_currentItemId, _accumulatedTime)
    } catch {
      // Non-critical — ignore failures silently
    }
  }
}

export function useAudioPlayer() {
  const playerStore = usePlayerStore()

  // Register our seek function into the store
  registerSeekFn(seekTo)

  // ── Audio event listeners ─────────────────────────────────────────────
  audio.addEventListener('timeupdate', () => {
    playerStore.setCurrentTime(audio.currentTime)

    // Record play once 30s of accumulated playback is reached
    if (
      !_historyPosted &&
      _currentItemId !== null &&
      audio.currentTime >= 30
    ) {
      maybeRecordPlay()
    }
  })

  audio.addEventListener('loadedmetadata', () => {
    playerStore.setDuration(audio.duration)
  })

  audio.addEventListener('ended', () => {
    maybeRecordPlay()
    playerStore.next()
  })

  audio.addEventListener('play', () => {
    playerStore.setIsPlaying(true)
    onAudioPlay()
  })

  audio.addEventListener('pause', () => {
    playerStore.setIsPlaying(false)
    onAudioPause()
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
      maybeRecordPlay()

      if (!url) {
        audio.pause()
        audio.src = ''
        playerStore.setIsBuffering(false)
        resetPlayTracking(null)
        return
      }

      resetPlayTracking(playerStore.currentTrack?.id ?? null)
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
