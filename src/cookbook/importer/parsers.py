"""Book-specific page parsers.

Each parser turns PDF pages into RecipeDraft objects. Two layouts are supported today, both from
InDesign-exported cookbooks:

* ``single_page``: one recipe per page; title, macros, "Ingredients (...)", "How to make", tips column.
* ``two_page``: "Recipe # N" cover page (photo, title, nutrition, blurb) followed by a page with
  INGREDIENTS / INSTRUCTIONS / IMPORTANT COOKING NOTES.

New layouts can be added by writing another parser and registering it in ``PARSERS``.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

import pymupdf

from .ingredients import Ingredient, canonical_name, parse_ingredient
from .layout import (Bullet, Line, assign_columns, has_bullet, join_lines, largest_image, page_lines,
                     paragraphs, video_links)

FOOTER_Y = 805
SKIP_RE = re.compile(r"^(tap icons for recipe video|return to table of contents|the meal prep cook ?book|»\s*continue)", re.I)
MACRO_RE = re.compile(r"(\d+(?:\.\d+)?)\s*g?\s*(CALORIES|KCAL|PROTEIN|CARBS|FAT)\b", re.I)
QTY_START_RE = re.compile(r"^(\d|½|¼|¾|⅓|⅔|juice of|handful|pinch|a pinch|ice\b)", re.I)


@dataclass
class IngredientGroup:
    name: str | None
    note: str | None = None
    items: list[Ingredient] = field(default_factory=list)


@dataclass
class RecipeDraft:
    title: str
    pages: list[int]
    number: int | None = None
    blurb: str = ""
    servings: float | None = None
    servings_text: str = ""
    kcal: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None
    groups: list[IngredientGroup] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    videos: dict[str, str] = field(default_factory=dict)
    image_xref: int | None = None
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- shared pieces

def _is_skip(line: Line) -> bool:
    return bool(SKIP_RE.match(line.clean)) or line.y0 > FOOTER_Y or not line.clean


def parse_servings(text: str) -> tuple[float | None, str]:
    m = re.search(r"\(([^)]*)\)", text)
    inner = m.group(1).strip() if m else ""
    n = re.search(r"(\d+)(?:\s*-\s*(\d+))?", inner or text)
    servings = None
    if n:
        servings = float(n.group(2) or n.group(1))
    return servings, inner


def parse_macros(lines: list[Line], draft: RecipeDraft) -> None:
    text = " ".join(l.clean for l in lines)
    for value, label in MACRO_RE.findall(text):
        key = {"CALORIES": "kcal", "KCAL": "kcal"}.get(label.upper(), label.lower())
        if getattr(draft, key) is None:
            setattr(draft, key, float(value))


def parse_macro_grid(lines: list[Line], draft: RecipeDraft) -> None:
    """Two-page layout: number on one line, label on the line below it."""
    labels = [l for l in lines if l.clean.upper() in ("CALORIES", "PROTEIN", "CARBS", "FAT")]
    for lab in labels:
        above = [l for l in lines if 0 < lab.y0 - l.y1 < 12 and abs((l.x0 + l.x1) / 2 - (lab.x0 + lab.x1) / 2) < 30]
        if above:
            m = re.match(r"(\d+(?:\.\d+)?)", above[0].clean)
            if m:
                key = "kcal" if lab.clean.upper() == "CALORIES" else lab.clean.lower()
                setattr(draft, key, float(m.group(1)))


def parse_ingredient_region(lines: list[Line], bullets: list[Bullet], draft: RecipeDraft) -> None:
    lines = [l for l in lines if not _is_skip(l)]
    if not lines:
        draft.warnings.append("no ingredient lines found")
        return
    cols = assign_columns(lines)

    def starts_item(l: Line) -> bool:
        return l.clean.startswith(("–", "- ")) or has_bullet(l, bullets)

    item_sizes = Counter(l.size for c in cols for l in c if starts_item(l))
    use_markers = bool(item_sizes)
    if not use_markers:
        item_sizes = Counter(l.size for c in cols for l in c)
        draft.warnings.append("no bullets in ingredient list; split by quantity")
    item_size = item_sizes.most_common(1)[0][0]

    current = IngredientGroup(None)
    draft.groups = [current]
    buf: list[Line] = []

    def flush():
        if buf:
            raw = join_lines(buf).lstrip("–- ").strip()
            if raw:
                current.items.append(parse_ingredient(raw))
            buf.clear()

    for col in cols:
        for l in col:
            t = l.clean
            is_heading = (not starts_item(l) and (l.size > item_size + 0.3 or t.endswith(":"))
                          and t[:1].isupper()
                          and not QTY_START_RE.match(t) and len(t) < 40)
            if is_heading:
                flush()
                current = IngredientGroup(t.rstrip(": "))
                draft.groups.append(current)
                continue
            new_item = starts_item(l) if use_markers else (not buf or QTY_START_RE.match(t))
            if new_item and buf and buf[-1].clean.endswith((",", "&", " or", " and")):
                new_item = False  # wrapped list: "1 Tsp Salt, Paprika, Cumin," / "Garlic Powder"
            if not new_item and not buf and not current.items and current.name:
                current.note = ((current.note or "") + " " + t).strip()
                continue
            if new_item:
                flush()
            buf.append(l)
        flush()
    draft.groups = [g for g in draft.groups if g.items]
    group_names = {canonical_name(g.name) for g in draft.groups if g.name}
    for g in draft.groups:
        for i in g.items:
            if i.kind != "item":
                continue
            if not i.item:
                draft.warnings.append(f"ingredient has no name in the book: {i.raw!r}")
            # "1 Serving Taco Spice Mix" refers to another component of this recipe, not something to buy
            if i.canonical and any(i.canonical in n or n in i.canonical for n in group_names if len(n) > 4):
                i.aisle = "Skip"


def numbered_steps(lines: list[Line], start_re: re.Pattern) -> list[str]:
    steps: list[list[Line]] = []
    for col in assign_columns([l for l in lines if not _is_skip(l)]):
        for l in col:
            m = start_re.match(l.clean)
            if m:
                rest = l.clean[m.end():].strip().lstrip(":").strip()
                if rest and rest.upper() == rest:
                    rest = ""  # letter-spaced step title such as "M A K E T H E S A U C E"
                steps.append([Line(rest, l.x0, l.y0, l.x1, l.y1, l.font, l.size)] if rest else [])
            elif steps:
                steps[-1].append(l)
    return [s for s in (join_lines(s) for s in steps) if s]


# ---------------------------------------------------------------- single-page layout

def detect_single_page(lines: list[Line]) -> bool:
    texts = [l.clean.lower() for l in lines]
    return any(t.startswith("ingredients") for t in texts) and any(t.startswith("how to make") for t in texts) or (
        any(t.startswith("ingredients") for t in texts) and any(l.size >= 24 for l in lines)
        and not any(t.startswith("recipe #") for t in texts) and not any(t == "instructions" for t in texts))


def parse_single_page(doc: pymupdf.Document, pno: int) -> RecipeDraft | None:
    page = doc[pno]
    lines, bullets = page_lines(page)
    title_lines = [l for l in lines if l.size >= 24]
    ing_head = next((l for l in lines if l.clean.lower().startswith("ingredients") and l.size >= 14), None)
    if not title_lines or not ing_head:
        return None
    draft = RecipeDraft(title=join_lines(sorted(title_lines, key=lambda l: l.y0)), pages=[pno + 1])
    title_bottom = max(l.y1 for l in title_lines)
    head = next((l for l in lines if l.clean.lower().startswith("macros per serving")), None)
    blurb_end = head.y0 if head else ing_head.y0
    draft.blurb = join_lines([l for l in lines if title_bottom - 2 < l.y0 < blurb_end and l.x0 < 400
                              and not _is_skip(l) and l.size < 14])
    parse_macros([l for l in lines if l.y0 < ing_head.y0], draft)
    draft.servings, draft.servings_text = parse_servings(ing_head.clean)

    how = next((l for l in lines if l.clean.lower().startswith("how to make") and l.size >= 14), None)
    ing_end = how.y0 if how else FOOTER_Y
    parse_ingredient_region([l for l in lines if ing_head.y1 < l.y0 < ing_end], bullets, draft)
    if how:
        body = [l for l in lines if how.y1 < l.y0 < FOOTER_Y and not _is_skip(l)]
        step_lines = [l for l in body if l.x0 < 395]
        tip_lines = [l for l in body if l.x0 >= 395]
        draft.steps = numbered_steps(step_lines, re.compile(r"^(\d+)[.)]\s*"))
        draft.notes = paragraphs(tip_lines)
    else:
        draft.warnings.append("no 'How to make' section")
    if not draft.steps and how:
        draft.warnings.append("no steps parsed")
    draft.videos = video_links(page)
    draft.image_xref = largest_image(page)
    return draft


# ---------------------------------------------------------------- two-page layout

def detect_two_page(lines: list[Line]) -> bool:
    return any(re.match(r"^recipe\s*#\s*\d+", l.clean, re.I) for l in lines)


def parse_two_page(doc: pymupdf.Document, pno: int) -> RecipeDraft | None:
    cover = doc[pno]
    lines, _ = page_lines(cover)
    num_line = next((l for l in lines if re.match(r"^recipe\s*#\s*\d+", l.clean, re.I)), None)
    if not num_line or pno + 1 >= len(doc):
        return None
    title_lines = sorted([l for l in lines if l.size >= 24], key=lambda l: l.y0)
    draft = RecipeDraft(title=join_lines(title_lines), pages=[pno + 1, pno + 2],
                        number=int(re.search(r"\d+", num_line.clean).group()))
    parse_macro_grid(lines, draft)
    per = next((l for l in lines if "per serving" in l.clean.lower()), None)
    if per:
        draft.servings, draft.servings_text = parse_servings(per.clean)
    nutrition_bottom = max((l.y1 for l in lines if l.clean.upper() in ("CALORIES", "FAT")), default=260)
    draft.blurb = join_lines([l for l in lines if l.y0 > nutrition_bottom + 5 and not _is_skip(l) and l.size < 20])
    draft.videos = video_links(cover)
    draft.image_xref = largest_image(cover)

    body = doc[pno + 1]
    blines, bullets = page_lines(body)

    def head(prefix: str) -> Line | None:
        return next((l for l in blines if l.clean.upper().startswith(prefix) and l.size >= 14), None)

    ing, ins, notes = head("INGREDIENTS"), head("INSTRUCTIONS"), head("IMPORTANT")
    if not ing:
        draft.warnings.append("no INGREDIENTS heading on second page")
        return draft
    if not draft.servings:
        draft.servings, draft.servings_text = parse_servings(ing.clean)
    ing_end = ins.y0 if ins else FOOTER_Y
    parse_ingredient_region([l for l in blines if ing.y1 < l.y0 < ing_end], bullets, draft)
    if ins:
        end = notes.y0 if notes else FOOTER_Y
        draft.steps = numbered_steps([l for l in blines if ins.y1 < l.y0 < end],
                                     re.compile(r"^S\s*T\s*E\s*P\s*\d+\s*", re.I))
    if notes:
        note_lines = [l for l in blines if notes.y1 < l.y0 < FOOTER_Y and not _is_skip(l)]
        items: list[list[Line]] = []
        for l in note_lines:
            if has_bullet(l, bullets) or not items:
                items.append([l])
            else:
                items[-1].append(l)
        draft.notes = [join_lines(i) for i in items]
    if not draft.steps:
        draft.warnings.append("no steps parsed")
    return draft


PARSERS = {
    "two_page": (detect_two_page, parse_two_page),
    "single_page": (detect_single_page, parse_single_page),
}


def parse_document(doc: pymupdf.Document, layout: str | None = None) -> list[RecipeDraft]:
    """Walk every page and parse the ones that start a recipe."""
    out: list[RecipeDraft] = []
    pno = 0
    while pno < len(doc):
        lines, _ = page_lines(doc[pno])
        draft = None
        for name, (detect, parse) in PARSERS.items():
            if layout and name != layout:
                continue
            if detect(lines):
                draft = parse(doc, pno)
                break
        if draft:
            out.append(draft)
            pno += len(draft.pages)
        else:
            pno += 1
    return out
