"""
relocate_service.py — Move an album's files to a new parent directory and update beets DB paths.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import beets.library


def _decode_path(p) -> str:
    if isinstance(p, (bytes, bytearray)):
        return p.decode("utf-8", errors="replace")
    return str(p)


def album_root(items: list) -> Path:
    """Return the deepest common ancestor directory of all item paths."""
    paths = [_decode_path(item.path) for item in items]
    if len(paths) == 1:
        return Path(paths[0]).parent
    common = Path(os.path.commonpath(paths))
    # commonpath may return a file if there's only one file — ensure we return a dir
    if common.is_file():
        return common.parent
    return common


def relocate_album(
    lib: "beets.library.Library",
    album_id: int,
    destination: str,
    music_base_path: str,
) -> dict:
    """
    Move an album's folder into `destination` and update all item paths in beets.

    Returns {"old_path": str, "new_path": str}.
    Raises:
      - ValueError if no items, destination is unsafe, or target already exists
      - OSError if filesystem move fails
    """
    album = lib.get_album(album_id)
    if album is None:
        raise ValueError(f"Album {album_id} not found")

    items = list(album.items())
    if not items:
        raise ValueError("Album has no items")

    root = album_root(items)
    dest_path = Path(destination).resolve()
    base = Path(music_base_path).resolve()

    # Security: destination must be within the allowed music base path
    try:
        dest_path.relative_to(base)
    except ValueError:
        raise ValueError(f"Destination is outside the permitted base path ({music_base_path})")

    new_root = dest_path / root.name

    if new_root.exists():
        raise FileExistsError(f"Target folder already exists: {new_root}")

    # Ensure destination parent exists
    dest_path.mkdir(parents=True, exist_ok=True)

    # Move the directory
    shutil.move(str(root), str(new_root))

    # Update each item's path in beets
    for item in items:
        old = Path(_decode_path(item.path))
        try:
            rel = old.relative_to(root)
        except ValueError:
            # item is outside the album root (shouldn't happen) — skip
            continue
        new_p = new_root / rel
        item.path = str(new_p).encode()
        item.store()

    return {"old_path": str(root), "new_path": str(new_root)}
