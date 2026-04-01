<template>
  <div class="app-layout" :style="{ '--sidebar-w': sidebarCollapsed ? '56px' : '200px' }">
    <AppSidebar
      :collapsed="sidebarCollapsed"
      :flyout-open="flyoutOpen"
      @toggle="toggleSidebar"
      @toggle-flyout="flyoutOpen = !flyoutOpen"
    />

    <ArtistBrowser
      :visible="flyoutOpen"
      :sidebar-collapsed="sidebarCollapsed"
      @close="flyoutOpen = false"
    />

    <div class="main-wrapper" :style="{ marginLeft: mainMargin }">
      <main class="main-content">
        <RouterView />
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
import { ref, computed } from 'vue'
import { RouterView } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import ArtistBrowser from './ArtistBrowser.vue'
import PlayerBar from './PlayerBar.vue'
import QueueDrawer from '@/components/player/QueueDrawer.vue'

const sidebarCollapsed = ref(localStorage.getItem('sidebar.collapsed') === 'true')
const queueOpen = ref(false)
const flyoutOpen = ref(false)

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar.collapsed', String(sidebarCollapsed.value))
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

</script>

<style scoped>
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

.main-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 72px;
}

.player-bar-shell {
  position: fixed;
  bottom: 0;
  right: 0;
  height: 72px;
  background-color: #09090b; /* zinc-950 */
  border-top: 1px solid #27272a; /* zinc-800 */
  z-index: 50;
  transition: left 0.2s ease;
}
</style>
