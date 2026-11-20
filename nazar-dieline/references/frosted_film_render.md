# Frosted film renders (showing matte translucent packs in 2D)

Frosted and tinted translucent pouches are hard to show. Clear film is easy (draw the product, put ink on top). Frosted film is a diffuser: what you see through it depends on how close the product sits to the film. This file covers how to fake that honestly in code (`engine/film.py`), where code stops, and the hybrid workflow that got a client to "yes".

## 1. The 7 cues (and how each is coded)
| # | What a photo shows | How `film.py` does it |
|---|---|---|
| 1 | **Contact clarity.** Sharp where the product presses the film, milky where there's air (headspace, edges, gusset). This one cue is most of the effect | A contact map from the fill's coverage (blurred density), zeroed in the headspace, near the side seals and over the gusset. Sharp blur where contact = 1, wide blur where 0, blended |
| 2 | **Milky veil.** The matte skin scatters light, so blacks lift | A near-white veil over the inside: about 6% at contact, up to 38% with no contact |
| 3 | **Tint.** The film colour filters what's behind it | Multiply by the tint (mixed 45/55 with white), then add 16% tint as scattered light |
| 4 | **Double film reads denser.** Header above the zip, side seals, the bottom gusset arc | A density mask (header 1.0, seals 0.8, gusset 0.55) pulls toward a denser tint |
| 5 | **White ink is opaque and on top.** Crisp, matte, not frosted | White and dark ink SVGs are composited after the frost, never blurred |
| 6 | **Coloured hard shadow.** Sun through tinted film throws faint coloured light into the shadow wherever ink and product don't block it | A transmission map (ink and dense product = low) tints the shadow in `composite` / `scene_photo` |
| 7 | **Matte surface.** Broad soft sheen, never glossy streaks; crimp ribs on seals; the zip is two tracks; small creases | Wide gaussian sheen bands, a crease map (light/dark pairs, softer where the product presses), sine ribs on the top seal, two dark-light zip lines, a lit cut edge (rim), then a low-frequency mesh warp so nothing is ruler-straight |

Then volume (`add_volume`): a filled pouch is a pillow. The sides pinch in through the body (mesh), a side light rolls off across the curve (lambert on a fake normal), a broad matte highlight sits on the lit shoulder, and the far edge darkens.

## 2. The honest ceiling
Code-only renders read as "good illustration of a pouch", not "photo of a pouch". What gives them away:
- drawn product. Drawn pieces look like clip-art through frosted film however well they're shaded. **A real product photo as the fill (`photo=`) is the biggest single jump**;
- a flat colour background. No table texture, no real light falloff;
- one light model for everything. Real film has micro-wrinkles, dust, uneven gusset folds.

Don't chase photoreal in numpy. Get the film right in code, and borrow reality for the parts code can't fake (product texture, the set).

## 3. The hybrid workflow that worked
Only with the client's written OK for AI imagery (`../../nazar-prompts/`). Log it.
1. **AI makes only the plates and the textures. Never the pack.** Image models can't render see-through frosted film (they make it opaque or glassy) and they don't keep label text or the logo. So generate:
   - empty background plates (a top-down table, an eye-level sweep, a ledge), with the light direction stated;
   - real product-texture photos: a top-down pile filling the frame, same light. Prompts: `../../nazar-prompts/references/product_texture_prompts.md`.
2. **Our renderer makes the pack:** the real artwork as white/dark ink SVGs, the texture photo as the pile inside (`render_pouch(..., photo=path)`).
3. **Composite into the plate** with matched light: `composite(plate, ...)` for top-down, `scene_photo(plate, ...)` for standing packs. Match the shadow direction to the plate's sun, and the shadow length to its sharpness.
4. **Label it.** Every output says "AI concept render" (`label()`), stays internal, and goes to the client as a concept, not a photo. Nothing is published until the client OKs it in writing. Real photography of printed samples replaces it later.

## 4. Composition (from client and art-director feedback)
- **Avoid the "mockup" look:** one pouch, upright, dead centre, front-on, on a plain sweep. It reads as a template.
- **Prefer top-down flat lays:** packs at varied angles (about ±5° to ±25°), overlapping, one or two cropped by the frame, the hero slightly bigger, loose product scattered at the edges (in the plate, not on the pack).
- **A neat row on a ledge** works for a range shot. Same base line, even gaps, light from one side.
- **Shadows must be dense.** A full pack blocks most light: a dark, hard shadow with only a faint tinted glow where the film is clear. A pale ghost copy of the pouch reads fake. Defaults: shadow = canvas × 0.56 (flat lay), × 0.40 (standing); tint adds at most 8 to 30%.
- One sun for the whole set: if the plate is lit from the top-left, every shadow falls bottom-right.

## 5. Running it
```bash
python engine/film.py --demo --out <folder>        # neutral grey stand-in: a single pack, a flat lay, a standing row
```
```python
import film
pim, trans, tint = film.render_pouch("#b9a7cf", white_svg, dark_svg,
                                     {"W": 120, "H": 180, "G": 60, "side_seal": 6, "top_seal": 8, "zip_from_top": 26, "zip_band": 6},
                                     photo="plates/texture.png", s=8, seed=1)
img = film.composite("plates/table_top.png", [(pim, trans, tint, 820, 520, 17, 0.55)], (3072, 2048), shadow_len=52)
film.label(img).save("flatlay.jpg", quality=93)
```
Ink SVGs use viewBox `0 0 W HP` (mm, HP = H − G/2, the front panel above the gusset). White = everything opaque white; dark = dark ink. Leave white off where the product should show. Export them from the art layer or draw them by hand.
