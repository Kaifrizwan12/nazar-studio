---
name: nazar-shoot
description: Nazar Studio's product shoot kit. Use for product shots, pack-in-scene images, hyper-real scenarios (shelf, kitchen, rooftop, street), flat-lays, Gemini / Nano Banana product imagery and flavour-cycle loops when there is no real photo shoot. Plans the shot before any prompt with engine/shotplan.py (lens, depth of field, perspective, light hardness, shadow geometry, glare on the pack via the family of angles, floor reflection via Fresnel, colour-temperature clashes -> diagram, plate prompt, composite args); three routes - empty plate, proxy stand-in (engine/proxy.py keeps the model's real shadows and reflections and puts our exact pack pixels in) and textures. Hybrid rule - AI may make only empty background plates and textures, stamped "AI-generated background plate"; the product is always the real artwork render, seated into the plate by engine/composite.py (perspective, contact and cast shadow, light wrap, tone and black-level match, sheen, bend, edge occlusion, shelf-lip re-lay, grain, lens, optional chromatic aberration). Pair with nazar-packaging for the renders and nazar-prompts for the plate prompts.
---

# Kaif shoot

Read `../nazar-core/SKILL.md` and `../nazar-core/references/kaif.md` first. The pack renders come from `nazar-packaging` / `nazar-dieline`; plate prompts follow `nazar-prompts`. This kit decides what the shot says, briefs the empty plate, and seats our exact render into it so it reads as a photograph.

## Owner rules (learned on real jobs, never skip)
1. **The product is always ours.** AI makes only empty plates and textures. Never let a model draw, redraw or "improve" the pack: its type, logo and print must be our pixels.
2. **Stamp every AI plate.** Output carries "AI-generated background plate · product is the real artwork render · concept" until the client approves in writing (`nazar-prompts` disclosure). Licensed real photo plates may drop the stamp; say which it is.
3. **Real look or nothing.** The owner rejects cartoony, glossy, "AI slop" looks at once: floating packs, pale ghost shadows, creaseless film, blown highlights eating type, lone dead-centre product, palm-shadow or beige-plinth stock plates, poster-bright colour. "Still looks AI" means the physics is wrong, not the strength: name what the real object does there and model that.
4. **Hyper-real scenes are parked unless asked.** Do not start scene work on your own initiative; offer it in one line.
5. **AI scene photos stay out of decks** unless the owner picks one by name. Decks show clean pack art, flats and views. A picked shot gets one page with its own layout device, never a grid of scenes.
6. **No other brands in frame.** Plates are briefed brand-free; no competitor packs, logos or shop names. English only in kit copy.
7. **Show before commit.** Contact sheet first, the self-check numbers beside it, then the owner's notes.

## Realism gates (a shot ships only if it passes all six)
The owner's verdict on a five-shot set was "only the hand and the hanging are ok, the others very very bad". My QA had compared each attempt with the previous attempt, so every step looked like progress. These gates compare against the world, not against yesterday:
1. **Beside a real photo, at 100%.** Put the composite next to a real photograph of the same kind of moment (a real basket, a real hand) at full size. If you can name one thing the real one does that ours doesn't, it fails.
2. **One or two packs, large in frame.** Every extra pack is another chance to be wrong. Multi-pack AI scenes (crates, stoves, shelves of our packs) failed every time; the drying line passed because the packs hang flat, in one light.
3. **The whole moment, not a crop.** The plates that passed show a person (arm, hand, clothes, aisle) and the pack as one object in their life. Packs filling a tight crop read as a pasted product shot.
4. **Motivated gesture.** Would the hand do this with no camera there? Tearing open, carrying a basket: yes. Raising a snack to the sky: no.
5. **Flat art only where the pack is flat.** Hanging, flat-lay, against a wall. A pillow bag or a full pouch in a hand needs the stand-in's real creases (`detail`, `displace`) or a real 3D render.
6. **Zoom on every edge and every overlap.** Fruit, rims and fingers in front must be solid (no see-through), no dark rims, no stand-in left in mesh, gaps or corners, no print painted on the floor or the rim.

## Workflow
| Step | Do | Output |
|---|---|---|
| 1 | Story first: who, where, what moment, why this product is in it (`references/scenes.md`) | one-line scene brief |
| 2 | Learn the target look from 6-20 references (`../nazar-study/`: `look.py set`, recipe cards) | `TARGET.md` + `set.json` |
| 3 | Plan the shot before any prompt: camera, lens, lights, reflections (`references/shot_plan.md`); `python engine/shotplan.py plan spec.json -o plan/`; clear every warning | plan, diagram, plate prompt, composite args |
| 4 | Choose the route (`references/gemini_routes.md`): A empty plate (default), B proxy stand-in, C textures; write the master prompt from the plan, translate per model (`../nazar-prompts/`) | prompt + reference roles |
| 5 | Generate, kill on physics first, read the kept plate's real light (`look.py card`, eight clues); re-plan to the plate if it disagrees | the plate |
| 6 | Render the product at the plate's camera angle (front for eye level, top for flat-lay) | RGBA render |
| 7 | Seat it. A: `python engine/composite.py --plate p.jpg --product a.png --at x,y --height px --light dx,dy --persp p [--relay y0,y1] --out o.jpg` (light and persp from the plan or the plate). B: `python engine/proxy.py --plate gen.jpg --product a.png --quad x,y,... --occlude --clip [--key green] --out o.jpg`; several packs: front pack first, pass `canvas=` and `quad_grow=0` from Python | composite |
| 8 | Camera pass and QA (`references/camera_pass.md`); `look.py compare o.jpg target/set.json`, fix the two biggest gaps | QA notes |
| 9 | Look at it yourself at 100% and phone size, fix the biggest physics miss, repeat; then show | contact sheet |
| 10 | Motion, if asked: flavour-cycle loop (`references/motion.md`) | MP4 + GIF + strip |

