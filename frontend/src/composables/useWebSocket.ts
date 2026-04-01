import { ref } from 'vue'

export interface UseWebSocketOptions {
  onMessage: (type: string, payload: unknown) => void
  onConnect?: () => void
  onDisconnect?: () => void
  reconnectDelay?: number  // base ms, doubles each attempt, max 30s
  maxReconnects?: number   // default 5, 0 = unlimited
}

export function useWebSocket(url: string, options: UseWebSocketOptions) {
  const isConnected = ref(false)

  let ws: WebSocket | null = null
  let reconnectCount = 0
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let manualDisconnect = false

  const baseDelay = options.reconnectDelay ?? 1000
  const maxReconnects = options.maxReconnects ?? 5

  function getReconnectDelay(): number {
    const delay = baseDelay * Math.pow(2, reconnectCount)
    return Math.min(delay, 30_000)
  }

  function connect(): void {
    manualDisconnect = false
    _connect()
  }

  function _connect(): void {
    if (ws) {
      ws.onopen = null
      ws.onmessage = null
      ws.onclose = null
      ws.onerror = null
      ws.close()
      ws = null
    }

    try {
      ws = new WebSocket(url)
    } catch (err) {
      console.error('[useWebSocket] Failed to create WebSocket', err)
      scheduleReconnect()
      return
    }

    ws.onopen = () => {
      isConnected.value = true
      reconnectCount = 0
      options.onConnect?.()
    }

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string) as { type: string; payload: unknown }
        options.onMessage(data.type, data.payload)
      } catch (err) {
        console.warn('[useWebSocket] Failed to parse message', event.data, err)
      }
    }

    ws.onclose = () => {
      isConnected.value = false
      ws = null
      options.onDisconnect?.()
      if (!manualDisconnect) {
        scheduleReconnect()
      }
    }

    ws.onerror = (event) => {
      console.error('[useWebSocket] WebSocket error', event)
      // onclose will fire after onerror, reconnect handled there
    }
  }

  function scheduleReconnect(): void {
    if (manualDisconnect) return
    if (maxReconnects > 0 && reconnectCount >= maxReconnects) {
      console.warn('[useWebSocket] Max reconnect attempts reached')
      return
    }
    const delay = getReconnectDelay()
    console.log(`[useWebSocket] Reconnecting in ${delay}ms (attempt ${reconnectCount + 1})`)
    reconnectTimer = setTimeout(() => {
      reconnectCount++
      _connect()
    }, delay)
  }

  function disconnect(): void {
    manualDisconnect = true
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws) {
      ws.onopen = null
      ws.onmessage = null
      ws.onclose = null
      ws.onerror = null
      ws.close()
      ws = null
    }
    isConnected.value = false
  }

  function send(type: string, payload?: unknown): void {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('[useWebSocket] Cannot send — socket not open')
      return
    }
    ws.send(JSON.stringify({ type, payload }))
  }

  return { isConnected, connect, disconnect, send }
}
