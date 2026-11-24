"""Meal plans and shopping lists."""
from __future__ import annotations

import datetime as dt
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from .. import plans as svc
from ..deps import get_conn
from ..models import CheckInput, EntryCreate, EntryPatch, ExtraInput, Plan, ShoppingList

router = APIRouter(prefix="/api/plans", tags=["plans"])


def _plan_or_404(conn: sqlite3.Connection, plan_id: int) -> None:
    if not svc.plan_exists(conn, plan_id):
        raise HTTPException(404, "Plan not found")


def _entry_or_404(conn: sqlite3.Connection, plan_id: int, entry_id: int) -> None:
    _plan_or_404(conn, plan_id)
    if not conn.execute("SELECT 1 FROM plan_entries WHERE id = ? AND plan_id = ?", (entry_id, plan_id)).fetchone():
        raise HTTPException(404, "Plan entry not found")


@router.get("/current", response_model=Plan)
def current_plan(week: dt.date | None = None, conn: sqlite3.Connection = Depends(get_conn)):
    plan_id = svc.get_or_create_plan(conn, week or dt.date.today())
    conn.commit()
    return svc.get_plan(conn, plan_id)


@router.post("/{plan_id}/entries", response_model=Plan)
def add_entry(plan_id: int, data: EntryCreate, conn: sqlite3.Connection = Depends(get_conn)):
    _plan_or_404(conn, plan_id)
    if not conn.execute("SELECT 1 FROM recipes WHERE id = ?", (data.recipe_id,)).fetchone():
        raise HTTPException(404, "Recipe not found")
    svc.add_entry(conn, plan_id, data.recipe_id, data.servings, data.day)
    conn.commit()
    return svc.get_plan(conn, plan_id)


@router.patch("/{plan_id}/entries/{entry_id}", response_model=Plan)
def update_entry(plan_id: int, entry_id: int, data: EntryPatch, conn: sqlite3.Connection = Depends(get_conn)):
    _entry_or_404(conn, plan_id, entry_id)
    sent = data.model_fields_set
    changes = {}
    if "servings" in sent:
        if data.servings is None:
            raise HTTPException(422, "servings cannot be null")
        changes["servings"] = data.servings
    if "day" in sent:
        changes["day"] = data.day  # null moves it to "anytime this week"
    if "position" in sent and data.position is not None:
        changes["position"] = data.position
    if changes:
        sets = ", ".join(f"{k} = ?" for k in changes)
        conn.execute(f"UPDATE plan_entries SET {sets} WHERE id = ?", [*changes.values(), entry_id])
        conn.commit()
    return svc.get_plan(conn, plan_id)


@router.delete("/{plan_id}/entries/{entry_id}", response_model=Plan)
def delete_entry(plan_id: int, entry_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    _entry_or_404(conn, plan_id, entry_id)
    conn.execute("DELETE FROM plan_entries WHERE id = ?", (entry_id,))
    conn.commit()
    return svc.get_plan(conn, plan_id)


@router.get("/{plan_id}/shopping", response_model=ShoppingList)
def shopping(plan_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    _plan_or_404(conn, plan_id)
    return svc.shopping_list(conn, plan_id)


@router.put("/{plan_id}/shopping/checked", response_model=ShoppingList)
def set_checked(plan_id: int, data: CheckInput, conn: sqlite3.Connection = Depends(get_conn)):
    _plan_or_404(conn, plan_id)
    if not svc.set_checked(conn, plan_id, data.key, data.checked):
        raise HTTPException(404, "Extra item not found")
    conn.commit()
    return svc.shopping_list(conn, plan_id)


@router.post("/{plan_id}/shopping/extras", response_model=ShoppingList)
def add_extra(plan_id: int, data: ExtraInput, conn: sqlite3.Connection = Depends(get_conn)):
    _plan_or_404(conn, plan_id)
    text = data.text.strip()
    if not text:
        raise HTTPException(422, "text cannot be empty")
    conn.execute("INSERT INTO shopping_extras (plan_id, text) VALUES (?, ?)", (plan_id, text))
    conn.commit()
    return svc.shopping_list(conn, plan_id)


@router.delete("/{plan_id}/shopping/extras/{extra_id}", response_model=ShoppingList)
def delete_extra(plan_id: int, extra_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    _plan_or_404(conn, plan_id)
    cur = conn.execute("DELETE FROM shopping_extras WHERE id = ? AND plan_id = ?", (extra_id, plan_id))
    if cur.rowcount == 0:
        raise HTTPException(404, "Extra item not found")
    conn.commit()
    return svc.shopping_list(conn, plan_id)
