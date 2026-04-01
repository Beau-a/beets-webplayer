<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar-inner">
      <!-- Logo / brand -->
      <div class="sidebar-logo">
        <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="9" cy="18" r="3"/>
          <circle cx="18" cy="15" r="3"/>
          <polyline points="12 18 12 2 21 5 21 9"/>
          <line x1="12" y1="10" x2="12" y2="18"/>
        </svg>
        <span v-if="!collapsed" class="logo-text">beets</span>
      </div>

      <!-- Nav links -->
      <nav class="sidebar-nav">
        <!-- Library: icon navigates when expanded; whole row toggles flyout when collapsed -->
        <div
          class="nav-link library-nav-item"
          :class="{ 'nav-link-active': isLibraryActive, 'flyout-open': flyoutOpen }"
        >
          <template v-if="collapsed">
            <!-- Collapsed: clicking the icon toggles flyout -->
            <button class="library-icon-btn" @click="$emit('toggle-flyout')" title="Browse artists">
              <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7"/>
                <rect x="14" y="3" width="7" height="7"/>
                <rect x="3" y="14" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/>
              </svg>
            </button>
          </template>
          <template v-else>
            <!-- Expanded: icon+label navigate; chevron toggles flyout -->
            <RouterLink to="/library" class="library-main-link">
              <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7"/>
                <rect x="14" y="3" width="7" height="7"/>
                <rect x="3" y="14" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/>
              </svg>
              <span class="nav-label">Library</span>
            </RouterLink>
            <button
              class="library-flyout-btn"
              :class="{ active: flyoutOpen }"
              @click="$emit('toggle-flyout')"
              title="Browse by artist"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="flyout-chevron" :class="{ rotated: flyoutOpen }">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </button>
          </template>
        </div>

        <RouterLink to="/search" class="nav-link" active-class="nav-link-active" title="Search">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <span v-if="!collapsed" class="nav-label">Search</span>
        </RouterLink>

        <RouterLink to="/import" class="nav-link" active-class="nav-link-active" title="Import">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          <span v-if="!collapsed" class="nav-label">Import</span>
        </RouterLink>

        <RouterLink to="/queue" class="nav-link" active-class="nav-link-active" title="Queue">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="8" y1="6" x2="21" y2="6"/>
            <line x1="8" y1="12" x2="21" y2="12"/>
            <line x1="8" y1="18" x2="21" y2="18"/>
            <line x1="3" y1="6" x2="3.01" y2="6"/>
            <line x1="3" y1="12" x2="3.01" y2="12"/>
            <line x1="3" y1="18" x2="3.01" y2="18"/>
          </svg>
          <span v-if="!collapsed" class="nav-label">Queue</span>
        </RouterLink>

        <RouterLink to="/settings" class="nav-link" active-class="nav-link-active" title="Settings">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          <span v-if="!collapsed" class="nav-label">Settings</span>
        </RouterLink>
      </nav>

      <!-- Collapse toggle -->
      <button class="collapse-btn" @click="$emit('toggle')" :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline v-if="collapsed" points="9 18 15 12 9 6"/>
          <polyline v-else points="15 18 9 12 15 6"/>
        </svg>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const props = defineProps<{
  collapsed: boolean
  flyoutOpen: boolean
}>()

defineEmits<{
  toggle: []
  'toggle-flyout': []
}>()

const route = useRoute()
const isLibraryActive = computed(() => route.path === '/library' || route.path.startsWith('/library'))
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 200px;
  background-color: #09090b; /* zinc-950 */
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width 0.2s ease;
}

.sidebar.collapsed {
  width: 56px;
}

.sidebar-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px 0;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px 16px;
  color: #a78bfa; /* violet-400 */
  overflow: hidden;
}

.logo-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 8px;
  border-radius: 8px;
  color: #71717a; /* zinc-500 */
  text-decoration: none;
  transition: background-color 0.15s, color 0.15s;
  overflow: hidden;
  white-space: nowrap;
}

.nav-link:hover {
  background-color: #27272a; /* zinc-800 */
  color: #d4d4d8; /* zinc-300 */
}

.nav-link-active {
  border-left: 2px solid #7c3aed;
  padding-left: 6px;
  color: #a78bfa; /* violet-400 */
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

/* Library nav item — custom layout to host a link + flyout toggle */
.library-nav-item {
  display: flex;
  align-items: center;
  padding: 0;
  gap: 0;
  cursor: default;
}

.library-nav-item.flyout-open {
  background-color: #2d2d35;
}

.library-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px 8px;
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  border-radius: 8px;
}

.library-main-link {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  padding: 10px 8px;
  text-decoration: none;
  color: inherit;
  overflow: hidden;
  white-space: nowrap;
  border-radius: 8px 0 0 8px;
  transition: background-color 0.15s, color 0.15s;
  min-width: 0;
}

.library-main-link:hover {
  background-color: #27272a;
  color: #d4d4d8;
}

.library-flyout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding: 10px 6px 10px 4px;
  background: none;
  border: none;
  cursor: pointer;
  color: #52525b;
  border-radius: 0 8px 8px 0;
  transition: color 0.15s, background-color 0.15s;
}

.library-flyout-btn:hover {
  color: #a1a1aa;
  background-color: #27272a;
}

.library-flyout-btn.active {
  color: #a78bfa;
}

.flyout-chevron {
  width: 14px;
  height: 14px;
  transition: transform 0.2s ease;
}

.flyout-chevron.rotated {
  transform: rotate(90deg);
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 8px;
  padding: 8px;
  border-radius: 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #52525b; /* zinc-600 */
  transition: background-color 0.15s, color 0.15s;
}

.collapse-btn:hover {
  background-color: #27272a;
  color: #a1a1aa; /* zinc-400 */
}
</style>
