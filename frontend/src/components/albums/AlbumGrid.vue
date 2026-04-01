<template>
  <div class="album-grid-wrapper">
    <!-- Loading skeleton -->
    <div v-if="loading" class="album-grid">
      <div v-for="(n, index) in skeletonCount" :key="n" class="skeleton-card">
        <div class="skeleton-art" :style="{ animationDelay: Math.min(index * 0.05, 0.8) + 's' }"></div>
        <div class="skeleton-meta" :style="{ '--delay': Math.min(index * 0.05, 0.8) + 's' }">
          <div class="skeleton-line skeleton-title"></div>
          <div class="skeleton-line skeleton-artist"></div>
          <div class="skeleton-footer">
            <div class="skeleton-line skeleton-year"></div>
            <div class="skeleton-line skeleton-badge"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Populated grid -->
    <div v-else-if="albums.length > 0" class="album-grid">
      <AlbumCard v-for="album in albums" :key="album.id" :album="album" />
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
        <circle cx="9" cy="18" r="3"/>
        <circle cx="18" cy="15" r="3"/>
        <polyline points="12 18 12 2 21 5 21 9"/>
        <line x1="12" y1="10" x2="12" y2="18"/>
      </svg>
      <p class="empty-text">No albums found</p>
      <p class="empty-subtext">Try adjusting your search or filters</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import AlbumCard from './AlbumCard.vue'
import type { AlbumSummary } from '@/types/album'

defineProps<{
  albums: AlbumSummary[]
  loading: boolean
}>()

const skeletonCount = 24
</script>

<style scoped>
.album-grid-wrapper {
  width: 100%;
}

.album-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
  padding: 4px 2px;
}

/* Skeleton cards */
.skeleton-card {
  width: 100%;
  background-color: #27272a;
  border-radius: 10px;
  overflow: hidden;
}

.skeleton-art {
  width: 100%;
  aspect-ratio: 1 / 1;
  background: linear-gradient(90deg, #3f3f46 25%, #52525b 50%, #3f3f46 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-meta {
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.skeleton-line {
  border-radius: 4px;
  background: linear-gradient(90deg, #3f3f46 25%, #52525b 50%, #3f3f46 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  animation-delay: var(--delay, 0s);
}

.skeleton-title {
  height: 12px;
  width: 80%;
}

.skeleton-artist {
  height: 11px;
  width: 60%;
}

.skeleton-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}

.skeleton-year {
  height: 10px;
  width: 28%;
}

.skeleton-badge {
  height: 16px;
  width: 36px;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 24px;
  gap: 12px;
}

.empty-icon {
  width: 56px;
  height: 56px;
  color: #3f3f46; /* zinc-700 */
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: #71717a; /* zinc-500 */
  margin: 0;
}

.empty-subtext {
  font-size: 13px;
  color: #52525b; /* zinc-600 */
  margin: 0;
}
</style>
