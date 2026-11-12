---
name: nazar-backdrops
description: Nazar Studio's backdrops kit. Use to turn a brand book or brand guidelines into a pack of static backdrops for routine, non-festive posting - dark and light versions of the feed post (4:5, 1:1, 3:4), carousel cover/text/image/end slides, story, reel cover, LinkedIn, X, YouTube thumbnail, highlight covers and avatar - each with a guide overlay showing the safe zones. Extracts tokens from the guidelines, asks the intake, renders the pack with the shared engine, and hands it off as editable templates.
---

# Kaif backdrops

Read `../nazar-core/SKILL.md`, `../nazar-core/references/kaif.md` and `../nazar-core/references/ai_tells.md` first. Then this.

A backdrop is the **static layer** of a routine post: the background, the edge device, the logo slot, the handle, the counter and the zones where content goes. It doesn't change from post to post; the content layer (headline, photo, number) changes every day. Getting the static layer right once is what makes 300 ordinary posts a year look like one brand. Karl Gerstner called this designing *programmes instead of solutions* [ARCH: Gerstner, *Designing Programmes*, 1964].

Festive, launch and campaign artwork is out of scope; those are one-offs (`nazar-social`, `nazar-ooh`).

## Rules
1. **The book's tokens, not the book's pages.** Every colour, typeface, logo file and device traces back to the guidelines (`references/extract.md`); if the book doesn't say, ask. But the book is a guide: backdrops are designed for the feed and for what the posts will say, never by shrinking the book's page layouts onto a 1080 canvas.
2. **One skeleton, every format.** The anchor corner, margin ratio, edge device and handle position stay put across 4:5, 1:1, story and the rest, so the brand reads before the content does (`references/anatomy.md`).
3. **Dark and light are one layout.** The modes swap colour only, never position. An accent mode is allowed for covers and quotes if its contrast passes.
4. **Quiet enough to carry anything.** The backdrop takes ≤ ~15% of the canvas. It's a frame, not a poster. If it competes with a headline, remove something.
5. **Asymmetric and flat.** Anchor to a corner and an edge, not the centre (circles excepted). Flat brand colour. No glows, no gradients behind type, no glass: run `ai_tells.md`.
6. **Safe zones are law.** The 3:4 grid crop, story and reel UI zones, the avatar circle and the YouTube timestamp are all kept clear (`references/formats.md`).
7. **Editable handoff.** PNGs alone aren't a system. Deliver what the team actually edits in: Figma components, a Canva brand template with locked layers, or layered files (`references/handoff.md`).

## Workflow
| Phase | Do | Output |
|---|---|---|
| 1 | Intake (`references/intake.md`) | `SPEC.md` → "Backdrops" |
| 2 | Extract tokens from the book or guidelines (`references/extract.md`) | `nazar-core/engine/brand.json` + `research/backdrops/extraction.md` |
| 3 | Fix the skeleton: anchor, margin, edge device, handle, counter (`references/anatomy.md`); confirm it in one sentence | skeleton note |
| 4 | Choose the pack (`references/set.md`), edit `templates/backdrops.json`, render: `python engine/backdrops.py templates/backdrops.json` | `exports/backdrops/*.png`, `*_guide.png`, `sheet.png` |
| 5 | QA: `references/qa.md`, `ai_tells.md`, the phone test (`references/craft.md`) | fixes + QA report |
| 6 | Handoff (`references/handoff.md`) | editable templates, usage sheet, named files |

## Files
- `references/intake.md`: the questions, with options and a recommended pick
- `references/extract.md`: reading a brand book into tokens; conversions, licences, the extraction log
- `references/formats.md`: canvases, crops and safe zones per platform, with sources
- `references/anatomy.md`: what a backdrop is made of, why consistency works (research), archive precedents
- `references/set.md`: the full pack (formats × roles × modes) and what each role is for
- `references/craft.md`: phone legibility, contrast, dark-mode viewing, compression, export
- `references/handoff.md`: Figma / Canva / layered delivery, naming, the usage sheet
- `references/qa.md`: kit-specific checks
- `templates/backdrops.json`: the pack config
- `engine/backdrops.py`: the renderer (uses `../nazar-core/engine/lib.py` and its `brand.json`)
