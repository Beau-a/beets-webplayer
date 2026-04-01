from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class AlbumRelocateRequest(BaseModel):
    destination: str  # absolute path to new parent directory


class AlbumUpdateRequest(BaseModel):
    """Partial update model for PATCH /api/albums/{id}. All fields optional."""
    album: Optional[str] = None
    albumartist: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    genres: Optional[str] = None
    label: Optional[str] = None
    country: Optional[str] = None
    albumtype: Optional[str] = None
    albumstatus: Optional[str] = None
    albumdisambig: Optional[str] = None
    comp: Optional[int] = None
    mb_albumid: Optional[str] = None
    mb_releasegroupid: Optional[str] = None
    mb_albumartistid: Optional[str] = None
    catalognum: Optional[str] = None
    barcode: Optional[str] = None
    asin: Optional[str] = None
    original_year: Optional[int] = None


class TrackInAlbum(BaseModel):
    """Lightweight track representation used inside album detail view."""

    id: int
    title: Optional[str] = None
    artist: Optional[str] = None
    track: Optional[int] = None
    disc: Optional[int] = None
    length: Optional[float] = None
    format: Optional[str] = None
    bitrate: Optional[int] = None
    samplerate: Optional[int] = None
    bitdepth: Optional[int] = None
    added: Optional[float] = None
    path: Optional[str] = None


class AlbumSummary(BaseModel):
    """Album representation for grid/list browsing."""

    id: int
    album: Optional[str] = None
    albumartist: Optional[str] = None
    year: Optional[int] = None
    genres: Optional[str] = None
    label: Optional[str] = None
    country: Optional[str] = None
    albumtype: Optional[str] = None
    track_count: int = 0
    total_length: Optional[float] = None
    has_art: bool = False
    added: Optional[float] = None
    # Derived: most common format among items in the album
    format: Optional[str] = None


class AlbumDetail(AlbumSummary):
    """Full album with all metadata fields and track list."""

    month: Optional[int] = None
    day: Optional[int] = None
    disctotal: Optional[int] = None
    comp: Optional[int] = None
    mb_albumid: Optional[str] = None
    mb_releasegroupid: Optional[str] = None
    catalognum: Optional[str] = None
    barcode: Optional[str] = None
    asin: Optional[str] = None
    albumstatus: Optional[str] = None
    albumdisambig: Optional[str] = None
    original_year: Optional[int] = None
    rg_album_gain: Optional[float] = None
    rg_album_peak: Optional[float] = None
    r128_album_gain: Optional[float] = None
    items: list[TrackInAlbum] = []
