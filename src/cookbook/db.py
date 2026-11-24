"""SQLite schema shared by the importer and the web server.

The database lives outside the repository (default: ``~/.local/share/cookbook/cookbook.db``) because it holds
recipe content from the user's own cookbooks.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

DEFAULT_DATA_DIR = Path(os.environ.get("COOKBOOK_DATA_DIR", Path.home() / ".local/share/cookbook"))

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    file_name   TEXT NOT NULL UNIQUE,
    file_sha256 TEXT,
    layout      TEXT,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recipes (
    id            INTEGER PRIMARY KEY,
    source_id     INTEGER REFERENCES sources(id) ON DELETE SET NULL,  -- NULL for recipes added in the app
    source_page   INTEGER,
    source_number INTEGER,
    slug          TEXT NOT NULL UNIQUE,
    title         TEXT NOT NULL,
    blurb         TEXT,
    servings      REAL,           -- macros below are per serving
    servings_text TEXT,
    kcal          REAL,
    protein       REAL,
    carbs         REAL,
    fat           REAL,
    tags          TEXT NOT NULL DEFAULT '[]',  -- JSON array
    videos        TEXT NOT NULL DEFAULT '{}',  -- JSON object: site -> url
    image         TEXT,           -- file name inside <data dir>/images
    favourite     INTEGER NOT NULL DEFAULT 0,
    user_edited   INTEGER NOT NULL DEFAULT 0,  -- re-imports never overwrite edited recipes
    warnings      TEXT NOT NULL DEFAULT '[]',
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingredient_groups (
    id        INTEGER PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    position  INTEGER NOT NULL,
    name      TEXT,
    note      TEXT
);

CREATE TABLE IF NOT EXISTS ingredients (
    id          INTEGER PRIMARY KEY,
    group_id    INTEGER NOT NULL REFERENCES ingredient_groups(id) ON DELETE CASCADE,
    recipe_id   INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    kind        TEXT NOT NULL DEFAULT 'item',  -- 'item' or 'note'
    raw         TEXT NOT NULL,
    qty         REAL,
    qty_max     REAL,
    unit        TEXT,
    alt_measure TEXT,
    item        TEXT,
    prep        TEXT,
    note        TEXT,
    canonical   TEXT,
    aisle       TEXT,
    each_of     TEXT NOT NULL DEFAULT '[]'  -- JSON array: "1 tsp each Salt, Paprika"
);
CREATE INDEX IF NOT EXISTS ingredients_canonical ON ingredients(canonical);

CREATE TABLE IF NOT EXISTS steps (
    id        INTEGER PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    position  INTEGER NOT NULL,
    text      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id        INTEGER PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    position  INTEGER NOT NULL,
    text      TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS recipe_search USING fts5(
    title, blurb, ingredients, tags, tokenize='porter unicode61'
);
"""


def connect(data_dir: Path = DEFAULT_DATA_DIR) -> sqlite3.Connection:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "images").mkdir(exist_ok=True)
    conn = sqlite3.connect(data_dir / "cookbook.db")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def reindex_search(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM recipe_search")
    rows = conn.execute("""
        SELECT r.id, r.title, coalesce(r.blurb, ''), r.tags,
               coalesce(group_concat(i.item, ' '), '') AS ings
        FROM recipes r LEFT JOIN ingredients i ON i.recipe_id = r.id AND i.kind = 'item'
        GROUP BY r.id
    """).fetchall()
    conn.executemany(
        "INSERT INTO recipe_search(rowid, title, blurb, ingredients, tags) VALUES (?, ?, ?, ?, ?)",
        [(r[0], r[1], r[2], r[4], " ".join(json.loads(r[3]))) for r in rows],
    )
