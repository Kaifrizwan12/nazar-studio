# engine/: the Kaif brand book renderer

A small Python renderer: SVG pages → PNG per page + bound PDF + contact sheet. Type is shaped with harfbuzz and outlined (so RTL scripts like Arabic and Urdu works and the PDF looks identical everywhere). Logos are placed from the client's exact SVG files, never redrawn.

## Set up (once per machine)
```
./setup.sh            # makes .venv (needs Python 3.9+ and Cairo: brew install cairo)
.venv/bin/python build.py && .venv/bin/python build.py     # twice: contents pick up real page numbers
```
Output goes to `exports/` (as set in brand.json): `pages/NN_<pid>.png`, `<Brand>_Brand_Book_<year>.pdf`, `sheet.png`.
Rebuild a few pages: `.venv/bin/python build.py 02 03.1` (page-id prefixes).

## Per brand
1. Copy this folder into the brand repo as `engine/`.
2. Edit `brand.json`: name, colours (base / light / secondary / secondary_dark / accent, plus names, meanings and shares), fonts by role, logo SVG paths (`mark`, `lockup`, and an optional `device` for the hidden device), sections, page modules, reveal page id.
3. Put the client's logo SVGs somewhere in the repo and point to them. **Crop each viewBox tight to the visible mark**, so centring is optical.
4. Write pages in `pages_a.py`, `pages_b.py` …, using `pages_example.py` as the pattern. Each page is a function returning a `Page`. Add the module names to `page_modules`.
5. Maps: `./fetch_map.sh <name> <lat> <lon>`, then `map_paths("<name>", Proj(lat, lon))`.

## The API in one screen (lib.py)
| | |
|---|---|
| `Page(pid, title, section_label, DARK/LIGHT, stamp=None)` | `.add(svg…)`, `.defs_(…)`, `.heading(kicker, title, sub)` (standard positions), `.device(x, y, size)`, `.grain = True`, `.furniture = False` |
| `text(s, x, y, size, role, fill, op, track, anchor)` | outlined text, baseline at y |
| `para(s, x, y, size, maxw, role, fill)` → `(svg, bottom)` | wrapped paragraph |
| `width / bounds / missing(role, s)` | measuring, and a missing-glyph check (QA) |
| `logo(name, x, y, w)`, `logo_centered(name, cx, cy, w)` | exact artwork |
| `hair, rect, circle, leader, dimension` | primitives; leaders and dimension lines for spec sheets |
| `halftone_defs, grain_uri` | textures |
| `Proj, map_paths, fmt_ll` | OSM maps; keep coordinates rounded near homes |
| `contrast(a, b)` | WCAG ratio, used on the pairings page |
| `col_x(n)`, `M`, `W`, `H` | grid: 12 columns, 24 px gutter, margin 120 |
| `page_numbers()` | `{pid: n}` from the last build, for contents and "see page N" |

## Known cairosvg quirks
- It drops paths under some chained transforms. If a shape vanishes, collapse its transforms into one `matrix()`.
- It ignores blur filters. Fake glows with radial gradients.
- Space Mono lacks ː ɪ ʒ. Check with `missing("label", s)`.
