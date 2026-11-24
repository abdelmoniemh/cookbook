"""Tags, sources, health."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..deps import get_conn
from ..models import Health, SourceInfo, TagCount

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/tags", response_model=list[TagCount])
def tags(conn: sqlite3.Connection = Depends(get_conn)):
    rows = conn.execute("""SELECT j.value AS tag, count(*) AS count FROM recipes r, json_each(r.tags) j
                           GROUP BY j.value ORDER BY count DESC, j.value""").fetchall()
    return [{"tag": r["tag"], "count": r["count"]} for r in rows]


@router.get("/sources", response_model=list[SourceInfo])
def sources(conn: sqlite3.Connection = Depends(get_conn)):
    rows = conn.execute("""SELECT s.id, s.name, count(r.id) AS recipe_count FROM sources s
                           LEFT JOIN recipes r ON r.source_id = s.id GROUP BY s.id ORDER BY s.name""").fetchall()
    return [dict(r) for r in rows]


@router.get("/health", response_model=Health)
def health(conn: sqlite3.Connection = Depends(get_conn)):
    return {"ok": True, "recipes": conn.execute("SELECT count(*) FROM recipes").fetchone()[0]}
