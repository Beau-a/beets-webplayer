import client from './client'
import type { AlbumDetail, PaginatedAlbums } from '@/types/album'

export interface FetchAlbumsParams {
  q?: string
  page?: number
  page_size?: number
  sort?: string
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
