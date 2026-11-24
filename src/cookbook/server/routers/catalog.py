"""Tags, sources, health."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..deps import get_conn
from ...importer.tags import CATEGORIES, COLLECTIONS
from ..models import CollectionInfo, Health, SourceInfo, TagCount

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/tags", response_model=list[TagCount])
def tags(conn: sqlite3.Connection = Depends(get_conn)):
    rows = conn.execute("""SELECT j.value AS tag, count(*) AS count FROM recipes r, json_each(r.tags) j
                           GROUP BY j.value ORDER BY count DESC, j.value""").fetchall()
    return [{"tag": r["tag"], "count": r["count"]} for r in rows]


@router.get("/collections", response_model=list[CollectionInfo])
def collections(conn: sqlite3.Connection = Depends(get_conn)):
    """Meal prep vs everyday recipes, each with its dish types in display order (empty types left out)."""
    rows = conn.execute("""SELECT coalesce(collection, 'recipes') AS collection, category, count(*) AS n
                           FROM recipes GROUP BY 1, 2""").fetchall()
    order = {c: i for i, c in enumerate(CATEGORIES)}
    out = []
    for col in COLLECTIONS:
        cats = sorted(((r["category"], r["n"]) for r in rows if r["collection"] == col),
                      key=lambda x: (order.get(x[0], len(order)), x[0] or ""))
        out.append({"collection": col, "count": sum(n for _, n in cats),
                    "categories": [{"category": c or "Proteins & mains", "count": n} for c, n in cats]})
    return out


@router.get("/sources", response_model=list[SourceInfo])
def sources(conn: sqlite3.Connection = Depends(get_conn)):
    rows = conn.execute("""SELECT s.id, s.name, count(r.id) AS recipe_count FROM sources s
                           LEFT JOIN recipes r ON r.source_id = s.id GROUP BY s.id ORDER BY s.name""").fetchall()
    return [dict(r) for r in rows]


@router.get("/health", response_model=Health)
def health(conn: sqlite3.Connection = Depends(get_conn)):
    return {"ok": True, "recipes": conn.execute("SELECT count(*) FROM recipes").fetchone()[0]}
