# Briefing empty plates

A plate is the room without the product. AI (with written client approval, `nazar-prompts`) or a licensed photo supplies it; we supply the product. The plate decides whether the composite can ever look real, so brief it like a photographer, not like a mood.

## The brief (fill every line)
| Line | Say | Why |
|---|---|---|
| Scene | One real place, one moment: "a kiryana shelf at 7 pm, tube light", "a rooftop charpai at noon" | Story, not a style word |
| Camera height | Eye level to the product's middle (front renders) or straight down (flat-lay renders) | Our render has one camera; the plate must match it. Oblique 3/4 plates need a 3/4 render |
| Lens | 50-85 mm equivalent, no wide-angle bulge near the product spot | Wide lenses bend verticals; our render's verticals are straight |
| Light | One key, named side and height: "hard window light from the upper left, 45 deg" | Shadows and sheen are set from it (`--light`) |
| The empty spot | "Empty space on the table, left third, nothing on it, surface continues under it" | We need clean surface where the product stands, and its shadow lands |
| Front objects | Shelf lip, table edge, a hand, a cup rim in front of the spot | These are re-laid over the product (`--relay`) and sell depth |
| Texture words | Real materials: worn laminate, jute, steel shelf with chipped paint, mid-day dust | Avoids "AI plastic" surfaces |
| Grade | "Shot on a phone or a 35 mm camera, natural grain, no HDR, no bokeh balls" | Matches the grain pass |
| Never | No product, no packs, no text, no logos, no shop names, no people's faces | The product is ours; no other brands in frame |

## Light direction
- Read it from the plate before seating: which side is brighter, where existing shadows fall, how hard they are. `composite.py` estimates left-right falloff (`--light auto`), but pass `--light dx,dy` when the plate shows clear shadows: dx, dy are the shadow offset as a fraction of product height (dx > 0 = shadow to the right, dy > 0 = shadow falls back).
- Shadow hardness follows the source: a small hard sun makes a crisp near edge; a window or overcast sky makes a wide penumbra. Contact is always darkest and sharpest.
- One key. If the plate has two strong shadow directions, reject it.

## Perspective and scale
- Place by the base: `--at` is where the product's base centre touches the surface. A product further back sits higher in frame and is smaller; scale by the plate's own objects (a shelf pitch, a cup, a tile) and say what you measured.
- `--persp` (0.02-0.05) narrows the top for a camera a little above the product. Horizon above the product's top = camera looking down; then a tiny keystone is right.
- Lean (`--angle`) only as much as the pack could physically lean against something. Free-standing pouches are near upright.

## Reject a plate when
- It has a product, a pack shape, text or a logo baked in.
- Its perspective cannot match a front or top render (strong 3/4, fisheye, tilt).
- The light is a glow with no direction, or two directions.
- It reads "chic slop": travertine plinths, palm shadows, beige gradient sweeps, neon on near-black.
- Surfaces are too clean or melted (AI texture smear) where the product will stand.

## Textures
AI may also make flat textures (paper, board, jute, a wall) for a backdrop or a pack substrate study. Same stamp rule. Never generate the pack's print art.
