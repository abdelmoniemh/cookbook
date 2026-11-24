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


# ---------------------------------------------------------------- collection and dish type

COLLECTIONS = ("meal_prep", "recipes")

# Dish types in display order. The first rule that matches the title wins, so the order of CATEGORY_RULES matters:
# "Butter Chicken Loaded Fries" is fries before it is a curry, "Chicken Fajita Mac n Cheese" is pasta, not a wrap.
CATEGORIES = [
    "Rice & bowls", "Pasta & mac n cheese", "Noodles", "Potatoes & fries", "Wraps, tacos & burgers", "Curries",
    "Pizza", "Proteins & mains", "Breakfast", "Sides", "Smoothies & drinks", "Desserts & snacks",
]
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("Smoothies & drinks", ["smoothie", "shake", "refresher", "juice", "latte"]),
    ("Breakfast", ["breakfast", "pancake", "french toast", "overnight oats", "omelette", "eggs on toast",
                   "scrambled", "egg sandwich", "creamy eggs", "steak & eggs", "blt", "bagel"]),
    ("Desserts & snacks", ["cookie", "brownie", "ice cream", "krispies", "cheesecake", "bars", "pizza bites"]),
    ("Pizza", ["pizza"]),
    ("Pasta & mac n cheese", ["pasta", "mac n cheese", "mac & cheese", "mac and cheese", "alfredo", "linguine",
                              "lasagna", "lasagne", "spaghetti", "penne", "bolognese"]),
    ("Noodles", ["noodle", "chow mein", "pad thai", "ramen", "lo mein"]),
    ("Potatoes & fries", ["potato", "fries", "chips", "mash", "skillet"]),
    ("Rice & bowls", ["bowl"]),
    ("Wraps, tacos & burgers", ["wrap", "burrito", "taco", "quesadilla", "dilla", "burger", "sandwich",
                                "nachos", "kebab", "gyro", "naan"]),
    ("Curries", ["curry", "masala", "butter chicken", "tikka", "korma", "biryani"]),
    ("Rice & bowls", ["rice"]),
]
PROTEIN_WORDS = re.compile(r"\b(chicken|beef|steak|shrimp|prawn|salmon|tuna|lamb|turkey|eggs?)\b")
SIDE_WORDS = re.compile(r"\b(fries|yellow rice|potatoes|chips|salad)\b")


def derive_collection(title: str, tags: list[str], source_name: str | None) -> str:
    """Meal prep = batch-cook recipes (the meal prep book, or a title that says so); everything else is a recipe."""
    text = f"{title} {source_name or ''}".lower()
    return "meal_prep" if "meal prep" in text or "meal prep" in tags else "recipes"


def derive_category(title: str, tags: list[str] | None = None) -> str:
    t = title.lower()
    if SIDE_WORDS.search(t) and not PROTEIN_WORDS.search(t) and not re.search(r"\bloaded\b", t):
        return "Sides"  # "Garlic Parmesan Fries", "Golden Yellow Rice"
    for category, keywords in CATEGORY_RULES:
        if any(re.search(rf"\b{re.escape(k)}", t) for k in keywords):
            return category
    tags = tags or []
    if "breakfast" in tags:
        return "Breakfast"
    if "smoothie" in tags:
        return "Smoothies & drinks"
    if "dessert" in tags:
        return "Desserts & snacks"
    return "Proteins & mains"
