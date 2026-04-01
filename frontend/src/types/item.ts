export interface ItemSummary {
  id: number
  title: string
  artist: string
  album: string
  album_id: number
  track: number
  disc: number
  year: number
  length: number       // seconds
  format: string
  bitrate: number
  added: number        // unix timestamp
}

export interface ItemDetail extends ItemSummary {
  albumartist: string
  samplerate: number
  bitdepth: number
  channels: number
  encoder: string | null
  mb_trackid: string | null
  mb_albumid: string | null
  mb_artistid: string | null
  composer: string | null
  genres: string | null
  label: string | null
  country: string | null
  language: string | null
  comments: string | null
  lyrics: string | null
  rg_track_gain: number | null
  rg_track_peak: number | null
  r128_track_gain: number | null
  path: string
}

export interface PaginatedItems {
  items: ItemSummary[]
  total: number
  page: number
  page_size: number
}
