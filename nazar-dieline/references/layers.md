# Layers, files and artwork on the dieline

## Line conventions (ours; follow the converter's if they differ)
| Layer / spot name | Line | Engine colour | Meaning |
|---|---|---|---|
| `CUT` | solid | magenta | Cut through, including windows, slots, notches |
| `CREASE` | dashed | cyan | Fold; mark reverse creases separately as `CREASE_REV` |
| `PERF` | short dash | orange | Perforation or tear line; note cut/tie |
| `GLUE` | hatched area | grey | Glue lands here: no ink, no varnish, no laminate |
| `BLEED` | band outside cut | pink tint | Artwork extends this far (usually 3 mm; ask) |
| `SAFE` | dotted | green | Keep type and logos inside |
| `ZONES` | hatched | grey | Seals, zipper bands, overlaps, variable-data areas |
| `GUIDE` / `DIM` / `LABELS` | thin | violet / grey | Non-printing notes |

In the artwork file, the dieline sits on its own **top layer** in a uniquely named spot colour (for example `DIELINE` or `CUT` / `CREASE`), set as the converter wants (often overprint, sometimes non-printing). It must never print, and it must never be outlined into the artwork. Finishes get their own spot layers (`SPOT_UV`, `FOIL`, `EMBOSS`, `WHITE`), see `../nazar-packaging/references/production.md`.

## File formats
| Format | Who uses it | Notes |
|---|---|---|
| **DXF** | Everyone; the neutral exchange | The engine writes R12 with CUT / CREASE / PERF / GLUE layers, in mm |
| **CF2 / CFF2** | Die-makers, sample tables | Common die-cutting format; ArtiosCAD and others import and export it [SRC] |
| **DDES** | Older die/CAD systems | Supported by ArtiosCAD alongside CFF2, DXF, DWG [SRC] |
| **ARD / MFG** | Esko ArtiosCAD | The converter's native file; ask for a PDF or DXF export |
| **PDF (layered)** | Designers, printers | Artwork template: dieline on its own layer |
| **SVG** | Our concepts | The engine's master view; layer groups import into Illustrator and Inkscape |

Ask the converter for: the dieline as **PDF + DXF (or CF2)**, the board and caliper it was drawn for, the print side, the grain, bleed, and their safe-area rule.

## Artwork on the dieline
1. **Only on the converter's dieline**, at 100%, never rescaled. If anything changes structurally, get a new version number from them.
2. **Know the print side.** Corrugated FEFCO drawings are shown from the inside, while printed layouts are shown from the print side. Confirm which you were sent.
3. **Panel orientation:** mark "art up" on every panel. Tuck flaps and bottom panels are often upside down relative to the front, and lids read from the front edge. Fold a paper sample with arrows drawn on it before laying out type.
4. **Bleed past every cut,** usually 3 mm, more for corrugated and rigid wraps. Backgrounds run across creases.
5. **Safe area:** type and logos 3–5 mm inside cuts and folds; more on corrugated and on curved creases.
6. **Glue areas:** knock out ink and varnish where the glue lands (the converter gives the exact area). Laminate also blocks adhesion [SRC].
7. **Across-fold elements** (a line that wraps a corner, a shape split over two panels) need generous tolerance: aim for designs that still look right at ±1 mm.
8. **Barcodes:** on a flat panel, away from folds, curves and seals, with quiet zones clear. Bar orientation follows the print direction on flexo (bars parallel to web travel) where the printer asks for it.
9. **Inside print:** it costs a second pass (or two-sided web). Decide early, since it changes the price.
10. **Mandatory panels:** size and place them on the real dieline early, because legal text is the thing that never fits.

## Naming and versions
`<brand>_<sku>_<style>_<LxWxD>_<board>_v<NN>_<status>.<ext>`
Status: `CONCEPT` (ours), `CONV` (the converter's), `APPROVED` (signed white sample). Example: `brand_sku01_rte_60x30x120_FBB045_v03_CONV.pdf`. Keep the approved dieline with the signed sample's photo in `assets/dielines/`.

## Handoff to production
- The converter's approved dieline (PDF + DXF/CF2), version-locked
- The structure spec (`templates/STRUCTURE_SPEC.md`), filled in
- White sample sign-off: photos plus who signed it and when
- The artwork template built on that dieline, layers named, for `nazar-packaging` production
