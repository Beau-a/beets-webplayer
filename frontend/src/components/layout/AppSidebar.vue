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
        <!-- Library row + inline letter drop-under -->
        <div class="library-section">
          <div
            class="nav-link library-nav-item"
            :class="{ 'nav-link-active': isLibraryActive, 'letters-open': lettersOpen }"
          >
            <template v-if="collapsed">
              <!-- Collapsed: Library icon is a plain nav link -->
              <RouterLink to="/library" class="library-icon-btn" title="Library" aria-label="Library">
                <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="7" height="7"/>
                  <rect x="14" y="3" width="7" height="7"/>
                  <rect x="3" y="14" width="7" height="7"/>
                  <rect x="14" y="14" width="7" height="7"/>
                </svg>
              </RouterLink>
            </template>
            <template v-else>
              <!-- Expanded: label navigates, chevron toggles letter drop-under -->
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
                :class="{ active: lettersOpen }"
                @click="toggleLetters"
                title="Browse by artist"
                aria-label="Browse by artist"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="flyout-chevron" :class="{ rotated: lettersOpen }">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </button>
            </template>
          </div>

          <!-- A–Z drop-under (expanded mode only) -->
          <Transition name="letters-drop">
            <div v-if="lettersOpen && !collapsed" class="letters-panel">
              <div class="letters-grid">
                <button
                  v-for="l in LETTERS"
                  :key="l"
                  class="letter-btn"
                  :class="{
                    'letter-active': activeLetter === l,
                    'letter-dim': !activeLetters.includes(l),
                  }"
                  @click="onLetterClick(l)"
                >
                  {{ l }}
                </button>
              </div>
            </div>
          </Transition>
        </div>

        <RouterLink to="/player" class="nav-link" active-class="nav-link-active" title="Player">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="8" y1="6" x2="21" y2="6"/>
            <line x1="8" y1="12" x2="21" y2="12"/>
            <line x1="8" y1="18" x2="21" y2="18"/>
            <line x1="3" y1="6" x2="3.01" y2="6"/>
            <line x1="3" y1="12" x2="3.01" y2="12"/>
            <line x1="3" y1="18" x2="3.01" y2="18"/>
          </svg>
          <span v-if="!collapsed" class="nav-label">Player</span>
        </RouterLink>

        <RouterLink to="/tools" class="nav-link" active-class="nav-link-active" title="Tools">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
          </svg>
          <span v-if="!collapsed" class="nav-label">Tools</span>
        </RouterLink>
      </nav>

      <!-- Collapse toggle -->
      <button class="collapse-btn" @click="$emit('toggle')" :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'" :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline v-if="collapsed" points="9 18 15 12 9 6"/>
          <polyline v-else points="15 18 9 12 15 6"/>
        </svg>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { fetchArtistLetters } from '@/api/library'

const props = defineProps<{
  collapsed: boolean
  activeLetter: string
}>()

const emit = defineEmits<{
  toggle: []
  'select-letter': [letter: string]
}>()

const route = useRoute()
const isLibraryActive = computed(() => route.path === '/library' || route.path.startsWith('/library'))

const LETTERS = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','#']
const lettersOpen = ref(false)
const activeLetters = ref<string[]>([])

async function loadLetters() {
  try {
    activeLetters.value = await fetchArtistLetters()
  } catch {
    activeLetters.value = []
  }
}

function toggleLetters() {
  lettersOpen.value = !lettersOpen.value
  if (lettersOpen.value && activeLetters.value.length === 0) loadLetters()
}

function onLetterClick(letter: string) {
  emit('select-letter', letter)
}

// Close drop-under when sidebar collapses
watch(() => props.collapsed, (val) => {
  if (val) lettersOpen.value = false
})

onMounted(loadLetters)
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 200px;
  background-color: #09090b;
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
  color: #a78bfa;
  overflow: hidden;
}

.logo-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}

.logo-text {
  font-size: var(--text-lg);
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
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: none;
}

.sidebar-nav::-webkit-scrollbar { width: 0; }

/* Library section */
.library-section {
  display: flex;
  flex-direction: column;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 8px;
  border-radius: 8px;
  color: #71717a;
  text-decoration: none;
  transition: background-color 0.15s, color 0.15s;
  overflow: hidden;
  white-space: nowrap;
  flex-shrink: 0;
}

.nav-link:hover {
  background-color: #27272a;
  color: #d4d4d8;
}

.nav-link-active {
  border-left: 2px solid #7c3aed;
  padding-left: 6px;
  color: #a78bfa;
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-label {
  font-size: var(--text-md);
  font-weight: 500;
}

.library-nav-item {
  display: flex;
  align-items: center;
  padding: 0;
  gap: 0;
  cursor: default;
  border-radius: 8px 8px 0 0;
}

.library-nav-item.letters-open {
  background-color: #1c1c1f;
}

.library-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px 8px;
  text-decoration: none;
  color: #71717a;
  border-radius: 8px;
  transition: background-color 0.15s, color 0.15s;
}

.library-icon-btn:hover {
  background-color: #27272a;
  color: #d4d4d8;
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
  transition: transform 0.25s ease;
}

.flyout-chevron.rotated {
  transform: rotate(90deg);
}

/* Inline letter drop-under */
.letters-panel {
  overflow: hidden;
  background-color: #111113;
  border-radius: 0 0 8px 8px;
  border-top: 1px solid #1f1f23;
  margin-bottom: 2px;
}

.letters-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  padding: 8px 6px 10px;
}

.letter-btn {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  border-radius: 5px;
  border: none;
  background: none;
  color: #71717a;
  cursor: pointer;
  transition: background-color 0.12s, color 0.12s;
  flex-shrink: 0;
}

.letter-btn:hover:not(.letter-dim) {
  background-color: #27272a;
  color: #d4d4d8;
}

.letter-active {
  background-color: #5b21b6 !important;
  color: #ede9fe !important;
}

.letter-dim {
  opacity: 0.25;
  cursor: default;
  pointer-events: none;
}

/* Drop-under transition — animates max-height so nav items shift smoothly */
.letters-drop-enter-active {
  transition: max-height 0.25s ease, opacity 0.2s ease;
  overflow: hidden;
  max-height: 200px;
}
.letters-drop-leave-active {
  transition: max-height 0.2s ease, opacity 0.15s ease;
  overflow: hidden;
  max-height: 200px;
}
.letters-drop-enter-from,
.letters-drop-leave-to {
  max-height: 0 !important;
  opacity: 0;
}

/* Collapse toggle */
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
  color: #52525b;
  transition: background-color 0.15s, color 0.15s;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background-color: #27272a;
  color: #a1a1aa;
}
</style>
