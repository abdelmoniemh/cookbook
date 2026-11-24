import pytest

from cookbook.importer.ingredients import canonical_name, classify_aisle, parse_ingredient


@pytest.mark.parametrize(
    "raw, qty, qty_max, unit, alt, canonical, aisle",
    [
        ("800g (28oz) Raw Chicken Breasts, cubed", 800, None, "g", "28oz", "chicken breast", "Meat & Fish"),
        ("1.5 Tsp Salt", 1.5, None, "tsp", None, "salt", "Spices & Seasonings"),
        ("½ Tsp Nutmeg (adds depth)", 0.5, None, "tsp", None, "nutmeg", "Spices & Seasonings"),
        ("25-30g (2 Tbsp) Corn Flour/Corn Starch", 25, 30, "g", "2 Tbsp", "corn flour", "Sauces & Pantry"),
        ("1 or 1/2 Tsp Chilli Flakes", 0.5, 1, "tsp", None, "chilli flake", "Spices & Seasonings"),
        ("1 Tbsp or 20ml Dark or Light Soy Sauce", 1, None, "tbsp", "20ml", "light soy sauce", "Sauces & Pantry"),
        ("Juice of 1 and 1/2 Lime", 1.5, None, "juice", None, "lime", "Produce"),
        ("416ml (14.6oz) of Water", 416, None, "ml", "14.6oz", "water", "Skip"),
        ("120ml Low Fat/ Skimmed Milk", 120, None, "ml", None, "skimmed milk", "Dairy & Eggs"),
        ("30g Honey or Sugar Free Syrup", 30, None, "g", None, "honey", "Sauces & Pantry"),
        ("2 Jalapeños, sliced", 2, None, None, None, "jalapeno", "Produce"),
        ("1 Cup Blueberries", 1, None, "cup", None, "blueberry", "Produce"),
        ("2x Brioche Buns", 2, None, None, None, "brioche bun", "Pasta, Rice & Grains"),
    ],
)
def test_parse_quantities(raw, qty, qty_max, unit, alt, canonical, aisle):
    ing = parse_ingredient(raw)
    assert ing.kind == "item"
    assert ing.qty == pytest.approx(qty)
    assert ing.qty_max == (pytest.approx(qty_max) if qty_max is not None else None)
    assert ing.unit == unit
    assert ing.alt_measure == alt
    assert ing.canonical == canonical
    assert ing.aisle == aisle


@pytest.mark.parametrize(
    "raw, each",
    [
        ("1 Tsp each Salt, Pepper, Garlic Powder", ["Salt", "Pepper", "Garlic Powder"]),
        ("1/2 Tsp each, Salt, Pepper and Basil", ["Salt", "Pepper", "Basil"]),
        ("1 Tsp each: Salt, Cumin", ["Salt", "Cumin"]),
        ("1 Tsp Salt, Paprika, Cumin", ["Salt", "Paprika", "Cumin"]),
        ("1/2 Tsp Salt & Black Pepper", ["Salt", "Black Pepper"]),
    ],
)
def test_each_lists(raw, each):
    assert parse_ingredient(raw).each == each


def test_prep_and_notes():
    ing = parse_ingredient("100g (3.5oz) Low Fat Cheddar Cheese (or any low fat cheese), grated")
    assert ing.item == "Low Fat Cheddar Cheese"
    assert ing.note == "or any low fat cheese"
    assert ing.prep == "grated"


def test_garnish_and_handful():
    assert parse_ingredient("Garnish with Parsley").prep == "for garnish"
    ing = parse_ingredient("Big Handful of Coriander/Cilantro")
    assert (ing.qty, ing.unit, ing.canonical) == (1, "handful", "coriander")


def test_instruction_lines_are_notes():
    assert parse_ingredient("Season both sides with salt and pepper").kind == "note"
    assert parse_ingredient("Distribute into 4 equal servings").kind == "note"


def test_unquantified_item_is_flagged_but_kept():
    ing = parse_ingredient("Shredded Lettuce")
    assert ing.kind == "item" and not ing.parsed and ing.canonical == "lettuce"


def test_canonical_and_aisle_helpers():
    assert canonical_name("Red or White Onion") == "white onion"
    assert canonical_name("Cherry Tomatoes") == "cherry tomato"
    assert classify_aisle("rice vinegar") == "Sauces & Pantry"


def test_prep_after_comma_is_not_an_each_list():
    i = parse_ingredient("1 Tbsp Garlic, Crushed")
    assert i.each == [] and i.item == "Garlic" and i.prep == "Crushed"
    assert parse_ingredient("1 Tsp Salt, Paprika, Cumin").each == ["Salt", "Paprika", "Cumin"]


def test_canonical_drops_dangling_or():
    from cookbook.importer.ingredients import canonical_name
    assert canonical_name("Shredded/Desiccated Coconut") == "desiccated coconut"
    assert canonical_name("Fresh or Dried Parsley") == "dried parsley"


def test_component_reference_rule():
    from cookbook.importer.parsers import is_component_reference
    groups = ["Chicken", "Taco Spice Mix", "Garlic Naan"]
    assert is_component_reference("taco spice mix", "serving", "Chicken", groups)
    assert not is_component_reference("chicken breast", "g", "Chicken", groups)
    assert not is_component_reference("garlic", "tbsp", "Chicken", groups)
    assert parse_ingredient("200ml Boiling Water").aisle == "Skip"
