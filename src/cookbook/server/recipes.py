"""Recipe reads and writes (plain sqlite3)."""
from __future__ import annotations

import json
import re
import sqlite3

from .. import db as dbmod
from ..importer.cli import slugify
from ..importer.ingredients import WATER_RE, classify_aisle, is_prep_word, parse_ingredient
from ..importer.parsers import is_component_reference
from .units import ingredient_display

SUMMARY_SQL = """
    SELECT r.id, r.slug, r.title, r.blurb, r.image, r.kcal, r.protein, r.carbs, r.fat, r.servings, r.tags,
           r.favourite, r.source_id, s.name AS source_name
    FROM recipes r LEFT JOIN sources s ON s.id = r.source_id
"""
DETAIL_SQL = SUMMARY_SQL.replace("r.favourite,", "r.favourite, r.servings_text, r.videos, r.source_page, r.user_edited,")


def summary(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "slug": row["slug"],
        "title": row["title"],
        "blurb": row["blurb"] or None,
        "image_url": f"/images/{row['image']}" if row["image"] else None,
        "kcal": row["kcal"],
        "protein": row["protein"],
        "carbs": row["carbs"],
        "fat": row["fat"],
        "servings": row["servings"],
        "tags": json.loads(row["tags"] or "[]"),
        "source": {"id": row["source_id"], "name": row["source_name"]} if row["source_id"] is not None else None,
        "favourite": bool(row["favourite"]),
    }


def get_summary(conn: sqlite3.Connection, recipe_id: int) -> dict | None:
    row = conn.execute(SUMMARY_SQL + " WHERE r.id = ?", (recipe_id,)).fetchone()
    return summary(row) if row else None


def resolve_id(conn: sqlite3.Connection, id_or_slug: str) -> int | None:
    if id_or_slug.isdigit():
        row = conn.execute("SELECT id FROM recipes WHERE id = ?", (int(id_or_slug),)).fetchone()
        if row:
            return row[0]
    row = conn.execute("SELECT id FROM recipes WHERE slug = ?", (id_or_slug,)).fetchone()
    return row[0] if row else None


def _scaled(x: float | None, factor: float) -> float | None:
    return None if x is None else round(x * factor, 4)


def split_each(each_json: str | None) -> tuple[list[str], list[str]]:
    """Stored each_of list -> (real names, prep words that older imports mistook for names)."""
    each = json.loads(each_json or "[]")
    names = [e for e in each if not is_prep_word(e)]
    prep = [e for e in each if is_prep_word(e)]
    return (names if len(names) > 1 else []), prep


def group_names(conn: sqlite3.Connection, recipe_id: int) -> list[str]:
    return [r[0] for r in conn.execute("SELECT name FROM ingredient_groups WHERE recipe_id = ? AND name IS NOT NULL",
                                       (recipe_id,))]


def effective_aisle(aisle: str | None, canonical: str, unit: str | None, own_group: str | None,
                    groups: list[str]) -> str:
    """Stored aisle, except that "Skip" is re-checked: older imports skipped plain ingredients that shared a
    word with a group name ("Chicken Breast" in a "Chicken" group)."""
    if aisle != "Skip":
        return aisle or "Other"
    if not canonical or WATER_RE.fullmatch(canonical) or is_component_reference(canonical, unit, own_group, groups):
        return "Skip"
    return classify_aisle(canonical)


def ingredient(row: sqlite3.Row, factor: float = 1.0, own_group: str | None = None,
               groups: list[str] | None = None) -> dict:
    qty, qty_max = _scaled(row["qty"], factor), _scaled(row["qty_max"], factor)
    item = row["item"] or ""
    kind = row["kind"]
    each, stray_prep = split_each(row["each_of"])
    prep = "; ".join(filter(None, [row["prep"], *stray_prep])) or None
    if kind == "note":
        display = row["raw"]
    elif each and item == each[0]:  # "1 tsp each Salt, Cumin"
        display = ingredient_display(qty, qty_max, row["unit"], "each " + ", ".join(each), prep)
    else:
        display = ingredient_display(qty, qty_max, row["unit"], item, prep)
    return {
        "id": row["id"], "kind": kind, "raw": row["raw"], "qty": qty, "qty_max": qty_max, "unit": row["unit"],
        "alt_measure": row["alt_measure"], "item": item, "prep": prep, "note": row["note"],
        "canonical": row["canonical"] or "",
        "aisle": effective_aisle(row["aisle"], row["canonical"] or "", row["unit"], own_group, groups or []),
        "each_of": each, "display": display,
    }


