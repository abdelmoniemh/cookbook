"""Parse free-text ingredient lines into structured quantities.

Examples handled:
    "800g (28oz) Raw Chicken Breasts, cubed"
    "1.5 Tsp Salt"
    "½ Tsp Nutmeg (adds a great deep flavour!)"
    "25-30g (2 Tbsp) Corn Flour/Corn Starch"
    "Juice of 3/4 Lemon"
    "Handful Fresh Parsley, chopped"
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, asdict

UNICODE_FRACTIONS = {
    "½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4",
    "⅛": "1/8", "⅕": "1/5", "⅙": "1/6",
}

# canonical unit -> spellings (lower case)
UNITS = {
    "g": ["g", "gr", "gram", "grams"],
    "kg": ["kg"],
    "ml": ["ml"],
    "l": ["l", "litre", "liter", "litres", "liters"],
    "oz": ["oz"],
    "lb": ["lb", "lbs"],
    "tsp": ["tsp", "tsps", "teaspoon", "teaspoons"],
    "tbsp": ["tbsp", "tbsps", "tablespoon", "tablespoons"],
    "cup": ["cup", "cups"],
    "scoop": ["scoop", "scoops"],
    "clove": ["clove", "cloves"],
    "slice": ["slice", "slices"],
    "pinch": ["pinch"],
    "handful": ["handful", "handfuls"],
    "can": ["can", "cans", "tin", "tins"],
    "pack": ["pack", "packs", "packet", "packets"],
    "piece": ["piece", "pieces", "pc", "pcs"],
    "serving": ["serving", "servings"],
}
UNIT_LOOKUP = {s: canon for canon, spellings in UNITS.items() for s in spellings}
_unit_alt = "|".join(sorted(UNIT_LOOKUP, key=len, reverse=True))

_num = r"(?:\d+(?:\s+and)?\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)"
QTY_RE = re.compile(
    rf"^(?P<qty>{_num})(?:\s*(?:-|–|to|or)\s*(?P<qty_max>{_num}))?\s*(?P<unit>{_unit_alt})?\b\.?,?\s*",
    re.IGNORECASE,
)
ALT_RE = re.compile(r"^\(([^)]*)\)\s*")
OR_ALT_RE = re.compile(rf"^or\s+({_num}\s*-?\s*(?:{_num})?\s*(?:{_unit_alt})\b)\s*", re.IGNORECASE)
JUICE_RE = re.compile(rf"^juice of\s+(?:a\s+)?(?P<qty>{_num})?\s*", re.IGNORECASE)
WORD_QTY = {"handful": "handful", "pinch": "pinch", "a pinch": "pinch", "a handful": "handful"}


def _to_float(s: str | None) -> float | None:
    if not s:
        return None
    s = s.strip()
    s = s.replace(" and ", " ")
    if " " in s:  # mixed number "1 1/2"
        whole, frac = s.split(None, 1)
        return float(whole) + _to_float(frac)
    if "/" in s:
        a, b = s.split("/")
        return float(a) / float(b)
    return float(s)


def normalize_text(s: str) -> str:
    for k, v in UNICODE_FRACTIONS.items():
        s = s.replace(k, " " + v if s and not s.startswith(k) else v)
    s = s.replace("’", "'").replace("\t", " ")
    s = re.sub(r"\s+", " ", s).strip(" -–»,")
    return s.strip()


@dataclass
class Ingredient:
    raw: str
    qty: float | None = None
    qty_max: float | None = None
    unit: str | None = None
    alt_measure: str | None = None
    item: str = ""
    prep: str | None = None
    note: str | None = None
    canonical: str = ""
    aisle: str = "Other"
    parsed: bool = True
    kind: str = "item"  # "item" goes on the shopping list, "note" is an instruction mixed into the list
    each: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


NOTE_RE = re.compile(r"^(note:|season|add |blend|use |distribute|serve|you |mix |cook|bring|let |stir|whisk|"
                     r"roughly|optional:|extra seasoning|then |evenly |or serve|to serve|for serving)", re.I)
GARNISH_RE = re.compile(r"^(garnish|top|topped)( with)?\s+", re.I)
SPICE_UNITS = {"tsp", "tbsp", "pinch"}


def parse_ingredient(raw: str) -> Ingredient:
    text = normalize_text(raw)
    ing = Ingredient(raw=text)
    if NOTE_RE.match(text) or len(text) > 140:
        ing.kind, ing.parsed, ing.item = "note", True, text
        return ing
    rest = text
    m = GARNISH_RE.match(rest)
    if m:
        rest = rest[m.end():]
        ing.prep = "for garnish"
    rest = re.sub(r"^\(optional\)\s*", "", rest, flags=re.I)
    rest = re.sub(r"^(\d+)x\s+", r"\1 ", rest)  # "2x Brioche Buns"
    rest = re.sub(r"^(a )?(good |big )?handful( of)?\s+", "Handful ", rest, flags=re.I)

    m = JUICE_RE.match(rest)
    if m:
        ing.qty = _to_float(m.group("qty")) or 1
        ing.unit = "juice"
        rest = rest[m.end():]
    else:
        lower = rest.lower()
        for word, unit in WORD_QTY.items():
            if lower.startswith(word + " "):
                ing.qty, ing.unit = 1, unit
                rest = rest[len(word):].strip()
                break
        else:
            m = QTY_RE.match(rest)
            if m:
                ing.qty = _to_float(m.group("qty"))
                ing.qty_max = _to_float(m.group("qty_max"))
                if ing.qty_max is not None and ing.qty_max < ing.qty:  # "1 or 1/2 Tsp"
                    ing.qty, ing.qty_max = ing.qty_max, ing.qty
                if m.group("unit"):
                    ing.unit = UNIT_LOOKUP[m.group("unit").lower()]
                rest = rest[m.end():]

    m = ALT_RE.match(rest) or OR_ALT_RE.match(rest)
    if m:
        ing.alt_measure = m.group(1).strip()
        rest = rest[m.end():]
    rest = re.sub(r"^of\s+", "", rest, flags=re.I)

    # trailing parenthetical notes: "(omit for milder flavour)"
    notes = re.findall(r"\(([^)]*)\)", rest)
    if notes:
        ing.note = "; ".join(n.strip() for n in notes)
        rest = re.sub(r"\s*\([^)]*\)", "", rest)
    # "Sriracha - Helps digestion" style descriptions
    if " - " in rest:
        rest, desc = rest.split(" - ", 1)
        ing.note = "; ".join(filter(None, [ing.note, desc.strip()]))
    each_kw = re.match(r"(?i)each\b[,:\s]*", rest)
    if each_kw:
        rest = rest[each_kw.end():]
        ing.each = [p.strip() for p in re.split(r",|&| and ", rest) if p.strip()]
        rest = ing.each[0] if ing.each else rest
    if "," in rest:
        head_, prep = rest.split(",", 1)
        parts = [p.strip() for p in prep.split(",") if p.strip()]
        if ing.unit in SPICE_UNITS and parts and all(p[:1].isupper() for p in parts):
            # "1 Tsp Salt, Paprika, Cumin" -> 1 tsp each
            ing.each = [head_.strip()] + parts
            rest = head_
        else:
            rest = head_
            ing.prep = "; ".join(filter(None, [ing.prep, prep.strip()])) or None

    rest = rest.strip()
    if not ing.each and re.fullmatch(r"(?i)(each )?salt (&|and) (black )?pepper", rest):
        ing.each = ["Salt", "Black Pepper"]
    ing.item = rest
    ing.canonical = canonical_name(ing.each[0] if ing.each else rest)
    ing.aisle = classify_aisle(ing.canonical)
    if re.fullmatch(r"(boiled |cold |warm |hot |pasta |of )?water|ice( cube)?|ice water", ing.canonical):
        ing.aisle = "Skip"  # never goes on the shopping list
    ing.parsed = bool(ing.item) and (ing.qty is not None or ing.unit is not None)
    return ing


_STRIP_WORDS = r"\b(raw|uncooked|fresh|freshly|chopped|minced|diced|sliced|cubed|grated|shredded|large|small|medium|boneless|skinless|optional)\b"


ADJECTIVES = {"low", "light", "red", "white", "rolled", "dark", "fat", "zero", "95%", "5%", "green", "yellow",
              "dried", "frozen", "plain", "greek", "lean", "ground", "reduced", "skimmed", "free", "brown", "long",
              "short", "sweet", "smoked", "hot", "mild", "extra", "virgin"}


def canonical_name(item: str) -> str:
    s = unicodedata.normalize("NFKD", item.lower()).encode("ascii", "ignore").decode()
    s = re.sub(_STRIP_WORDS, " ", s)
    s = re.sub(r"\s*/\s*", " or ", s)
    alts = [a.strip() for a in re.split(r"\bor\b", s) if a.strip()]
    if len(alts) > 1:
        # "red or white onion" -> "white onion"; "honey or sugar free syrup" -> "honey"
        first_words = alts[0].split()
        s = alts[-1] if all(w in ADJECTIVES for w in first_words) else alts[0]
    s = re.sub(r"[^a-z0-9%& ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    words = s.split()
    if words and len(words[-1]) > 4 and words[-1].endswith("ies"):
        words[-1] = words[-1][:-3] + "y"
    elif words and len(words[-1]) > 3 and words[-1].endswith("es") and words[-1][:-2].endswith(("tomato", "potato")):
        words[-1] = words[-1][:-2]
    elif words and len(words[-1]) > 3 and words[-1].endswith("s") and not words[-1].endswith(("ss", "us")):
        words[-1] = words[-1][:-1]
    return " ".join(words)


# Aisle keywords, checked in order. Loosely follows the "Master Grocery List" in the Meal Prep Cookbook.
AISLES: list[tuple[str, list[str]]] = [
    ("Meat & Fish", ["chicken", "beef", "steak", "mince", "turkey", "lamb", "shrimp", "prawn", "salmon",
                      "tuna", "fish", "bacon", "sausage", "topside", "sirloin", "cod"]),
    ("Dairy & Eggs", ["parmigiano", "milk", "cheese", "cheddar", "mozzarella", "parmesan", "feta", "yogurt", "yoghurt",
                       "butter", "cream", "egg", "skyr", "quark"]),
    ("Spices & Seasonings", ["salt", "pepper flake", "black pepper", "white pepper", "paprika", "powder", "cumin",
                              "oregano", "chilli flake", "chili flake", "turmeric", "garam masala", "thyme",
                              "basil", "sumac", "seasoning", "cinnamon", "nutmeg", "parsley flake", "dried",
                              "cajun", "spice", "coriander seed", "red pepper flake"]),
    ("Produce", ["onion", "garlic", "potato", "tomato", "parsley", "coriander", "cilantro", "lemon", "lime",
                  "pepper", "cucumber", "carrot", "ginger", "lettuce", "spinach", "broccoli", "mushroom",
                  "avocado", "banana", "berry", "blueberr", "strawberr", "raspberr", "blackberr", "apple", "mango", "watermelon", "mint", "chilli",
                  "jalapeno", "scallion", "shallot", "sweetcorn", "pickle", "gherkin", "kimchi", "spring onion", "cabbage", "kale", "zucchini", "courgette", "corn",
                  "celery", "pineapple", "orange", "date"]),
    ("Pasta, Rice & Grains", ["pasta", "macaroni", "penne", "spaghetti", "fettuccine", "linguine", "noodle",
                               "rice", "oat", "tortilla", "wrap", "bread", "bun", "naan", "flour", "lasagne",
                               "lasagna", "pita", "bagel", "muffin"]),
    ("Sauces & Pantry", ["sauce", "honey", "soy", "ketchup", "vinegar", "paste", "mustard", "oil", "syrup",
                          "sriracha", "mayo", "stock", "broth", "bean", "chickpea", "sugar", "sweetener",
                          "cocoa", "chocolate", "peanut butter", "jam", "marinade", "salsa", "tamarind",
                          "gochujang", "harissa", "pesto", "coconut", "sesame", "vanilla", "baking soda", "nut",
                          "peanut", "almond", "walnut", "flatbread", "herb"]),
    ("Other", []),
]


OVERRIDES = [
    (r"corn ?(flour|starch)|cornflour|cornstarch|plain flour|self raising", "Sauces & Pantry"),
    (r"coconut milk|almond milk|oat milk|peanut butter|cocoa butter|protein powder|whey", "Sauces & Pantry"),
    (r"vinegar|paste|stock|broth", "Sauces & Pantry"),
    (r"bell pepper|chilli pepper|green chilli|red chilli|jalapeno", "Produce"),
]


def classify_aisle(canonical: str) -> str:
    for pattern, aisle in OVERRIDES:
        if re.search(pattern, canonical):
            return aisle
    for aisle, keywords in AISLES:
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}", canonical):
                return aisle
    return "Other"
