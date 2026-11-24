"""Command line entry point: ``cookbook-import <pdf> [<pdf> ...]``."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf

from .. import db as dbmod
from .parsers import PARSERS, RecipeDraft, parse_document
from .tags import derive_tags


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_image(doc: pymupdf.Document, xref: int, dest: Path, max_width: int = 1400) -> bool:
    try:
        pix = pymupdf.Pixmap(doc, xref)
        if pix.colorspace is None or pix.colorspace.n not in (1, 3) or pix.alpha:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        while pix.width > max_width:
            pix.shrink(1)
        dest.write_bytes(pix.tobytes("jpeg", jpg_quality=82))
        return True
    except Exception as e:  # images are nice-to-have
        print(f"  ! image {xref}: {e}", file=sys.stderr)
        return False


def store(conn, source_id: int, src_slug: str, doc: pymupdf.Document, r: RecipeDraft, images_dir: Path,
          meal_prep_book: bool, used_slugs: set[str]) -> str:
    slug = slugify(r.title) or f"recipe-{r.pages[0]}"
    if slug in used_slugs:  # same title twice (e.g. two "Healthy Pad Thai" pages)
        slug = f"{slug}-{src_slug}-p{r.pages[0]}"
    used_slugs.add(slug)

    existing = conn.execute("SELECT id, user_edited FROM recipes WHERE slug = ?", (slug,)).fetchone()
    if existing and existing["user_edited"]:
        return "kept (edited in app)"

    image_name = None
    if r.image_xref:
        image_name = f"{slug}.jpg"
        if not save_image(doc, r.image_xref, images_dir / image_name):
            image_name = None

    items = [i for g in r.groups for i in g.items if i.kind == "item"]
    tags = derive_tags(r.title, [i.canonical for i in items], meal_prep_book or "meal prep" in r.title.lower())
    values = dict(source_id=source_id, source_page=r.pages[0], source_number=r.number, slug=slug, title=r.title,
                  blurb=r.blurb, servings=r.servings, servings_text=r.servings_text, kcal=r.kcal,
                  protein=r.protein, carbs=r.carbs, fat=r.fat, tags=json.dumps(tags),
                  videos=json.dumps(r.videos), image=image_name, warnings=json.dumps(r.warnings))
    if existing:
        rid = existing["id"]
        sets = ", ".join(f"{k} = :{k}" for k in values)
        conn.execute(f"UPDATE recipes SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = :id", {**values, "id": rid})
        for t in ("ingredient_groups", "steps", "notes"):
            conn.execute(f"DELETE FROM {t} WHERE recipe_id = ?", (rid,))
        action = "updated"
    else:
        cols = ", ".join(values)
        rid = conn.execute(f"INSERT INTO recipes ({cols}) VALUES ({', '.join(':' + k for k in values)})", values).lastrowid
        action = "added"

    for gpos, g in enumerate(r.groups):
        gid = conn.execute("INSERT INTO ingredient_groups (recipe_id, position, name, note) VALUES (?, ?, ?, ?)",
                           (rid, gpos, g.name, g.note)).lastrowid
        for pos, i in enumerate(g.items):
            conn.execute(
                """INSERT INTO ingredients (group_id, recipe_id, position, kind, raw, qty, qty_max, unit, alt_measure,
                   item, prep, note, canonical, aisle, each_of) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (gid, rid, pos, i.kind, i.raw, i.qty, i.qty_max, i.unit, i.alt_measure, i.item, i.prep, i.note,
                 i.canonical, i.aisle, json.dumps(i.each)))
    conn.executemany("INSERT INTO steps (recipe_id, position, text) VALUES (?, ?, ?)",
                     [(rid, n, s) for n, s in enumerate(r.steps)])
    conn.executemany("INSERT INTO notes (recipe_id, position, text) VALUES (?, ?, ?)",
                     [(rid, n, s) for n, s in enumerate(r.notes)])
    return action


def import_pdf(conn, path: Path, data_dir: Path, name: str | None, layout: str | None) -> list[tuple[RecipeDraft, str]]:
    doc = pymupdf.open(path)
    name = name or path.stem
    digest = sha256(path)
    row = conn.execute("SELECT id FROM sources WHERE file_name = ?", (path.name,)).fetchone()
    if row:
        source_id = row["id"]
        conn.execute("UPDATE sources SET name = ?, file_sha256 = ?, imported_at = CURRENT_TIMESTAMP WHERE id = ?",
                     (name, digest, source_id))
    else:
        source_id = conn.execute("INSERT INTO sources (name, file_name, file_sha256) VALUES (?, ?, ?)",
                                 (name, path.name, digest)).lastrowid
    drafts = parse_document(doc, layout)
    used = {r["slug"] for r in conn.execute("SELECT slug FROM recipes WHERE source_id IS NOT ? ", (source_id,))}
    src_slug = slugify(name)[:12]
    results = []
    for r in drafts:
        results.append((r, store(conn, source_id, src_slug, doc, r, data_dir / "images", "meal prep" in name.lower(), used)))
    layouts = sorted({"two_page" if len(r.pages) == 2 else "single_page" for r in drafts})
    conn.execute("UPDATE sources SET layout = ? WHERE id = ?", (",".join(layouts), source_id))
    return results


def write_report(path: Path, per_file: dict[str, list[tuple[RecipeDraft, str]]]) -> None:
    out = ["# Import report", ""]
    for fname, results in per_file.items():
        out += [f"## {fname}", "", f"{len(results)} recipes. "
                f"{sum(1 for r, _ in results if r.warnings)} with warnings.", ""]
        for r, action in results:
            if r.warnings:
                out.append(f"- p{r.pages[0]} **{r.title}** ({action}): " + "; ".join(r.warnings))
        out.append("")
    path.write_text("\n".join(out))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Import cookbook PDFs into the local recipe database.")
    ap.add_argument("pdfs", nargs="+", type=Path)
    ap.add_argument("--data-dir", type=Path, default=dbmod.DEFAULT_DATA_DIR)
    ap.add_argument("--name", help="display name for the source (single PDF only)")
    ap.add_argument("--layout", choices=list(PARSERS), help="force a page layout instead of auto-detecting")
    ap.add_argument("--report", type=Path, help="write a Markdown report of recipes that need a look")
    ap.add_argument("--dry-run", action="store_true", help="parse and report without writing to the database")
    args = ap.parse_args(argv)

    conn = dbmod.connect(args.data_dir)
    per_file = {}
    for pdf in args.pdfs:
        print(f"Importing {pdf.name} ...")
        results = import_pdf(conn, pdf, args.data_dir, args.name if len(args.pdfs) == 1 else None, args.layout)
        per_file[pdf.name] = results
        counts: dict[str, int] = {}
        for _, a in results:
            counts[a] = counts.get(a, 0) + 1
        print("  " + ", ".join(f"{v} {k}" for k, v in counts.items()) or "  no recipes found")
    if args.dry_run:
        conn.rollback()
    else:
        dbmod.reindex_search(conn)
        conn.commit()
    if args.report:
        write_report(args.report, per_file)
        print(f"Report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
