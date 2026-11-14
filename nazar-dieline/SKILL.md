---
name: nazar-dieline
description: Nazar Studio's dieline and structural packaging kit. Use for any dieline or pack structure, and for designing MVP artwork drafts on a dieline (logo, label, brand block, copy, barcode, windows placed panel by panel and checked automatically): choosing a box style (ECMA folding-carton and FEFCO corrugated codes), drawing concept dielines from inside dimensions (tuck ends, sleeves, trays, slotted cases, mailers, pillow packs, rigid set-up boxes, cone and wrap labels, stand-up pouches, chips/snack flow-wrap packets, shrink-sleeve maps), transparent and partly transparent packs (clear and metallised film, windows, white-ink plates, carton window patches), board and flute choice, caliper allowances, grain, creases, locks, tolerances, die-making basics, layer and file conventions (CUT/CREASE/PERF, DXF, CF2, ArtiosCAD), artwork-on-dieline rules, flexibles and labels, rigid and luxury boxes, shelf-ready and display units, e-commerce and transit testing, tamper-evident, child-resistant and braille, and structural ideation from folding-craft archives. Works with nazar-packaging (branding, shelf, print production).
---

# Nazar dieline

Read `../nazar-core/SKILL.md` and `../nazar-core/references/kaif.md` first. For the brand side of a pack (shelf, range, front-of-pack, print production) use `../nazar-packaging/`. This kit owns the **structure**: the flat shape that becomes the object.

A dieline is the one drawing everyone builds from: the die-maker cuts steel rule to it, the printer imposes artwork on it, the gluer folds it, the filler runs it, and the shopper opens it. If it's 1 mm wrong, it's wrong for all of them. So this kit is fussy on purpose.

## Rules
1. **Product first, box second.** Measure the real product (three samples, largest wins) and add clearance before drawing anything. Never design to a spec-sheet size.
2. **Inside dimensions, L × W × D.** ECMA convention: L and W are the opening (L the longer), D the depth. Say "inside" or "outside" every time a number is written down.
3. **The converter's dieline goes to press.** Ours are concepts and briefs. The converter redraws for their board, their machine and their die standards, and their CAD file is the master (`references/layers.md`).
4. **Name the style by its code.** "ECMA A20.20-type reverse tuck" or "FEFCO 0427" gets you a quote; "a normal box" gets you a guess (`references/styles.md`).
5. **Caliper changes everything.** Every fold eats board thickness. Allowances, clearances and grain are engineering, not taste (`references/engineering.md`).
6. **White sample before artwork.** Cut and fold an unprinted sample on the real board, fill it with the real product and drop it, before a single colour goes on.
7. **Structure carries the idea too.** The opening, the reveal, the reuse, the shape on shelf: the strongest brand assets can be structural. Ideate structure with the same rigour as graphics (`references/ideation.md`), from archives, not from the trending feed.
8. **Honest structure.** No oversized boxes to look premium, no false bottoms that mislead on quantity, no claims (recyclable, child-resistant, compostable) that the actual structure and test reports don't back.
9. **Images stay private.** Reference photos of other people's packs go in the client's `research/` folder for study, never into deliverables or public repos (`references/inspiration.md`).

## Workflow
| Phase | Do | Output |
|---|---|---|
| 1 | Intake (`references/intake.md`): product, channel, line, converter, budget, sustainability | `SPEC.md` → "Structure" |
| 2 | Measure the product; set clearance; list what the pack must survive | product sheet |
| 3 | Research: category structures, archive and craft forms, the competitor shelf in 3D (`references/ideation.md`, `references/inspiration.md`) | `research/structure/` |
| 4 | Ideate structure: 3 routes (one standard-code, one modified, one unorthodox), each with the reason | route sheet |
| 5 | Concept dielines with the engine (below); check fit, nesting, board area | `exports/dielines/` |
| 6 | Paper and white samples; test fit, fill, open, close, drop, stack | test notes |
| 7 | Brief the converter with the structure spec (`templates/STRUCTURE_SPEC.md`); get their CAD dieline and white sample | converter dieline |
| 8 | MVP drafts on the concept dieline (`references/design_on_dieline.md`), then final artwork on the converter's dieline (`references/layers.md`) → hand to `nazar-packaging` production | drafts → print-ready files |
| 9 | QA (`references/qa.md`), sign-off, archive the approved dieline with its version | handover |

## Engine
`engine/dieline.py` draws parametric concept dielines: SVG with named layers, PDF, PNG, DXF (CUT / CREASE / PERF / GLUE) and a spec sheet with flat size, board area, rule lengths, rough nesting and, for corrugated, a McKee compression estimate.
```bash
python engine/dieline.py templates/dieline.json                   # all 12 examples + contact sheet
python engine/dieline.py --style rte --L 60 --W 30 --D 120 --caliper 0.45
```
Styles: `rte` `ste` `sleeve` `tray` `rsc` `hsc` `mailer` `pillow` `rigid` `cone_label` `wrap_label` `pouch` `flowwrap` `sleeve_grid`. Every drawing is stamped CONCEPT. The allowances are documented starting rules, not a standard.

**Design mode (MVP drafts).** Add an `"art"` block to a job and the engine places your design on the dieline: brand tokens and outlined fonts from `../nazar-core/engine/brand.json`, the client's exact logo file, text, bands, patterns that run across folds, copy and barcode placeholders, and windows. Every panel reads the right way up when folded. It writes `<name>_art.png/.pdf/.svg`, a folded oblique view `<name>_box.png`, a white-ink plate `<name>_white.png` for clear and metallised film, and `<name>_art_qa.md` with automatic checks (type size, real contrast, safe areas, overflow, barcode size, net-quantity position, glue, windows near creases or seals, light-sensitive products). Five worked examples are in `templates/dieline.json`. Full guide: `references/design_on_dieline.md`.

Needs CairoSVG and Pillow; uses the core engine's harfbuzz type when installed (`../nazar-core/engine/requirements.txt`), and falls back to system fonts otherwise. **To add a structure, block or check for your own product, follow `EXTENDING.md`.**

## Files
- `references/intake.md`: the questions, with options and a recommended pick
- `references/design_on_dieline.md`: designing on the structure: panel jobs, art across folds and seals, shelf blocking, transparency and windows, chips packets, MVP drafts with the engine
- `references/styles.md`: ECMA and FEFCO families, which style for which job, what the engine covers
- `references/engineering.md`: board and flute, caliper allowances, grain, creases, clearances, locks, tolerances, die-making, nesting, compression
- `references/layers.md`: layer and colour conventions, file formats, artwork-on-dieline rules, naming, handoff
- `references/flexibles_labels.md`: pouches, sachets, flow-wrap packets, wrap and cone labels, shrink sleeves
- `references/rigid.md`: set-up boxes, wraps, turn-ins, closures, inserts, unboxing
- `references/display_shipping.md`: shelf-ready packs, counter and floor displays, mailers, e-commerce, transit testing
- `references/special.md`: tamper evidence, child resistance, braille, food contact, sustainability claims
- `references/ideation.md`: structural ideation methods and the folding-craft archive
- `references/inspiration.md`: where to find the best structural references, and how to collect them
- `references/qa.md`: dieline QA, plus test protocols
- `references/sources.md`: every source, by topic
- `templates/dieline.json`: engine examples (structures + 5 MVP drafts); `templates/STRUCTURE_SPEC.md`: the converter brief; `templates/sample_mark.svg`: a neutral stand-in mark
- `EXTENDING.md`: how any user's Claude adds structures, art blocks and checks for their own product
