---
name: nazar-shoot
description: Nazar Studio's product shoot kit. Use for product shots, pack-in-scene images, hyper-real scenarios (shelf, kitchen, rooftop, street), flat-lays and flavour-cycle loops when there is no real photo shoot. Hybrid rule - AI may make only empty background plates and textures, stamped "AI-generated background plate"; the product is always the real artwork render, seated into the plate by engine/composite.py (perspective, contact and cast shadow, light wrap, tone and black-level match, sheen, bend, edge occlusion, shelf-lip re-lay, grain, lens, optional chromatic aberration). Pair with nazar-packaging for the renders and nazar-prompts for the plate prompts.
---

# Kaif shoot

Read `../nazar-core/SKILL.md` and `../nazar-core/references/kaif.md` first. The pack renders come from `nazar-packaging` / `nazar-dieline`; plate prompts follow `nazar-prompts`. This kit decides what the shot says, briefs the empty plate, and seats our exact render into it so it reads as a photograph.

## Owner rules (learned on real jobs, never skip)
1. **The product is always ours.** AI makes only empty plates and textures. Never let a model draw, redraw or "improve" the pack: its type, logo and print must be our pixels.
2. **Stamp every AI plate.** Output carries "AI-generated background plate · product is the real artwork render · concept" until the client approves in writing (`nazar-prompts` disclosure). Licensed real photo plates may drop the stamp; say which it is.
3. **Real look or nothing.** The owner rejects cartoony, glossy, "AI slop" looks at once: floating packs, pale ghost shadows, creaseless film, blown highlights eating type, lone dead-centre product, palm-shadow or beige-plinth stock plates, poster-bright colour. "Still looks AI" means the physics is wrong, not the strength: name what the real object does there and model that.
4. **Hyper-real scenes are parked unless asked.** Do not start scene work on your own initiative; offer it in one line.
5. **AI scene photos stay out of decks** unless the owner picks one by name. Decks show clean pack art, flats and views.
6. **No other brands in frame.** Plates are briefed brand-free; no competitor packs, logos or shop names. English only in kit copy.
7. **Show before commit.** Contact sheet first, the self-check numbers beside it, then the owner's notes.

## Workflow
| Step | Do | Output |
|---|---|---|
| 1 | Story first: who, where, what moment, why this product is in it (`references/scenes.md`) | one-line scene brief |
| 2 | Brief the empty plate: camera height, lens, light direction, the empty spot where the product will stand (`references/plates.md`) | plate prompt + plate notes |
| 3 | Render the product at the plate's camera angle (front for eye level, top for flat-lay) | RGBA render |
| 4 | Seat it: `python engine/composite.py --plate p.jpg --product a.png --at x,y --height px [--angle] --relay y0,y1 --out o.jpg` | composite |
| 5 | Camera pass and QA checklist (`references/camera_pass.md`); run `--selftest` after any engine change | QA notes |
| 6 | Look at it yourself, fix the biggest physics miss, repeat; then show | contact sheet |
| 7 | Motion, if asked: flavour-cycle loop (`references/motion.md`) | MP4 + GIF + strip |

## Engine
`engine/composite.py` (numpy + Pillow only). `Scene(plate).seat(...).relay(...).finish(out)` or the CLI. `python engine/composite.py --selftest` builds a synthetic plate and two products, writes `examples/composite_demo.jpg`, and reports PASS/FAIL against the QA list (grounding, shadow direction and falloff, black level, edge fringe, light wrap, grain, print sharpness, re-lay, stamp, chromatic aberration limits). On Windows run `export PYTHONUTF8=1` (bash) first.

`engine/flavour_cycle.py` (numpy + Pillow + ffmpeg via imageio-ffmpeg or the PATH): the flavour-cycle film for any range. Input is a plain JSON job (`items`: name, pack PNG, tint hex or `auto`, marquee label; `brand`: title, tagline, sign, fonts (bundled OFL fallback), paper, ink; `options`: aspect (4:5, 1:1, 9:16, 16:9, any WxH), platform preset, fps, style `cinematic` (36-frame shots, 12-frame crisp light-edge wipe) or `snap` (14-frame hard cuts, faster second round), rounds, loop, endcard, music, bpm, gif, webp) or the CLI (`--pack a.png --pack b.png --title ...`). `--stills` renders the review sheet before any video; a render writes MP4 + GIF (+ WebP) + strip + `_qa.json` (timing, platform limits, WCAG flash check). `--platforms` lists the presets. `python engine/flavour_cycle.py --selftest` (synthetic pouches) and `python engine/test_flavour_cycle.py` (or pytest) check timing, sizes, the no-blend wipe, contact shadow, end card, pixel-exact loop and flash safety. Example job (demo only, the owner's stand-in range): `examples/flavour_cycle_demo_job.json`.

## Files
- `references/plates.md`: briefing empty plates, light direction, perspective and camera height, what to reject
- `references/camera_pass.md`: light wrap, tone match, black lift, halation, lens, grain, chromatic aberration, and the QA checklist
- `references/scenes.md`: story-driven scenes with hands, sky and local life; what to show and never show
- `references/motion.md`: flavour-cycle loops (beat, cuts, push-in, end card, exports, platform presets, timing, loops, flash safety, web formats)
- `references/research_flavour_cycle.md`: dated sources for platform specs, pacing, loops, flash safety and GIF/MP4/WebP
- `engine/flavour_cycle.py`, `engine/test_flavour_cycle.py`: the film engine and its tests
- `examples/flavour_cycle_demo_job.json`: demo job (owner's stand-in range; skipped if the packs are absent)
- `references/research.md`: dated sources behind the rules
- `LESSONS.md`: what failed on real work
