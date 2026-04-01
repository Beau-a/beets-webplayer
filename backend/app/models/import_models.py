"""
import_models.py — Pydantic models for the interactive import API.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ImportOptions(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    copy: bool = True
    move: bool = False
    write_tags: bool = True
    autotag: bool = True
    timid: bool = False


class ImportStartRequest(BaseModel):
    directory: str
    options: ImportOptions = ImportOptions()


class ImportStartResponse(BaseModel):
    session_id: str
    ws_url: str
