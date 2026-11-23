# Lessons (nazar-dieline)

## 2026-11-20 · Windows run
- **What failed:** `dieline.py` crashed on Windows twice. (1) `print("✓ ...")` raised UnicodeEncodeError on the cp1252 console. (2) `art.py` `write_qa` calls `open(path, "w")` with no encoding, and the "≥" in the QA text crashed it. Spec files also came out garbled (× and ² as `?`).
- **Workaround used:** run with `PYTHONUTF8=1`.
- **Patched 2026-11-20 (owner okayed):** add `encoding="utf-8"` to every `open(..., "w")` in `dieline.py` and `art.py`, and `sys.stdout.reconfigure(encoding="utf-8")` at startup.
- **Also:** CairoSVG needs `libcairo-2.dll` on Windows. `requirements.txt` doesn't say so, and selftest doesn't test the dieline engine. Any GTK runtime works, and so does the Tesseract-OCR install folder (it ships libcairo-2.dll) on PATH. Proposed: add a dieline render to `selftest.py` and a Windows note to the README.
- **QA gap:** a placeholder zone overlapping a pouch's rounded corner seal was not flagged (seen only by eye). Proposed: include the corner-seal arcs in `check_box` zones.

## 2026-11-20: flat-bottom pouch and display header added
- **Added `box_pouch`** (flat-bottom box pouch print layout: front | gusset | back | gusset + separate bottom, edge seals, zip, base fold-unders). It was needed for a kitchen range; it's drawn as one strip for planning, and the converter's template sets the real web split.
- **`tray` now draws `header`** (mm): the note had mentioned the option but it wasn't implemented.
- **QA gap confirmed again:** pouch rounded corner seals are not checked. On a small doypack (110 wide) a batch box at the back's bottom-right sat on the arc with no flag. Proposed: add the corner arcs to the zone check in `art.py`.

## 2026-11-20: frosted film renders (`engine/film.py`)
- **What happened:** a client's frosted tinted pouches had to be shown before samples existed. Image models couldn't render see-through frosted film or keep the label; drawn product through the film looked like clip-art.
- **What worked:** code for the film (contact clarity, veil, tint, double film, opaque ink, volume), a real product-texture photo as the pile inside, AI only for empty plates and textures, composited with matched light. Labelled "AI concept render", internal until the client OKed it in writing.
- **Feedback that changed the layout:** the single upright dead-centre pouch read as a mockup; top-down flat lays at varied angles, overlapping, cropped by the frame, won. Shadows had to be dense, not a pale ghost.
- **Added:** `engine/film.py` (generic, brand-free, `--demo` runs standalone) and `references/frosted_film_render.md`.

## 2026-11-20: opaque chips bags (pillow / flow-wrap) that look real
- **What failed:** (1) code-only pillow shading looked like smooth plastic ("creaseless, slop"); (2) a height-map crinkle model first did nothing because `film.blur` clips to 0..1 (use a float blur for height maps), then looked glossy and noodle-like; (3) using a blank-bag photo's own silhouette cut the artwork where the bag's shadowed edge matched the backdrop grey (white jagged "torn" sides), and its blown highlights hid white type.
- **What worked:** take only the **crease shading** from a photo of a blank white matte bag (inset past its curled edges), multiply/screen it over the flat art (highlight screen capped ~0.2 so white ink stays legible), wobble the print along the crease gradient with **bilinear** sampling (nearest = jagged type), and draw our **own silhouette** (crimped serrated ends, side pinch, edge roll-off).
- **Layout:** keep type ≥10 mm in from the sides of a pillow bag (it curves away). Same family layout as the pouch line.
- **Hero photo:** shot on paper in the exact bag colour and feathered into the flood, so there's no cut-out halo.
- **Proposed:** move `bag_from_blank` into `engine/film.py` as a generic `mockup_from_blank(art, blank_photo, silhouette)`.

