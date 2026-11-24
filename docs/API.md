# HTTP API

The FastAPI server (`cookbook-serve`, default `127.0.0.1:8000`) serves this JSON API under `/api`, recipe photos under `/images/<file>`, and the built web UI (`web/dist`) at `/` with an SPA fallback to `index.html`.

All responses are JSON. Errors use FastAPI's default `{"detail": "..."}` with a 4xx status.

## Types

```ts
type Ingredient = {
  id: number
  kind: "item" | "note"        // notes are instructions mixed into the list; never shopped
  raw: string                  // original text, always shown if parsing looks off
  qty: number | null           // already multiplied by the scale factor
  qty_max: number | null       // upper bound of a range ("25-30g"), scaled
  unit: string | null          // g, kg, ml, l, oz, lb, tsp, tbsp, cup, scoop, clove, slice, pinch, handful, can, pack, piece, serving, juice
  alt_measure: string | null   // "28oz", "2 Tbsp" (not scaled)
  item: string                 // "Raw Chicken Breasts"
  prep: string | null          // "cubed"
  note: string | null          // "or any low fat cheese"
  canonical: string            // "chicken breast" - merge key for shopping
  aisle: string                // Produce | Meat & Fish | Dairy & Eggs | Pasta, Rice & Grains | Sauces & Pantry | Spices & Seasonings | Other | Skip
  each_of: string[]            // "1 tsp each Salt, Cumin" -> ["Salt", "Cumin"]
  display: string              // human string for the scaled amount + item, e.g. "1.2 kg Raw Chicken Breasts, cubed"
}

type IngredientGroup = { name: string | null; note: string | null; items: Ingredient[] }

type RecipeSummary = {
  id: number
  slug: string
  title: string
  blurb: string | null
  image_url: string | null     // "/images/<file>.jpg"
  kcal: number | null          // per serving (never scaled)
  protein: number | null
  carbs: number | null
  fat: number | null
  servings: number | null      // the book's servings
  tags: string[]
  source: { id: number; name: string } | null   // null = created in the app
  favourite: boolean
  collection: "meal_prep" | "recipes"           // batch-cook meal preps vs everyday recipes
  category: string                              // dish type, e.g. "Rice & bowls" (see /api/collections)
}

type CollectionInfo = {
  collection: "meal_prep" | "recipes"
  count: number
  categories: { category: string; count: number }[]   // display order; empty types omitted
}

type RecipeDetail = RecipeSummary & {
  servings_text: string | null
  videos: { youtube?: string; tiktok?: string; instagram?: string }
  source_page: number | null
  scale: number                // factor applied to ingredient quantities
  scaled_servings: number | null
  groups: IngredientGroup[]
  steps: string[]
  notes: string[]              // tips / important cooking notes
  user_edited: boolean
}

type RecipeInput = {          // create / update
  title: string
  blurb?: string | null
  servings?: number | null
  kcal?: number | null; protein?: number | null; carbs?: number | null; fat?: number | null
  tags?: string[]
  collection?: "meal_prep" | "recipes"   // derived from the title when omitted
  category?: string                      // derived from the title when omitted
  groups: { name: string | null; note?: string | null; lines: string[] }[]   // raw ingredient lines; the server parses them
  steps: string[]
  notes?: string[]
}

type PlanEntry = {
  id: number
  recipe: RecipeSummary
  servings: number             // how many servings to cook (defaults to recipe.servings or 1)
  day: string | null           // "mon".."sun" or null for "anytime this week"
  position: number
}

type Plan = {
  id: number
  week_start: string           // ISO date of the Monday
  entries: PlanEntry[]
  totals: { servings: number; kcal: number; protein: number; carbs: number; fat: number }  // sum of per-serving macros x servings
}

type ShoppingItem = {
  key: string                  // stable id: canonical + "|" + unit family, or "extra:<id>"
  name: string                 // display name, e.g. "Chicken breast"
  qty: number | null           // summed, in the base unit of the family (g, ml) or count
  unit: string | null
  display: string              // "1.6 kg", "3 tbsp", "2", "as needed"
  recipes: string[]            // titles that need it
  checked: boolean
  extra: boolean               // manually added
}

type ShoppingList = { plan_id: number; aisles: { aisle: string; items: ShoppingItem[] }[] }
```

## Endpoints

| Method | Path | Body / query | Returns |
| --- | --- | --- | --- |
| GET | `/api/recipes` | `q` (full-text), `tag` (repeatable, AND), `source` (id), `collection`, `category`, `favourite` (bool), `max_kcal`, `min_protein`, `sort` = `title` \| `protein` \| `kcal` \| `recent` (default `title`), `limit` (default 50), `offset` | `{ items: RecipeSummary[], total: number }` |
| GET | `/api/recipes/{id or slug}` | `servings` (optional number; scales ingredients) | `RecipeDetail` |
| POST | `/api/recipes` | `RecipeInput` | `RecipeDetail` (201) |
| PUT | `/api/recipes/{id}` | `RecipeInput` | `RecipeDetail` (marks `user_edited`) |
| DELETE | `/api/recipes/{id}` | | 204 |
| PUT | `/api/recipes/{id}/favourite` | `{ favourite: boolean }` | `RecipeSummary` |
| GET | `/api/tags` | | `{ tag: string; count: number }[]` sorted by count |
| GET | `/api/collections` | | `CollectionInfo[]` (meal prep first) |
| GET | `/api/sources` | | `{ id, name, recipe_count }[]` |
| POST | `/api/import` | multipart `file` (PDF) | `{ source: string; added: number; updated: number; kept: number; warnings: { title: string; page: number; warnings: string[] }[] }` |
| GET | `/api/plans/current` | `week` (ISO date, any day in the week; default today) | `Plan` (created empty if missing) |
| POST | `/api/plans/{plan_id}/entries` | `{ recipe_id, servings?, day? }` | `Plan` |
| PATCH | `/api/plans/{plan_id}/entries/{entry_id}` | `{ servings?, day?, position? }` | `Plan` |
| DELETE | `/api/plans/{plan_id}/entries/{entry_id}` | | `Plan` |
| GET | `/api/plans/{plan_id}/shopping` | | `ShoppingList` |
| PUT | `/api/plans/{plan_id}/shopping/checked` | `{ key, checked }` | `ShoppingList` |
| POST | `/api/plans/{plan_id}/shopping/extras` | `{ text }` | `ShoppingList` |
| DELETE | `/api/plans/{plan_id}/shopping/extras/{id}` | | `ShoppingList` |
| GET | `/api/health` | | `{ ok: true, recipes: number }` |

## Shopping list rules

- Built from every plan entry: each ingredient of kind `item` scaled by `entry.servings / recipe.servings` (recipe servings null counts as 1).
- `aisle == "Skip"` (water, ice, references to another component of the same recipe) is left out.
- `each_of` expands into one line per name with the same amount, then re-canonicalised.
- Merge by `canonical` within a unit family: mass (g, kg, oz, lb -> g), volume (ml, l, tsp=5ml, tbsp=15ml, cup=240ml -> ml), and count units kept by unit name. Spices and seasonings (aisle "Spices & Seasonings") show the summed amount but are typically "check the cupboard" items; the UI may collapse them.
- Items with no quantity show `display: "as needed"`.
- Display: g >= 1000 -> kg with one decimal; ml >= 1000 -> l; small volumes shown back in tsp/tbsp when < 60 ml.
