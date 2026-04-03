<template>
  <div class="notif-bell-wrapper" ref="wrapperRef">
    <button
      class="bell-btn"
      :class="{ 'bell-btn-active': open }"
      :aria-label="`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`"
      @click="toggleOpen"
    >
      <!-- Bell SVG -->
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="bell-icon">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
      <!-- Unread badge -->
      <span v-if="unreadCount > 0" class="bell-badge">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
    </button>

    <!-- Dropdown panel -->
    <Transition name="notif-drop">
      <div v-if="open" class="notif-panel">
        <div class="notif-header">
          <span class="notif-title">Notifications</span>
          <button v-if="notifications.length > 0" class="notif-clear-btn" @click="onClear">
            Clear all
          </button>
        </div>

        <div v-if="notifications.length === 0" class="notif-empty">
          No notifications
        </div>

        <ul v-else class="notif-list">
          <li
            v-for="n in notifications"
            :key="n.id"
            class="notif-item"
            :class="{ 'notif-item-unread': !n.read }"
          >
            <span class="notif-msg">{{ n.message }}</span>
            <span class="notif-time">{{ formatTime(n.timestamp) }}</span>
          </li>
        </ul>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useNotificationsStore } from '@/stores/notifications'

const store = useNotificationsStore()
const notifications = computed(() => store.notifications)
const unreadCount = computed(() => store.unreadCount)

const open = ref(false)
const wrapperRef = ref<HTMLElement | null>(null)

function toggleOpen() {
  open.value = !open.value
  if (open.value) {
    store.markAllRead()
  }
}

function onClear() {
  store.clear()
  open.value = false
}

function formatTime(ts: number): string {
  const d = new Date(ts)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60_000)
  if (diffMin < 1) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}h ago`
  return d.toLocaleDateString()
}

function onDocClick(e: MouseEvent) {
  if (open.value && wrapperRef.value && !wrapperRef.value.contains(e.target as Node)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', onDocClick))
onUnmounted(() => document.removeEventListener('mousedown', onDocClick))
</script>

<style scoped>
.notif-bell-wrapper {
  position: relative;
}

.bell-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  background: transparent;
  color: #71717a;
  border-radius: 8px;
  cursor: pointer;
  transition: color 0.15s, background-color 0.15s;
  flex-shrink: 0;
}

.bell-btn:hover {
  color: #d4d4d8;
  background-color: #27272a;
}

.bell-btn-active {
  color: #a78bfa;
  background-color: #27272a;
}

.bell-icon {
  width: 18px;
  height: 18px;
}

.bell-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 16px;
  height: 16px;
  padding: 0 3px;
  border-radius: 8px;
  background-color: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  pointer-events: none;
}

/* Dropdown panel */
.notif-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 320px;
  max-height: 400px;
  background-color: #18181b;
  border: 1px solid #27272a;
  border-radius: 10px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6);
  z-index: 200;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.notif-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px 10px;
  border-bottom: 1px solid #27272a;
  flex-shrink: 0;
}

.notif-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: #f4f4f5;
}

.notif-clear-btn {
  font-size: var(--text-sm);
  color: #71717a;
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: color 0.15s, background-color 0.15s;
}

.notif-clear-btn:hover {
  color: #d4d4d8;
  background-color: #27272a;
}

.notif-empty {
  padding: 24px;
  text-align: center;
  color: #52525b;
  font-size: var(--text-sm);
}

.notif-list {
  list-style: none;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  max-height: 340px;
}

.notif-list::-webkit-scrollbar {
  width: 4px;
}
.notif-list::-webkit-scrollbar-thumb {
  background-color: #3f3f46;
  border-radius: 2px;
}

.notif-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 14px;
  border-bottom: 1px solid #1f1f23;
  transition: background-color 0.12s;
}

.notif-item:last-child {
  border-bottom: none;
}

.notif-item:hover {
  background-color: #27272a;
}

.notif-item-unread {
  background-color: rgba(124, 58, 237, 0.06);
}

.notif-msg {
  font-size: var(--text-sm);
  color: #d4d4d8;
  line-height: 1.4;
  word-break: break-word;
}

.notif-time {
  font-size: var(--text-xs);
  color: #52525b;
}

/* Dropdown animation */
.notif-drop-enter-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.notif-drop-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}
.notif-drop-enter-from,
.notif-drop-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
