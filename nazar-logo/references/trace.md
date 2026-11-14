# Sketch → vector (hands first)

The studio rule: **the hand makes the idea, the machine cleans it up.** Kaif draws on paper; `../../nazar-core/engine/trace.py` turns the scan or phone photo into clean Bézier curves. Then the mark is refined by eye. The trace is the start of the craft work, never the end.

## 1. Draw for tracing
- **Black marker or brush pen on white paper.** Pencil traces poorly unless it's scanned dark.
- **Draw big.** The mark should fill at least half the page; small details survive better at size.
- **Close your shapes.** Gaps become breaks in the vector. Fill solids fully, or the tracer will keep the marker streaks.
- Draw **3–6 versions on one sheet.** Crop each one with `--crop`.

## 2. Capture
- **Scan at 600 dpi** (best), or photograph in flat daylight with the phone parallel to the page, filling the frame, with no shadow of the phone.
- The tracer flattens uneven light itself, but it can't fix blur or perspective.

## 3. Trace
```bash
python nazar-core/engine/trace.py scan.jpg --name mark_v1 --width-mm 60                  # 3 variants + compare + report
python nazar-core/engine/trace.py scan.jpg --crop 120,80,1400,1200 --variants balanced    # one version from a sheet
python nazar-core/engine/trace.py chalk.jpg --invert                                      # light drawing on a dark ground
python nazar-core/engine/trace.py shaded.jpg --levels 3 --palette "#EFE9DF,#E8572A,#1B1A17" # tones as layers (package art)
```
| Variant | Keeps | Use when |
|---|---|---|
| `tight` | Most wobble and every nuance | The hand **is** the mark (brush lettering, signatures, illustrated marks) |
| `balanced` | Clean curves that still feel drawn | Default |
| `smooth` | Fewest nodes, calmest curves | The intent was geometric; a first step before rebuilding |

How it works: light flattening → Otsu threshold → despeckle → boundary loops → corners found at two scales and **pinned** while smoothing → nodes placed on **true extremes** (where the curve is really horizontal or vertical) → Schneider least-squares Bézier fitting → one evenodd SVG path (counters work). Outputs: `<name>_<variant>.svg`, `<name>_compare.png` (sketch, threshold, each trace with its nodes), `<name>_report.md`.

## 4. Refine (this is where the craft is)
1. **Check the overlay.** The trace should hug the drawing. If it doesn't, adjust `--threshold` (lower picks up less ink) or `--min-area`.
2. **Decide what is intended and what is accident.** Keep the wobble that carries character; rebuild what was meant to be geometric (circles, straights, parallel stems) with real geometry.
3. **Node hygiene:** nodes on extremes, tangents horizontal or vertical there, no nodes in the middle of smooth runs, no kinks where curves meet (`craft.md`).
4. **Optical fixes:** rounds overshoot flats, stems balance, counters breathe (`craft.md`).
5. **Test it:** blur, 16 px, one colour, reversed, at distance (`testing.md`).

## 5. Where traced art goes next
- Logos: the export matrix in `files.md`.
- Package art (hand-drawn illustrations, lettering, patterns): drop the SVG into a `logo` block in **nazar-dieline** design mode, or send it to Figma with `set_svg` (`../../nazar-dieline/FIGMA.md`).
- Multi-tone traces: recolour the `tone_1…n` layers to brand tokens, and check each tone prints as a solid (or a spot colour) at the printer's minimum line weight.
