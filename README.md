# Cookbook

A small self-hosted app for meal prep, cooking and shopping lists, built from cookbook PDFs you own.

- **Importer** reads cookbook PDFs and turns each recipe into structured data: macros, servings, ingredient groups with parsed quantities and units, steps, tips, the photo and any recipe video links.
- **Web app** lets you browse and search recipes, scale servings, cook step by step, plan the week and get one combined shopping list grouped by aisle.

Recipe content stays on your machine. The database, photos and PDFs live in a data folder outside the repo (`~/.local/share/cookbook` by default, or `$COOKBOOK_DATA_DIR`), and `.gitignore` keeps them out of git.

## Requirements

- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- Node.js + npm to build the web UI
- No Docker needed. The app runs as a plain Python process, as a systemd user service in production.

## Import your cookbooks

```sh
uv sync
uv run cookbook-import path/to/Cookbook.pdf path/to/Another.pdf --report import-report.md
```

Re-running the import updates recipes in place. Recipes you've edited in the app are never overwritten. `--report` writes a list of recipes that might need a quick look, such as an ingredient the book printed without a name.

### Supported layouts

The importer auto-detects two common InDesign cookbook layouts:

| Layout | What a recipe looks like |
| --- | --- |
| `single_page` | One page: title, "Macros per serving", "Ingredients (…)", "How to make" and a tips column |
| `two_page` | A "Recipe # N" cover page with photo and nutrition, then a page with INGREDIENTS, INSTRUCTIONS and IMPORTANT COOKING NOTES |

To support another book, add a detect and parse function pair in `src/cookbook/importer/parsers.py` and register it in `PARSERS`.

## Run the server

```sh
uv run cookbook-serve                     # http://127.0.0.1:8000
uv run cookbook-serve --host 0.0.0.0 --port 8000 --data-dir ~/.local/share/cookbook
```

It serves the JSON API under `/api` (documented in [docs/API.md](docs/API.md); interactive docs at `/docs`), recipe
photos under `/images`, and the built web UI from `web/dist` (build it with `cd web && npm ci && npm run build`).

To run it permanently on a home machine and reach it over Tailscale, see [deploy/README.md](deploy/README.md).

## Data model

SQLite tables: `sources`, `recipes`, `ingredient_groups`, `ingredients`, `steps`, `notes`, plus an FTS5 index `recipe_search`, and `meal_plans`, `plan_entries`, `shopping_checks`, `shopping_extras` for the weekly plan and shopping list. Each ingredient keeps the original text (`raw`) alongside the parsed `qty`, `qty_max`, `unit`, `item`, `prep`, a `canonical` name used to merge shopping lists, and an `aisle`.

## Development

```sh
uv run pytest
```

Tests use small synthetic PDFs and made-up recipes, so no cookbook content is needed.

## License

MIT
