import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Notification {
  id: number
  message: string
  timestamp: number
  read: boolean
}

let _nextId = 1

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])

  const unreadCount = computed(() =>
    notifications.value.filter((n) => !n.read).length,
  )

  function add(message: string) {
    notifications.value.unshift({
      id: _nextId++,
      message,
      timestamp: Date.now(),
      read: false,
    })
    // Keep max 20
    if (notifications.value.length > 20) {
      notifications.value = notifications.value.slice(0, 20)
    }
  }

  function markAllRead() {
    notifications.value.forEach((n) => {
      n.read = true
    })
  }

  function clear() {
    notifications.value = []
  }

  return {
    notifications,
    unreadCount,
    add,
    markAllRead,
    clear,
  }
})
