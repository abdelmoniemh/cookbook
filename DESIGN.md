---
name: Cookbook
description: Self-hosted meal-prep cookbook, weekly plan and shopping list
colors:
  plate-blue: "oklch(41% 0.165 265)"
  plate-blue-hover: "oklch(36% 0.16 265)"
  plate-blue-ink: "oklch(43% 0.17 265)"
  plate-blue-tint: "oklch(92% 0.04 265)"
  on-blue: "oklch(99% 0.005 265)"
  on-blue-muted: "oklch(86% 0.04 265)"
  protein-red: "oklch(56% 0.205 27)"
  protein-red-ink: "oklch(50% 0.19 27)"
  carbs-yellow: "oklch(84% 0.16 88)"
  fat-green: "oklch(59% 0.14 152)"
  chalk-ground: "oklch(96.8% 0.006 255)"
  surface: "oklch(99.6% 0.002 255)"
  surface-raised: "oklch(93.6% 0.011 258)"
  surface-track: "oklch(90% 0.014 260)"
  ink: "oklch(21% 0.03 266)"
  ink-secondary: "oklch(40% 0.03 266)"
  ink-tertiary: "oklch(50% 0.026 266)"
  rule: "oklch(87.5% 0.013 262)"
  rule-strong: "oklch(78% 0.018 262)"
  danger: "oklch(52% 0.19 27)"
  success: "oklch(50% 0.13 152)"
typography:
  display:
    fontFamily: "Barlow Condensed, Barlow, system-ui, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 700
    lineHeight: 1.02
    letterSpacing: "0em"
  headline:
    fontFamily: "Barlow Condensed, Barlow, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.15
  title:
    fontFamily: "Barlow Condensed, Barlow, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.15
  figure:
    fontFamily: "Barlow Condensed, Barlow, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.05
    fontFeature: "'tnum' 1"
  body:
    fontFamily: "Barlow, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.3
rounded:
  sm: "4px"
  md: "6px"
  lg: "10px"
  pill: "999px"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "5": "20px"
  "6": "24px"
  "8": "32px"
  "12": "48px"
  "16": "64px"
components:
  button-primary:
    backgroundColor: "{colors.plate-blue}"
    textColor: "{colors.on-blue}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.plate-blue-hover}"
  button-default:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "44px"
  button-secondary:
    backgroundColor: "{colors.plate-blue-tint}"
    textColor: "{colors.plate-blue-ink}"
    rounded: "{rounded.md}"
  chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    height: "40px"
  chip-selected:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.chalk-ground}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    height: "44px"
  shell-bar:
    backgroundColor: "{colors.plate-blue}"
    textColor: "{colors.on-blue}"
    height: "60px"
---

# Design System: Cookbook

## Overview

**Creative North Star: "The Loaded Bar"**

A working kitchen-and-store tool dressed in competition bumper plates. Plate blue owns the shell (desktop top bar, phone tab bar, primary actions); red, yellow and green are the plates, and they only ever mean protein, carbs and fat. Numbers are set like plate lettering: heavy, condensed, tabular, readable from across a kitchen. The food photos carry the browse experience; the interface around them stays on a cool chalk ground with thin rules and no ornament.

It is an Operate product first. Every control is a standard web control (buttons, selects, chips, steppers, a `<dialog>` sheet); the world contributes only palette, type, density and one signature move, the loaded bar. Light and dark follow the system setting: light for the fluorescent store aisle and bright kitchen, rubber-graphite dark for evenings.

**Key Characteristics:**
- Plate-blue shell, chalk ground (light) or rubber graphite (dark).
- Macro colours are data, never decoration.
- Condensed uppercase for titles and section heads; Barlow for everything you read.
- Big targets: 44px minimum, 60px shopping rows, 72px cook-mode buttons.
- Flat surfaces with hairline rules; shadows only on things floating over photos or the page.

## Colors

A restrained neutral ground with one committed shell colour and three data colours.

