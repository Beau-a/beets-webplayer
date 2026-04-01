export interface TrackInAlbum {
  id: number
  title: string
  artist: string
  track: number
  disc: number
  length: number       // seconds
  format: string
  bitrate: number
  samplerate: number
  bitdepth: number
  added: number        // unix timestamp
  path: string | null
}

export interface AlbumSummary {
  id: number
  album: string
  albumartist: string
  year: number
  genres: string | null
  label: string | null
  country: string | null
  albumtype: string | null
  track_count: number
  total_length: number  // seconds
  has_art: boolean
  added: number
  format: string | null
}

export interface AlbumDetail extends AlbumSummary {
  month: number | null
  day: number | null
  disctotal: number
  comp: boolean
  mb_albumid: string | null
  mb_releasegroupid: string | null
  catalognum: string | null
  barcode: string | null
  asin: string | null
  albumstatus: string | null
  albumdisambig: string | null
  original_year: number | null
  rg_album_gain: number | null
  rg_album_peak: number | null
  r128_album_gain: number | null
  items: TrackInAlbum[]
}

export interface PaginatedAlbums {
  items: AlbumSummary[]
  total: number
  page: number
  page_size: number
}
