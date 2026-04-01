import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { QueueTrack, RepeatMode } from '@/types/player'

// seekTo is set by the useAudioPlayer composable after it initializes
// This avoids circular dependency: store needs to call seek on the audio element
let _seekTo: ((seconds: number) => void) | null = null

export function registerSeekFn(fn: (seconds: number) => void) {
  _seekTo = fn
}

function formatTime(seconds: number): string {
  if (!seconds || isNaN(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

export const usePlayerStore = defineStore('player', () => {
  // ── State ────────────────────────────────────────────────────────────────
  const currentTrack = ref<QueueTrack | null>(null)
  const queue = ref<QueueTrack[]>([])
  const queueIndex = ref(-1)
  const isPlaying = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)
  const volume = ref(0.8)
  const isMuted = ref(false)
  const repeatMode = ref<RepeatMode>('off')
  const shuffleEnabled = ref(false)
  const isBuffering = ref(false)

  // Tracks which indices have been played when shuffling so we don't repeat
  const shuffleHistory = ref<number[]>([])

  // ── Getters ──────────────────────────────────────────────────────────────
  const streamUrl = computed<string | null>(() =>
    currentTrack.value ? `/api/stream/${currentTrack.value.id}` : null,
  )

  const progress = computed<number>(() => {
    if (!duration.value) return 0
    return Math.min(100, (currentTime.value / duration.value) * 100)
  })

  const formattedCurrentTime = computed(() => formatTime(currentTime.value))
  const formattedDuration = computed(() => formatTime(duration.value))

  const hasNext = computed<boolean>(() => {
    if (!queue.value.length) return false
    if (repeatMode.value === 'one' || repeatMode.value === 'all') return true
    return queueIndex.value < queue.value.length - 1
  })

  const hasPrevious = computed<boolean>(() => {
    if (!queue.value.length) return false
    // Can always restart the current track if >0 seconds in
    if (currentTime.value > 3) return true
    return queueIndex.value > 0
  })

  // ── Actions ──────────────────────────────────────────────────────────────
  function _setTrackAtIndex(index: number) {
    if (index < 0 || index >= queue.value.length) return
    queueIndex.value = index
    currentTrack.value = queue.value[index]
    currentTime.value = 0
    duration.value = 0
    isPlaying.value = true
  }

  function playTrack(track: QueueTrack) {
    // If the track is already in the queue, jump to it
    const existing = queue.value.findIndex((t) => t.id === track.id)
    if (existing !== -1) {
      _setTrackAtIndex(existing)
      return
    }
    // Otherwise add it and play
    queue.value.push(track)
    _setTrackAtIndex(queue.value.length - 1)
  }

  function playAlbum(tracks: QueueTrack[], startIndex = 0) {
    queue.value = [...tracks]
    shuffleHistory.value = []
    _setTrackAtIndex(Math.max(0, Math.min(startIndex, tracks.length - 1)))
  }

  function addToQueue(track: QueueTrack) {
    queue.value.push(track)
  }

  function addToQueueNext(track: QueueTrack) {
    const insertAt = queueIndex.value + 1
    queue.value.splice(insertAt, 0, track)
  }

  function removeFromQueue(index: number) {
    if (index < 0 || index >= queue.value.length) return
    queue.value.splice(index, 1)
    if (index < queueIndex.value) {
      queueIndex.value--
    } else if (index === queueIndex.value) {
      // Removed the currently playing track
      if (queue.value.length === 0) {
        currentTrack.value = null
        queueIndex.value = -1
        isPlaying.value = false
        currentTime.value = 0
        duration.value = 0
      } else {
        const newIndex = Math.min(queueIndex.value, queue.value.length - 1)
        _setTrackAtIndex(newIndex)
      }
    }
  }

  function clearQueue() {
    queue.value = []
    queueIndex.value = -1
    currentTrack.value = null
    isPlaying.value = false
    currentTime.value = 0
    duration.value = 0
    shuffleHistory.value = []
  }

  function next() {
    if (!queue.value.length) return

    if (repeatMode.value === 'one') {
      // Restart current track
      seek(0)
      isPlaying.value = true
      return
    }

    if (shuffleEnabled.value) {
      const unplayed = queue.value
        .map((_, i) => i)
        .filter((i) => i !== queueIndex.value && !shuffleHistory.value.includes(i))

      if (unplayed.length > 0) {
        const pick = unplayed[Math.floor(Math.random() * unplayed.length)]
        shuffleHistory.value.push(queueIndex.value)
        _setTrackAtIndex(pick)
      } else if (repeatMode.value === 'all') {
        // Reset shuffle history and start over
        shuffleHistory.value = []
        const allExcept = queue.value.map((_, i) => i).filter((i) => i !== queueIndex.value)
        if (allExcept.length > 0) {
          shuffleHistory.value.push(queueIndex.value)
          _setTrackAtIndex(allExcept[Math.floor(Math.random() * allExcept.length)])
        }
      } else {
        // End of queue
        isPlaying.value = false
      }
      return
    }

    const nextIndex = queueIndex.value + 1
    if (nextIndex < queue.value.length) {
      _setTrackAtIndex(nextIndex)
    } else if (repeatMode.value === 'all') {
      _setTrackAtIndex(0)
    } else {
      isPlaying.value = false
    }
  }

  function previous() {
    if (!queue.value.length) return

    // If more than 3 seconds in, restart current track
    if (currentTime.value > 3) {
      seek(0)
      return
    }

    if (shuffleEnabled.value && shuffleHistory.value.length > 0) {
      const prevIndex = shuffleHistory.value.pop()!
      queueIndex.value = prevIndex
      currentTrack.value = queue.value[prevIndex]
      currentTime.value = 0
      duration.value = 0
      isPlaying.value = true
      return
    }

    const prevIndex = queueIndex.value - 1
    if (prevIndex >= 0) {
      _setTrackAtIndex(prevIndex)
    } else if (repeatMode.value === 'all') {
      _setTrackAtIndex(queue.value.length - 1)
    } else {
      seek(0)
    }
  }

  function seek(seconds: number) {
    currentTime.value = seconds
    _seekTo?.(seconds)
  }

  function setVolume(v: number) {
    volume.value = Math.max(0, Math.min(1, v))
    if (v > 0) isMuted.value = false
  }

  function toggleMute() {
    isMuted.value = !isMuted.value
  }

  function toggleShuffle() {
    shuffleEnabled.value = !shuffleEnabled.value
    shuffleHistory.value = []
  }

  function cycleRepeat() {
    const modes: RepeatMode[] = ['off', 'all', 'one']
    const current = modes.indexOf(repeatMode.value)
    repeatMode.value = modes[(current + 1) % modes.length]
  }

  // Called by the composable to sync audio element state
  function setCurrentTime(t: number) {
    currentTime.value = t
  }

  function setDuration(d: number) {
    duration.value = d
  }

  function setIsPlaying(v: boolean) {
    isPlaying.value = v
  }

  function jumpToIndex(index: number) {
    if (index >= 0 && index < queue.value.length) {
      _setTrackAtIndex(index)
    }
  }

  function setIsBuffering(v: boolean) {
    isBuffering.value = v
  }

  return {
    // State
    currentTrack,
    queue,
    queueIndex,
    isPlaying,
    isBuffering,
    currentTime,
    duration,
    volume,
    isMuted,
    repeatMode,
    shuffleEnabled,
    // Getters
    streamUrl,
    progress,
    formattedCurrentTime,
    formattedDuration,
    hasNext,
    hasPrevious,
    // Actions
    playTrack,
    playAlbum,
    addToQueue,
    addToQueueNext,
    removeFromQueue,
    clearQueue,
    next,
    previous,
    seek,
    setVolume,
    toggleMute,
    toggleShuffle,
    cycleRepeat,
    setCurrentTime,
    setDuration,
    setIsPlaying,
    setIsBuffering,
    jumpToIndex,
  }
})
