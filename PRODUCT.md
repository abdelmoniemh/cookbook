# Product

<!-- impeccable:product-schema 1 -->

<!-- Written by an agent from the owner's written brief; no live interview was possible.
     Facts marked (inferred) were not confirmed by the owner. -->

## Platform

web

## Stack

Vite + React + TypeScript single-page app in `web/`, React Router, plain CSS with custom properties, self-hosted fonts (no third-party CDNs). Python/FastAPI backend in `src/cookbook` serves `/api`, `/images` and the built `web/dist` with an SPA fallback. Specified by the owner in the brief.

## Users

One user: the owner. Personal use, no accounts, no sharing. They cook high-protein meal prep from two fitness cookbooks they own.

Three situations, in order of how often the screens get used:

1. **In the store, on the phone, one hand on a basket.** Ticking items off a combined shopping list, aisle by aisle.
2. **In the kitchen, phone propped against something.** Following a recipe step by step with messy hands, glancing from a distance.
3. **At a desk or on the sofa, planning the week.** Browsing photos, comparing macros, picking two-ish meal preps for a Sunday batch cook, sometimes breakfasts or snacks, scaling servings.

## Product Purpose

Turn a pile of cookbook PDFs into a working weekly routine: pick recipes, scale them, get one shopping list grouped by aisle, cook from the phone. Success is a Sunday batch cook that starts from a list already ticked off in the store, with no flipping through PDFs.

## Positioning

It is the owner's own books, on their own machine, structured by an importer that understands those books' layouts: grams, per-serving macros, grouped ingredients, the books' own photos and video links. Not a recipe-discovery service, not a calorie tracker, not social.

## Operating Context

- Served from a home PC over Tailscale; reached from a phone and a desktop browser on the tailnet. No internet dependency at runtime (fonts, icons, scripts are all local).
- Added to the phone home screen (PWA-lite: manifest + icons).
- Typical week: choose recipes for the plan (Monday-start week), adjust servings, open the shopping list in the store, check items off, cook Sunday with the phone screen kept awake.
- Shopping aisles in store order: Produce, Meat & Fish, Dairy & Eggs, Pasta Rice & Grains, Sauces & Pantry, Spices & Seasonings, Other. Spices are usually already in the cupboard.

## Capabilities and Constraints

- ~270 recipes from two books. Each has a large food photo, macros per serving (kcal, protein, carbs, fat), servings, ingredient groups in grams (with "note" lines mixed in that are instructions, not things to buy), numbered steps, tips, and YouTube/TikTok/Instagram links.
- Server-side scaling (`?servings=N`), full-text search, tags (protein, meal type, style, "meal prep"), sources (books), favourites.
- Plans per week with entries, servings and an optional day; a derived shopping list with persisted check state and manual extras.
- Recipes can be created and edited in the app; PDFs can be imported from the app.
- API contract: `docs/API.md`.
- Terminology: "recipe", "plan" / "this week", "shopping list", "servings", "macros", "meal prep", "book" for a source.

## Evidence on Hand

- The real recipe content and photos live only in the owner's local data folder (outside git). They must never be committed, screenshotted into the repo, or used in mock data.
- Mock/demo data in `web/mock/` is synthetic and must stay so.

## Product Principles

1. **The photos sell the food.** Browsing is choosing by eye first, macros second; the interface stays out of the photo's way.
2. **Built for the hand that is busy.** Big targets, one-handed reach, readable at arm's length, nothing that needs precision tapping in a store or kitchen.
3. **Numbers you can trust at a glance.** Protein and kcal are decision data; show them consistently, scaled correctly, never buried.
4. **One week at a time.** The plan and the shopping list are the spine of the product; everything else feeds them.
5. **Local and quiet.** Works offline on the tailnet, no accounts, no nudges.

## Accessibility & Inclusion

No specific user need stated (inferred: WCAG AA contrast, keyboard operable, respects reduced motion and light/dark preference, large touch targets for kitchen and store use).