## 2026-11-20: frosted stand-up pouch, the details that read "real" vs "AI"
- **Crinkles on frosted film:** same trick as chips, but take a **high-pass** of the blank pouch photo (luminance ÷ its own heavy blur), so only the creases come over and our own volume/light model stays in charge. Cap highlights so white ink reads.
- **The window is what makes Azbuka look real:** a clearer rounded window (r≈9 mm, 3 mm in from the side seals, 4 mm under the zip band, 4 mm above the gusset) inside a milkier matte frame, with a thin lit line on the window's top edge. On press this is a **spot matte varnish plate**: add it to the print file, or the render promises something the print can't do.
- **Empty headspace under the zip reads lighter** (air behind frosted film). Only at the top: the bottom is never empty.
- **The bottom read as AI** when the product faded into a fog above the gusset. Real: product presses the film right down into the gusset (sharp contact), the gusset seal curve is a **crisp** line (dark ply edge + lit roll just below), the gusset is only slightly milkier, and **tension wrinkles** fan up from each bottom corner seal at 30–60°.
- **Rule:** any soft gradient fade where a physical edge should be (product end, seal, window) reads as generated. Physical things end in edges.
- **Corrected after the owner zoomed into the reference (approved look):** the product does NOT stop at the gusset seal; it fills right down. Below the seal curve the film is the same clear film, just **extra frosted** where the inner gusset plies overlap (product seen softer, milkier, still visible). Add the **heat-seal knurl** (fine ~0.85 mm diamond texture) on that band and the small **light-grey corner punch squares** at the side edges where the gusset starts. The seal curve is a flat-bottomed U (sides ~0.82 H, centre ~0.88 H).
- **Rejected:** switching to a "printed colour frame + neutral clear window" (fruit in natural colour). On paper it matched one reference, but it killed the colour family the owner liked. Don't change the base film look while fixing a detail: fix only the region flagged.
- **Method:** before modelling any region, crop that region from 3+ reference photos at 2–3× zoom and list what is physically there (edges, plies, textures, punches). Model only that list.

## 2026-11-20: claims pills, origin cue, unorthodox scenes
- **Pills:** one exact right edge, stacked nearly touching (~0.35 mm) so they read as one cluster; last (secondary) claim outlined, not filled; regular-weight dark type. A deliberate stagger (alternate offsets) read as an error ("why zigzag").
- **White ink must stay bright in renders:** it sits on the outer surface, so re-lift it after film shading/creases (and never paint it over the dark type printed on top of it).
- **Frost strength:** Azbuka's window is clearer than a uniform haze (deep gaps where product presses the film), but going all the way lost realism; the owner picked the halfway setting. Make big look changes in halves and show both.
- **Origin cue in the top band** (from the Ararre reference): crescent-star + "MADE IN PAKISTAN", drawn as paths so it is one-colour safe.
- **Scenes that beat the "AI lineup":** a real local practice as the set (pouches pegged on a washing line next to apricots sun-drying; charpai rooftop). Re-layer the plate's pegs/rope over the pack tops; match the plate's own shadow throw and slant (copy it from an existing object's shadow in the plate); leave one peg empty and hang one pack by a corner for a human touch.

## 2026-11-21: press files 4% small (SVG width vs viewBox)
- **What happened:** pouch masters had `viewBox="-3 -3 W+6 H+6"` (bleed included) but `width="W mm"`. Every PDF export shrank to about 96%, and preview PNGs were letterboxed with black strips. Nobody saw it on screen.
- **Fix:** the width and height in mm must equal the viewBox span. `nazar-packaging/engine/press_pdf.py` now flags any mismatch and gives panels without bleed 3 mm at export. Guide: `nazar-packaging/references/press_files.md`.

## 2026-11-21: doypack base, in then out
- The gusset folds IN then back OUT (a W when empty); filled, weight opens it into a floor. `engine/base_fold.py` draws it from the real print art. See `references/flexibles_labels.md`.
- 2026-11-23 · A spec job needed a flip-top pack and the engine had none · styles.md said 'ask the converter', but portfolio and speculative jobs have no converter, so the pack had no structure to sit on. · `hinge_lid` concept style (wrap blank, glued ends, lid cut + diagonal sides to a back hinge, separate inner frame), example job `hinge_lid_carton`, docs updated; still stamped CONCEPT.