## Engine
`engine/composite.py` (numpy + Pillow only). `Scene(plate).seat(...).relay(...).finish(out)` or the CLI. `python engine/composite.py --selftest` builds a synthetic plate and two products, writes `examples/composite_demo.jpg`, and reports PASS/FAIL against the QA list (grounding, shadow direction and falloff, black level, edge fringe, light wrap, grain, print sharpness, re-lay, stamp, chromatic aberration limits). On Windows run `export PYTHONUTF8=1` (bash) first.

`engine/flavour_cycle.py` (numpy + Pillow + ffmpeg via imageio-ffmpeg or the PATH): the flavour-cycle film for any range. Input is a plain JSON job (`items`: name, pack PNG, tint hex or `auto`, marquee label; `brand`: title, tagline, sign, fonts (bundled OFL fallback), paper, ink; `options`: aspect (4:5, 1:1, 9:16, 16:9, any WxH), platform preset, fps, style `cinematic` (36-frame shots, 12-frame crisp light-edge wipe) or `snap` (14-frame hard cuts, faster second round), rounds, loop, endcard, music, bpm, gif, webp) or the CLI (`--pack a.png --pack b.png --title ...`). `--stills` renders the review sheet before any video; a render writes MP4 + GIF (+ WebP) + strip + `_qa.json` (timing, platform limits, WCAG flash check). `--platforms` lists the presets. `python engine/flavour_cycle.py --selftest` (synthetic pouches) and `python engine/test_flavour_cycle.py` (or pytest) check timing, sizes, the no-blend wipe, contact shadow, end card, pixel-exact loop and flash safety. Example job (demo only, the owner's stand-in range): `examples/flavour_cycle_demo_job.json`.

## Engine (planning and proxy)
`engine/shotplan.py` (numpy + Pillow): `plan spec.json -o dir` writes `plan.json`, `plan.md`, `plan_diagram.png` (top and side view, glaring lights in red) and `plate_prompt.txt`; `example` prints a spec; `--selftest` checks FOV, depth of field, hardness, Fresnel, shadow direction, glare on gloss vs matte, the glare fixer, two-shadow and mired warnings, signed perspective. `engine/proxy.py`: fits our render into the model's stand-in, carries its shading, light colour and specular highlights onto our print, leaves the model's shadows and reflections untouched, matches grain, stamps. Hand-held and basket shots: `occlude` keeps fingers, rims and fruit in front; `quad` fits four corners; `clip` covers the stand-in's own edge; `KEY="green"` keys a #00B140 stand-in (use it on warm plates where shaded white looks like shaded skin; white works on neutral fluorescent or daylight plates). Python options: `canvas` (multi-pack: every test reads the untouched plate, earlier packs are never overwritten), `detail` (the stand-in's creases on our print), `displace` (the print bends over each crease), `soften` (match the plate's lens), `match` (calm saturation and the photo's black floor), `recolor_key(img, rgb, plate=, region=)` for leftover stand-in green. `--selftest` checks shading transfer, shadow untouched, print contrast kept, no stand-in edge, hue intact, fingers and banana green in front, no dark rim from transparent pixels.

## Files
- `references/shot_plan.md`: plan before the prompt: the twelve steps, the spec, reading the planner's output
- `references/gemini_routes.md`: empty plate, proxy stand-in and texture routes; the eleven-slot master prompt; reference roles; iterating like a photographer
- `references/research_realism.md`: papers on perceived realism, composites, forensic shadows and reflections, generative geometry
- `references/plates.md`: briefing empty plates, light direction, perspective and camera height, what to reject
- `references/camera_pass.md`: light wrap, tone match, black lift, halation, lens, grain, chromatic aberration, and the QA checklist
- `references/scenes.md`: story-driven scenes with hands, sky and local life; what to show and never show
- `references/motion.md`: flavour-cycle loops (beat, cuts, push-in, end card, exports, platform presets, timing, loops, flash safety, web formats)
- `references/research_flavour_cycle.md`: dated sources for platform specs, pacing, loops, flash safety and GIF/MP4/WebP
- `engine/flavour_cycle.py`, `engine/test_flavour_cycle.py`: the film engine and its tests
- `examples/flavour_cycle_demo_job.json`: demo job (owner's stand-in range; skipped if the packs are absent)
- `references/research.md`: dated sources behind the rules
- `LESSONS.md`: what failed on real work
