<template>
  <div class="home-view">
    <div class="home-header">
      <h1 class="home-title">Home</h1>

      <!-- Stats strip -->
      <div v-if="stats" class="stats-strip">
        <span class="stat-item">{{ stats.total_albums.toLocaleString() }} albums</span>
        <span class="stat-sep">·</span>
        <span class="stat-item">{{ stats.total_items.toLocaleString() }} tracks</span>
        <span class="stat-sep">·</span>
        <span class="stat-item">{{ stats.artists_count.toLocaleString() }} artists</span>
        <span class="stat-sep">·</span>
        <span class="stat-item">{{ formatDuration(stats.total_duration) }}</span>
      </div>
    </div>

    <!-- Recently Added -->
    <section class="shelf">
      <h2 class="shelf-title">Recently Added</h2>
      <div v-if="recentAlbums.length" class="shelf-scroll">
        <div class="shelf-track">
          <div
            v-for="album in recentAlbums"
            :key="album.id"
            class="shelf-card"
          >
            <AlbumCard :album="album" />
          </div>
        </div>
      </div>
      <div v-else class="shelf-empty">Loading...</div>
    </section>

    <!-- Recently Played -->
    <section class="shelf">
      <h2 class="shelf-title">Recently Played</h2>
      <div v-if="playHistory.length" class="shelf-scroll">
        <div class="shelf-track">
          <div
            v-for="entry in playHistory"
            :key="entry.item_id"
            class="shelf-card"
          >
            <AlbumCard :album="entry" />
          </div>
        </div>
      </div>
      <div v-else class="shelf-empty">No play history yet. Start listening!</div>
    </section>

    <!-- Genres -->
    <section class="shelf">
      <h2 class="shelf-title">Genres</h2>
      <div v-if="genres.length" class="shelf-scroll">
        <div class="shelf-track">
          <RouterLink
            v-for="g in genres"
            :key="g.genre"
            :to="`/library?q=${encodeURIComponent('genre:' + g.genre)}`"
            class="genre-chip"
          >
            <span class="genre-name">{{ g.genre }}</span>
            <span class="genre-count">{{ g.album_count }}</span>
          </RouterLink>
        </div>
      </div>
      <div v-else class="shelf-empty">Loading...</div>
    </section>

    <!-- Recommended -->
    <section class="shelf">
      <h2 class="shelf-title">
        Recommended
        <span class="shelf-subtitle">Based on your least-played artists</span>
      </h2>
      <div v-if="recommendedAlbums.length" class="shelf-scroll">
        <div class="shelf-track">
          <div
            v-for="album in recommendedAlbums"
            :key="album.id"
            class="shelf-card"
          >
            <AlbumCard :album="album" />
          </div>
        </div>
      </div>
      <div v-else class="shelf-empty">Loading...</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import AlbumCard from '@/components/albums/AlbumCard.vue'
import { fetchRecentAlbums, fetchRecommendedAlbums, fetchGenres } from '@/api/albums'
import type { AlbumSummary } from '@/types/album'
import type { GenreWithCount } from '@/api/albums'
import type { PlayHistoryRecord } from '@/api/playback'
import { fetchPlayHistory } from '@/api/playback'
import client from '@/api/client'

interface LibraryStats {
  total_albums: number
  total_items: number
  total_duration: number
  artists_count: number
}

const recentAlbums = ref<AlbumSummary[]>([])
const playHistory = ref<PlayHistoryRecord[]>([])
const genres = ref<GenreWithCount[]>([])
const recommendedAlbums = ref<AlbumSummary[]>([])
const stats = ref<LibraryStats | null>(null)

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h.toLocaleString()}h ${m}m`
  return `${m}m`
}

onMounted(async () => {
  // Load all sections in parallel
  const [recent, history, genreList, recommended, statsRes] = await Promise.allSettled([
    fetchRecentAlbums(12),
    fetchPlayHistory(20),
    fetchGenres(),
    fetchRecommendedAlbums(12),
    client.get<LibraryStats>('/library/stats'),
  ])

  if (recent.status === 'fulfilled') recentAlbums.value = recent.value
  if (history.status === 'fulfilled') playHistory.value = history.value
  if (genreList.status === 'fulfilled') genres.value = genreList.value
  if (recommended.status === 'fulfilled') recommendedAlbums.value = recommended.value
  if (statsRes.status === 'fulfilled') stats.value = statsRes.value.data
})
</script>

<style scoped>
.home-view {
  padding: 28px 28px 0;
  max-width: 1400px;
}

.home-header {
  margin-bottom: 28px;
}

.home-title {
  font-size: var(--text-2xl, 1.5rem);
  font-weight: 700;
  color: #f4f4f5;
  margin: 0 0 8px;
}

/* Stats strip */
.stats-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-item {
  font-size: var(--text-sm, 0.8125rem);
  color: #71717a;
}

.stat-sep {
  color: #3f3f46;
  font-size: var(--text-sm, 0.8125rem);
}

/* Shelf */
.shelf {
  margin-bottom: 36px;
}

.shelf-title {
  font-size: var(--text-lg, 1.0625rem);
  font-weight: 600;
  color: #e4e4e7;
  margin: 0 0 14px;
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.shelf-subtitle {
  font-size: var(--text-sm, 0.8125rem);
  font-weight: 400;
  color: #52525b;
}

.shelf-scroll {
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}

.shelf-scroll::-webkit-scrollbar {
  display: none;
}

.shelf-track {
  display: flex;
  gap: 14px;
  padding-bottom: 8px;
}

.shelf-card {
  flex: 0 0 160px;
  width: 160px;
}

.shelf-empty {
  font-size: var(--text-sm, 0.8125rem);
  color: #52525b;
  padding: 16px 0;
}

/* Genre chips */
.genre-chip {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 110px;
  padding: 16px 20px;
  border-radius: 10px;
  background-color: #27272a;
  text-decoration: none;
  color: inherit;
  transition: background-color 0.15s, transform 0.15s;
  cursor: pointer;
}

.genre-chip:hover {
  background-color: #3f3f46;
  transform: translateY(-2px);
}

.genre-name {
  font-size: var(--text-base, 0.9375rem);
  font-weight: 600;
  color: #e4e4e7;
  white-space: nowrap;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.genre-count {
  font-size: var(--text-xs, 0.75rem);
  color: #71717a;
}
</style>
