import client from './client'
import type { AlbumDetail, AlbumSummary, PaginatedAlbums } from '@/types/album'

export interface FetchAlbumsParams {
  q?: string
  page?: number
  page_size?: number
  sort?: string
}

export interface GenreWithCount {
  genre: string
  album_count: number
}

export async function fetchAlbums(params: FetchAlbumsParams = {}): Promise<PaginatedAlbums> {
  const res = await client.get<PaginatedAlbums>('/albums', { params })
  return res.data
}

export async function fetchAlbum(id: number): Promise<AlbumDetail> {
  const res = await client.get<AlbumDetail>(`/albums/${id}`)
  return res.data
}

export function getAlbumArtUrl(id: number): string {
  return `/api/albums/${id}/art`
}

export async function fetchRecentAlbums(limit = 12): Promise<AlbumSummary[]> {
  const res = await client.get<AlbumSummary[]>('/albums/recent', { params: { limit } })
  return res.data
}

export async function fetchRandomAlbums(limit = 12): Promise<AlbumSummary[]> {
  const res = await client.get<AlbumSummary[]>('/albums/random', { params: { limit } })
  return res.data
}

export async function fetchRecommendedAlbums(limit = 12): Promise<AlbumSummary[]> {
  const res = await client.get<AlbumSummary[]>('/albums/recommended', { params: { limit } })
  return res.data
}

export async function fetchGenres(): Promise<GenreWithCount[]> {
  const res = await client.get<GenreWithCount[]>('/genres')
  return res.data
}
