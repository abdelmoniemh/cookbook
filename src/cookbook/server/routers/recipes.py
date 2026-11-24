from __future__ import annotations

import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from .. import recipes as repo
from ..deps import get_conn
from ..models import FavouriteInput, RecipeDetail, RecipeInput, RecipeList, RecipeSummary

router = APIRouter(prefix="/api/recipes", tags=["recipes"])

SORTS = {
    "title": "r.title COLLATE NOCASE ASC, r.id",
    "protein": "r.protein IS NULL, r.protein DESC, r.title COLLATE NOCASE",
    "kcal": "r.kcal IS NULL, r.kcal ASC, r.title COLLATE NOCASE",
    "recent": "r.created_at DESC, r.id DESC",
}


@router.get("", response_model=RecipeList)
def list_recipes(
    q: str | None = None,
    tag: list[str] = Query(default=[]),
    source: int | None = None,
    favourite: bool | None = None,
    max_kcal: float | None = None,
    min_protein: float | None = None,
    sort: Literal["title", "protein", "kcal", "recent"] = "title",
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    conn: sqlite3.Connection = Depends(get_conn),
):
    where, params = [], []
    if q and q.strip():
        match = repo.fts_query(q)
        if match:
            where.append("r.id IN (SELECT rowid FROM recipe_search WHERE recipe_search MATCH ?)")
            params.append(match)
    for t in tag:
        where.append("EXISTS (SELECT 1 FROM json_each(r.tags) WHERE value = ?)")
        params.append(t)
    if source is not None:
        where.append("r.source_id = ?")
        params.append(source)
    if favourite is not None:
        where.append("r.favourite = ?")
        params.append(int(favourite))
    if max_kcal is not None:
        where.append("r.kcal <= ?")
        params.append(max_kcal)
    if min_protein is not None:
        where.append("r.protein >= ?")
        params.append(min_protein)
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    total = conn.execute(f"SELECT count(*) FROM recipes r{clause}", params).fetchone()[0]
    rows = conn.execute(f"{repo.SUMMARY_SQL}{clause} ORDER BY {SORTS[sort]} LIMIT ? OFFSET ?",
                        [*params, limit, offset]).fetchall()
    return {"items": [repo.summary(r) for r in rows], "total": total}


@router.get("/{id_or_slug}", response_model=RecipeDetail)
def get_recipe(id_or_slug: str, servings: float | None = Query(default=None, gt=0),
               conn: sqlite3.Connection = Depends(get_conn)):
    rid = repo.resolve_id(conn, id_or_slug)
    if rid is None:
        raise HTTPException(404, "Recipe not found")
    return repo.get_detail(conn, rid, servings)


@router.post("", response_model=RecipeDetail, status_code=201)
def create_recipe(data: RecipeInput, conn: sqlite3.Connection = Depends(get_conn)):
    rid = repo.save(conn, data)
    conn.commit()
    return repo.get_detail(conn, rid)


def _require(conn: sqlite3.Connection, recipe_id: int) -> None:
    if not conn.execute("SELECT 1 FROM recipes WHERE id = ?", (recipe_id,)).fetchone():
        raise HTTPException(404, "Recipe not found")


@router.put("/{recipe_id}", response_model=RecipeDetail)
def update_recipe(recipe_id: int, data: RecipeInput, conn: sqlite3.Connection = Depends(get_conn)):
    _require(conn, recipe_id)
    repo.save(conn, data, recipe_id)
    conn.commit()
    return repo.get_detail(conn, recipe_id)


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    _require(conn, recipe_id)
    repo.delete(conn, recipe_id)
    conn.commit()
    return Response(status_code=204)


@router.put("/{recipe_id}/favourite", response_model=RecipeSummary)
def set_favourite(recipe_id: int, data: FavouriteInput, conn: sqlite3.Connection = Depends(get_conn)):
    _require(conn, recipe_id)
    conn.execute("UPDATE recipes SET favourite = ? WHERE id = ?", (int(data.favourite), recipe_id))
    conn.commit()
    return repo.get_summary(conn, recipe_id)
