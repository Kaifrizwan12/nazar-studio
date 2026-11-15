---
name: nazar-colour
description: Nazar Studio's colour kit. Use to build brand and campaign palettes that don't look generic or AI-made, sourced from the client's own material, regional craft (ajrak, truck art, kashi tilework, Mughal miniature pigments), art-history systems (Sanzo Wada, Werner, Vanderpoel, Albers, Itten) and how strong studios build palettes; with OKLCH ramps, WCAG and APCA contrast, colour-blindness checks, and screen-to-print translation (CMYK, Pantone C/U, RAL).
---

# Nazar colour

Read `../nazar-core/SKILL.md` first. **The user's prompt leads; use what the job needs.**

## Rules
1. **Source order:** the client's own material (product, place, heritage) → a regional archive (ajrak, truck art, kashi, miniature) → a historical system (Wada, Werner, Vanderpoel) → trend tools last (`references/colour.md` §1).
2. **Own one colour, then support it.** Ground 60–80% (paper, stone, a deep neutral), ink (a near-black tinted toward the brand hue), **one accent at 5–10%**, and 1–2 supports. Write the proportions down (Itten's contrast of extension; Kaif's pop colour on a sober grid).
3. **Every brand colour gets:** a name (Werner-style, local), OKLCH, hex, CMYK coated and uncoated, Pantone C and U, and RAL for physical builds.
4. **Build ramps in OKLCH:** step lightness at a fixed hue; lower chroma at the extremes to stay in gamut.
5. **Pass WCAG 2** (4.5:1 text, 3:1 large text and UI) for compliance; use APCA only as a supplementary look at dark mode and thin type (its WCAG 3 status is unresolved and there is no official threshold to cite). **The palette must work in greyscale and for colour-blind viewers.**
6. **No AI palette tells:** no purple-blue gradients, neon on black, teal and orange, even-lightness pastel rainbows, or pure #000/#FFF with one stock blue. Add one earthy, slightly "wrong" colour (lac maroon, ajrak indigo, orpiment yellow): historical friction reads as human.
7. **Test relativity (Albers)** before approval: put every colour on every other colour.
8. **Print is a different medium.** Use the printer's ICC profile, keep total ink to roughly 300% or less, supply Pantone C and U, and press-check. Truck-art saturation on a pack usually needs spot or fluorescent inks.

## Workflow
| Phase | Do | Output |
|---|---|---|
| 1 | Collect evidence: photographed material, archive plates, place (calibrated photos) | `research/colour/` |
| 2 | Reduce to proportional grids (Vanderpoel method) and name the colours | colour studies |
| 3 | 2–3 palettes with proportions, each with its reason | palette routes |
| 4 | OKLCH ramps, contrast pairs (WCAG 2.2; APCA supplementary), colour-blind and greyscale checks, Albers sheet | palette spec |
| 5 | Print translation (CMYK coated and uncoated, Pantone C/U, RAL), wet proof | tokens in `brand.json` + spec sheet |

## Files
- `engine/palette_check.py`: archive images → OKLab palette → WCAG contrast per pair, colour-blind and greyscale checks. Demo: `examples/make_colour_card.py`.
- `references/colour.md`: sources (Wada, Werner, Vanderpoel, Albers, Itten, Munsell, OKLCH), Pakistani and South Asian palettes, studio methods, technical checks, print translation, AI tells, sources
