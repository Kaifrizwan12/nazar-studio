# Hyper-real product images with Gemini (or any image model): three routes

Use only with the client's written approval of AI imagery (`../../nazar-prompts/SKILL.md`). The product's print is never generated: models redraw type and logos, and Google's own guide says small text and fine detail "may not work perfectly" [SRC: Google Cloud, *The ultimate Nano Banana prompting guide*, 2026-03-06]. Every route ends with our exact pixels on the pack.

## Choose the route
| Route | What the model makes | What we make | Best for | Engine |
|---|---|---|---|---|
| **A. Empty plate** (default) | The scene with an empty spot | The pack render, seated with physics | Most shots; front or top views; fastest to control | `composite.py` |
| **B. Proxy** | The scene **with a blank, unprinted stand-in pack** of the same shape and size (matte white or 18% grey) | Our render replaces the stand-in and takes on its shading, specular highlights and the scene's real shadows and reflections | Glossy floors, hands, tight contact, packs among props, anything where light must bounce between pack and scene | `proxy.py` |
| **C. Texture and props** | Real product contents (fruit, crumbs), surfaces, papers, fabrics, flat textures | Layout and pack | Fill textures inside windows, food styling around the pack, backdrops | `../../nazar-prompts/references/product_texture_prompts.md` |

Never: a model drawing the pack, a model "enhancing" our render, a model generating a hand gripping our pack (it redraws the pack), generated fruit inside a window pretending to be the product.

## The master prompt (fill every slot; the smallest details are the realism)
Build it from the shot plan (`shot_plan.md`); `shotplan.py` writes slots 1-6 for you.
1. **Purpose and canvas:** "An empty background plate for a product added in post, 4:5, 2K." State the copy-safe zone if there is a headline.
2. **Scene and moment:** one real place, one hour, one thing that just happened. "A steel kiryana shelf at 7 pm, the shopkeeper has just restocked the lower row."
3. **Camera:** focal length (35 mm equivalent), distance, lens height, tilt, aperture, the depth of field in words. "85 mm, 1.4 m away, lens at 42 cm, level, f/8, about 12 cm of sharp focus around the empty spot."
4. **Light, in numbers:** each source's kind, side, height, size or hardness, colour temperature; what motivates it. "One soft strip light from camera-left, 55 degrees off axis and 38 degrees up, from the tube light over the counter, about 5000 K; a low white bounce from the right two stops darker; no other light."
5. **Shadows:** direction, length relative to an object's height, edge. "Shadows fall right and slightly back, about 1.3 times as long as a 23 cm object is tall, sharp at the base and soft at the tip."
6. **Surface and reflections:** material, finish, wear; whether it mirrors. "Chipped grey enamel steel, satin, faint scratches, a soft sheen but no sharp mirror image."
7. **The empty spot (route A) or the stand-in (route B):**
   - A: "a clear patch of surface about 26 cm wide at the lower-middle third, the surface continuing unbroken under it, lit by the same key."
   - B: "a plain, unprinted matte white stand-up pouch, 16 cm wide and 23 cm tall, slightly filled so its face curves, no text, no logo, no graphics, standing at the lower-middle third, casting its own contact and cast shadow."
8. **Layers:** something in front (shelf lip, cup rim, a hand at the frame edge), the spot, something behind. These sell depth and get re-laid over the pack (`--relay`).
9. **Imperfection:** one real flaw: dust in the corner, a ring stain, a torn price strip, a crumb. One, not ten.
10. **Grade and capture:** "shot on a 35 mm film camera, natural grain, restrained colour, no HDR, no bloom." Or the target look's words from `look.py`.
11. **Keep out of frame (phrased as what to show, where possible):** "an empty, unbranded shelf" is better than "no logos". Then list: no other products, no text, no logos, no shop names, no faces.

**Reference images (Nano Banana takes up to 14; give each a role in words)** [SRC: Google, *7 tips for Nano Banana Pro*, 2025-11-20; Google Cloud guide 2026-03-06]:
- Image 1: the light and grade reference (a CC0 still life from `../../nazar-study/references/archives.md`, or our own earlier approved plate). "Use image 1 only for the light quality and colour grade."
- Image 2: the location reference (a real photo of the place type, ours or licensed). "Use image 2 for the shelf's material and wear."
- Route B only, image 3: our pack's **silhouette** as a flat white shape on grey (never the printed pack). "The stand-in pouch has exactly the outline of image 3, plain white, no print."
- State the aspect ratio explicitly; with several inputs, edits inherit the last image's ratio [SRC: Google image-generation docs, `../../nazar-prompts/references/models.md`].

## Iterate like a photographer, not a gambler
1. Generate 4. Kill on physics first, beauty second: shadows from two directions, a melted surface where the pack will stand, a wrong camera height, baked-in text or logos (`plates.md` reject list).
2. Keep the best; edit one thing per turn with "keep everything else exactly the same" [SRC: Google guide]. Light changes in edit mode "can sometimes produce unnatural artifacts" [SRC: Google guide]: for a new light, generate a new plate instead.
3. Read the kept plate: `look.py card`, the eight clues. If its light disagrees with the plan, update the spec to match the plate and re-run `shotplan.py` for the composite args.
4. Composite (route A or B), then `look.py compare` against the target and fix the two biggest gaps.
5. Log every run (`../../nazar-prompts/references/assets.md`: date, model ID, settings, full prompt, references, keep or kill and why).
6. Stamp and disclose. Outputs carry SynthID and C2PA credentials [SRC: Google guide]; keep them.

## Route B, step by step (proxy)
1. Plan as usual; brief the stand-in exactly (size, fill, finish = matte white).
2. Generate; reject any where the stand-in has print, a wrong shape, or is not standing on the surface.
3. Read the stand-in's bounding box in pixels (tight).
4. `python engine/proxy.py --plate gen.jpg --product our_front.png --box x0,y0,x1,y1 --out out.jpg` (`--spec 0.5` carries the stand-in's real highlights; `--strength 0.9` how much shading reaches the print).
5. Check the self-test's guarantees by eye on the real image: the scene's shadow untouched, the print's contrast kept, no white stand-in edge showing, the pack's own colour intact.
6. Limits: the stand-in must match our render's view (front render for a front stand-in). If the model drew it at 3/4, use a 3/4 render or reject.

## Where it goes
Hyper-real scenes stay optional (owner rule 4 in `SKILL.md`) and out of decks unless the owner picks one by name (rule 5).
