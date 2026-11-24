"""Derive simple tags (protein, meal type, dish style) from a recipe's title and ingredients."""
from __future__ import annotations

import re

PROTEIN = {
    "chicken": ["chicken", "wings", "tenders"],
    "beef": ["beef", "steak", "burger", "bolognese", "bolognaise", "lasagna", "mince", "philly", "smash"],
    "seafood": ["salmon", "shrimp", "prawn", "tuna", "fish", "cod"],
    "egg": ["egg", "omelette"],
}
MEAL = {
    "breakfast": ["breakfast", "pancake", "french toast", "oats", "omelette", "eggs on toast", "scrambled", "muffin"],
    "smoothie": ["smoothie", "shake", "refresher"],
    "dessert": ["cookie", "brownie", "ice cream", "rice krispies", "tiramisu", "cheesecake"],
    "side": ["garlic parmesan fries", "crispy fries", "yellow rice"],
}
STYLE = {
    "pasta": ["pasta", "mac", "lasagna", "spaghetti", "alfredo", "penne"],
    "rice": ["rice", "biryani", "burrito bowl"],
    "noodles": ["noodle", "chow mein", "pad thai"],
    "wrap": ["wrap", "burrito", "taco", "quesadilla", "dilla"],
    "burger": ["burger", "sandwich", "bun"],
    "bowl": ["bowl"],
    "potato": ["potato", "fries", "chips"],
    "curry": ["curry", "masala", "butter chicken", "tikka"],
    "pizza": ["pizza"],
}


def _hits(text: str, table: dict[str, list[str]]) -> list[str]:
    return [tag for tag, kws in table.items() if any(re.search(rf"\b{re.escape(k)}", text) for k in kws)]


def derive_tags(title: str, ingredient_names: list[str], meal_prep_book: bool) -> list[str]:
    t = title.lower()
    ings = " ".join(ingredient_names).lower()
    tags = _hits(t, PROTEIN) or _hits(ings, {k: v for k, v in PROTEIN.items() if k != "egg"})
    meal = _hits(t, MEAL)
    tags += meal or ["main"]
    tags += _hits(t, STYLE)
    if meal_prep_book:
        tags.append("meal prep")
    out: list[str] = []
    for tag in tags:
        if tag not in out:
            out.append(tag)
    return out
