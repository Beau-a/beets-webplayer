import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 10_000,
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error(`[API] ${error.response.status} ${error.config?.url}`, error.response.data)
    } else if (error.request) {
      console.error(`[API] No response for ${error.config?.url}`, error.message)
    } else {
      console.error('[API] Request error', error.message)
    }
    return Promise.reject(error)
  },
)

export default client
