"""Pydantic models mirroring the types in docs/API.md."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Day = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class Ingredient(BaseModel):
    id: int
    kind: Literal["item", "note"]
    raw: str
    qty: float | None
    qty_max: float | None
    unit: str | None
    alt_measure: str | None
    item: str
    prep: str | None
    note: str | None
    canonical: str
    aisle: str
    each_of: list[str]
    display: str


class IngredientGroup(BaseModel):
    name: str | None
    note: str | None
    items: list[Ingredient]


class SourceRef(BaseModel):
    id: int
    name: str


class RecipeSummary(BaseModel):
    id: int
    slug: str
    title: str
    blurb: str | None
    image_url: str | None
    kcal: float | None
    protein: float | None
    carbs: float | None
    fat: float | None
    servings: float | None
    tags: list[str]
    source: SourceRef | None
    favourite: bool
    collection: Literal["meal_prep", "recipes"]
    category: str


class RecipeDetail(RecipeSummary):
    servings_text: str | None
    videos: dict[str, str]
    source_page: int | None
    scale: float
    scaled_servings: float | None
    groups: list[IngredientGroup]
    steps: list[str]
    notes: list[str]
    user_edited: bool


class RecipeList(BaseModel):
    items: list[RecipeSummary]
    total: int


class GroupInput(BaseModel):
    name: str | None = None
    note: str | None = None
    lines: list[str] = Field(default_factory=list)


class RecipeInput(BaseModel):
    title: str = Field(min_length=1)
    blurb: str | None = None
    servings: float | None = Field(default=None, gt=0)
    kcal: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None
    tags: list[str] = Field(default_factory=list)
    collection: Literal["meal_prep", "recipes"] | None = None  # derived from the title when omitted
    category: str | None = None                                # derived from the title when omitted
    groups: list[GroupInput] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class FavouriteInput(BaseModel):
    favourite: bool


class CategoryCount(BaseModel):
    category: str
    count: int


class CollectionInfo(BaseModel):
    collection: Literal["meal_prep", "recipes"]
    count: int
    categories: list[CategoryCount]


class TagCount(BaseModel):
    tag: str
    count: int


class SourceInfo(BaseModel):
    id: int
    name: str
    recipe_count: int


class ImportWarning(BaseModel):
    title: str
    page: int
    warnings: list[str]


class ImportResult(BaseModel):
    source: str
    added: int
    updated: int
    kept: int
    warnings: list[ImportWarning]


class PlanEntry(BaseModel):
    id: int
    recipe: RecipeSummary
    servings: float
    day: Day | None
    position: int


class PlanTotals(BaseModel):
    servings: float
    kcal: float
    protein: float
    carbs: float
    fat: float


class Plan(BaseModel):
    id: int
    week_start: str
    entries: list[PlanEntry]
    totals: PlanTotals


class EntryCreate(BaseModel):
    recipe_id: int
    servings: float | None = Field(default=None, gt=0)
    day: Day | None = None


class EntryPatch(BaseModel):
    servings: float | None = Field(default=None, gt=0)
    day: Day | None = None
    position: int | None = None


class ShoppingItem(BaseModel):
    key: str
    name: str
    qty: float | None
    unit: str | None
    display: str
    recipes: list[str]
    checked: bool
    extra: bool


class Aisle(BaseModel):
    aisle: str
    items: list[ShoppingItem]


class ShoppingList(BaseModel):
    plan_id: int
    aisles: list[Aisle]


class CheckInput(BaseModel):
    key: str
    checked: bool


class ExtraInput(BaseModel):
    text: str = Field(min_length=1)


class Health(BaseModel):
    ok: bool
    recipes: int
