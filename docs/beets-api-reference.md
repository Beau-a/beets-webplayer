# Beets API Reference for GUI Frontend Development

Source: beets v1.4.6 — https://github.com/beetbox/beets/tree/v1.4.6/docs/dev/

---

## Core Concepts

Beets is a music library manager. Its central data store is a SQLite database accessed through the `beets.library` module. The two primary model objects are:

- **Item** — a single track/song, with ~91 metadata fields
- **Album** — a group of items, with ~42 metadata fields

Items link to Albums via `item.album_id → album.id`.

The library at `/mnt/nfs/musiclibrary.db` contains **5,565 items** and **497 albums**.

---

## Opening the Library

```python
import beets.library

lib = beets.library.Library('/mnt/nfs/musiclibrary.db')
```

No beets configuration is required for read-only access. For write operations or plugin use, a full beets config must be loaded.

---

## Library API (`beets.library.Library`)

### Querying Items

```python
# All items
items = lib.items()

# Items matching a query string
items = lib.items('artist:Beatles')
items = lib.items('year:1990..1999')
items = lib.items('format:FLAC')

# Iterate results (lazy)
for item in lib.items('artist:Radiohead'):
    print(item.title, item.album, item.year)
```

### Querying Albums

```python
albums = lib.albums()
albums = lib.albums('year:2000..2010')

for album in lib.albums('albumartist:Beatles'):
    print(album.album, album.year)
```

### Fetching by ID

```python
item  = lib.get_item(item_id)    # returns Item or None
album = lib.get_album(album_id)  # returns Album or None
```

### Transactions (for writes)

```python
with lib.transaction() as tx:
    items = lib.items(query)
    # modify and save items here
```

---

## Item Fields (tracks)

All fields accessible as `item.field_name` or `item['field_name']`.

### Identity & Metadata
| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `album_id` | int | FK → albums.id |
| `path` | bytes | Filesystem path |
| `title` | str | Track title |
| `artist` | str | Track artist |
| `artists` | str | Multiple artists (JSON-ish) |
| `artist_sort` | str | Sortable artist name |
| `artist_credit` | str | Artist credit string |
| `album` | str | Album name |
| `albumartist` | str | Album artist |
| `albumartist_sort` | str | Sortable album artist |

### Track Position
| Field | Type |
|-------|------|
| `track` | int |
| `tracktotal` | int |
| `disc` | int |
| `disctotal` | int |

### Date
| Field | Type |
|-------|------|
| `year` | int |
| `month` | int |
| `day` | int |
| `original_year` | int |
| `original_month` | int |
| `original_day` | int |

### Genre & Classification
| Field | Type |
|-------|------|
| `genres` | str |
| `style` | str |
| `grouping` | str |
| `comp` | int (bool) |
| `albumtype` | str |
| `albumtypes` | str |

### Audio Technical Info
| Field | Type |
|-------|------|
| `length` | float (seconds) |
| `bitrate` | int (bps) |
| `bitrate_mode` | str |
| `format` | str (e.g. "MP3", "FLAC") |
| `samplerate` | int (Hz) |
| `bitdepth` | int |
| `channels` | int |
| `encoder` | str |
| `encoder_info` | str |
| `encoder_settings` | str |

### ReplayGain
| Field | Type |
|-------|------|
| `rg_track_gain` | float |
| `rg_track_peak` | float |
| `rg_album_gain` | float |
| `rg_album_peak` | float |
| `r128_track_gain` | float |
| `r128_album_gain` | float |

### MusicBrainz IDs
| Field |
|-------|
| `mb_trackid` |
| `mb_albumid` |
| `mb_artistid` |
| `mb_artistids` |
| `mb_albumartistid` |
| `mb_albumartistids` |
| `mb_releasetrackid` |
| `mb_releasegroupid` |

### Discogs IDs
| Field |
|-------|
| `discogs_albumid` |
| `discogs_artistid` |
| `discogs_labelid` |

### Release Info
| Field | Type |
|-------|------|
| `label` | str |
| `barcode` | str |
| `catalognum` | str |
| `country` | str |
| `language` | str |
| `script` | str |
| `media` | str |
| `albumstatus` | str |
| `albumdisambig` | str |
| `releasegroupdisambig` | str |
| `release_group_title` | str |
| `asin` | str |
| `isrc` | str |

### Other
| Field | Type |
|-------|------|
| `lyrics` | str |
| `comments` | str |
| `bpm` | int |
| `initial_key` | str |
| `acoustid_fingerprint` | str |
| `acoustid_id` | str |
| `composer` | str |
| `composer_sort` | str |
| `lyricist` | str |
| `arranger` | str |
| `remixer` | str |
| `work` | str |
| `mb_workid` | str |
| `work_disambig` | str |
| `trackdisambig` | str |
| `disctitle` | str |
| `added` | float (Unix timestamp) |
| `mtime` | float (Unix timestamp) |

---

## Album Fields

