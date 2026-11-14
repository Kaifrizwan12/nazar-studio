---
name: nazar-illustration
description: Nazar Studio's illustration kit. Use when Claude should draw (spot and editorial illustrations, simple characters, icons, pack illustrations, patterns, pen-and-ink or riso looks, math and generative art) with code that behaves like a human hand, via engine/ink.py (pressure strokes, real corners, hatching, stipple, offset print flats, print grain). Concept first, a one-thing-at-a-time look-and-fix loop. For complex figurative scenes, or when code drawing fails review after a few rounds, also hand over a ready image prompt (Gemini or similar) for use with client approval. Kaif's own sketches are traced with nazar-core/engine/trace.py instead.
---

# Nazar illustration

Read `../nazar-core/SKILL.md` first. **The user's prompt leads; take only what the job needs from here.**

## Where code drawing shines, and where it doesn't
- **Shines:** small, sharp concepts built from a few objects. Lines, tools, icons, spot illustrations, patterns, hatching, op-art and math art. Reference: `examples/pencil_cursor.py`.
- **Struggles:** complex figurative scenes (several people, clothes on bodies, precise hand actions) and photorealism. Make at most 3–4 honest rounds, then simplify the concept, **and** offer a ready image prompt for the advanced version (to be used only with the client's written approval). The `examples/helping_hands.py` stress test, with its Gemini prompt in the header notes, shows this route.
- Cute for its own sake reads childish. Keep Kaif's register: sober, one wink.

## Rules
1. **Concept lock first.** At the top of the scene script, write the idea in one sentence, the focal point, the light, the budget (paper + ink + 3–5 flats + one accent; 3 line weights) and what it must say. Propose 2–3 concepts and let Kaif pick before drawing anything sizeable.
2. **Draw like a hand** (`engine/ink.py`):
   - Filled pressure strokes with taper.
   - Key points through centripetal Catmull–Rom splines.
   - Low-frequency wobble only.
   - `corners=True` for anything with corners.
   - Tone from hatching and stipple, not blur.
   - Flats offset like print.
   - `hand=0` for deliberately mechanical parts, such as the vector half of the demo.
3. **Paint order is depth.** Run backgrounds past the frame. Hide joins: tops tuck under rims, limbs start under clothes.
4. **Look, then fix one thing.** Render, open the PNG, name the most visible fault, fix only that. Check for:
   - the image contradicting the brand message,
   - a shape reading as something it isn't,
   - occlusion errors,
   - flat-on-flat value with no edge,
   - spline-rounded corners,
   - AI tells (gradients, glow, uniform jitter).
5. **Archive grammar, never copies.** Study CC0 and public-domain sources (Met, Smithsonian, Rijks, BHL, pre-1929 cartooning manuals, Pennell on pen drawing). Never trace other artists.

## Engine
`engine/ink.py`:
- `Sheet(w, h, paper, seed, hand)`
- `stroke(pts, width, taper, pressure, closed, corners)`
- `flat(pts, colour, offset)`
- `hatch(poly, angle, gap, tone 1–4)`
- `stipple(poly, n)`
- `save(base, riso=True)`: print look, occlusion kept
- `save(..., overprint=True)`: true riso overprint
- helpers: `ellipse_pts`, `arc_pts`, `catmull_rom`

Examples: `python examples/pencil_cursor.py` → `exports/illustration/`.
