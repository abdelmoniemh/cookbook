"""Quantity formatting and unit conversion for recipe display and shopping lists."""
from __future__ import annotations

MASS = {"g": 1.0, "kg": 1000.0, "oz": 28.3495, "lb": 453.592}
VOLUME = {"ml": 1.0, "l": 1000.0, "tsp": 5.0, "tbsp": 15.0, "cup": 240.0}
FRACTION_UNITS = {"tsp", "tbsp", "cup"}

PLURALS = {
    "clove": "cloves", "slice": "slices", "pinch": "pinches", "handful": "handfuls", "can": "cans",
    "pack": "packs", "piece": "pieces", "serving": "servings", "scoop": "scoops", "cup": "cups",
}

_FRACTIONS = [(0.0, ""), (0.125, "⅛"), (0.25, "¼"), (1 / 3, "⅓"), (0.5, "½"), (2 / 3, "⅔"), (0.75, "¾"), (1.0, "")]


def unit_family(unit: str | None) -> str:
    """Merge family for a unit: "mass", "volume", the unit name for count units, or "count" for none."""
    if unit in MASS:
        return "mass"
    if unit in VOLUME:
        return "volume"
    return unit or "count"


def to_base(qty: float, unit: str | None) -> tuple[float, str | None]:
    """Convert to the family's base unit (g or ml); count units pass through."""
    if unit in MASS:
        return qty * MASS[unit], "g"
    if unit in VOLUME:
        return qty * VOLUME[unit], "ml"
    return qty, unit


def _trim(x: float, places: int = 1) -> str:
    s = f"{x:.{places}f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def nice_fraction(x: float) -> str:
    """1.5 -> "1½", 0.25 -> "¼", 2.4 -> "2⅓" (nearest of eighths, quarters, thirds)."""
    if x <= 0:
        return "0"
    whole = int(x)
    frac = x - whole
    options = _FRACTIONS if whole == 0 else [f for f in _FRACTIONS if f[1] != "⅛"]  # "1⅛" reads oddly
    _, best = min(options, key=lambda f: abs(frac - f[0]))
    if best == "" and frac > 0.5:
        whole += 1
    if whole == 0 and best == "":
        best = "⅛"
    return f"{whole if whole else ''}{best}"


def fmt_number(x: float, unit: str | None) -> str:
    """Format one quantity in the given unit (no unit conversion)."""
    if unit in FRACTION_UNITS:
        return nice_fraction(x)
    if unit in ("g", "ml"):
        if x < 10:
            return _trim(x)
        if x < 100:
            return str(round(x))
        return str(int(round(x / 5) * 5))
    if unit in ("kg", "l"):
        return _trim(x, 2 if x < 1 else 1)
    if unit in ("oz", "lb"):
        return _trim(x)
    # count-like units: halves and quarters read naturally ("1½ cans", "¼")
    if abs(x - round(x)) < 0.01:
        return str(int(round(x)))
    return nice_fraction(x)


def _metric_upgrade(qty: float, qty_max: float | None, unit: str | None):
    """g -> kg and ml -> l once the amount reaches 1000."""
    if unit == "g" and qty >= 997.5:  # would round to "1000 g"
        return qty / 1000, (qty_max / 1000 if qty_max is not None else None), "kg"
    if unit == "ml" and qty >= 997.5:
        return qty / 1000, (qty_max / 1000 if qty_max is not None else None), "l"
    return qty, qty_max, unit


def unit_label(unit: str | None, qty: float | None) -> str:
    if not unit:
        return ""
    if qty is not None and qty > 1 and unit in PLURALS:
        return PLURALS[unit]
    return unit


def fmt_amount(qty: float | None, qty_max: float | None, unit: str | None) -> str:
    """Amount part of a display string, e.g. "1.2 kg", "½ tsp", "25-30 g", "2 cloves"."""
    if qty is None:
        return ""
    qty, qty_max, unit = _metric_upgrade(qty, qty_max, unit)
    num = fmt_number(qty, unit)
    if qty_max is not None and qty_max != qty:
        num = f"{num}-{fmt_number(qty_max, unit)}"
    if unit == "juice":
        return f"Juice of {num}"
    top = qty_max if qty_max is not None else qty
    label = unit_label(unit, top)
    if unit in ("g", "ml", "kg", "l", "oz", "lb"):
        return f"{num} {label}"
    return f"{num} {label}".strip()


def ingredient_display(qty, qty_max, unit, item: str, prep: str | None) -> str:
    amount = fmt_amount(qty, qty_max, unit)
    text = f"{amount} {item}".strip() if amount else (item or "")
    if prep:
        text = f"{text}, {prep}"
    return text


def shopping_display(qty: float | None, unit: str | None) -> str:
    """Display for a summed shopping quantity in its base unit (g, ml, or a count unit)."""
    if qty is None:
        return "as needed"
    if unit == "ml" and qty < 60:
        tbsp = qty / 15
        if qty >= 15 and (abs(tbsp * 2 - round(tbsp * 2)) < 0.02 or qty / 5 > 8):
            return fmt_amount(tbsp, None, "tbsp")  # 1 tbsp, 1½ tbsp, 3 tbsp
        return fmt_amount(qty / 5, None, "tsp")  # 3½ tsp rather than 1⅛ tbsp
    return fmt_amount(qty, None, unit)  # g >= 1000 -> kg, ml >= 1000 -> l
