# Reading light from a picture

What `look.py` cannot measure, an eye can. These are the clues a gaffer reads off a frame to rebuild the setup. Read them in this order; write the answer to each on the recipe card. Tags as in `../../nazar-core/references/research_path.md`.

## The eight clues
| # | Clue | Look at | It tells you |
|---|---|---|---|
| 1 | **Cast shadow direction** | Where every shadow points, traced back past the object | The key's side and height. All shadows from one source meet at one point (the light's projection); shadows that don't converge mean two lights or a fake [SRC: Kee, O'Brien & Farid 2013] |
| 2 | **Shadow length** | Shadow length vs object height | Elevation: length = height / tan(elevation). Equal length = 45 degrees; twice the height = about 27 degrees [KNOWN, geometry] |
| 3 | **Shadow edge (penumbra)** | How fast the shadow goes from dark to light, at the base and at the tip | Source size relative to distance. Crisp all the way = small or far (sun, bare bulb); sharp at contact, wide at the tip = medium; no edge at all = a large source close (window, big softbox). Penumbra width = shadow distance x source size / source distance [KNOWN, similar triangles] |
| 4 | **Terminator** | The line where a round or bent surface turns from lit to shadow | Same as 3, on the object: a hard terminator is a small source; a long, slow roll is a big one |
| 5 | **Specular highlight shape** | The brightest reflection on glossy parts (bottles, foil, lacquer, eyes) | The source's shape and size: a rectangle with bars = a window; a long thin line = a strip box; a round dot = a bare or octa source. Its position tells you where the source sits in the "family of angles" [SRC: Hunter, Biver & Fuqua, *Light: Science & Magic*] |
| 6 | **Shadow density and colour** | How dark the shadow side is, and what colour it leans | Fill: how much light returns to the shadows, and from what (a white card = neutral, a blue sky = cool, a warm floor = warm). Shadow colour is the fill's colour, never just "darker key" |
| 7 | **Falloff across the frame** | Brightness from near to far, left to right | How close the key is (inverse square: a close light falls off fast across the set) and whether there is a flag or vignette. `look.py` gives the left-right and top-bottom numbers |
| 8 | **Rim, edge and backlight** | A bright edge on the far side of the subject, glow through translucent parts | A light behind the subject; on frosted or liquid products it is how translucency is shown [KNOWN] |

## Counting the sources
- One shadow per object = one hard source (plus soft fill that casts no edge). Two shadows of different darkness = two sources. The **darker** shadow is cast by the **stronger** light: that patch is blocked from the strong light and lit only by the weak one. Where the two shadows overlap, nothing reaches, so it is darkest of all.
- Count specular highlights on a curved glossy object: each distinct shape is a source.
- A catchlight in an eye or on a bottle shoulder is a map of the room's bright things.

## Ratios in stops
- Key-to-fill: compare the lit side and the shadow side of the same flat colour. 1 stop = half as bright. Product and food work commonly sits at 1 to 2 stops; dramatic still life at 3 or more [KNOWN].
- `look.py`'s `contrast_p95_p5` and `black_point` say how far the whole frame is pushed; the ratio is read on the object.

## Colour temperature
- Warm highlights with cool shadows = a warm key with a sky or daylight fill (golden hour, tungsten interior with a window). Cool highlights with warm shadows = daylight key bouncing off a warm floor or wall.
- Mixed sources are a decision. 20-30 mired is roughly the point where a shift becomes visible side by side [KNOWN, colour-correction practice]; `shotplan.py` warns above 30.

## Reflections on the surface
- A sharp, mirrored copy of the object = gloss (lacquer, glass, wet stone). A soft smear = satin. Nothing = matte.
- Reflection strength rises fast as the camera gets lower (Fresnel): a low camera on a glossy table shows a strong reflection; from above it nearly vanishes [KNOWN, Schlick's approximation; `shotplan.py` computes it].

## What generators get wrong (check these first on any AI plate)
- Shadows that point different ways, or that don't start at the object's contact point [SRC: Sarkar et al., CVPR 2024; Farid 2022].
- Reflections that don't mirror the object, or that appear on matte surfaces [SRC: Farid, "Perspective (In)consistency of Paint by Text", 2022].
- Lines that should be parallel converging to several vanishing points [SRC: Sarkar et al. 2024].
- Light with no source: a glow, an even brightness with no falloff, shadows with no edge at all.
- People rarely notice lighting errors on their own (Ostrovsky, Cavanagh & Sinha 2005), but a trained viewer and a forensic tool do, and several small errors together read as "AI" (`../../nazar-core/references/ai_tells.md`). So check with the clues above; don't trust a first glance.

## Sources
In `../../nazar-shoot/references/research_realism.md` (papers) and `archives.md` (where to study).
