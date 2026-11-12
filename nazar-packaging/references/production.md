# Print production

## 0. Ask the printer or converter first (week 1)
Print process (offset, digital, flexo, rotogravure) · substrate and laminate · surface or reverse print · the colour profile or printing condition and the **total ink limit** · number of colour stations, spot inks, white · minimum type and line sizes (positive and reverse) · trap values · bleed, safe area and dieline conventions · file format (PDF/X-4 or X-1a) and their preflight profile · proofing options · MOQ and lead time.

## 1. Colour management
- Design in RGB and convert late, to **the printer's profile**. Never pick CMYK values off a screen.
- Common printing conditions [SRC]: coated offset Europe **PSO Coated v3 / FOGRA51** (current) or **ISO Coated v2 / FOGRA39** (older, still widely requested); uncoated **PSO Uncoated v3 / FOGRA52**; US G7 **GRACoL 2013 (CRPC6)** coated and **CRPC3** uncoated. Packaging presses usually have their own profiles. The printer's condition matters more than which is newest.
- **Total ink limit:** commonly about 300% for coated offset, and often lower for uncoated and flexo. Dark areas are where it breaks.
- **Rich black** only for large areas, with the printer's recipe. **Small text and fine lines are 100% K only.**
- Black overprints; colours knock out unless trapped.
- Proof under D50 light on a calibrated monitor. Never approve colour on a phone.

## 2. Brand colours in print
For each brand colour, record: HEX/RGB · CMYK coated · CMYK uncoated · Pantone C and U · a substrate note.
- **Choose Pantone from a physical guide under D50**, not the screen. The Pantone Color Bridge guides show spot vs process side by side; a CMYK build is a simulation, not a match [SRC].
- "485 C" and "485 U" are different references. Name spot swatches exactly and consistently (mismatched names create extra plates).
- If recognition depends on one colour (a distinctive asset), **budget a spot ink** on key packs.

## 3. Finishes (1–2, for meaning)
Matte or soft-touch lamination · gloss varnish · **spot UV** on one element · hot or cold **foil** · emboss or deboss · die-cut window · registered matte and gloss. Each finish is a **separate layer** in its own named spot colour (`SPOT_UV`, `FOIL`, `EMBOSS`), set to overprint, at 100%.

## 4. Dielines
- **The converter supplies the dieline.** Draw your own only for concepts.
- Put it on its own layer, in a uniquely named spot colour (`DIELINE`). The overprint or non-printing setting follows the converter's convention. It must never print [SRC].
- Mark cuts (solid), folds and creases (dashed), seals, zipper, tear notch, hang hole, window, glue areas (no ink), bleed (often 3 mm for print; packaging can need more) and safe area (text 3–5 mm inside folds and cuts).

## 5. Small things that ruin runs
- Type below the minimum (often around 5–6 pt positive and larger reversed; flexo is stricter). Use bold sans for tiny legal text [SRC].
- Reverse type on multicolour backgrounds fills in: use one colour behind it, or a keyline [SRC].
- Hairlines below about 0.25 pt (thicker for flexo).
- Gradients that band in flexo: add noise and avoid long fades to 0%.
- Fine detail built from several inks drifts in registration: keep it to one ink.
- Images under 300 ppi at final size; RGB images left unconverted.
- A white object set to overprint (it disappears).

## 6. Preflight
- [ ] Trim size correct; bleed on every edge
- [ ] Dieline and finishes on their own named spot layers
- [ ] Profile as specified; ink limit respected
- [ ] Only the agreed spot colours, each named once
- [ ] Small black = 100% K, set to overprint; no white overprint
- [ ] Type and lines above the minimums; nothing important on seals or in the safe margin
- [ ] Images ≥ 300 ppi, in the correct colour mode
- [ ] Fonts embedded or outlined (keep a live master)
- [ ] Barcode at the right size, quiet zones clear, scans
- [ ] Legal text proofread against the client's approved copy
- [ ] Export PDF/X-4 or X-1a as requested; the printer's preflight profile run [SRC]
- [ ] Name: `<brand>_<sku>_<item>_v<NN>_PRINT.pdf`, plus a low-res proof PDF

## 7. Proofing and press check
1. **PDF proof:** layout, copy, dieline fit. The client signs off on the copy.
2. **Contract proof:** the colour reference.
3. **Proof on the actual substrate** (or a wet proof) for kraft, film or metal, where screen proofs lie.
4. **Physical mock-up:** print, cut and fold. Check fit, window position and shelf-distance reading.
5. **Press check** on the first run: approve against the proof under D50, and sign the approved sheet.
Record the approved values in the README for reorders.

## Sources
ICC registry (PSO Coated v3): https://registry.color.org/profile-registry/PSOcoated_v3 · Fogra: https://fogra.org/en/downloads/work-tools/characterisation-data · Pantone Color Bridge: https://www.pantone.com/products/graphics/color-bridge-guide-set-coated-uncoated · Flexo design: https://flexopedia.net/how-to-design-for-flexo-printing/ · Gravure artwork manual (SIG): https://api.sig.biz/media/ciejz5eu/artwork-manual-for-rotogravure-printing_v7.pdf · White underlay study: https://jpmtr.org/index.php/journal/article/view/50/46 · Packaging prepress (Esko): https://www.esko.com/en/blog/a-guide-to-the-full-packaging-prepress-process · Preflight (PRINTING United): https://www.printing.org/blog/main-blog/2023/04/11/preflight-for-success-a-guide-for-designers · Dieline checks (GlobalVision): https://www.globalvision.co/artwork-best-practices/pdf-creation · GS1 EAN/UPC: https://www.gs1ca.org/gs1ca-components/documents/EAN-UPC-Symbol-Reference.pdf · GS1 quiet zone: https://www.gs1uk.org/knowledge-hub/barcodes/what-is-a-quiet-zone · Low-migration inks: https://www.printweek.in/features/select-inks-food-packaging-25180 · Pack system: https://confetti.design/blog/packaging-design-system-guide · Shelf visibility: https://www.metrixlab.com/?p=25294
