import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { fetchAlbums as apiFetchAlbums, fetchAlbum as apiFetchAlbum } from '@/api/albums'
import { fetchItems as apiFetchItems } from '@/api/items'
import client from '@/api/client'
import { useBeetsQuery } from '@/composables/useBeetsQuery'
import type { AlbumSummary, AlbumDetail } from '@/types/album'
import type { ItemSummary } from '@/types/item'

interface Facets {
  genres: string[]
  formats: string[]
  labels: string[]
  year_range: [number, number]
}

interface LibraryFilters {
  query: string
  genre: string | null
  yearFrom: number | null
  yearTo: number | null
  format: string | null
  sort: string
}

export const useLibraryStore = defineStore('library', () => {
  const { buildQuery } = useBeetsQuery()

  // State
  const albums = ref<AlbumSummary[]>([])
  const totalAlbums = ref(0)
  const currentAlbum = ref<AlbumDetail | null>(null)
  const searchResults = reactive<{ albums: AlbumSummary[]; items: ItemSummary[] }>({
    albums: [],
    items: [],
  })
  const filters = reactive<LibraryFilters>({
    query: '',
    genre: null,
    yearFrom: null,
    yearTo: null,
    format: null,
    sort: 'albumartist+',
  })
  const page = ref(1)
  const pageSize = ref(50)
  const isLoading = ref(false)
  const facets = ref<Facets | null>(null)

  // Actions
  async function fetchAlbums() {
    isLoading.value = true
    try {
      const q = buildQuery({
        query: filters.query,
        genre: filters.genre,
        yearFrom: filters.yearFrom,
        yearTo: filters.yearTo,
        format: filters.format,
      })
      const data = await apiFetchAlbums({
        q: q || undefined,
        page: page.value,
        page_size: pageSize.value,
        sort: filters.sort,
      })
      albums.value = data.items
      totalAlbums.value = data.total
    } catch (err) {
      console.error('[library] fetchAlbums failed', err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchAlbum(id: number) {
    isLoading.value = true
    try {
      const data = await apiFetchAlbum(id)
      currentAlbum.value = data
    } catch (err) {
      console.error('[library] fetchAlbum failed', err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchFacets() {
    try {
      const res = await client.get<Facets>('/library/facets')
      facets.value = res.data
    } catch (err) {
      console.error('[library] fetchFacets failed', err)
    }
  }

  async function searchLibrary(query: string) {
    isLoading.value = true
    try {
      const [albumsRes, itemsRes] = await Promise.all([
        apiFetchAlbums({ q: query, page: 1, page_size: 50 }),
        apiFetchItems({ q: query, page: 1, page_size: 100 }),
      ])
      searchResults.albums = albumsRes.items
      searchResults.items = itemsRes.items
    } catch (err) {
      console.error('[library] searchLibrary failed', err)
    } finally {
      isLoading.value = false
    }
  }

  function setFilter<K extends keyof LibraryFilters>(key: K, value: LibraryFilters[K]) {
    Object.assign(filters, { [key]: value })
    page.value = 1
  }

  function setPage(n: number) {
    page.value = n
  }

  function setPageSize(n: number) {
    pageSize.value = n
    page.value = 1
  }

  function resetFilters() {
    filters.query = ''
    filters.genre = null
    filters.yearFrom = null
    filters.yearTo = null
    filters.format = null
    filters.sort = 'albumartist+'
    page.value = 1
  }

  return {
    albums,
    totalAlbums,
    currentAlbum,
    searchResults,
    filters,
    page,
    pageSize,
    isLoading,
    facets,
    fetchAlbums,
    fetchAlbum,
    fetchFacets,
    searchLibrary,
    setFilter,
    setPage,
    setPageSize,
    resetFilters,
  }
})
