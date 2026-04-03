export interface FileTrack {
  filename: string
  title: string
  artist: string
  track: number
  length: number  // seconds
}

export interface CandidateTrack {
  title: string
  artist: string
  track: number
  length: number  // seconds
  mb_trackid: string
}

export interface ImportCandidate {
  index: number
  distance: number          // 0.0 = perfect, higher = worse
  artist: string
  album: string
  year: number
  label: string
  country: string
  mb_albumid: string
  track_count: number
  tracks: CandidateTrack[]
  extra_items: number       // file tracks not in MB candidate
  missing_tracks: number    // MB tracks not in files
}

export interface CandidatesPayload {
  album_path: string
  file_tracks: FileTrack[]
  candidates: ImportCandidate[]
  rec: 'none' | 'low' | 'medium' | 'strong'
}

export interface ImportLogEntry {
  type: 'imported' | 'skipped' | 'error'
  path: string
  album_id?: number
  album?: string
  artist?: string
  year?: number
  message?: string
}

export interface ImportProgress {
  completed: number
  total: number
  currentPath: string
}

export type ImportSessionState =
  | 'idle'
  | 'connecting'
  | 'running'
  | 'waiting_choice'
  | 'waiting_no_candidates'
  | 'complete'
  | 'error'

export interface NoCandidatesPayload {
  album_path: string
  file_tracks: FileTrack[]
}

export interface MBSearchResult {
  artist: string
  album: string
  year: number
  label: string
  country: string
  mb_albumid: string
  track_count: number
  tracks: CandidateTrack[]
}

export interface ImportChoice {
  action: 'apply' | 'as_is' | 'skip' | 'singleton' | 'abort'
  candidate_index?: number
  mb_id?: string
}

export interface ImportSessionSummary {
  total_imported: number
  total_skipped: number
  total_errors: number
  duration_s: number
}
