# Flexibles and labels

## Stand-up pouches and sachets
**Anatomy:** front and back panels, bottom gusset (a W-fold that becomes the base), side and top seals, zipper or slider, tear notch, optional hang hole, window, valve (coffee), spout. Formats: stand-up (Doyen or K-seal bottom), flat-bottom (box pouch, with side gussets), side-gusset, three-side seal sachet, pillow (flow wrap), stick pack.

**Layout (engine `pouch`):** on the printed web, the front panel reads upright; the back is commonly rotated 180° beyond the gusset [SRC]. Front panel height ≈ total height minus the top seal and zipper headspace minus the gusset [SRC]. **Treat every number as a placeholder until the converter's template arrives.**

| Item | Starting value | Notes |
|---|---|---|
| Side seals | ≈ 6–12 mm | Seals print but distort; keep barcodes out [SRC] |
| Top seal | ≈ 8–12 mm | Above the zipper |
| Zipper band | ≈ 10 mm, ≈ 20–35 mm from the top | Nothing important on it |
| Tear notch | On the side seal, between the top seal and the zipper | |
| Gusset | Often 30–60% of the width [SRC] | The base is visible on shelf: design it |
| Clear zone near seals | ≈ 6 mm (¼") for type and logos [SRC] | |
| Eye mark | A solid block (for example 6 × 12 mm) in a contrasting colour, in a non-image area | The filling machine reads it to cut and register. The converter specifies the size and position |

**Web and unwind direction:** the converter and the filler choose the unwind (rewind) position, which sets which way the art runs on the reel. Always get it from their spec; never guess.

**Materials change the art:** clear film is reverse-printed with a white underlay where colour must be opaque; metallised film shimmers wherever white is left out; kraft-paper laminates darken colours. See `../nazar-packaging/references/structure.md`.

**Structural ideas:** a window shaped by the brand, a gusset base as a second face, a pouch that stands as a display, a reclosable feature that is the brand's gesture.

## Flow-wrap and VFFS pillow bags (chips packets): engine `flowwrap`
- The film is formed around the product with a **fin seal** down the back and **crimped end seals** top and bottom, cut with a serrated knife [SRC].
- Web layout: fin | back half | (gusset) | front | (gusset) | back half | fin. **The back art is split across both edges**; the engine renders one "Back" design into both halves and flags type under the folded fin.
- Seal areas take colour but not small type or barcodes; print drifts up to ~4 mm against folds and seals [SRC]. The eye mark goes in a non-image area per the converter.
- **Snacks with fats need a light barrier:** metallised film plus nitrogen flush is the standard answer for chips; a clear window shortens shelf life [SRC]. See `design_on_dieline.md` §4.
- Print orientation (parallel to the fin or the end seals), cut-off (repeat) length, unwind direction and registration come from the wrapper and the converter.

## Labels
### Wrap-around (cylindrical): engine `wrap_label`
Width = π × diameter × coverage + overlap (full wraps often 5–10 mm overlap). Measure the diameter where the label sits, on a production sample. Leave a label-free gap if the container has a seam, and keep the overlap free of barcodes. On tight curves, run the barcode **picket-fence** (bars vertical) so it scans around the curve.

### Tapered (cone, frustum): engine `cone_label`
A tapered container's side unrolls into an annular sector, so a rectangle printed flat will slant [SRC].
- slant s = √(h² + ((D − d)/2)²)
- outer radius R1 = s × D / (D − d), inner radius R2 = R1 − s
- full sector angle = 180° × D / R1 (in degrees); multiply by the coverage you need [SRC]
- If D = d it's a cylinder: use the wrap label.
On the sector, **verticals become radial lines and horizontals become arcs**: set type on arcs and line up uprights with the radial guides. Generators are exact only for true cones; necks and irregular tapers need a test print [SRC].

### Label production notes
- Die-cut corner radius, matrix waste, label gap, core size and **wind direction** (which way the label comes off the roll for the applicator: wind positions 1–8) come from the label printer and the applicator.
- Clear-on-clear ("no-label look") needs a white underlay where colour must read.
- Embellishments (foil, emboss, tactile varnish) need their own spot layers.

## Shrink sleeves: engine `sleeve_grid`
A full-body sleeve shrinks around the container: little at the full diameter and a lot at the neck. Art at a narrow section shrinks horizontally, so it must be **pre-distorted** (stretched) to land right.
- Films: PETG shrinks most (up to ≈ 75–78% TD), PVC ≈ 60%, OPS and others less [SRC]. The film supplier's TD/MD shrink curve is the authority.
- Lay-flat width ≈ half the circumference at the widest point, plus ease (a few %).
- **Engine:** give a profile of (height, diameter) pairs. It reports horizontal shrink by height and the pre-stretch factor, shades bands above 30% shrink, and draws ellipses that show how a circle must be stretched to come out round.
- Rules: no barcodes, small type or faces in high-shrink zones; keep the barcode in the flattest, least-shrink band; avoid fine horizontal lines where shrink changes fast.
- The professional route is 3D shrink simulation in prepress software plus a **printed grid shrunk on the real container**, often several rounds [SRC]. Our map is the first pass that keeps the layout honest before that.
- Perforated tear strips for tamper evidence and recycling (the sleeve should come off so the bottle can be recycled).
