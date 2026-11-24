"""PDF upload and import."""
from __future__ import annotations

import re
import shutil
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ... import db as dbmod
from ...importer.cli import import_pdf
from ..deps import data_dir, get_conn
from ..models import ImportResult

router = APIRouter(prefix="/api", tags=["import"])


def _safe_name(name: str | None) -> str:
    stem = Path(name or "upload.pdf").name
    stem = re.sub(r"[^\w.\- ()]+", "_", stem).strip(" .") or "upload.pdf"
    return stem if stem.lower().endswith(".pdf") else f"{stem}.pdf"


@router.post("/import", response_model=ImportResult)
def import_upload(file: UploadFile = File(...), conn: sqlite3.Connection = Depends(get_conn),
                  ddir: Path = Depends(data_dir)):
    head = file.file.read(5)
    if head != b"%PDF-":
        raise HTTPException(400, "Upload must be a PDF file")
    file.file.seek(0)
    pdf_dir = ddir / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    dest = pdf_dir / _safe_name(file.filename)
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    try:
        results = import_pdf(conn, dest, ddir, None, None)
    except Exception as e:  # malformed PDF, unknown layout, ...
        conn.rollback()
        raise HTTPException(422, f"Import failed: {e}") from e
    dbmod.reindex_search(conn)
    conn.commit()
    counts = {"added": 0, "updated": 0, "kept": 0}
    for _, action in results:
        counts["kept" if action.startswith("kept") else action] += 1
    return {
        "source": dest.stem,
        **counts,
        "warnings": [{"title": r.title, "page": r.pages[0], "warnings": r.warnings} for r, _ in results if r.warnings],
    }
