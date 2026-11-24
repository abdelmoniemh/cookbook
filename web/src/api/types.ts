// Types for the cookbook HTTP API. Mirrors docs/API.md exactly; keep the two in sync.

export type Aisle =
  | 'Produce'
  | 'Meat & Fish'
  | 'Dairy & Eggs'
  | 'Pasta, Rice & Grains'
  | 'Sauces & Pantry'
  | 'Spices & Seasonings'
  | 'Other'
  | 'Skip'

export type Ingredient = {
  id: number
  kind: 'item' | 'note'
  raw: string
  qty: number | null
  qty_max: number | null
  unit: string | null
  alt_measure: string | null
  item: string
  prep: string | null
  note: string | null
  canonical: string
  aisle: Aisle | string
  each_of: string[]
  display: string
}

export type IngredientGroup = { name: string | null; note: string | null; items: Ingredient[] }

export type Source = { id: number; name: string }

export type RecipeSummary = {
  id: number
  slug: string
  title: string
  blurb: string | null
  image_url: string | null
  kcal: number | null
  protein: number | null
  carbs: number | null
  fat: number | null
  servings: number | null
  tags: string[]
  source: Source | null
  favourite: boolean
}

export type Videos = { youtube?: string; tiktok?: string; instagram?: string }

export type RecipeDetail = RecipeSummary & {
  servings_text: string | null
  videos: Videos
  source_page: number | null
  scale: number
  scaled_servings: number | null
  groups: IngredientGroup[]
  steps: string[]
  notes: string[]
  user_edited: boolean
}

export type RecipeInput = {
  title: string
  blurb?: string | null
  servings?: number | null
  kcal?: number | null
  protein?: number | null
  carbs?: number | null
  fat?: number | null
  tags?: string[]
  groups: { name: string | null; note?: string | null; lines: string[] }[]
  steps: string[]
  notes?: string[]
}

export type Day = 'mon' | 'tue' | 'wed' | 'thu' | 'fri' | 'sat' | 'sun'

export type PlanEntry = {
  id: number
  recipe: RecipeSummary
  servings: number
  day: Day | null
  position: number
}

export type MacroTotals = { servings: number; kcal: number; protein: number; carbs: number; fat: number }

export type Plan = {
  id: number
  week_start: string
  entries: PlanEntry[]
  totals: MacroTotals
}

export type ShoppingItem = {
  key: string
  name: string
  qty: number | null
  unit: string | null
  display: string
  recipes: string[]
  checked: boolean
  extra: boolean
}

export type ShoppingList = { plan_id: number; aisles: { aisle: string; items: ShoppingItem[] }[] }

export type RecipeList = { items: RecipeSummary[]; total: number }
export type TagCount = { tag: string; count: number }
export type SourceCount = Source & { recipe_count: number }

export type ImportResult = {
  source: string
  added: number
  updated: number
  kept: number
  warnings: { title: string; page: number; warnings: string[] }[]
}

export type RecipeQuery = {
  q?: string
  tag?: string[]
  source?: number
  favourite?: boolean
  max_kcal?: number
  min_protein?: number
  sort?: 'title' | 'protein' | 'kcal' | 'recent'
  limit?: number
  offset?: number
}
