"""End-to-end importer test against small synthetic PDFs that mimic the two supported layouts."""
import json
import sqlite3

import pymupdf
import pytest

from cookbook.importer.cli import main
from cookbook.importer.parsers import parse_document

def make_single_page_pdf(path):
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((36, 225), "Test Chicken Wraps", fontsize=28)
    page.insert_text((36, 252), "A quick weeknight dinner.", fontsize=9)
    page.insert_text((36, 290), "Macros per serving", fontsize=12)
    page.insert_text((36, 312), "350 CALORIES", fontsize=10)
    page.insert_text((138, 312), "40g PROTEIN", fontsize=10)
    page.insert_text((241, 312), "25g CARBS", fontsize=10)
    page.insert_text((346, 312), "10g FAT", fontsize=10)
    page.insert_text((63, 355), "Ingredients (4 Servings)", fontsize=16)
    page.insert_text((40, 383), "Chicken:", fontsize=10)
    y = 400
    for line in ["600g (21oz) Chicken Breast", "1 Tsp Paprika", "1 Tsp Salt"]:
        page.insert_text((58, y), line, fontsize=9.5)
        y += 14
    page.insert_text((203, 383), "Sauce:", fontsize=10)
    y = 400
    for line in ["100g Fat Free Yogurt", "20g Sriracha"]:
        page.insert_text((221, y), line, fontsize=9.5)
        y += 14
    page.insert_text((63, 550), "How to make", fontsize=16)
    page.insert_text((44, 580), "1. Season the chicken and cook for 4 minutes", fontsize=9.5)
    page.insert_text((58, 593), "on each side.", fontsize=9.5)
    page.insert_text((44, 610), "2. Mix the sauce and serve.", fontsize=9.5)
    page.insert_text((411, 580), "Toast the wraps for crunch.", fontsize=9)
    doc.save(path)


def make_two_page_pdf(path):
    doc = pymupdf.open()
    cover = doc.new_page(width=595, height=842)
    cover.insert_text((248, 65), "Recipe # 1", fontsize=17)
    cover.insert_text((164, 110), "Test Beef Bowls", fontsize=28)
    cover.insert_text((225, 192), "PER SERVING (MAKES 4)", fontsize=12)
    for x, num, label in [(144, "500", "CALORIES"), (236, "45g", "PROTEIN"), (330, "50g", "CARBS"), (419, "12g", "FAT")]:
        cover.insert_text((x, 228), num, fontsize=14)
        cover.insert_text((x - 10, 246), label, fontsize=12)
    cover.insert_text((252, 745), "Great for the week ahead.", fontsize=12)
    body = doc.new_page(width=595, height=842)
    body.insert_text((45, 92), "INGREDIENTS (4 SERVINGS)", fontsize=16)
    body.insert_text((40, 121), "Beef", fontsize=11)
    body.insert_text((44, 140), "- 800g (28oz) Lean Ground Beef", fontsize=10)
    body.insert_text((44, 157), "- 1 Tsp each Salt, Cumin", fontsize=10)
    body.insert_text((302, 121), "Rice", fontsize=11)
    body.insert_text((306, 140), "- 250g Basmati Rice", fontsize=10)
    body.insert_text((45, 384), "INSTRUCTIONS", fontsize=16)
    body.insert_text((37, 412), "STEP 1", fontsize=10)
    body.insert_text((50, 426), "Brown the beef with the spices.", fontsize=10)
    body.insert_text((37, 446), "STEP 2", fontsize=10)
    body.insert_text((50, 460), "Cook the rice and portion into 4 boxes.", fontsize=10)
    body.insert_text((45, 735), "IMPORTANT COOKING NOTES", fontsize=16)
    body.insert_text((58, 756), "Freeze half of the portions.", fontsize=10)
    doc.save(path)


@pytest.fixture
def pdfs(tmp_path):
    a, b = tmp_path / "single.pdf", tmp_path / "Meal Prep Test.pdf"
    make_single_page_pdf(a)
    make_two_page_pdf(b)
    return a, b


def test_single_page_layout(pdfs):
    [r] = parse_document(pymupdf.open(pdfs[0]))
    assert r.title == "Test Chicken Wraps"
    assert (r.kcal, r.protein, r.carbs, r.fat) == (350, 40, 25, 10)
    assert r.servings == 4
    assert [g.name for g in r.groups] == ["Chicken", "Sauce"]
    assert [i.canonical for i in r.groups[0].items] == ["chicken breast", "paprika", "salt"]
    assert r.steps == ["Season the chicken and cook for 4 minutes on each side.", "Mix the sauce and serve."]
    assert r.notes == ["Toast the wraps for crunch."]


def test_two_page_layout(pdfs):
    [r] = parse_document(pymupdf.open(pdfs[1]))
    assert r.number == 1 and r.title == "Test Beef Bowls"
    assert (r.kcal, r.protein, r.carbs, r.fat) == (500, 45, 50, 12)
    assert r.servings == 4
    assert [g.name for g in r.groups] == ["Beef", "Rice"]
    assert r.groups[0].items[1].each == ["Salt", "Cumin"]
    assert r.steps == ["Brown the beef with the spices.", "Cook the rice and portion into 4 boxes."]
    assert r.notes == ["Freeze half of the portions."]


def test_cli_writes_database_and_is_idempotent(pdfs, tmp_path):
    data = tmp_path / "data"
    assert main([str(p) for p in pdfs] + ["--data-dir", str(data)]) == 0
    assert main([str(p) for p in pdfs] + ["--data-dir", str(data)]) == 0  # re-import updates in place
    conn = sqlite3.connect(data / "cookbook.db")
    assert conn.execute("SELECT count(*) FROM recipes").fetchone()[0] == 2
    tags = json.loads(conn.execute("SELECT tags FROM recipes WHERE title = 'Test Beef Bowls'").fetchone()[0])
    assert "beef" in tags and "meal prep" in tags
    hits = conn.execute("SELECT rowid FROM recipe_search WHERE recipe_search MATCH 'sriracha'").fetchall()
    assert len(hits) == 1


def test_user_edits_survive_reimport(pdfs, tmp_path):
    data = tmp_path / "data"
    main([str(pdfs[0]), "--data-dir", str(data)])
    conn = sqlite3.connect(data / "cookbook.db")
    conn.execute("UPDATE recipes SET title = 'My Wraps', user_edited = 1")
    conn.commit()
    main([str(pdfs[0]), "--data-dir", str(data)])
    assert conn.execute("SELECT title FROM recipes").fetchone()[0] == "My Wraps"