def get_detail(conn: sqlite3.Connection, recipe_id: int, servings: float | None = None) -> dict | None:
    row = conn.execute(DETAIL_SQL + " WHERE r.id = ?", (recipe_id,)).fetchone()
    if not row:
        return None
    base = row["servings"] or 1
    factor = servings / base if servings else 1.0
    out = summary(row)
    groups = []
    names = group_names(conn, recipe_id)
    for g in conn.execute("SELECT id, name, note FROM ingredient_groups WHERE recipe_id = ? ORDER BY position, id",
                          (recipe_id,)):
        items = conn.execute("SELECT * FROM ingredients WHERE group_id = ? ORDER BY position, id", (g["id"],))
        groups.append({"name": g["name"] or None, "note": g["note"] or None,
                       "items": [ingredient(i, factor, g["name"], names) for i in items]})
    out.update(
        servings_text=row["servings_text"] or None,
        videos=json.loads(row["videos"] or "{}"),
        source_page=row["source_page"],
        scale=round(factor, 4),
        scaled_servings=servings if servings else row["servings"],
        groups=groups,
        steps=[r[0] for r in conn.execute("SELECT text FROM steps WHERE recipe_id = ? ORDER BY position, id",
                                          (recipe_id,))],
        notes=[r[0] for r in conn.execute("SELECT text FROM notes WHERE recipe_id = ? ORDER BY position, id",
                                          (recipe_id,))],
        user_edited=bool(row["user_edited"]),
    )
    return out


def unique_slug(conn: sqlite3.Connection, title: str, exclude_id: int | None = None) -> str:
    base = slugify(title) or "recipe"
    slug, n = base, 2
    while conn.execute("SELECT 1 FROM recipes WHERE slug = ? AND id IS NOT ?", (slug, exclude_id)).fetchone():
        slug, n = f"{base}-{n}", n + 1
    return slug


def _clean(lines: list[str]) -> list[str]:
    return [l.strip() for l in lines if l and l.strip()]


def save(conn: sqlite3.Connection, data, recipe_id: int | None = None) -> int:
    """Create (recipe_id None) or replace a recipe from a RecipeInput. Caller commits."""
    tags = list(dict.fromkeys(t.strip() for t in data.tags if t.strip()))
    values = dict(title=data.title.strip(), blurb=data.blurb, servings=data.servings, kcal=data.kcal,
                  protein=data.protein, carbs=data.carbs, fat=data.fat, tags=json.dumps(tags))
    if recipe_id is None:
        values["slug"] = unique_slug(conn, data.title)
        cols = ", ".join(values)
        recipe_id = conn.execute(f"INSERT INTO recipes ({cols}) VALUES ({', '.join(':' + k for k in values)})",
                                 values).lastrowid
    else:
        sets = ", ".join(f"{k} = :{k}" for k in values)
        conn.execute(f"UPDATE recipes SET {sets}, user_edited = 1, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
                     {**values, "id": recipe_id})
        for t in ("ingredient_groups", "ingredients", "steps", "notes"):
            conn.execute(f"DELETE FROM {t} WHERE recipe_id = ?", (recipe_id,))

    names = [g.name.strip() for g in data.groups if g.name and g.name.strip()]
    for gpos, g in enumerate(data.groups):
        gname = (g.name or "").strip() or None
        gid = conn.execute("INSERT INTO ingredient_groups (recipe_id, position, name, note) VALUES (?, ?, ?, ?)",
                           (recipe_id, gpos, gname, g.note)).lastrowid
        for pos, line in enumerate(_clean(g.lines)):
            i = parse_ingredient(line)
            if i.kind == "item" and is_component_reference(i.canonical, i.unit, gname, names):
                i.aisle = "Skip"  # "1 Serving Spice Mix" made in another group of this recipe
            conn.execute(
                """INSERT INTO ingredients (group_id, recipe_id, position, kind, raw, qty, qty_max, unit, alt_measure,
                   item, prep, note, canonical, aisle, each_of) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (gid, recipe_id, pos, i.kind, i.raw, i.qty, i.qty_max, i.unit, i.alt_measure, i.item, i.prep,
                 i.note, i.canonical, i.aisle, json.dumps(i.each)))
    conn.executemany("INSERT INTO steps (recipe_id, position, text) VALUES (?, ?, ?)",
                     [(recipe_id, n, s) for n, s in enumerate(_clean(data.steps))])
    conn.executemany("INSERT INTO notes (recipe_id, position, text) VALUES (?, ?, ?)",
                     [(recipe_id, n, s) for n, s in enumerate(_clean(data.notes))])
    dbmod.index_recipe(conn, recipe_id)
    return recipe_id


def delete(conn: sqlite3.Connection, recipe_id: int) -> None:
    conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    dbmod.index_recipe(conn, recipe_id)


def fts_query(q: str) -> str | None:
    """Turn free text into a safe FTS5 query: every word must match, as a prefix."""
    words = re.findall(r"\w+", q, flags=re.UNICODE)
    return " ".join(f'"{w}"*' for w in words) or None
