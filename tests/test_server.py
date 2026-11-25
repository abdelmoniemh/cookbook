"""API tests against a fresh database in tmp_path. Synthetic recipes only."""
import json

import pymupdf
import pytest
from fastapi.testclient import TestClient

from cookbook import db as dbmod
from cookbook.server import create_app
from cookbook.server.units import fmt_amount, nice_fraction, shopping_display


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "data"


@pytest.fixture
def client(data_dir, tmp_path):
    app = create_app(data_dir, web_dist=tmp_path / "no-ui")
    with TestClient(app) as c:
        yield c


def make(client, title="Test Bowl", servings=2, lines=None, groups=None, **kw):
    body = {"title": title, "servings": servings, "steps": ["Cook it.", "Eat it."],
            "groups": groups or [{"name": None, "lines": lines or ["400g Chicken Breast, cubed", "1 Tsp Salt"]}],
            **kw}
    r = client.post("/api/recipes", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def items_by_key(shopping):
    return {i["key"]: {**i, "aisle": a["aisle"]} for a in shopping["aisles"] for i in a["items"]}


# ---------------------------------------------------------------- recipes

def test_health(client):
    assert client.get("/api/health").json() == {"ok": True, "recipes": 0}
    make(client)
    assert client.get("/api/health").json()["recipes"] == 1


def test_create_and_detail(client):
    r = make(client, title="Zesty Test Wraps", servings=4, kcal=400, protein=35, carbs=30, fat=10,
             tags=["chicken", "wrap"], blurb="A test.",
             groups=[{"name": "Filling", "note": "makes plenty", "lines": ["800g (28oz) Chicken Breast, cubed",
                                                                          "", "1 Tsp each Salt, Cumin"]},
                     {"name": "Sauce", "lines": ["Season to taste with lemon", "2 Tbsp Light Mayo"]}],
             notes=["Keeps 4 days."])
    assert r["slug"] == "zesty-test-wraps"
    assert r["source"] is None and r["user_edited"] is False and r["favourite"] is False
    assert r["scale"] == 1 and r["scaled_servings"] == 4
    assert r["tags"] == ["chicken", "wrap"] and r["notes"] == ["Keeps 4 days."]
    assert r["steps"] == ["Cook it.", "Eat it."]
    filling, sauce = r["groups"]
    assert filling["name"] == "Filling" and filling["note"] == "makes plenty"
    chicken, spices = filling["items"]  # blank line dropped
    assert chicken["qty"] == 800 and chicken["unit"] == "g" and chicken["alt_measure"] == "28oz"
    assert chicken["canonical"] == "chicken breast" and chicken["aisle"] == "Meat & Fish"
    assert chicken["display"] == "800 g Chicken Breast, cubed"
    assert spices["each_of"] == ["Salt", "Cumin"] and spices["display"] == "1 tsp each Salt, Cumin"
    assert sauce["items"][0]["kind"] == "note"
    # by slug too
    assert client.get(f"/api/recipes/{r['slug']}").json()["id"] == r["id"]
    assert client.get("/api/recipes/does-not-exist").status_code == 404


def test_scaling_and_display(client):
    r = make(client, servings=4, lines=["800g Chicken Breast", "25-30g Corn Flour", "1 Tsp Paprika",
                                        "1/2 Cup Milk", "Juice of 1 Lemon", "2 Garlic Cloves", "Fresh Parsley"])
    d = client.get(f"/api/recipes/{r['id']}", params={"servings": 6}).json()
    assert d["scale"] == 1.5 and d["scaled_servings"] == 6
    shown = [i["display"] for i in d["groups"][0]["items"]]
    assert shown == ["1.2 kg Chicken Breast", "38-45 g Corn Flour", "1½ tsp Paprika", "¾ cup Milk",
                     "Juice of 1½ Lemon", "3 Garlic Cloves", "Fresh Parsley"]
    first = d["groups"][0]["items"][0]
    assert first["qty"] == 1200 and first["unit"] == "g"
    assert d["kcal"] == r["kcal"]  # macros are per serving, never scaled
    half = client.get(f"/api/recipes/{r['id']}?servings=1").json()
    assert [i["display"] for i in half["groups"][0]["items"]][:3] == ["200 g Chicken Breast", "6.2-7.5 g Corn Flour",
                                                                     "¼ tsp Paprika"]


def test_scaling_with_unknown_servings(client):
    r = make(client, servings=None, lines=["100g Rice"])
    d = client.get(f"/api/recipes/{r['id']}?servings=3").json()
    assert d["scale"] == 3 and d["groups"][0]["items"][0]["display"] == "300 g Rice"


def test_format_helpers():
    assert nice_fraction(0.5) == "½" and nice_fraction(1.25) == "1¼" and nice_fraction(2) == "2"
    assert nice_fraction(0.125) == "⅛" and nice_fraction(0.66) == "⅔"
    assert fmt_amount(2, None, "clove") == "2 cloves" and fmt_amount(1, None, "pinch") == "1 pinch"
    assert fmt_amount(999, None, "g") == "1 kg"
    assert shopping_display(None, None) == "as needed"
    assert shopping_display(1640, "g") == "1.6 kg" and shopping_display(1500, "ml") == "1.5 l"
    assert shopping_display(10, "ml") == "2 tsp" and shopping_display(45, "ml") == "3 tbsp"
    assert shopping_display(250, "ml") == "250 ml" and shopping_display(3, None) == "3"


def test_update_marks_user_edited_and_reindexes(client):
    r = make(client, title="Plain Oats", lines=["50g Oats"])
    assert client.get("/api/recipes", params={"q": "oats"}).json()["total"] == 1
    body = {"title": "Banana Porridge", "servings": 1, "groups": [{"name": None, "lines": ["1 Banana", "40g Oats"]}],
            "steps": ["Stir."]}
    u = client.put(f"/api/recipes/{r['id']}", json=body).json()
    assert u["user_edited"] is True and u["title"] == "Banana Porridge" and u["slug"] == "plain-oats"
    assert [i["item"] for i in u["groups"][0]["items"]] == ["Banana", "Oats"]
    assert client.get("/api/recipes", params={"q": "porridge"}).json()["total"] == 1
    assert client.get("/api/recipes", params={"q": "plain"}).json()["total"] == 0
    assert client.get("/api/recipes", params={"q": "banana"}).json()["total"] == 1
    assert client.put("/api/recipes/999", json=body).status_code == 404


def test_delete(client):
    r = make(client, title="Doomed Dish")
    plan = client.get("/api/plans/current").json()
    client.post(f"/api/plans/{plan['id']}/entries", json={"recipe_id": r["id"]})
    assert client.delete(f"/api/recipes/{r['id']}").status_code == 204
    assert client.get(f"/api/recipes/{r['id']}").status_code == 404
    assert client.get("/api/recipes", params={"q": "doomed"}).json()["total"] == 0
    assert client.get("/api/plans/current").json()["entries"] == []
    assert client.delete(f"/api/recipes/{r['id']}").status_code == 404


def test_unique_slugs(client):
    a, b = make(client, title="Same Name"), make(client, title="Same Name")
    assert (a["slug"], b["slug"]) == ("same-name", "same-name-2")


def test_validation(client):
    assert client.post("/api/recipes", json={"title": "", "groups": [], "steps": []}).status_code == 422
    assert client.get("/api/recipes/1", params={"servings": 0}).status_code == 422


def test_list_filter_search_sort(client):
    make(client, title="Alpha Chicken", kcal=500, protein=50, tags=["chicken", "rice"])
    make(client, title="Bravo Beef", kcal=300, protein=40, tags=["beef", "rice"],
         lines=["500g Lean Beef Mince", "100g Basmati Rice"])
    make(client, title="Charlie Salad", kcal=200, protein=None, tags=["veg"], lines=["1 Cucumber"])
    get = lambda **p: client.get("/api/recipes", params=p).json()

    res = get()
    assert res["total"] == 3 and [i["title"] for i in res["items"]] == ["Alpha Chicken", "Bravo Beef", "Charlie Salad"]
    assert [i["title"] for i in get(sort="protein")["items"]] == ["Alpha Chicken", "Bravo Beef", "Charlie Salad"]
    assert [i["title"] for i in get(sort="kcal")["items"]] == ["Charlie Salad", "Bravo Beef", "Alpha Chicken"]
    assert get(sort="recent")["items"][0]["title"] == "Charlie Salad"
    assert get(tag="rice")["total"] == 2
    assert [i["title"] for i in get(tag=["rice", "beef"])["items"]] == ["Bravo Beef"]
    assert get(max_kcal=300)["total"] == 2 and get(min_protein=45)["total"] == 1
    assert [i["title"] for i in get(q="basmati")["items"]] == ["Bravo Beef"]  # ingredient text is indexed
    assert get(q="chick")["total"] == 1  # prefix match
    assert get(q='"bad (fts syntax')["total"] == 0  # never a 500
    page = get(limit=1, offset=1)
    assert page["total"] == 3 and [i["title"] for i in page["items"]] == ["Bravo Beef"]
    assert client.get("/api/recipes", params={"sort": "nope"}).status_code == 422


def test_favourites(client):
    r = make(client)
    s = client.put(f"/api/recipes/{r['id']}/favourite", json={"favourite": True}).json()
    assert s["favourite"] is True and "groups" not in s
    assert client.get("/api/recipes", params={"favourite": True}).json()["total"] == 1
    assert client.get("/api/recipes", params={"favourite": False}).json()["total"] == 0
    client.put(f"/api/recipes/{r['id']}/favourite", json={"favourite": False})
    assert client.get(f"/api/recipes/{r['id']}").json()["favourite"] is False


def test_tags_and_sources(client, data_dir):
    make(client, title="One", tags=["rice", "chicken"])
    make(client, title="Two", tags=["rice"])
    assert client.get("/api/tags").json() == [{"tag": "rice", "count": 2}, {"tag": "chicken", "count": 1}]
    conn = dbmod.connect(data_dir)
    sid = conn.execute("INSERT INTO sources (name, file_name) VALUES ('Test Book', 'test.pdf')").lastrowid
    conn.execute("UPDATE recipes SET source_id = ?, source_page = 7, image = 'one.jpg' WHERE title = 'One'", (sid,))
    conn.commit()
    assert client.get("/api/sources").json() == [{"id": sid, "name": "Test Book", "recipe_count": 1}]
    one = client.get("/api/recipes", params={"source": sid}).json()["items"]
    assert [i["title"] for i in one] == ["One"]
    assert one[0]["source"] == {"id": sid, "name": "Test Book"} and one[0]["image_url"] == "/images/one.jpg"


def test_images_and_spa(data_dir, tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>app</html>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    with TestClient(create_app(data_dir, web_dist=dist)) as c:
        (data_dir / "images" / "x.jpg").write_bytes(b"\xff\xd8fake")
        assert c.get("/images/x.jpg").content == b"\xff\xd8fake"
        assert c.get("/images/missing.jpg").status_code == 404
        assert c.get("/").text == "<html>app</html>"
        assert c.get("/recipes/some-slug").text == "<html>app</html>"
        assert c.get("/assets/app.js").text == "console.log(1)"
        assert c.get("/api/unknown").status_code == 404


def test_no_ui_message(client):
    r = client.get("/")
    assert r.status_code == 200 and "web UI has not been built" in r.text


# ---------------------------------------------------------------- plans

def test_plan_crud_and_totals(client):
    a = make(client, title="Plan A", servings=4, kcal=500, protein=40, carbs=50, fat=10)
    b = make(client, title="Plan B", servings=None, kcal=300, protein=20, carbs=None, fat=5)
    plan = client.get("/api/plans/current", params={"week": "2026-03-05"}).json()  # a Thursday
    assert plan["week_start"] == "2026-03-02" and plan["entries"] == []
    assert client.get("/api/plans/current", params={"week": "2026-03-08"}).json()["id"] == plan["id"]
    pid = plan["id"]

    plan = client.post(f"/api/plans/{pid}/entries", json={"recipe_id": a["id"], "day": "mon"}).json()
    plan = client.post(f"/api/plans/{pid}/entries", json={"recipe_id": b["id"]}).json()
    ea, eb = plan["entries"]
    assert (ea["servings"], ea["day"], ea["position"]) == (4, "mon", 0)
    assert (eb["servings"], eb["day"], eb["position"]) == (1, None, 1)
    assert eb["recipe"]["title"] == "Plan B"
    assert plan["totals"] == {"servings": 5, "kcal": 2300, "protein": 180, "carbs": 200, "fat": 45}

    plan = client.patch(f"/api/plans/{pid}/entries/{eb['id']}", json={"servings": 2, "day": "fri", "position": -1}).json()
    assert [e["recipe"]["title"] for e in plan["entries"]] == ["Plan B", "Plan A"]
    assert plan["entries"][0]["day"] == "fri" and plan["totals"]["kcal"] == 2600
    plan = client.patch(f"/api/plans/{pid}/entries/{eb['id']}", json={"day": None}).json()
    assert plan["entries"][0]["day"] is None and plan["entries"][0]["servings"] == 2

    assert client.patch(f"/api/plans/{pid}/entries/{eb['id']}", json={"day": "funday"}).status_code == 422
    assert client.post(f"/api/plans/{pid}/entries", json={"recipe_id": 999}).status_code == 404
    assert client.post("/api/plans/999/entries", json={"recipe_id": a["id"]}).status_code == 404

    plan = client.delete(f"/api/plans/{pid}/entries/{ea['id']}").json()
    assert [e["id"] for e in plan["entries"]] == [eb["id"]]
    assert client.delete(f"/api/plans/{pid}/entries/{ea['id']}").status_code == 404


# ---------------------------------------------------------------- shopping

@pytest.fixture
def shop(client):
    """A plan with two recipes sharing chicken, salt and oil in different units."""
    r1 = make(client, title="Recipe One", servings=2, groups=[
        {"name": "Chicken", "lines": ["500g Raw Chicken Breast, cubed", "1 Tsp each Salt, Paprika",
                                      "1 Tbsp Olive Oil", "200ml Boiling Water", "Fresh Parsley"]},
        {"name": "Spice Mix", "lines": ["1 Tsp Cumin"]},
        {"name": "Bowls", "lines": ["1 Serving Spice Mix", "2 Onions"]},
    ])
    r2 = make(client, title="Recipe Two", servings=4, groups=[
        {"name": None, "lines": ["1.2kg Chicken Breasts", "2 Tsp Salt", "50ml Olive Oil", "1 Onion",
                                 "1 Handful Parsley", "Black Pepper"]},
    ])
    pid = client.get("/api/plans/current").json()["id"]
    client.post(f"/api/plans/{pid}/entries", json={"recipe_id": r1["id"], "servings": 4})  # x2
    client.post(f"/api/plans/{pid}/entries", json={"recipe_id": r2["id"]})  # x1
    return pid


def test_shopping_aggregation(client, shop):
    sl = client.get(f"/api/plans/{shop}/shopping").json()
    assert sl["plan_id"] == shop
    items = items_by_key(sl)

    chicken = items["chicken breast|mass"]
    assert (chicken["qty"], chicken["unit"], chicken["display"]) == (2200, "g", "2.2 kg")
    assert chicken["name"] == "Chicken breast" and chicken["aisle"] == "Meat & Fish"  # not skipped by "Chicken" group
    assert chicken["recipes"] == ["Recipe One", "Recipe Two"]

    salt = items["salt|volume"]  # 2 x 1 tsp (each_of) + 2 tsp = 4 tsp
    assert (salt["qty"], salt["unit"], salt["display"]) == (20, "ml", "4 tsp")
    assert items["paprika|volume"]["display"] == "2 tsp"  # each_of expanded
    assert items["cumin|volume"]["display"] == "2 tsp"
    oil = items["olive oil|volume"]  # 2 x 15ml + 50ml
    assert (oil["qty"], oil["display"]) == (80, "80 ml")
    assert items["onion|count"]["display"] == "5"

    # "Parsley" as needed in one recipe joins the quantified handful from the other
    parsley = items["parsley|handful"]
    assert parsley["display"] == "1 handful" and sorted(parsley["recipes"]) == ["Recipe One", "Recipe Two"]
    pepper = items["black pepper|any"]
    assert (pepper["qty"], pepper["display"]) == (None, "as needed")

    assert not [k for k in items if "water" in k]  # Skip aisle
    assert not [k for k in items if "spice mix" in k]  # reference to another component

    aisles = [a["aisle"] for a in sl["aisles"]]
    assert aisles == ["Produce", "Meat & Fish", "Sauces & Pantry", "Spices & Seasonings"]
    assert all(not i["checked"] and not i["extra"] for i in items.values())


def test_shopping_checked_survives_recompute(client, shop):
    sl = client.put(f"/api/plans/{shop}/shopping/checked", json={"key": "chicken breast|mass", "checked": True}).json()
    assert items_by_key(sl)["chicken breast|mass"]["checked"] is True
    # change the plan: quantities change, the tick stays
    entry = client.get("/api/plans/current").json()["entries"][0]
    client.patch(f"/api/plans/{shop}/entries/{entry['id']}", json={"servings": 2})
    items = items_by_key(client.get(f"/api/plans/{shop}/shopping").json())
    assert items["chicken breast|mass"]["checked"] is True and items["chicken breast|mass"]["qty"] == 1700
    assert items["salt|volume"]["checked"] is False
    client.put(f"/api/plans/{shop}/shopping/checked", json={"key": "chicken breast|mass", "checked": False})
    assert items_by_key(client.get(f"/api/plans/{shop}/shopping").json())["chicken breast|mass"]["checked"] is False


def test_shopping_extras(client, shop):
    sl = client.post(f"/api/plans/{shop}/shopping/extras", json={"text": "Kitchen roll"}).json()
    assert sl["aisles"][-1]["aisle"] == "Extras"
    extra = sl["aisles"][-1]["items"][0]
    assert extra["name"] == "Kitchen roll" and extra["extra"] is True and extra["key"].startswith("extra:")
    sl = client.put(f"/api/plans/{shop}/shopping/checked", json={"key": extra["key"], "checked": True}).json()
    assert sl["aisles"][-1]["items"][0]["checked"] is True
    extra_id = extra["key"].split(":")[1]
    sl = client.delete(f"/api/plans/{shop}/shopping/extras/{extra_id}").json()
    assert "Extras" not in [a["aisle"] for a in sl["aisles"]]
    assert client.delete(f"/api/plans/{shop}/shopping/extras/{extra_id}").status_code == 404
    assert client.put(f"/api/plans/{shop}/shopping/checked", json={"key": "extra:999", "checked": True}).status_code == 404
    assert client.post(f"/api/plans/{shop}/shopping/extras", json={"text": "  "}).status_code == 422
    assert client.get("/api/plans/999/shopping").status_code == 404


def test_shopping_reads_legacy_skip_rows(client, data_dir):
    """Databases imported before the reference fix marked "Chicken Breast" in a "Chicken" group as Skip."""
    r = make(client, title="Legacy", servings=1, groups=[{"name": "Chicken", "lines": ["300g Chicken Breast",
                                                                                    "100ml Cold Water"]}])
    conn = dbmod.connect(data_dir)
    conn.execute("UPDATE ingredients SET aisle = 'Skip' WHERE recipe_id = ?", (r["id"],))
    conn.commit()
    pid = client.get("/api/plans/current").json()["id"]
    sl = client.post(f"/api/plans/{pid}/entries", json={"recipe_id": r["id"]})
    items = items_by_key(client.get(f"/api/plans/{pid}/shopping").json())
    assert list(items) == ["chicken breast|mass"]
    detail = client.get(f"/api/recipes/{r['id']}").json()
    assert [i["aisle"] for i in detail["groups"][0]["items"]] == ["Meat & Fish", "Skip"]


# ---------------------------------------------------------------- import

def _tiny_pdf(path):
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((36, 225), "Test Upload Bowl", fontsize=28)
    page.insert_text((36, 290), "Macros per serving", fontsize=12)
    page.insert_text((36, 312), "350 CALORIES", fontsize=10)
    page.insert_text((138, 312), "40g PROTEIN", fontsize=10)
    page.insert_text((63, 355), "Ingredients (2 Servings)", fontsize=16)
    page.insert_text((40, 383), "Bowl:", fontsize=10)
    page.insert_text((58, 400), "300g Chicken Breast", fontsize=9.5)
    page.insert_text((58, 414), "1 Tsp Salt", fontsize=9.5)
    page.insert_text((63, 550), "How to make", fontsize=16)
    page.insert_text((44, 580), "1. Cook the chicken.", fontsize=9.5)
    doc.save(path)


def test_import_upload(client, data_dir, tmp_path):
    pdf = tmp_path / "Upload Test.pdf"
    _tiny_pdf(pdf)
    r = client.post("/api/import", files={"file": ("Upload Test.pdf", pdf.read_bytes(), "application/pdf")})
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["source"] == "Upload Test" and res["added"] == 1 and res["updated"] == 0 and res["kept"] == 0
    assert (data_dir / "pdfs" / "Upload Test.pdf").exists()
    assert client.get("/api/recipes", params={"q": "upload"}).json()["total"] == 1
    again = client.post("/api/import", files={"file": ("Upload Test.pdf", pdf.read_bytes(), "application/pdf")}).json()
    assert again["updated"] == 1
    assert client.post("/api/import", files={"file": ("x.pdf", b"not a pdf", "application/pdf")}).status_code == 400


# ---------------------------------------------------------------- collections and dish types

def test_collection_and_category_are_derived_and_filterable(client):
    a = make(client, title="Garlic Chicken Rice Bowls Meal Prep")
    b = make(client, title="Spicy Test Wraps")
    c = make(client, title="Berry Protein Smoothie")
    d = make(client, title="Test Noodles", collection="meal_prep", category="Noodles")
    assert (a["collection"], a["category"]) == ("meal_prep", "Rice & bowls")
    assert (b["collection"], b["category"]) == ("recipes", "Wraps, tacos & burgers")
    assert (c["collection"], c["category"]) == ("recipes", "Smoothies & drinks")
    assert (d["collection"], d["category"]) == ("meal_prep", "Noodles")

    mp = client.get("/api/recipes", params={"collection": "meal_prep"}).json()
    assert {r["title"] for r in mp["items"]} == {a["title"], d["title"]}
    wraps = client.get("/api/recipes", params={"collection": "recipes", "category": "Wraps, tacos & burgers"}).json()
    assert [r["id"] for r in wraps["items"]] == [b["id"]]

    cols = {c["collection"]: c for c in client.get("/api/collections").json()}
    assert cols["meal_prep"]["count"] == 2
    # dish types come back in display order, not alphabetically
    assert [x["category"] for x in cols["meal_prep"]["categories"]] == ["Rice & bowls", "Noodles"]
    assert cols["recipes"]["count"] == 2


def test_old_databases_are_backfilled(data_dir, tmp_path):
    conn = dbmod.connect(data_dir)
    conn.execute("INSERT INTO recipes (slug, title, tags) VALUES ('x', 'Creamy Test Pasta', '[]')")
    conn.execute("UPDATE recipes SET collection = NULL, category = NULL")
    conn.commit()
    conn.close()
    conn = dbmod.connect(data_dir)
    assert tuple(conn.execute("SELECT collection, category FROM recipes").fetchone()) == ("recipes", "Pasta & mac n cheese")
