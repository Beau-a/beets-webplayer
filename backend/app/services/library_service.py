"""
library_service.py — Direct SQLite read layer for the beets library.

All queries use parameterized placeholders (?). No f-string SQL interpolation.
"""

from __future__ import annotations

import sqlite3
from typing import Optional


# ---------------------------------------------------------------------------
# Query parsing
# ---------------------------------------------------------------------------

# Fields that support exact match rather than LIKE for albums
_ALBUM_EXACT_FIELDS = {"format", "albumtype", "albumstatus", "country", "script", "language", "media"}

# Fields that map to items table when querying albums via JOIN
_ITEM_FIELDS_IN_ALBUM_QUERY = {"format", "bitrate", "samplerate", "bitdepth", "channels", "length"}

# Sortable field names for albums
_ALBUM_SORT_FIELDS = {
    "albumartist", "album", "year", "added", "track_count", "total_length",
    "label", "country", "genres", "albumtype", "original_year",
}

# Sortable field names for items
_ITEM_SORT_FIELDS = {
    "title", "artist", "album", "albumartist", "year", "added",
    "track", "disc", "length", "bitrate", "format",
}


def _parse_sort(sort_str: str, valid_fields: set[str], default_field: str, default_dir: str = "ASC", prefix: str = "") -> str:
    """
    Convert a beets sort token (e.g. 'albumartist+', 'year-') into an SQL ORDER BY clause.

    Returns a safe ORDER BY fragment — only allows known field names.
    Use prefix="a." when the query uses a table alias to avoid ambiguous column names.
    """
    if not sort_str:
        return f"{prefix}{default_field} {default_dir}"

    # Only take the last token (simple single-sort implementation)
    token = sort_str.strip().split()[-1]
    if token.endswith("+"):
        field = token[:-1]
        direction = "ASC"
    elif token.endswith("-"):
        field = token[:-1]
        direction = "DESC"
    else:
        field = token
        direction = default_dir

    if field not in valid_fields:
        # Fall back to default if field name is unrecognised
        field = default_field
        direction = default_dir

    return f"{prefix}{field} {direction}"


def parse_beets_query(q: str, table: str = "items", col_prefix: str = "") -> tuple[str, list]:
    """
    Translate a simplified beets query string into a SQL WHERE fragment and params.

    Supported syntax:
      - field:value         → field LIKE %value% (or exact for certain fields)
      - year:1990..1999     → year BETWEEN 1990 AND 1999
      - year:2010..         → year >= 2010
      - year:..1999         → year <= 1999
      - bare word           → LIKE search across title/artist/album/albumartist
      - ^token              → NOT match

    Multiple space-separated tokens are ANDed together.
    col_prefix is prepended to column names (e.g. "a." when using a JOIN with alias).

    Returns (where_clause_str, params_list).
    If there are no conditions, returns ("", []).
    """
    if not q or not q.strip():
        return "", []

    clauses: list[str] = []
    params: list = []

    # Tokenise: split on spaces but respect simple quoted strings
    tokens = _tokenise_query(q)

    for token in tokens:
        if not token:
            continue

        negate = False
        if token.startswith("^"):
            negate = True
            token = token[1:]

        if ":" in token:
            field, _, value = token.partition(":")
            field = field.lower()

            clause, p = _build_field_clause(col_prefix + field, value, table)
            if clause:
                if negate:
                    clause = f"NOT ({clause})"
                clauses.append(clause)
                params.extend(p)
        else:
            # Bare-word: substring match across key text fields
            if table == "albums":
                search_fields = [col_prefix + f for f in ["albumartist", "album", "genres"]]
            else:
                search_fields = [col_prefix + f for f in ["title", "artist", "album", "albumartist"]]

            like_clauses = [f"{f} LIKE ?" for f in search_fields]
            sub = "(" + " OR ".join(like_clauses) + ")"
            if negate:
                sub = f"NOT {sub}"
            clauses.append(sub)
            for _ in search_fields:
                params.append(f"%{token}%")

    if not clauses:
        return "", []

    return " AND ".join(clauses), params


def _tokenise_query(q: str) -> list[str]:
    """Split on whitespace, honouring simple double-quoted strings."""
    tokens = []
    current = []
    in_quotes = False
    for ch in q:
        if ch == '"':
            in_quotes = not in_quotes
        elif ch == " " and not in_quotes:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(ch)
    if current:
        tokens.append("".join(current))
    return tokens


