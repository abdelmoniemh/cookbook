"""Low-level helpers for reading positioned text out of a PDF page with PyMuPDF."""
from __future__ import annotations

import re
from dataclasses import dataclass

import pymupdf


@dataclass
class Line:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    font: str
    size: float

    @property
    def yc(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def clean(self) -> str:
        return re.sub(r"\s+", " ", self.text.replace("\t", " ")).strip()


@dataclass
class Bullet:
    x: float
    yc: float


def page_lines(page: pymupdf.Page) -> tuple[list[Line], list[Bullet]]:
    """Return text lines and bullet glyph positions (the books use a Wingdings 'z' as a bullet)."""
    lines: list[Line] = []
    bullets: list[Bullet] = []
    d = page.get_text("dict")
    for b in d["blocks"]:
        if b["type"] != 0:
            continue
        for ln in b["lines"]:
            spans = [s for s in ln["spans"] if s["text"]]
            if not spans:
                continue
            # A Wingdings span is a bullet; it may share a line with text ("z S T E P 1").
            text_spans = []
            for s in spans:
                if "Wingdings" in s["font"]:
                    if s["text"].strip() in ("z", "l", "n", "§"):
                        bullets.append(Bullet(s["bbox"][0], (s["bbox"][1] + s["bbox"][3]) / 2))
                        continue
                    # wingdings span carrying real text (e.g. "z S T E P 1 ")
                    t = s["text"].strip()
                    if t.startswith("z"):
                        bullets.append(Bullet(s["bbox"][0], (s["bbox"][1] + s["bbox"][3]) / 2))
                        s = dict(s, text=t[1:])
                text_spans.append(s)
            text = "".join(s["text"] for s in text_spans)
            if not text.strip():
                continue
            main = max(text_spans, key=lambda s: len(s["text"].strip()))
            size = max(s["size"] for s in text_spans if s["text"].strip())
            x0 = min(s["bbox"][0] for s in text_spans if s["text"].strip())
            lines.append(Line(text, x0, ln["bbox"][1], ln["bbox"][2], ln["bbox"][3], main["font"], round(size, 1)))
    return lines, bullets


def assign_columns(lines: list[Line], gap: float = 60) -> list[list[Line]]:
    """Split lines into columns by left edge, then sort each column top to bottom."""
    if not lines:
        return []
    xs = sorted({round(l.x0) for l in lines})
    starts = [xs[0]]
    for x in xs[1:]:
        if x - starts[-1] > gap:
            starts.append(x)
    cols: list[list[Line]] = [[] for _ in starts]
    for l in lines:
        idx = max(i for i, s in enumerate(starts) if l.x0 >= s - 5)
        cols[idx].append(l)
    return [sorted(c, key=lambda l: l.y0) for c in cols]


def has_bullet(line: Line, bullets: list[Bullet], max_dx: float = 25) -> bool:
    return any(abs(b.yc - line.yc) < 4.5 and 0 < line.x0 - b.x < max_dx for b in bullets)


def paragraphs(lines: list[Line], gap: float = 4) -> list[str]:
    """Join consecutive lines into paragraphs, splitting on vertical gaps."""
    out: list[list[Line]] = []
    for l in sorted(lines, key=lambda l: l.y0):
        if out and l.y0 - out[-1][-1].y1 <= gap:
            out[-1].append(l)
        else:
            out.append([l])
    return [join_lines(p) for p in out]


def join_lines(lines: list[Line]) -> str:
    text = ""
    for l in lines:
        t = l.clean
        if text.endswith("-") and not text.endswith(" -"):
            text = text[:-1] + t
        else:
            text = (text + " " + t).strip()
    return re.sub(r"\s*»+\s*$", "", text).strip()


def video_links(page: pymupdf.Page) -> dict[str, str]:
    out = {}
    for link in page.get_links():
        uri = link.get("uri") or ""
        for site in ("youtube", "youtu.be", "tiktok", "instagram"):
            if site in uri:
                key = "youtube" if site.startswith("you") else site
                out.setdefault(key, uri)
    return out


def largest_image(page: pymupdf.Page) -> int | None:
    best, best_area = None, 0
    for img in page.get_images(full=True):
        xref, w, h = img[0], img[2], img[3]
        if w * h > best_area:
            best, best_area = xref, w * h
    return best
