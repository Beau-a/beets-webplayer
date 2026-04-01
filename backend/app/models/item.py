from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class ItemUpdateRequest(BaseModel):
    """Partial update model for PATCH /api/items/{id}. All fields optional."""
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    albumartist: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    track: Optional[int] = None
    tracktotal: Optional[int] = None
    disc: Optional[int] = None
    disctotal: Optional[int] = None
    genres: Optional[str] = None
    label: Optional[str] = None
    country: Optional[str] = None
    media: Optional[str] = None
    bpm: Optional[int] = None
    initial_key: Optional[str] = None
    comp: Optional[int] = None
    mb_trackid: Optional[str] = None
    mb_albumid: Optional[str] = None
    mb_artistid: Optional[str] = None
    mb_albumartistid: Optional[str] = None
    catalognum: Optional[str] = None
    isrc: Optional[str] = None

# Fields that may be written back to the beets DB and audio file tags.
ITEM_EDITABLE_FIELDS = (
    "title", "artist", "album", "albumartist",
    "year", "month", "day",
    "track", "tracktotal", "disc", "disctotal",
    "genres", "label", "country", "media",
    "bpm", "initial_key", "comp",
    "mb_trackid", "mb_albumid", "mb_artistid", "mb_albumartistid",
    "catalognum", "isrc",
)


class ItemSummary(BaseModel):
    """Track representation for search results and item list."""

    id: int
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_id: Optional[int] = None
    track: Optional[int] = None
    disc: Optional[int] = None
    year: Optional[int] = None
    genres: Optional[str] = None
    length: Optional[float] = None
    format: Optional[str] = None
    bitrate: Optional[int] = None
    samplerate: Optional[int] = None
    bitdepth: Optional[int] = None
    added: Optional[float] = None


class ItemDetail(ItemSummary):
    """Full item with all metadata (path and acoustid_fingerprint excluded)."""

    artists: Optional[str] = None
    albumartist: Optional[str] = None
    month: Optional[int] = None
    day: Optional[int] = None
    tracktotal: Optional[int] = None
    disctotal: Optional[int] = None
    comp: Optional[int] = None
    label: Optional[str] = None
    country: Optional[str] = None
    media: Optional[str] = None
    bpm: Optional[int] = None
    initial_key: Optional[str] = None
    mb_trackid: Optional[str] = None
    mb_albumid: Optional[str] = None
    mb_artistid: Optional[str] = None
    mb_albumartistid: Optional[str] = None
    catalognum: Optional[str] = None
    isrc: Optional[str] = None
    acoustid_id: Optional[str] = None
    rg_track_gain: Optional[float] = None
    rg_track_peak: Optional[float] = None
    r128_track_gain: Optional[float] = None
    original_year: Optional[int] = None
    mtime: Optional[float] = None