def _build_field_clause(prefixed_field: str, value: str, table: str) -> tuple[str, list]:
    """Build a SQL clause for a field:value token. prefixed_field already includes any table prefix."""

    # Strip prefix for field-type lookup (e.g. "a.year" → "year")
    bare_field = prefixed_field.split(".")[-1]

    # Numeric range: year:1990..1999 / year:2010.. / year:..1999
    if ".." in value:
        lo, _, hi = value.partition("..")
        lo = lo.strip()
        hi = hi.strip()

        numeric_fields = {
            "year", "original_year", "bitrate", "samplerate", "bitdepth",
            "bpm", "track", "disc", "length",
        }
        if bare_field in numeric_fields:
            try:
                if lo and hi:
                    return f"{prefixed_field} BETWEEN ? AND ?", [int(lo), int(hi)]
                elif lo:
                    return f"{prefixed_field} >= ?", [int(lo)]
                elif hi:
                    return f"{prefixed_field} <= ?", [int(hi)]
            except ValueError:
                pass
        return f"{prefixed_field} LIKE ?", [f"%{value}%"]

    # Exact match fields
    exact_fields = {"format", "albumtype", "albumstatus", "script", "language", "media", "country"}
    if bare_field in exact_fields:
        return f"{prefixed_field} = ?", [value]

    # Default: LIKE substring
    return f"{prefixed_field} LIKE ?", [f"%{value}%"]


# ---------------------------------------------------------------------------
# Album queries
# ---------------------------------------------------------------------------

_ALBUM_SELECT = """
SELECT
    a.id,
    a.album,
    a.albumartist,
    a.year,
    a.month,
    a.day,
    a.genres,
    a.label,
    a.country,
    a.albumtype,
    a.albumtypes,
    a.albumstatus,
    a.albumdisambig,
    a.disctotal,
    a.comp,
    a.mb_albumid,
    a.mb_releasegroupid,
    a.mb_albumartistid,
    a.catalognum,
    a.barcode,
    a.asin,
    a.original_year,
    a.rg_album_gain,
    a.rg_album_peak,
    a.r128_album_gain,
    a.added,
    a.artpath,
    COUNT(i.id)           AS track_count,
    SUM(i.length)         AS total_length,
    (a.artpath IS NOT NULL AND a.artpath != '') AS has_art,
    (
        SELECT i2.format
        FROM items i2
        WHERE i2.album_id = a.id
        GROUP BY i2.format
        ORDER BY COUNT(*) DESC
        LIMIT 1
    ) AS format
FROM albums a
LEFT JOIN items i ON i.album_id = a.id
"""


def get_albums(
    db: sqlite3.Connection,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    sort: str = "albumartist+",
) -> tuple[list[dict], int]:
    """
    Return a paginated list of albums with aggregated fields.

    Returns (rows, total_count).
    """
    page_size = min(page_size, 200)
    offset = (page - 1) * page_size

    where_clause, params = parse_beets_query(q or "", table="albums", col_prefix="a.")
    where_sql = f"WHERE {where_clause}" if where_clause else ""

    order_by = _parse_sort(sort, _ALBUM_SORT_FIELDS, "albumartist", "ASC", prefix="a.")

    # Count query
    count_sql = f"""
        SELECT COUNT(*) FROM (
            SELECT a.id
            FROM albums a
            LEFT JOIN items i ON i.album_id = a.id
            {where_sql}
            GROUP BY a.id
        ) sub
    """
    total = db.execute(count_sql, params).fetchone()[0]

    # Data query
    data_sql = f"""
        {_ALBUM_SELECT}
        {where_sql}
        GROUP BY a.id
        ORDER BY {order_by}
        LIMIT ? OFFSET ?
    """
    rows = db.execute(data_sql, params + [page_size, offset]).fetchall()

    return [_album_row_to_dict(row) for row in rows], total


def get_album(db: sqlite3.Connection, album_id: int) -> Optional[dict]:
    """
    Return a single album with all fields and its items ordered by disc/track.
    """
    sql = f"""
        {_ALBUM_SELECT}
        WHERE a.id = ?
        GROUP BY a.id
    """
    row = db.execute(sql, [album_id]).fetchone()
    if row is None:
        return None

    album = _album_row_to_dict(row)

    # Fetch tracks
    items_sql = """
        SELECT
            id, title, artist, track, disc, length,
            format, bitrate, samplerate, bitdepth, added, path
        FROM items
        WHERE album_id = ?
        ORDER BY disc, track
    """
    item_rows = db.execute(items_sql, [album_id]).fetchall()
    items = []
    for r in item_rows:
        row = dict(r)
        p = row.get("path")
        if isinstance(p, (bytes, bytearray)):
            row["path"] = p.decode("utf-8", errors="replace")
        items.append(row)
    album["items"] = items

    return album


