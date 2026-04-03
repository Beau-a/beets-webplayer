import client from './client'
import type { AlbumSummary } from '@/types/album'

export interface PlayHistoryRecord extends AlbumSummary {
  // play_history-specific fields
  item_id: number
  played_at: number
  duration_played: number
}

export async function fetchPlayHistory(limit = 20): Promise<PlayHistoryRecord[]> {
  const res = await client.get<PlayHistoryRecord[]>('/playback/history', { params: { limit } })
  return res.data
}

export async function recordPlay(item_id: number, duration_played: number): Promise<void> {
  await client.post('/playback/history', { item_id, duration_played })
}
