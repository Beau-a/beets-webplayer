import sqlite3
from fastapi import Request
import beets.library


def get_library(request: Request) -> beets.library.Library:
    return request.app.state.lib


def get_db(request: Request) -> sqlite3.Connection:
    return request.app.state.db