def _album_row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict, decoding BLOB fields."""
    d = dict(row)
    # artpath is stored as BLOB — decode to string for the has_art flag;
    # we do NOT expose the raw path in the response.
    artpath = d.get("artpath")
    if isinstance(artpath, (bytes, bytearray)):
        d["artpath"] = artpath.decode("utf-8", errors="replace")
    # has_art comes from SQL as 0/1 integer
    d["has_art"] = bool(d.get("has_art", 0))
    return d


# ---------------------------------------------------------------------------
# Item queries
# ---------------------------------------------------------------------------

# Fields to SELECT for ItemSummary
_ITEM_SUMMARY_COLS = (
    "id", "title", "artist", "album", "album_id", "track", "disc",
    "year", "genres", "length", "format", "bitrate", "samplerate",
    "bitdepth", "added",
)

# Additional fields for ItemDetail (excludes path and acoustid_fingerprint)
_ITEM_DETAIL_EXTRA_COLS = (
    "artists", "albumartist", "month", "day", "tracktotal", "disctotal",
    "comp", "label", "country", "media", "bpm", "initial_key",
    "mb_trackid", "mb_albumid", "mb_artistid", "mb_albumartistid",
    "catalognum", "isrc", "acoustid_id",
    "rg_track_gain", "rg_track_peak", "r128_track_gain",
    "original_year", "mtime",
)


def get_items(
    db: sqlite3.Connection,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    sort: str = "artist+",
) -> tuple[list[dict], int]:
    """
    Return a paginated list of items (tracks).

    Returns (rows, total_count).
    """
    page_size = min(page_size, 200)
    offset = (page - 1) * page_size

    where_clause, params = parse_beets_query(q or "", table="items")
    where_sql = f"WHERE {where_clause}" if where_clause else ""

    order_by = _parse_sort(sort, _ITEM_SORT_FIELDS, "artist", "ASC")

    col_list = ", ".join(_ITEM_SUMMARY_COLS)

    count_sql = f"SELECT COUNT(*) FROM items {where_sql}"
    total = db.execute(count_sql, params).fetchone()[0]

    data_sql = f"""
        SELECT {col_list}
        FROM items
        {where_sql}
        ORDER BY {order_by}
        LIMIT ? OFFSET ?
    """
    rows = db.execute(data_sql, params + [page_size, offset]).fetchall()

    return [dict(r) for r in rows], total


def get_item(db: sqlite3.Connection, item_id: int, include_lyrics: bool = False) -> Optional[dict]:
    """
    Return a single item with full metadata.
    Deliberately excludes path and acoustid_fingerprint.
    Pass include_lyrics=True to also fetch the lyrics column.
    """
    all_cols = _ITEM_SUMMARY_COLS + _ITEM_DETAIL_EXTRA_COLS
    if include_lyrics:
        all_cols = all_cols + ("lyrics",)
    col_list = ", ".join(all_cols)

    sql = f"SELECT {col_list} FROM items WHERE id = ?"
    row = db.execute(sql, [item_id]).fetchone()
    if row is None:
        return None
    return dict(row)


# ---------------------------------------------------------------------------
# Library-level stats and facets
# ---------------------------------------------------------------------------

def get_stats(db: sqlite3.Connection) -> dict:
    """
    Return aggregate library statistics.
    """
    total_albums = db.execute("SELECT COUNT(*) FROM albums").fetchone()[0]
    total_items = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    total_duration = db.execute("SELECT SUM(length) FROM items").fetchone()[0] or 0.0

    format_rows = db.execute(
        "SELECT format, COUNT(*) AS cnt FROM items WHERE format != '' GROUP BY format ORDER BY cnt DESC"
    ).fetchall()
    format_breakdown = {r["format"]: r["cnt"] for r in format_rows}

    year_row = db.execute(
        "SELECT MIN(year), MAX(year) FROM albums WHERE year IS NOT NULL AND year > 0"
    ).fetchone()
    year_range = [year_row[0] or 0, year_row[1] or 0]

    artists_count = db.execute(
        "SELECT COUNT(DISTINCT albumartist) FROM albums WHERE albumartist IS NOT NULL AND albumartist != ''"
    ).fetchone()[0]

    return {
        "total_albums": total_albums,
        "total_items": total_items,
        "total_duration": round(total_duration, 2),
        "format_breakdown": format_breakdown,
        "year_range": year_range,
        "artists_count": artists_count,
    }


def get_facets(db: sqlite3.Connection) -> dict:
    """
    Return distinct values for filter UI facets.

    Genres are split on comma since beets stores them as "Rock, Alternative" etc.
    """
    # Genres: split on comma, strip, deduplicate
    genre_rows = db.execute(
        "SELECT DISTINCT genres FROM albums WHERE genres IS NOT NULL AND genres != ''"
    ).fetchall()
    genre_set: set[str] = set()
    for row in genre_rows:
        for g in row["genres"].split(","):
            g = g.strip()
            if g:
                genre_set.add(g)
    genres = sorted(genre_set)

    # Formats from items
    format_rows = db.execute(
        "SELECT DISTINCT format FROM items WHERE format IS NOT NULL AND format != '' ORDER BY format"
    ).fetchall()
    formats = [r["format"] for r in format_rows]

    # Labels from albums
    label_rows = db.execute(
        "SELECT DISTINCT label FROM albums WHERE label IS NOT NULL AND label != '' ORDER BY label"
    ).fetchall()
    labels = [r["label"] for r in label_rows]

    # Year range
    year_row = db.execute(
        "SELECT MIN(year), MAX(year) FROM albums WHERE year IS NOT NULL AND year > 0"
    ).fetchone()
    year_range = [year_row[0] or 0, year_row[1] or 0]

    return {
        "genres": genres,
        "formats": formats,
        "labels": labels,
        "year_range": year_range,
    }
