"""
items.py — /api/items endpoints.

GET    /api/items        — paginated item/track list (ItemSummary)
GET    /api/items/{id}   — single item with full metadata (ItemDetail)
PATCH  /api/items/{id}   — update item metadata (writes tags to file)
DELETE /api/items/{id}   — remove item from library (does not delete file)
"""

from __future__ import annotations

import sqlite3
from typing import Optional

import beets.library
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.dependencies import get_db, get_library
from app.models.common import PaginatedResponse
from app.models.item import ITEM_EDITABLE_FIELDS, ItemDetail, ItemSummary, ItemUpdateRequest
from app.services import library_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ItemSummary])
async def list_items(
    q: Optional[str] = Query(default=None, description="Beets-style query string"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    sort: str = Query(default="artist+"),
    db: sqlite3.Connection = Depends(get_db),
) -> PaginatedResponse[ItemSummary]:
    rows, total = library_service.get_items(db, q=q, page=page, page_size=page_size, sort=sort)
    items = [ItemSummary(**row) for row in rows]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{item_id}", response_model=ItemDetail)
async def get_item(
    item_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> ItemDetail:
    row = library_service.get_item(db, item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemDetail(**row)


@router.patch("/{item_id}", response_model=ItemDetail)
async def update_item(
    item_id: int,
    body: ItemUpdateRequest,
    lib: beets.library.Library = Depends(get_library),
    db: sqlite3.Connection = Depends(get_db),
) -> ItemDetail:
    """
    Update item metadata.  Only fields included in the request body are changed.
    Tags are written to the audio file via beets, then stored in the library DB.
    """
    item = lib.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="No fields provided for update")

    for field, value in updates.items():
        if field in ITEM_EDITABLE_FIELDS:
            setattr(item, field, value)

    try:
        item.write()   # write tags to the audio file
        item.store()   # persist changes to the beets DB
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save item: {exc}") from exc

    row = library_service.get_item(db, item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found after update")
    return ItemDetail(**row)


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    lib: beets.library.Library = Depends(get_library),
) -> Response:
    """
    Remove an item from the beets library.  The audio file is NOT deleted from disk.
    """
    item = lib.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        item.remove(delete=False)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to remove item: {exc}") from exc

    return Response(status_code=204)
