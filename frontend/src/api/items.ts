import client from './client'
import type { ItemDetail, PaginatedItems } from '@/types/item'

export interface FetchItemsParams {
  q?: string
  page?: number
  page_size?: number
  sort?: string
}

export async function fetchItems(params: FetchItemsParams = {}): Promise<PaginatedItems> {
  const res = await client.get<PaginatedItems>('/items', { params })
  return res.data
}

export async function fetchItem(id: number): Promise<ItemDetail> {
  const res = await client.get<ItemDetail>(`/items/${id}`)
  return res.data
}
