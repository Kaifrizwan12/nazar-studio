# Extending the dieline engine (for any user's Claude)

This kit is open source. If your product needs a structure, block or check the engine doesn't have, **ask Claude to extend it using this file.** For example: "Read nazar-dieline/EXTENDING.md and add a hexagonal gift box", or "add a check for our retailer's 8 mm barcode margin".

Claude: follow these steps in order. Don't skip the visual check.

## 0. Before writing code
1. Read `SKILL.md`, `references/styles.md` and the parts of `engine/dieline.py` and `engine/art.py` you'll touch.
2. Ask the user what the engine can't know: the product's real dimensions, board or film, converter, machine, and any retailer or legal rule. Ask for the converter's dieline if one exists. **Match it rather than inventing geometry.**
3. Check whether the structure has an ECMA or FEFCO code (`styles.md`). Name the new style after the code family where possible (`ecma_a20_snaplock`, `fefco_0203`).
4. If the structure is complex (snap-lock and crash-lock bottoms, Beers trays, displays), say so: the engine draws **concepts**. It's better to draw a simplified, clearly labelled concept and send the converter the code than to fake precision.

## 1. Adding a structure (a new style)
Styles live in `engine/dieline.py` as functions `s_<name>(d, p)`, registered in `STYLES` and `TITLES`.
- **The model:** a `Piece` is a body rectangle; flaps are `Prof` profiles attached to its edges (`top`, `right`, `bottom`, `left`). In a profile, `u` runs along the edge (clockwise), `v` points outward, and the edge segment is `[a, b]`. The outline is traced automatically from the body plus all profiles, so you get a single closed cut contour, free.
- Reuse the profiles that exist: `p_flap`, `p_dust`, `p_tuck`, `p_glue`. Write new ones in the same style (return a `Prof` with `pts`, `crease()`, `glue`, `holes`, `panel(name, poly, safe, up)`).
- **Leave relief gaps** (`c ≈ caliper`, min 0.8 mm) where two flaps meet at a corner, or the outline will touch itself.
- **Panels need an art-up vector** (`up` in uv): walls that fold up from a base use `(0, 1)`; lids and closures that read toward their hinge use `(0, -1)`. Body panels default to "up = top of the flat". Wrong `up` = upside-down art on the folded pack, so verify on the folded view.
- Non-box layouts (labels, flexibles) can write directly to `d.outlines`, `d.lines`, `d.zones`, `d.panels`, as `s_pouch`, `s_flowwrap` and `s_cone_label` do.
- Put the assumptions in `d.notes`, the key numbers in `d.facts`, and the risks in `d.warn`. Every allowance you choose must be written down (and added to `references/engineering.md` if it's new).
- If the style has a natural folded view, add it to `BOXVIEW` in `engine/art.py` as `(front, right side, top)` panel names.

## 2. Adding an art block or an art check
Blocks are `PanelArt.b_<type>(self, b)` methods in `engine/art.py`. They draw in the panel's upright frame: `self.X(f)` and `self.Y(f)` turn safe-box fractions into mm.
- Register any filled area in `self.fills` so the contrast checks know what's behind text.
- Checks call `self.flag(level, msg)`. **P1** = wrong or unprintable (fix before showing), **P2** = fix before the converter, **P3** = a note. Messages say what's wrong, the number, and the fix.
- Product-specific rules (a retailer's barcode position, a market's minimum type size, a brand's minimum logo size) go in as checks driven by keys in the job's `"art"` block, so other users can switch them off.

## 3. Test protocol (every change)
1. Add an example job to `templates/dieline.json` with **generic** content (no client names; this repo is public).
2. Run `python engine/dieline.py templates/dieline.json` and read the warnings.
3. **Look at the PNGs.** Open `<name>.png`, `<name>_art.png` and `<name>_box.png`. Check that the outline is one clean contour, creases sit where folds are, flaps don't collide, art reads the right way on every panel, and the folded view assembles.
4. Validate the DXF opens (for example with `ezdxf`: zero audit errors, layers CUT / CREASE / PERF / GLUE).
5. Run a deliberately bad design through any new check, to prove it fires. Run a good one, to prove it stays quiet.
6. Print the PDF at 100% and fold it. Paper doesn't lie.

## 4. House rules (don't break these)
- Concept dielines stay stamped CONCEPT. The converter's CAD is the master.
- No AI-generated imagery, no fake product photos, no logo redraws: placeholders and the client's exact files only.
- No dependencies beyond the core engine's `requirements.txt` unless the user agrees. The engine must still run (with system fonts) when `nazar-core` isn't present.
- Keep examples generic and cross-industry. Client work lives in the client's repo, not here.
- Update `SKILL.md` (styles list), `references/styles.md` (the engine table) and this file if you change the model.

## 5. Ideas the engine doesn't do yet (good first extensions)
Snap-lock and crash-lock bottoms · hinged-lid (flip-top) cartons · Beers / Brightwood trays · counter displays with headers · partitions · hexagonal and octagonal cartons · gable-top and sleeve-with-tray combinations · shrink-sleeve artwork pre-distortion from a full profile · interlocked nesting · CF2 export · spot-colour (separations) PDF export.
