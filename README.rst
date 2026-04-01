beets-webplayer
===============

A self-hosted web music player and library manager built on top of `beets <https://beets.io>`_.

Browse your beets music library, stream tracks directly in the browser, manage
imports, and maintain your collection — all from a clean dark-themed web UI.

.. image:: https://img.shields.io/badge/backend-FastAPI-009688?style=flat
.. image:: https://img.shields.io/badge/frontend-Vue%203-42b883?style=flat
.. image:: https://img.shields.io/badge/requires-beets-blueviolet?style=flat

Features
--------

- **Album browser** — grid and list views with filtering by genre, format, year range, and artist
- **Artist view** — per-artist album list with blurred header art
- **Track playback** — HTML5 audio streaming with range request support, queue management, and player bar
- **Import UI** — browser-based beets import with candidate selection and track comparison
- **Library management** — edit track/album metadata, relocate artist files, remove albums
- **Album art** — served directly from your beets library

Stack
-----

- **Backend**: Python / FastAPI — thin API layer over the beets SQLite library database
- **Frontend**: Vue 3 + TypeScript + Vite — single-page app served separately

Requirements
------------

- `beets <https://beets.io>`_ must be installed and your music library already set up.
  This project does not manage or modify beets itself — it reads from the beets
  SQLite database and calls beets CLI commands for import and file operations.
- Python 3.11+
- Node.js 18+

Installation
------------

Clone the repo and run the install script::

    git clone https://github.com/Beau-a/beets-webplayer.git
    cd beets-webplayer
    ./install.sh

The script will:

- Check for required dependencies (python3, pip, node, npm, beet)
- Ask for your beets library database path, music root directory, import base path, and backend port
- Write a ``backend/.env`` configuration file
- Create a Python virtualenv and install backend dependencies
- Install frontend Node packages

Configuration
-------------

All runtime configuration lives in ``backend/.env`` (created by the install script).
A template is provided at ``backend/.env.example``::

    BEETS_DB_PATH=/path/to/musiclibrary.db
    MUSIC_BASE_PATH=/path/to/music
    IMPORT_BASE_PATH=/path/to/incoming
    PORT=5000

Running
-------

Start backend and frontend in separate terminals::

    make backend      # FastAPI on http://localhost:5000
    make frontend     # Vite dev server on http://localhost:3000

Or build the frontend for production and serve everything through the backend::

    cd frontend && npm run build
    make backend      # serves SPA + API at http://localhost:5000

Note
----

This project is a fork of the `beets <https://github.com/beetbox/beets>`_ repository
but is an independent application built alongside beets, not a modification of it.
The beets source code is not used directly — only the beets library database and CLI.
