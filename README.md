# Cookbook

A small self-hosted app for meal prep, cooking and shopping lists, built from cookbook PDFs you own.

- **Importer** reads cookbook PDFs and turns each recipe into structured data: macros, servings, ingredient groups with parsed quantities and units, steps, tips, the photo and any recipe video links.
- **Web app** (coming next) lets you browse and search recipes, scale servings, cook step by step, plan the week and get one combined shopping list grouped by aisle.

Recipe content stays on your machine. The database, photos and PDFs live in a data folder outside the repo (`~/.local/share/cookbook` by default, or `$COOKBOOK_DATA_DIR`), and `.gitignore` keeps them out of git.

## Requirements

- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- No Docker needed. The app runs as a plain Python process (a systemd user unit is provided later).

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

## Data model

SQLite tables: `sources`, `recipes`, `ingredient_groups`, `ingredients`, `steps`, `notes`, plus an FTS5 index `recipe_search`. Each ingredient keeps the original text (`raw`) alongside the parsed `qty`, `qty_max`, `unit`, `item`, `prep`, a `canonical` name used to merge shopping lists, and an `aisle`.

## Development

```sh
uv run pytest
```

Tests use small synthetic PDFs, so no cookbook content is needed.

## License

MIT
