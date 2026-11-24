"""Weekly meal plans and the shopping list built from them."""
from __future__ import annotations

import datetime as dt
import sqlite3

from ..importer.ingredients import WATER_RE, canonical_name, classify_aisle
from .recipes import effective_aisle, get_summary, group_names, split_each
from .units import shopping_display, to_base, unit_family

AISLE_ORDER = ["Produce", "Meat & Fish", "Dairy & Eggs", "Pasta, Rice & Grains", "Sauces & Pantry",
               "Spices & Seasonings", "Other"]
EXTRAS_AISLE = "Extras"


def week_start(day: dt.date) -> str:
    return (day - dt.timedelta(days=day.weekday())).isoformat()


def get_or_create_plan(conn: sqlite3.Connection, day: dt.date) -> int:
    ws = week_start(day)
    conn.execute("INSERT OR IGNORE INTO meal_plans (week_start) VALUES (?)", (ws,))
    return conn.execute("SELECT id FROM meal_plans WHERE week_start = ?", (ws,)).fetchone()[0]


def plan_exists(conn: sqlite3.Connection, plan_id: int) -> bool:
    return conn.execute("SELECT 1 FROM meal_plans WHERE id = ?", (plan_id,)).fetchone() is not None


def get_plan(conn: sqlite3.Connection, plan_id: int) -> dict | None:
    plan = conn.execute("SELECT id, week_start FROM meal_plans WHERE id = ?", (plan_id,)).fetchone()
    if not plan:
        return None
    entries = []
    totals = {"servings": 0.0, "kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    rows = conn.execute("SELECT id, recipe_id, servings, day, position FROM plan_entries WHERE plan_id = ? "
                        "ORDER BY position, id", (plan_id,)).fetchall()
    for e in rows:
        recipe = get_summary(conn, e["recipe_id"])
        if recipe is None:
            continue
        entries.append({"id": e["id"], "recipe": recipe, "servings": e["servings"], "day": e["day"],
                        "position": e["position"]})
        totals["servings"] += e["servings"]
        for k in ("kcal", "protein", "carbs", "fat"):
            totals[k] += (recipe[k] or 0) * e["servings"]
    return {"id": plan["id"], "week_start": plan["week_start"], "entries": entries,
            "totals": {k: round(v, 1) for k, v in totals.items()}}


