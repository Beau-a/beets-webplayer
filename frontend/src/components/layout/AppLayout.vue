<template>
  <div class="app-layout" :style="{ '--sidebar-w': sidebarCollapsed ? '56px' : '200px' }">
    <AppSidebar
      :collapsed="sidebarCollapsed"
      :active-letter="activeLetter"
      @toggle="toggleSidebar"
      @select-letter="onSelectLetter"
    />

    <ArtistBrowser
      :visible="flyoutOpen"
      :sidebar-collapsed="sidebarCollapsed"
      :active-letter="activeLetter"
      @close="closeFlyout"
    />

    <div class="main-wrapper" :style="{ marginLeft: mainMargin }">
      <!-- Top bar with notification bell -->
      <div class="app-topbar">
        <div class="topbar-right">
          <NotificationBell />
        </div>
      </div>

      <main class="main-content">
        <RouterView v-slot="{ Component }">
          <Transition name="fade">
            <component :is="Component" :key="$route.path" />
          </Transition>
        </RouterView>
      </main>

      <!-- Real player bar -->
      <div class="player-bar-shell" :style="{ left: playerBarLeft }">
        <PlayerBar :queue-open="queueOpen" @toggle-queue="queueOpen = !queueOpen" />
      </div>
    </div>

    <!-- Queue drawer -->
    <QueueDrawer v-model="queueOpen" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watchEffect } from 'vue'
import { RouterView } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import ArtistBrowser from './ArtistBrowser.vue'
import PlayerBar from './PlayerBar.vue'
import NotificationBell from './NotificationBell.vue'
import QueueDrawer from '@/components/player/QueueDrawer.vue'

const sidebarCollapsed = ref(localStorage.getItem('sidebar.collapsed') === 'true')
const queueOpen = ref(false)
const activeLetter = ref('')

const flyoutOpen = computed(() => activeLetter.value !== '')

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar.collapsed', String(sidebarCollapsed.value))
}

function onSelectLetter(letter: string) {
  // Toggle: clicking the active letter closes the flyout
  activeLetter.value = activeLetter.value === letter ? '' : letter
}

function closeFlyout() {
  activeLetter.value = ''
}

const sidebarWidth = computed(() => sidebarCollapsed.value ? 56 : 200)
const flyoutWidth = 220

const mainMargin = computed(() => {
  const base = sidebarWidth.value
  const extra = flyoutOpen.value ? flyoutWidth : 0
  return `${base + extra}px`
})

const playerBarLeft = computed(() => {
  const base = sidebarWidth.value
  const extra = flyoutOpen.value ? flyoutWidth : 0
  return `${base + extra}px`
})

// Expose sidebar width to :root so teleported overlays (import, etc.) can use it
watchEffect(() => {
  document.documentElement.style.setProperty('--sidebar-w', `${sidebarWidth.value}px`)
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: margin-left 0.2s ease;
}

/* Top bar */
.app-topbar {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 14px;
  flex-shrink: 0;
  border-bottom: 1px solid #1c1c1f;
  background-color: #09090b;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 72px;
  padding-top: 0;
}

.player-bar-shell {
  position: fixed;
  bottom: 0;
  right: 0;
  height: 72px;
  background-color: #09090b;
  border-top: 1px solid #27272a;
  z-index: 50;
  transition: left 0.2s ease;
}
</style>
