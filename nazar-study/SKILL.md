---
name: nazar-study
description: Nazar Studio's visual back-engineering kit. Use to learn from the best work before making anything - product and still-life photographers, studios, cinematographers, painters, packaging and Behance case studies - by measuring references (engine/look.py - blacks, clipping, contrast, saturation, shadow and highlight colour lean, light falloff, vignette, grain, sharpness, visual weight, empty space, palette), reading their light by eye (shadow edges, highlight shapes, catchlights, terminator), writing a recipe card per reference and a target look for the set, then checking our own output against that target. Archives, masters' practices and research papers included. Pair with nazar-shoot (shots), nazar-story (case studies) and nazar-art-direction (briefs).
---

# Nazar study (visual back-engineering)

Read `../nazar-core/SKILL.md` first. **The person's prompt leads.** This kit is the research step done with a camera person's eye: before we light, prompt or lay out anything, we take apart how the best did it and turn that into numbers and rules we can brief and check. It serves other kits; it never makes the deliverable itself.

## Rules
1. **Study, never copy.** References are data. Their pixels never enter our work; we take the *decision* (light from where, how hard, how much air), not the image. Name a master's practice; never ask a model to imitate a living artist by name (`../nazar-prompts/SKILL.md` rule 9).
2. **Primary first.** Museum records, the photographer's own archive, the film itself, the studio's own case page outrank blog roundups (`references/archives.md`). Tag every finding as in `../nazar-core/references/research_path.md`.
3. **6 to 20 references per target look,** from at least 3 different makers, so the target is a practice and not one picture. Fewer than 6 is a moodboard, not a target.
4. **Numbers and eyes together.** `look.py` measures what can be measured; `references/reading_light.md` covers what only an eye reads (shadow-edge hardness, number of lights, highlight shape). A recipe card has both.
5. **Every reference earns one sentence:** what it does that ours should do, in practical terms ("one large soft source high camera-left; shadows 1 stop under; blacks held at about 12; 40% empty space"). If you can't write it, drop the reference.
6. **Close the loop.** After making, run `look.py compare` against the target and fix the two biggest gaps, then look again. The target is a range, not a point: inside the range is done.
7. **Credit and rights.** Record maker, title, year, holder and licence for every reference (`templates/recipe_card.md`). Open-access (CC0) items may be shown in a moodboard; everything else stays private study.

## Workflow
| Step | Do | Output |
|---|---|---|
| 1 | Name the job and what to learn: a pack shot, a scene, a film look, a case-study structure | one line |
| 2 | Pull references from the archives, at least 3 makers (`references/archives.md`, `references/masters_still_life.md`, `references/cinema_light.md`) | `study/refs/` with source in each filename |
| 3 | Measure: `python engine/look.py set study/refs -o study/look` | `set.json`, `set.md`, a look sheet per image, contact sheet |
| 4 | Read the light by eye on each (`references/reading_light.md`) and write a recipe card (`templates/recipe_card.md`) | `study/cards/*.md` |
| 5 | Write the target: the set's shared words, the numeric ranges, the 5 rules we take, the 3 things we refuse | `study/TARGET.md` |
| 6 | Hand the target to the making kit: `nazar-shoot` (shot spec for `shotplan.py`, plate prompt, grade), `nazar-story` (case-study flatplan), `nazar-art-direction` (brief) | spec / prompt / flatplan |
| 7 | After making: `python engine/look.py compare ours.jpg study/look/set.json`; fix the two biggest gaps; repeat | gap list, before/after |

For a case study, the teardown is structural, not tonal: `references/teardown.md` §3 (panel count, beats, devices, text share, cover type).

## Engine
`engine/look.py` (numpy + Pillow): `card <img>`, `set <folder>`, `compare <ours> <set.json>`, `--selftest` (known answers: light falloff side, warm cast, grain sigma, clipping share, weight centroid, empty space, compare flags). On Windows set `PYTHONUTF8=1`.

## Files
- `references/reading_light.md`: reading light from a picture: the eight clues, hardness, number of sources, colour of shadows, reflections, what a model gets wrong
- `references/teardown.md`: back-engineering protocols for a still, a film scene, a pack shot and a Behance case study; the recipe card fields
- `references/masters_still_life.md`: the product and still-life lineage (painters to studio photographers), each with the practice to take and where to study it
- `references/cinema_light.md`: cinematographers' and painters' light, translated to product work
- `references/archives.md`: where to look (open-access museums, photographers' archives, ad archives, film-still libraries, packaging and case-study galleries) and their rights
- `templates/recipe_card.md`: one card per reference
- `LESSONS.md`: what real jobs taught