### Primary
- **Plate Blue** (oklch(41% 0.165 265)): the shell (top bar, tab bar, add-mode bar), primary buttons, step numbers, the cook-mode progress, ticked checkboxes, the shopping meter. In dark mode the shell deepens (oklch(30% 0.11 265)) and buttons lift (oklch(48% 0.17 265)).
- **Plate Blue Ink** (oklch(43% 0.17 265); dark oklch(76% 0.12 265)): blue as text on the ground: links, focus rings, stepper glyphs, "Step 2" labels.

### Secondary (macro data)
- **Protein Red** (oklch(56% 0.205 27)) with **Protein Red Ink** (oklch(50% 0.19 27)) for numbers: the protein plate and every protein figure. Protein is the lead number on cards, recipe and plan.
- **Carbs Yellow** (oklch(84% 0.16 88)): the carbs plate. Never carries text.
- **Fat Green** (oklch(59% 0.14 152)): the fat plate.
- kcal is keyed in Plate Blue (round key) and set in ink.

### Neutral
- **Chalk Ground** (oklch(96.8% 0.006 255)): page background. Dark: **Rubber Graphite** (oklch(17.5% 0.012 262)).
- **Surface** (oklch(99.6% 0.002 255)): panels, inputs, list rows on desktop, entry cards.
- **Surface Raised** (oklch(93.6% 0.011 258)): tips box, recipe-note lines, skeletons, hover fill.
- **Ink / Ink Secondary / Ink Tertiary**: text, supporting text, captions and counts. Tertiary still clears 4.5:1 on the ground.
- **Rule / Rule Strong**: hairline dividers, control borders and the bar sleeve.

### Named Rules
**The Plates Mean Macros Rule.** Red, yellow and green appear only where they encode protein, carbs or fat (plus red on the favourite heart). State colours (danger, success) are separate tokens and never borrow the plates for decoration.

**The Blue Shell Rule.** The shell is always Plate Blue, on every screen except cook mode, which is full-screen on the ground so the step text owns the phone.

## Typography

**Display Font:** Barlow Condensed (600, 700; self-hosted via @fontsource)
**Body Font:** Barlow (400 to 700; self-hosted)

**Character:** Highway-sign clarity. Barlow Condensed is the plate lettering: titles, section heads (uppercase) and every figure. Barlow is the calm reading and UI face.

### Hierarchy
- **Display** (700, 2.25rem phone / 3rem desktop, 1.02, uppercase): recipe title, page titles (2.25rem).
- **Headline** (700, 1.75rem, uppercase): section heads (Ingredients, Method), empty-state titles, aisle names (1.375rem).
- **Title** (600, 1.125 to 1.25rem, sentence case): card titles, plan entry titles.
- **Figure** (700, 1.5 to 2.75rem, tabular): macro numbers, quantities, counts. Units sit at 0.6em in ink-secondary.
- **Body** (400, 1rem, 1.5): blurbs and steps (steps at 1.125rem, 68ch max); cook-mode step text 1.75rem phone / 2.5rem desktop.
- **Label** (600, 0.75 to 0.875rem): field labels, chip text, captions.

### Named Rules
**The Lettering Rule.** Any number a user decides with (protein, kcal, servings, grams, counts) is set in Barlow Condensed with tabular numerals. Running text never is.

## Layout

Phone first for shopping and cooking, desktop for planning. One breakpoint changes the shell at 900px: below it a fixed 64px bottom tab bar (Browse, Plan, Shopping, Add); above it a sticky 60px top bar with the wordmark, nav, "Import PDF" and "New recipe". Content max width 1360px, 16px gutter on phone, 32px on desktop. Spacing runs on a 4px base (4, 8, 12, 16, 20, 24, 32, 48, 64).

- Browse grid: 2 columns (phone), 3 (620px), 4 (1100px), 5 (1500px). Photos are 4:3.
- Recipe: phone stacks full-bleed photo, head, ingredients, method. Desktop puts photo (7fr) beside a sticky head (5fr), then ingredients (sticky, 5fr) beside method (7fr).
- Plan: entries list plus a 340px sticky totals panel on desktop; totals follow the entries on phone.
- Shopping: single 720px column; sticky progress meter; aisle headers in store order.
- Cook mode: full-screen grid (top bar, progress, step, two big buttons); content capped at 30 to 34ch.

