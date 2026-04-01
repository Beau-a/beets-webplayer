export interface LibraryFilters {
  query?: string
  genre?: string | null
  yearFrom?: number | null
  yearTo?: number | null
  format?: string | null
}

export function useBeetsQuery() {
  function buildQuery(filters: LibraryFilters): string {
    const parts: string[] = []

    if (filters.query && filters.query.trim()) {
      parts.push(filters.query.trim())
    }

    if (filters.genre) {
      parts.push(`genre:${filters.genre}`)
    }

    if (filters.yearFrom != null && filters.yearTo != null) {
      parts.push(`year:${filters.yearFrom}..${filters.yearTo}`)
    } else if (filters.yearFrom != null) {
      parts.push(`year:${filters.yearFrom}..`)
    } else if (filters.yearTo != null) {
      parts.push(`year:..${filters.yearTo}`)
    }

    if (filters.format) {
      parts.push(`format:${filters.format}`)
    }

    return parts.join(' ')
  }

  return { buildQuery }
}
