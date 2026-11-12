# 07 · Graphic language

## Find the atom
Every Kaif system has **one atom**: the smallest part of the brand that can stand alone and still be the brand. Pull it out of the logo or the product, never invent it from nothing.
- A logo detail (a dot, a counter, a stroke end) becomes the avatar, favicon, page stamp and hidden device.
- Food: the seed, a cross-section, the tool that makes it, the knot on a sack.
- Tech: a cursor, a bracket, a pixel, a status dot.
The atom gets its own page: the atom alone, the atom in states (single, pair, pattern, moving), and its rules. Document when the atom is used instead of the full logo (avatars, favicons, small sizes) and that it never sits *next to* the full logo.

## Textures (two at most, and each must mean something)
| Texture | Meaning it can carry | How it's made |
|---|---|---|
| Halftone at an angle | Print, street, the past | SVG dot pattern, rotated (take the angle from the logo, if it has one) |
| Pixel or dither | Screen, digital, data | Ordered dither, square pixels |
| Grain | Film, warmth; kills gradient banding | ±4% noise tile |
| Riso misregistration | Handmade, zine, overprint | Two plates offset 2–4 px, multiply |
| Kraft fibre | Packaging honesty | A scanned public-domain paper texture, licensed |
| Engraving lines | Heritage, money, botanical plates | Parallel line hatching following the form |
| Reflective tape | Street, night, safety | Thin reflective stripes, a geometric grid |
Pair two textures only when they're the brand's tension (for example: halftone = print or street, pixels = screen, joined by one accent line).

## Maps and real places
If the brand belongs to a place, use **real maps**: OpenStreetMap via the Overpass API (the engine has `fetch_map.sh` and `map_paths()`). Style roads by class (lanes 6%, residential 13%, main roads 34%) and highlight one real street. Use a true-scale bar and a north arrow, and credit "© OpenStreetMap contributors" **once** on the sources page. Round home coordinates for privacy.

## Icons
Draw them from the atom's geometry (the same stroke, corner and angle). 24 px grid, one stroke weight. If the brand needs pictograms, study Isotype (Neurath and Arntz, checking the Pictoright terms) for the logic: one figure, repeated, counts quantity.

## Data and diagrams
Diagrams are drawn like technical drawings: 1 px lines, dotted leaders, mono labels. No 3D charts and no pie charts. Any number that isn't real says "sample".

## Photography (when it's used)
Kaif's books avoid stock photos completely. If the brand needs photography: write a shot list (real place, real product, real hands, a set time of day), with art direction rules (light, angle, crop, colour grade) and 3 archive references for the mood. Until it's shot, use a flat graphic placeholder labelled "PHOTO: [shot name]", never a stock image or an AI image.

## Motion (stills in the book, rules in words)
State 3 rules: the atom moves first; the ease is one curve (for example cubic-bezier(0.2, 0, 0, 1)) at 600–1200 ms; nothing bounces unless the brand is a toy. Show motion as a storyboard of 5 frames.

## Texture practice from print-led designers (see `../nazar-core/references/masters.md`)
1. **Source it real.** Scan real surfaces (paper, ink, walls, packaging, fabric) at 600–1200 dpi, or license scans. Log each source. No generic texture packs as the hero.
2. **One reason per texture.** Each texture carries one meaning tied to the brand's tension. Two textures at most.
3. **Halftone done well:** small dots, high contrast, **one** screen angle with a reason (taken from the logo or a period press). Never stack random angles. Check it for moiré at print size.
4. **Grain below notice:** about 2–6% noise, felt not seen. Kill it wherever it hurts readability (small text, UI).
5. **Resolution and tiling:** use scans at native resolution and never upscale for print. Build seamless tiles and check the seams at 200%.
6. **Riso, digitally:** separate the artwork into 2–3 spot-colour layers, multiply-blend them, offset one layer by 1–3 px, and don't align textures across layers. **Riso, physically:** expect 0–3 mm of shift between passes. Avoid tight registration and large dark solids, and remember that print order changes the overprint colour.
7. **Texture in the system:** document each texture's opacity, scale and blend mode, and where it's *never* used (logo, small text, UI controls).
8. **Construction grids, then optical correction:** build icons and patterns from one grid (Aicher), then correct them by eye (overshoots, weight balance), as even Aicher's finished forms departed from his grid.
