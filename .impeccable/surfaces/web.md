---
version: 1
slug: "web"
primary_target: "web"
related_targets: []
---

## Scope

The whole web app in `web/`: Browse, Recipe, Cook mode, Plan, Shopping, Add/Edit/Import. Mode: Operate (Recipe leans Read). Phone first for Shopping and Cook; desktop for planning.

## Audience and task

The owner, alone. Choose recipes by photo and protein, plan a week, shop one-handed, cook with the phone propped up. Content: ~270 recipes with photos and per-serving macros. Constraints: offline on the tailnet, self-hosted fonts, no real cookbook content in the repo.

## Direction contract

THESIS: A meal-prep app that reads macros the way a lifter reads a loaded bar: colour-coded weight you can count from across the room. Refuses the category default of a white recipe grid with a green accent and grey macro text.

OWN-WORLD: Competition bumper plates. Plate blue (deep, slightly violet IWF blue) owns the shell: top bar on desktop, tab bar on phone, primary actions. Cool chalk-white ground (light) / rubber graphite (dark). Plate red = protein, plate yellow = carbs, plate green = fat, used only as data series. Barlow for UI, Barlow Condensed heavy for numerals and titles, like plate lettering. Square-ish 6px radii, thin rules, no glass.

STORY: The visitor sees food first, then protein and kcal on every card, picks two meal preps, scales servings, gets one list by aisle, checks it off, cooks step by step.

FIRST VIEWPORT: Browse: blue app bar with search field and nav; filter chip row; photo grid (2 columns phone, 4-5 desktop) with each card's photo full-bleed, condensed title, and the loaded-bar strip plus big protein number under it. Primary action on recipe: "Add to plan" in plate blue.

FORM: Loaded bar. Each recipe's macro split (protein/carbs/fat by kcal share) is drawn as plate-coloured segments on a bar; the same strip scales up on the recipe page and sums the week on the plan. Position 5 of 7 on the grounded list. seed:cc990e0993e7f6fe (degraded roll, no challengers).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Unresolved

Roll ran degraded (impeccable.style roll API unreachable); no decision page could be shown to the owner (agent ran unattended), so the assigned direction was built without user confirmation.
