import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 10_000,
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    // Build a human-readable message
    let message: string
    if (error.response) {
      const detail = error.response.data?.detail
      const status = error.response.status
      const url = error.config?.url ?? ''
      message = detail
        ? `API ${status}: ${detail}`
        : `API error ${status} on ${url}`
      console.error(`[API] ${status} ${url}`, error.response.data)
    } else if (error.request) {
      message = `No response from server (${error.config?.url ?? ''})`
      console.error(`[API] No response for ${error.config?.url}`, error.message)
    } else {
      message = error.message ?? 'Unknown request error'
      console.error('[API] Request error', error.message)
    }

    // Lazy import to avoid circular dependency at module load time
    import('@/stores/notifications').then(({ useNotificationsStore }) => {
      try {
        useNotificationsStore().add(message)
      } catch {
        // Store not yet initialized (e.g. during app boot) — swallow silently
      }
    })

    return Promise.reject(error)
  },
)

export default client
