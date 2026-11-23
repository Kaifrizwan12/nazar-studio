# 3D pack renders (Blender, Cycles): real board, not plastic

Use when a pack has to be shown as a real object (mockups, case studies, hero shots). Flat art with a painted sheen reads as AI slop; build the object instead. Blender is free (GPL), and renders belong to you.

## Pipeline
1. **Maps per face** at true mm (≥ 24 px/mm for renders): `col` (print), `foil` (white = foil → metallic), `height` (grey 128 = flat; brighter = emboss, darker = crease/deboss), `gloss` (white = spot-UV → clear-coat weight).
2. **Atlas**: pack the faces into one sheet per map; UVs are computed from position on each face, so the art lands exactly.
3. **Geometry from the dieline**, not a cube: each part is a hollow shell (Solidify = caliper, ~0.3 mm), outside = print, inside = inside print, rim = board core.
4. **Materials**: soft-touch matte (roughness ~0.75, low specular ~0.2, little or no sheen, or black reads grey) · foil = metal (roughness ~0.2, a little anisotropy, slight roughness noise) · spot-UV = coat weight from the gloss map (coat roughness 0.15–0.3 plus smudge variation; a mirror coat reads as chrome plastic).
5. **Camera**: a 100 mm lens at ~0.4 m, **f/7–8 depth of field** focused on the face toward the camera. A pin-sharp small object reads as a big hard block.
6. **Finish**: fine grain, slight halation, gentle vignette, and the "speculative / not a real product" caption where needed.

## Board realism checklist (each item cost a review round)
- **Hinge-lid (flip-top)**: the cut runs across the front and down the sides only. The back is one panel with a soft hinge crease (taper the gap to 0 at the back; cover the modelling seam and dent the crease in the height map). Never cut across the back.
- **Die cut**: a visible but modest gap (~0.3 mm) with the lid a hair proud (~0.08 mm) at the front and sides. A new, sealed pack sits flush; a lifted lid lip means a used pack.
- **Folds**: crease radius ~0.4 mm, not a moulded 0.8 mm+. Soft-touch greys slightly where it stretches over a crease (Bevel-node edge mask). Glued flap edges show the board core as a hairline.
- **Panels pillow** ~0.2 mm (front/back) and ~0.1 mm (sides), zero at the edges. A lid can sit a fraction of a degree off.
- **Foil + emboss**: ~0.1 mm with a crisp edge (a small blur only). A deep, blurred emboss looks like a cast coin.
- **Text inside a lid**: confirm with a render which inner face actually faces the camera when open (geometry intuition is unreliable). Inner faces are seen mirrored; flip the art in UV space and check.
- **Top face text**: confirm the orientation with a top-down test render.

## Light (a product table)
- Raking key from above and to the side, out of the front face's mirror angle (a softbox in the mirror angle fills a gloss panel and reads as silver).
- Gloss: a **black flag** in its mirror path plus **one thin, far strip** = one crisp line. Foil on the same plane needs a soft panel just above the gloss's mirror angle.
- Put look and exposure on separate lines (a bad look name throws and silently skips the exposure). Turn the light rig with the camera for each shot; for a back view turn the object, not the camera.
- Parented objects (a lid on a hinge empty) must be skipped when re-centring, or they move twice.

## Design note
Stacking every luxury code (black + gold + crest + spaced serif + gloss + gold rule + emboss) reads as "forcibly premium". Subtract to one gold moment and let the material and the structure carry the rest.
