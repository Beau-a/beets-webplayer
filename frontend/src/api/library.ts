import client from './client'
import type { AlbumDetail } from '@/types/album'
import type { MBSearchResult } from '@/types/import'

export interface ImportStartOptions {
  copy?: boolean
  move?: boolean
  write_tags?: boolean
  autotag?: boolean
}

export interface ImportStartResponse {
  session_id: string
  ws_url: string
}

export async function searchMusicBrainz(q: string): Promise<MBSearchResult[]> {
  const res = await client.get<{ results: MBSearchResult[] }>('/library/import/mb-search', {
    params: { q },
  })
  return res.data.results
}

export async function startImport(
  directory: string,
  options: ImportStartOptions = {},
): Promise<ImportStartResponse> {
  const res = await client.post<ImportStartResponse>('/library/import', {
    directory,
    options,
  })
  return res.data
}

export interface LibraryStats {
  total_albums: number
  total_items: number
  total_duration: number
  format_breakdown: Record<string, number>
  year_range: [number, number]
  artists_count: number
}

export async function fetchLibraryStats(): Promise<LibraryStats> {
  const res = await client.get<LibraryStats>('/library/stats')
  return res.data
}

// ---------------------------------------------------------------------------
// Item metadata editing
// ---------------------------------------------------------------------------

export interface ItemUpdatePayload {
  title?: string
  artist?: string
  album?: string
  albumartist?: string
  year?: number
  month?: number
  day?: number
  track?: number
  tracktotal?: number
  disc?: number
  disctotal?: number
  genres?: string
  label?: string
  country?: string
  media?: string
  bpm?: number
  initial_key?: string
  comp?: number
  mb_trackid?: string
  mb_albumid?: string
  mb_artistid?: string
  mb_albumartistid?: string
  catalognum?: string
  isrc?: string
}

export async function updateItem(id: number, updates: ItemUpdatePayload): Promise<unknown> {
  const res = await client.patch(`/items/${id}`, updates)
  return res.data
}

export async function deleteItem(id: number): Promise<void> {
  await client.delete(`/items/${id}`)
}

// ---------------------------------------------------------------------------
// Album metadata editing
// ---------------------------------------------------------------------------

export interface AlbumUpdatePayload {
  album?: string
  albumartist?: string
  year?: number
  month?: number
  day?: number
  genres?: string
  label?: string
  country?: string
  albumtype?: string
  albumstatus?: string
  albumdisambig?: string
  comp?: number
  mb_albumid?: string
  mb_releasegroupid?: string
  mb_albumartistid?: string
  catalognum?: string
  barcode?: string
  asin?: string
  original_year?: number
}

export async function updateAlbum(id: number, updates: AlbumUpdatePayload): Promise<unknown> {
  const res = await client.patch(`/albums/${id}`, updates)
  return res.data
}

export async function deleteAlbum(id: number): Promise<void> {
  await client.delete(`/albums/${id}`)
}

// ---------------------------------------------------------------------------
// Management tasks
// ---------------------------------------------------------------------------

export interface LibraryTaskResponse {
  task_id: string
  status: string
  output?: string
}

export async function runLibraryTask(
  task: string,
  albumIds: number[] = [],
  itemIds: number[] = [],
): Promise<LibraryTaskResponse> {
  const res = await client.post<LibraryTaskResponse>('/library/tasks', {
    task,
    album_ids: albumIds,
    item_ids: itemIds,
  })
  return res.data
}

export async function getLibraryTask(taskId: string): Promise<LibraryTaskResponse> {
  const res = await client.get<LibraryTaskResponse>(`/library/tasks/${taskId}`)
  return res.data
}

// ---------------------------------------------------------------------------
// Artist browser
// ---------------------------------------------------------------------------

export interface ArtistEntry {
  name: string
  album_count: number
}

export async function fetchArtists(letter: string): Promise<ArtistEntry[]> {
  const res = await client.get<ArtistEntry[]>('/library/artists', {
    params: letter ? { letter } : {},
  })
  return res.data
}

export async function fetchArtistLetters(): Promise<string[]> {
  const res = await client.get<string[]>('/library/artists/letters')
  return res.data
}

export async function removeArtist(artistName: string): Promise<void> {
  await client.delete(`/library/artists/${encodeURIComponent(artistName)}`)
}

export async function relocateAlbum(albumId: number, destination: string): Promise<AlbumDetail> {
  const res = await client.post<AlbumDetail>(`/albums/${albumId}/relocate`, { destination })
  return res.data
}

export async function relocateArtist(
  artistName: string,
  destination: string,
): Promise<{ relocated: number; failed: number; errors: string[] }> {
  const res = await client.post(`/library/artists/${encodeURIComponent(artistName)}/relocate`, {
    destination,
  })
  return res.data
}
