# Camera pass: making a composite read as a photo

A render is cleaner, sharper and more saturated than any photograph. The plate already carries a camera; the product must carry the same one. Each step below is a known tell of a fake composite (sources in `research.md`), the engine parameter that fixes it, and the check `--selftest` runs.

## Steps, in engine order
| Step | What a real camera/room does | `composite.py` | Default |
|---|---|---|---|
| Perspective | Verticals converge a little when the camera is above | `persp` | 0.03 |
| Bend | A filled pack pinches at the sides and rolls off the light | `bend`, side roll-off shading | 0.02 |
| Contact shadow | The darkest, tightest dark where the object meets the surface; a small shape under the base, not an outline round the silhouette | `_contact`, `contact_dark` | 0.55 |
| Cast shadow | Shaped by the light, lying on the surface (projected, not a drop shadow); darkest and sharpest at the base, softer and lighter further out | `_ground_shadow`, `shadow_dark` | 0.5 |
| Tone match | The plate's light falloff and colour cast reach the product; room saturation is lower than a render's | `light_k`, `cast_k`, `sat` | 1.0, 0.45, 0.88 |
| Black lift | The product's darkest tones sit at the plate's black level, not pure render black | `lift` (to plate P2) | 0.4 |
| Sheen | One broad soft highlight on the side facing the key; never glossy streaks on matte film | `sheen` | 0.08 |
| Edge occlusion | The outer edge turns away from the light and darkens slightly | always on | - |
| Light wrap | The room's light spills a few px over the edge; stronger where the background is bright, weaker against dark ground | `wrap` (uses the local plate, not a global colour) | 0.35 |
| Re-lay | Anything in front (shelf lip, table edge, hand) is pasted back over the product | `relay` / `--relay` | - |
| Micro-softness | Lenses never resolve as hard as a vector edge | `soften` + 0.5 px pre-blur | 0.5 |
| Halation | Bright highlights glow warm (red-orange), only where they clip; a blurred white edge alone is not halation | `halation` | 0.08 |
| Vignette | Light falls off toward every corner | `vignette` | 0.14 |
| Chromatic aberration | R and B displaced against G, radially, growing toward the corners; visible only on tangential edges | `ca` (% of centre-to-corner), off by default | 0; subtle 0.05; cap 0.12 |
| Grain | Matched to the plate's measured noise, on the product only; the plate keeps its own grain | `grain` (auto from plate) | auto |
| Stamp | Disclosure, bottom-left, small | `stamp` | on |

## Limits
- **Chromatic aberration:** lens-test practice measures lateral CA as % of the distance from the image centre: under 0.04 insignificant, 0.04-0.08 low, 0.08-0.15 moderate, over 0.15 strong and visible. The engine caps at 0.12. Use it only on synthetic or very clean plates; a real photo plate already has its own lens, and adding more doubles it.
- **Halation** belongs to bright tungsten or sun highlights; around LED or overcast light it barely exists. Keep it at 0.05-0.10 and never on the pack's printed whites unless they actually clip.
- **Grain** is level-dependent (heavier in shadows and in blue on digital sensors). Match by measurement, then look at 200% beside the plate.
- **Never** sharpen the product above the plate's own sharpness to "save the type". Type must stay readable at the plate's resolution; if it doesn't, the product is too small in frame.

## QA checklist (what `--selftest` reports, and what to check by eye on every real composite)
- [ ] Size matches the plate; nothing cropped by accident
- [ ] Contact shadow: the base is clearly darker than the bare surface beside it (engine test: at least 25% darker)
- [ ] Cast shadow falls away from the key light, the same direction as every other shadow in the plate
- [ ] Cast shadow is darkest at the base and fades and softens with distance; no hard far edge
- [ ] Black level: the product's darkest tones are not below the plate's (P1 within 90%)
- [ ] Edges: no dark or bright fringe just outside the silhouette; no aliasing
- [ ] Light wrap: the outermost product pixels lean toward the room colour behind them
- [ ] Grain on the product within 0.6-1.6x of the plate's measured grain
- [ ] Print stays sharp: type keeps real contrast after the camera pass; nothing mirrored, nothing redrawn
- [ ] Front objects (lip, edge, hand) sit over the product where they physically would
- [ ] Disclosure stamp present on AI plates
- [ ] CA off unless asked; when on, zero at the centre, outward at the edges, within the cap
- By eye only: scale against the plate's own objects; light direction matches; colour cast of the room is on the product; focus/depth of field matches the product's distance; no floating; the film creases and sheen read like the real pack.