def add_entry(conn: sqlite3.Connection, plan_id: int, recipe_id: int, servings: float | None, day: str | None) -> None:
    if servings is None:
        row = conn.execute("SELECT servings FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        servings = row["servings"] or 1
    pos = conn.execute("SELECT coalesce(max(position) + 1, 0) FROM plan_entries WHERE plan_id = ?",
                       (plan_id,)).fetchone()[0]
    conn.execute("INSERT INTO plan_entries (plan_id, recipe_id, servings, day, position) VALUES (?, ?, ?, ?, ?)",
                 (plan_id, recipe_id, servings, day, pos))


# ---------------------------------------------------------------- shopping list

def _display_name(canonical: str) -> str:
    return canonical[:1].upper() + canonical[1:]


def _lines(conn: sqlite3.Connection, plan_id: int):
    """Yield (canonical, aisle, qty, unit, recipe_title) for every shoppable line of the plan, scaled."""
    rows = conn.execute("""
        SELECT e.servings AS entry_servings, r.id AS recipe_id, r.servings AS recipe_servings, r.title,
               i.qty, i.qty_max, i.unit, i.item, i.canonical, i.aisle, i.each_of, g.name AS group_name
        FROM plan_entries e
        JOIN recipes r ON r.id = e.recipe_id
        JOIN ingredients i ON i.recipe_id = r.id AND i.kind = 'item'
        JOIN ingredient_groups g ON g.id = i.group_id
        WHERE e.plan_id = ?
        ORDER BY e.position, e.id, i.group_id, i.position, i.id
    """, (plan_id,)).fetchall()
    groups: dict[int, list[str]] = {}
    for r in rows:
        if r["recipe_id"] not in groups:
            groups[r["recipe_id"]] = group_names(conn, r["recipe_id"])
        factor = r["entry_servings"] / (r["recipe_servings"] or 1)
        # buy for the top of a range ("25-30g" -> 30 g)
        amount = r["qty_max"] if r["qty_max"] is not None else r["qty"]
        qty = amount * factor if amount is not None else None
        each, _ = split_each(r["each_of"])
        if each:
            for name in each:
                canon = canonical_name(name)
                if not canon or WATER_RE.fullmatch(canon):
                    continue
                yield canon, classify_aisle(canon), qty, r["unit"], r["title"]
        else:
            canon = (r["canonical"] or canonical_name(r["item"] or "")).removeprefix("or ")
            aisle = effective_aisle(r["aisle"], canon, r["unit"], r["group_name"], groups[r["recipe_id"]])
            if not canon or aisle == "Skip":
                continue
            yield canon, aisle, qty, r["unit"], r["title"]


def shopping_list(conn: sqlite3.Connection, plan_id: int) -> dict:
    items: dict[str, dict] = {}
    as_needed: list[tuple[str, str, str]] = []
    for canon, aisle, qty, unit, title in _lines(conn, plan_id):
        if qty is None:
            as_needed.append((canon, aisle, title))
            continue
        family = unit_family(unit)
        key = f"{canon}|{family}"
        amount, base_unit = to_base(qty, unit)
        it = items.get(key)
        if it is None:
            it = items[key] = {"key": key, "name": _display_name(canon), "qty": 0.0, "unit": base_unit,
                               "recipes": [], "aisle": aisle, "canon": canon}
        it["qty"] += amount
        if title not in it["recipes"]:
            it["recipes"].append(title)

    # Unquantified lines ("Salt", "Fresh Parsley") join a quantified item of the same name when there is one.
    for canon, aisle, title in as_needed:
        target = next((it for it in items.values() if it["canon"] == canon), None)
        if target is None:
            key = f"{canon}|any"
            target = items.setdefault(key, {"key": key, "name": _display_name(canon), "qty": None, "unit": None,
                                            "recipes": [], "aisle": aisle, "canon": canon})
        if title not in target["recipes"]:
            target["recipes"].append(title)

    checks = {r["key"]: bool(r["checked"])
              for r in conn.execute("SELECT key, checked FROM shopping_checks WHERE plan_id = ?", (plan_id,))}
    by_aisle: dict[str, list[dict]] = {}
    for it in items.values():
        qty = round(it["qty"], 2) if it["qty"] is not None else None
        by_aisle.setdefault(it["aisle"] if it["aisle"] in AISLE_ORDER else "Other", []).append({
            "key": it["key"], "name": it["name"], "qty": qty, "unit": it["unit"],
            "display": shopping_display(qty, it["unit"]), "recipes": it["recipes"],
            "checked": checks.get(it["key"], False), "extra": False,
        })
    aisles = [{"aisle": a, "items": sorted(by_aisle[a], key=lambda i: (i["name"].lower(), i["key"]))}
              for a in AISLE_ORDER if a in by_aisle]
    extras = [{"key": f"extra:{r['id']}", "name": r["text"], "qty": None, "unit": None, "display": "",
               "recipes": [], "checked": bool(r["checked"]), "extra": True}
              for r in conn.execute("SELECT id, text, checked FROM shopping_extras WHERE plan_id = ? ORDER BY id",
                                    (plan_id,))]
    if extras:
        aisles.append({"aisle": EXTRAS_AISLE, "items": extras})
    return {"plan_id": plan_id, "aisles": aisles}


def set_checked(conn: sqlite3.Connection, plan_id: int, key: str, checked: bool) -> bool:
    """Persist a tick. Returns False for an unknown extra."""
    if key.startswith("extra:"):
        try:
            extra_id = int(key.split(":", 1)[1])
        except ValueError:
            return False
        cur = conn.execute("UPDATE shopping_extras SET checked = ? WHERE id = ? AND plan_id = ?",
                           (int(checked), extra_id, plan_id))
        return cur.rowcount > 0
    conn.execute("""INSERT INTO shopping_checks (plan_id, key, checked) VALUES (?, ?, ?)
                    ON CONFLICT(plan_id, key) DO UPDATE SET checked = excluded.checked""",
                 (plan_id, key, int(checked)))
    return True
