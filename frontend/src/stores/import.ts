import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { startImport as apiStartImport, type ImportStartOptions } from '@/api/library'
import type {
  ImportSessionState,
  ImportCandidate,
  CandidatesPayload,
  NoCandidatesPayload,
  ImportLogEntry,
  ImportProgress,
  ImportChoice,
  ImportSessionSummary,
} from '@/types/import'

export const useImportStore = defineStore('import', () => {
  // State
  const sessionState = ref<ImportSessionState>('idle')
  const sessionId = ref<string | null>(null)
  const wsConnected = ref(false)
  const currentAlbumPath = ref<string | null>(null)
  const candidates = ref<ImportCandidate[]>([])
  const candidatesPayload = ref<CandidatesPayload | null>(null)
  const selectedCandidateIndex = ref<number>(0)
  const noCandidatesPayload = ref<NoCandidatesPayload | null>(null)
  const importLog = ref<ImportLogEntry[]>([])
  const importedAlbumIds = ref<number[]>([])
  const progress = reactive<ImportProgress>({
    completed: 0,
    total: 0,
    currentPath: '',
  })
  const error = ref<string | null>(null)
  const directory = ref<string>('')
  const sessionSummary = ref<ImportSessionSummary | null>(null)

  // WebSocket instance (held in module scope so it persists)
  let ws: ReturnType<typeof useWebSocket> | null = null

  // Actions
  async function startImport(dir: string, options: ImportStartOptions = {}) {
    error.value = null
    directory.value = dir
    sessionState.value = 'connecting'
    importLog.value = []
    importedAlbumIds.value = []
    progress.completed = 0
    progress.total = 0
    progress.currentPath = ''
    sessionSummary.value = null

    try {
      const result = await apiStartImport(dir, options)
      sessionId.value = result.session_id
      connectWebSocket(result.ws_url)
    } catch (err: unknown) {
      if (
        err &&
        typeof err === 'object' &&
        'response' in err &&
        (err as { response?: { status?: number } }).response?.status === 409
      ) {
        error.value = 'Import already in progress'
      } else {
        error.value = 'Failed to start import session'
        console.error('[import] startImport failed', err)
      }
      sessionState.value = 'error'
    }
  }

  function connectWebSocket(wsUrl: string) {
    // Build absolute WebSocket URL
    let absoluteUrl: string
    if (wsUrl.startsWith('ws://') || wsUrl.startsWith('wss://')) {
      absoluteUrl = wsUrl
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      absoluteUrl = `${protocol}//${window.location.host}${wsUrl}`
    }

    ws = useWebSocket(absoluteUrl, {
      onMessage: handleMessage,
      onConnect: () => {
        wsConnected.value = true
      },
      onDisconnect: () => {
        wsConnected.value = false
      },
      reconnectDelay: 1000,
      maxReconnects: 5,
    })

    ws.connect()
  }

  function handleMessage(type: string, payload: unknown) {
    console.log('[import WS]', type, 'state=', sessionState.value, payload)
    switch (type) {
      case 'connected':
        // WebSocket handshake confirmed
        break

      case 'session_start': {
        const p = payload as { estimated_albums: number }
        progress.total = p.estimated_albums || 0
        sessionState.value = 'running'
        break
      }

      case 'album_start': {
        const p = payload as { path: string }
        progress.currentPath = p.path
        currentAlbumPath.value = p.path
        break
      }

      case 'candidates': {
        const p = payload as CandidatesPayload
        candidatesPayload.value = p
        candidates.value = p.candidates
        // Auto-select first candidate; if rec=strong auto-select index 0 (still requires explicit confirm)
        selectedCandidateIndex.value = 0
        sessionState.value = 'waiting_choice'
        break
      }

      case 'no_candidates': {
        const p = payload as NoCandidatesPayload
        noCandidatesPayload.value = p
        sessionState.value = 'waiting_no_candidates'
        break
      }

      case 'album_imported': {
        const p = payload as { album_id: number; album: string; artist: string; year: number; track_count: number }
        if (p.album_id) importedAlbumIds.value.push(p.album_id)
        importLog.value.push({
          type: 'imported',
          path: progress.currentPath,
          album_id: p.album_id,
          album: p.album,
          artist: p.artist,
          year: p.year,
        })
        progress.completed++
        // Only leave waiting_choice if this event is for the current album being decided.
        // If sessionState is waiting_choice it means the user is still making a choice —
        // don't hide the candidate panel just because an earlier album finished importing.
        if (sessionState.value === 'running') {
          // already running, no state change needed
        }
        break
      }

      case 'album_skipped': {
        const p = payload as { path: string; reason?: string }
        importLog.value.push({
          type: 'skipped',
          path: p.path,
          message: p.reason,
        })
        progress.completed++
        // Same rationale: don't collapse candidate view for a skip of an earlier album
        break
      }

      case 'item_moved':
        // No UI update needed; progress events cover this
        break

      case 'error': {
        const p = payload as { path: string; message: string }
        importLog.value.push({
          type: 'error',
          path: p.path,
          message: p.message,
        })
        progress.completed++
        break
      }

      case 'session_complete': {
        const p = payload as {
          total_imported: number
          total_skipped: number
          total_errors: number
          duration_s: number
        }
        sessionSummary.value = {
          total_imported: p.total_imported,
          total_skipped: p.total_skipped,
          total_errors: p.total_errors,
          duration_s: p.duration_s,
        }
        sessionState.value = 'complete'
        ws?.disconnect()
        break
      }

      case 'heartbeat':
        // Keepalive — no action needed
        break

      default:
        console.warn('[import] Unknown WS message type:', type)
    }
  }

  function submitChoice(choice: ImportChoice) {
    if (!ws) {
      console.warn('[import] No WebSocket to send choice')
      return
    }
    ws.send('choice', choice)
    candidates.value = []
    candidatesPayload.value = null
    noCandidatesPayload.value = null
    sessionState.value = 'running'
  }

  function selectCandidate(index: number) {
    selectedCandidateIndex.value = index
  }

  function abortImport() {
    submitChoice({ action: 'abort' })
    sessionState.value = 'error'
    error.value = 'Import aborted by user'
    ws?.disconnect()
  }

  function resetSession() {
    ws?.disconnect()
    ws = null
    sessionState.value = 'idle'
    sessionId.value = null
    wsConnected.value = false
    currentAlbumPath.value = null
    candidates.value = []
    candidatesPayload.value = null
    noCandidatesPayload.value = null
    selectedCandidateIndex.value = 0
    importLog.value = []
    importedAlbumIds.value = []
    progress.completed = 0
    progress.total = 0
    progress.currentPath = ''
    error.value = null
    directory.value = ''
    sessionSummary.value = null
  }

  return {
    // State
    sessionState,
    sessionId,
    wsConnected,
    currentAlbumPath,
    candidates,
    candidatesPayload,
    noCandidatesPayload,
    selectedCandidateIndex,
    importLog,
    importedAlbumIds,
    progress,
    error,
    directory,
    sessionSummary,
    // Actions
    startImport,
    connectWebSocket,
    handleMessage,
    submitChoice,
    selectCandidate,
    abortImport,
    resetSession,
  }
})
