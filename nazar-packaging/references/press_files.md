# Press files: one master, two branches

## The pipeline
Each pack has **one master SVG** (in mm, named layers). Everything else is built from it by code:

```
tokens (name, tints, copy) -> art engine (outlined type, layers) -> MASTER SVG
                                                                  |-> press branch:   press_pdf.py -> <name>_PRINT.pdf
                                                                  '-> picture branch: renderer (e.g. nazar-dieline/engine/film.py) -> mockups -> deck, case study, film
```

- **Print file and mockup are siblings, not parent and child.** Never rebuild a mockup by hand from the PDF: both read the same master, so they cannot drift.
- **When the converter changes the dieline,** update the master once and rerun. Both branches rebuild.
- **One QA script rebuilds every line and re-checks it** after any change: change one, rebuild all, check all.

## What a concept press PDF holds (`engine/press_pdf.py`)
| Page | Content |
|---|---|
| 1 | The composite: ink plates only, never notes or dielines |
| 2..n | One page per ink plate, drawn in black (a separation preview): tint, white underlay, dark ink, varnish |
| last | The technical layers (cut, crease, glue, dieline) in magenta, labelled "never prints" |

- **Boxes:**
  - BleedBox is the art including bleed;
  - TrimBox is the art minus bleed;
  - MediaBox adds a slug strip carrying the file, plate, trim and bleed.
- **Layer ids** are matched by name; keep them consistent across every engine.
- **Notes and placeholders** go in their own layers, which never print.

## Rules that held up
1. **The SVG `width`/`height` in mm must equal the viewBox span.** If the viewBox includes bleed (`-3 -3 W+6 H+6`), the width must be `W+6` mm. Otherwise every export silently scales (about 96% on a 140 mm pouch), and preview PNGs get letterboxed. The press script flags any mismatch.
2. **Every panel gets 3 mm bleed, flexible packs too.** Panels without bleed get their background extended at export. Any photo touching a trim edge must be extended by hand; the report says which files.
3. **CMYK from RGB is a screen estimate only.** The final CMYK comes from the printer's profile. Spot colours are picked on a physical guide under D50 light, against the approved digital swatch. Leave the spot column empty until then.
4. **Ask the printer before final files:**
   - process;
   - film and laminate;
   - profile and total ink limit;
   - stations and white;
   - minimum positive and reverse type;
   - trap;
   - bleed conventions;
   - PDF/X version and their preflight profile;
   - a proof on the real substrate.
5. **Split the readiness report.**
   - "Blocked on others": profile, CAD dieline, barcodes and lab values, the proof.
   - "Our fixes": bleed, missing plates, raster resolution, scale.
   The report is regenerated on every QA run.
6. **A sent version is frozen.** Never re-render into a version the client already has; new work publishes as the next version.
7. **The client never sees mm, bleed or plates.** Mockups show the pack after trimming. Press files are for the printer and converter only.