## Elevation & Depth

Flat by default. Depth comes from the ground/surface step and hairline rules. Shadows appear only on things that float: buttons over photos (favourite, add, back), toasts and the ingredients sheet.

### Shadow Vocabulary
- **Float** (`0 1px 2px oklch(20% 0.03 265 / 0.08), 0 2px 6px oklch(20% 0.03 265 / 0.06)`): round buttons over photos.
- **Overlay** (`0 4px 12px oklch(20% 0.03 265 / 0.12), 0 12px 32px oklch(20% 0.03 265 / 0.12)`): toasts, the cook-mode sheet.

## Shapes

Gently squared: 6px on controls, 10px on photos, panels and large controls, pills for chips and floating card actions, circles for checkboxes, step numbers and photo buttons. Borders are 1px hairlines; aisle headers use a 2px ink underline as the shelf edge.

## Components

### Loaded Bar (signature)
The macro split by calories (protein ×4, carbs ×4, fat ×9) drawn as plate-coloured segments on a thin sleeve with a collar at each end, protein loaded first. 8px on cards, 14px on the recipe page and week totals. Always has an `aria-label` with the percentages. Use it wherever a recipe or set of recipes has macros; never as a progress bar.

### Buttons
- **Shape:** 6px radius, 44px tall (52px `lg`, 72px `xl` in cook mode).
- **Primary:** Plate Blue fill, on-blue text, 600 weight. One per view.
- **Default:** surface fill with Rule Strong border. **Secondary:** blue tint with blue-ink text (Add to plan). **Ghost:** transparent until hover. **On-shell:** on-blue fill with blue text inside the blue bar. **Danger:** outlined red, needs a second tap to confirm.
- **States:** hover darkens or fills surface-raised; active nudges down 1px; disabled at 50%; focus is a 2.5px blue-ink ring.

### Chips
Pills, 40px tall, uppercase-free capitalised tag names with a condensed count. Selected = ink fill with ground text. Favourites selected = protein red. On phone the chip row scrolls horizontally and holds the book and sort selects; on desktop it wraps.

### Cards / Containers
Recipe card: photo (4:3, 10px radius), two-line condensed title, protein figure (red, left) and kcal (right), loaded bar. No card box: the photo is the container. Panels (plan totals, forms, plan entries, shopping extras) are surface with a 1px rule and 10px radius, never nested.

### Inputs / Fields
Surface fill, 1px Rule Strong border, 6px radius (search and selects 10px, 48px tall). Focus swaps the border to blue ink plus the focus ring. Labels sit above in 600 label type; "optional" in tertiary.

### Steppers
Bordered group: minus, condensed value with a small unit word, plus. 44px targets; used for servings everywhere.

### Checklists
Shopping rows and cook-mode ingredients are whole-row buttons with `role="checkbox"`: a 26 to 28px circle that fills Plate Blue with a white tick. Checked shopping rows dim to 50%, strike through and sink to the bottom of their aisle.

### Navigation
Desktop: top bar links in on-blue-muted, active link white with a 3px white underline. Phone: tab bar icons (24px, 1.8 stroke) with labels; active tab white with a 3px top tab.

## Do's and Don'ts

### Do:
- **Do** put protein first and in Protein Red Ink wherever macros are summarised.
- **Do** keep every tap target at least 44px; shopping rows at least 60px.
- **Do** use the authored icon set in `web/src/components/Icon.tsx` (24px grid, 1.8 stroke, round caps).
- **Do** let recipe photos run edge to edge on phone and keep text off them.
- **Do** respect `prefers-reduced-motion` (all durations drop to 0) and both colour schemes via the tokens in `web/src/styles/tokens.css`.

### Don't:
- **Don't** use red, yellow or green for anything other than protein, carbs and fat (and the favourite heart).
- **Don't** put macro numbers in the body face or proportional numerals.
- **Don't** add drop shadows to flat panels or cards; depth is tonal.
- **Don't** load fonts or scripts from a CDN; the app runs offline on the tailnet.