| Field | Type |
|-------|------|
| `id` | int |
| `artpath` | bytes (filesystem path to cover art) |
| `album` | str |
| `albumartist` | str |
| `albumartist_sort` | str |
| `albumartist_credit` | str |
| `albumartists` | str |
| `albumartists_sort` | str |
| `albumartists_credit` | str |
| `year` | int |
| `month` | int |
| `day` | int |
| `original_year` | int |
| `original_month` | int |
| `original_day` | int |
| `disctotal` | int |
| `comp` | int (bool) |
| `genres` | str |
| `style` | str |
| `label` | str |
| `barcode` | str |
| `catalognum` | str |
| `country` | str |
| `language` | str |
| `script` | str |
| `albumstatus` | str |
| `albumtype` | str |
| `albumtypes` | str |
| `albumdisambig` | str |
| `releasegroupdisambig` | str |
| `release_group_title` | str |
| `asin` | str |
| `rg_album_gain` | float |
| `rg_album_peak` | float |
| `r128_album_gain` | float |
| `mb_albumid` | str |
| `mb_albumartistid` | str |
| `mb_albumartistids` | str |
| `mb_releasegroupid` | str |
| `discogs_albumid` | int |
| `discogs_artistid` | int |
| `discogs_labelid` | int |
| `added` | float (Unix timestamp) |

### Album methods

```python
album.items()           # returns list of Item objects in this album
album.item_dir()        # returns path (bytes) to album directory
album.art_destination() # returns expected art path
```

---

## Query Syntax

Queries are strings passed to `lib.items()` or `lib.albums()`.

### Keyword (substring match across key fields)
```
love            # matches title, artist, album, albumartist, genre, comments
```

### Field-specific
```
artist:beatles
album:abbey
year:2012
format:FLAC
```

### Regular expression (double colon)
```
artist::Ann(a|ie)
title::^$          # empty title
```

### Numeric ranges (two dots)
```
year:1990..1999
bitrate:..128000
year:2010..        # 2010 and later
length:..4:30      # under 4m30s
```

### Date queries (added/mtime)
```
added:2024
added:2023..2024
added:-1w..        # added in the last week (relative)
mtime:2024-01-01..2024-06-30
```

### Boolean AND (default, space-separated)
```
artist:radiohead format:FLAC
```

### Boolean OR (comma)
```
artist:beatles , artist:stones
```

### Negation (^ or -)
```
^love              # does NOT contain "love"
^year:1980..1989
```

### Sort order (field+ or field-)
```
year+              # ascending by year
year-              # descending
genre+ year+       # multi-sort
```

### Path query
```
path:/mnt/nfs/music/Rock
```

### Programmatic query objects

```python
from beets.dbcore.query import SubstringQuery, RegexpQuery, NumericQuery, AndQuery

q = SubstringQuery('artist', 'beatles')
items = lib.items(q)
```

---

## Direct SQLite Access (no beets required)

For a GUI that reads only (no writes), direct SQLite is the simplest approach:

```python
import sqlite3

conn = sqlite3.connect('/mnt/nfs/musiclibrary.db')
conn.row_factory = sqlite3.Row  # access columns by name

# All albums
albums = conn.execute(
    "SELECT id, albumartist, album, year, artpath FROM albums ORDER BY albumartist, year"
).fetchall()

# Tracks for an album
items = conn.execute(
    "SELECT id, path, title, artist, track, disc, length, format, bitrate "
    "FROM items WHERE album_id = ? ORDER BY disc, track",
    (album_id,)
).fetchall()

# Full-text search
results = conn.execute(
    "SELECT * FROM items WHERE title LIKE ? OR artist LIKE ?",
    (f'%{query}%', f'%{query}%')
).fetchall()
```

Flexible plugin fields are stored in separate key-value tables:
```sql
SELECT * FROM item_attributes WHERE entity_id = ?;
SELECT * FROM album_attributes WHERE entity_id = ?;
```

---

## Plugin Architecture (for future extension)

If the GUI needs to trigger beets operations (import, tag, etc.), a plugin is the right integration point.

```python
# beetsplug/myguiplugin.py
from beets.plugins import BeetsPlugin

class MyGUIPlugin(BeetsPlugin):
    def __init__(self):
        super().__init__()
        self.register_listener('library_opened', self.on_library_open)
        self.register_listener('database_change', self.on_db_change)

    def on_library_open(self, lib):
        # lib is the Library object — store reference for GUI use
        pass

    def on_db_change(self, lib, model):
        # model is the Item or Album that changed — trigger UI refresh
        pass
```

Key events for a GUI:
| Event | When fired |
|-------|-----------|
| `library_opened` | beets starts up, lib ready |
| `database_change` | any item/album modified |
| `album_imported` | album added via import |
| `item_imported` | singleton added |
| `item_moved` | file moved |
| `item_removed` | item deleted |

---

## Recommended GUI Architecture

Given the read-heavy nature of browsing a music library, **direct SQLite access** is recommended over using the beets Python API for the GUI backend. This avoids loading the full beets stack and is faster.

**Suggested stack:**
- **Backend**: Python with `sqlite3` module directly querying `/mnt/nfs/musiclibrary.db`
- **Frontend options**:
  - PyQt6 / PySide6 — native desktop, richest widget set
  - Textual — terminal UI, fast to develop
  - Flask/FastAPI + Vue/React — web UI, accessible from any device on the network

**Key UI features to implement:**
1. Album browser (grid/list) with cover art from `albums.artpath`
2. Track list per album
3. Search/filter bar using SQL LIKE or FTS
4. Sort by artist, year, genre, format
5. Now-playing / playback integration (MPD or direct via python-vlc)
6. Stats view (format breakdown, bitrate distribution, etc.)
