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

-- Meal planning and shopping (written by the web app)
CREATE TABLE IF NOT EXISTS meal_plans (
    id         INTEGER PRIMARY KEY,
    week_start TEXT NOT NULL UNIQUE,   -- ISO date of the Monday
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plan_entries (
    id        INTEGER PRIMARY KEY,
    plan_id   INTEGER NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    servings  REAL NOT NULL,
    day       TEXT,                    -- mon..sun, NULL = any day this week
    position  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS plan_entries_plan ON plan_entries(plan_id);

CREATE TABLE IF NOT EXISTS shopping_checks (
    plan_id INTEGER NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    key     TEXT NOT NULL,             -- ShoppingItem.key: canonical|family
    checked INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (plan_id, key)
);

CREATE TABLE IF NOT EXISTS shopping_extras (
    id      INTEGER PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    text    TEXT NOT NULL,
    checked INTEGER NOT NULL DEFAULT 0
);
"""


def open_db(data_dir: Path, check_same_thread: bool = True) -> sqlite3.Connection:
    """Open an existing database without running the schema (cheap; used per web request)."""
    conn = sqlite3.connect(Path(data_dir) / "cookbook.db", check_same_thread=check_same_thread, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def connect(data_dir: Path = DEFAULT_DATA_DIR, check_same_thread: bool = True) -> sqlite3.Connection:
    """Open the database, creating the data folder and any missing tables."""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "images").mkdir(exist_ok=True)
    conn = open_db(data_dir, check_same_thread)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA)
    migrate(conn)
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    """Small in-place upgrades for databases created by older versions."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(recipes)")}
    if "collection" not in cols:
        conn.execute("ALTER TABLE recipes ADD COLUMN collection TEXT")  # 'meal_prep' | 'recipes'
    if "category" not in cols:
        conn.execute("ALTER TABLE recipes ADD COLUMN category TEXT")    # dish type, see importer.tags.CATEGORIES
    missing = conn.execute("""SELECT r.id, r.title, r.tags, s.name FROM recipes r
                              LEFT JOIN sources s ON s.id = r.source_id
                              WHERE r.collection IS NULL OR r.category IS NULL""").fetchall()
    if missing:
        from .importer.tags import derive_category, derive_collection
        conn.executemany(
            "UPDATE recipes SET collection = coalesce(collection, ?), category = coalesce(category, ?) WHERE id = ?",
            [(derive_collection(r[1], json.loads(r[2] or "[]"), r[3]), derive_category(r[1], json.loads(r[2] or "[]")),
              r[0]) for r in missing])
        conn.commit()


def ingredient_text(conn: sqlite3.Connection, recipe_id: int) -> str:
    rows = conn.execute("SELECT item FROM ingredients WHERE recipe_id = ? AND kind = 'item' ORDER BY id",
                        (recipe_id,)).fetchall()
    return " ".join(r[0] or "" for r in rows)


def index_recipe(conn: sqlite3.Connection, recipe_id: int) -> None:
    """Refresh one recipe's row in the full-text index (or drop it if the recipe is gone)."""
    conn.execute("DELETE FROM recipe_search WHERE rowid = ?", (recipe_id,))
    r = conn.execute("SELECT title, coalesce(blurb, ''), tags FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if r:
        conn.execute("INSERT INTO recipe_search(rowid, title, blurb, ingredients, tags) VALUES (?, ?, ?, ?, ?)",
                     (recipe_id, r[0], r[1], ingredient_text(conn, recipe_id), " ".join(json.loads(r[2]))))


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
