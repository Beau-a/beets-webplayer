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

- `beets <https://beets.io>`_ must be installed and your library already set up.
  This project does not manage or modify beets itself — it reads from the beets
  SQLite database and calls beets CLI commands for import and file operations.
- Python 3.11+
- Node.js 18+ (for frontend dev / build)

Getting Started
---------------

1. Configure ``backend/app/config.py`` with your beets DB path and music base path.
2. Start the backend::

    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --host 0.0.0.0 --port 5000

3. Start the frontend (dev)::

    cd frontend
    npm install
    npm run dev

   Or build for production::

    npm run build

4. Open ``http://localhost:5173`` in your browser.

Note
----

This project is a fork of the `beets <https://github.com/beetbox/beets>`_ repository
but is an independent application built alongside beets, not a modification of it.
The beets source code is not used directly — only the beets library database and CLI.
