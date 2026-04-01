export type RepeatMode = 'off' | 'all' | 'one'

export interface QueueTrack {
  id: number
  title: string
  artist: string
  album: string
  album_id: number
  length: number        // seconds
  format: string
  bitrate: number
}
