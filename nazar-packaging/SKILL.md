---
name: nazar-packaging
description: Nazar Studio's packaging kit. Use for product packaging, labels, pouches, cartons, bottles, tins, gift boxes, range and SKU systems, shelf strategy, structural choices, mandatory panels, and print production (colour management, CMYK and Pantone, substrates, finishes, preflight, proofing, press checks). For structure, dielines and MVP drafts on the dieline, pair it with nazar-dieline.
---

# Kaif packaging

Read `../nazar-core/SKILL.md` first. Structure, dielines and drafting art onto the dieline live in `../nazar-dieline/` (this kit decides what the pack says and how it looks; that kit decides its shape and where everything sits). Packaging is the brand in the customer's hand: it has to win at shelf distance in 2 seconds, then reward up close. Production is half the job. A beautiful pack that prints muddy, or a barcode that won't scan, is a failed job.

## Rules
1. **Shelf first, then hand.** Design for findability (it's found when sought) and visibility (it catches the eye) among real competitors, then for the detail up close [SRC].
2. **A brand block plus variant clarity.** A consistent brand block across the range, and one variant cue that never breaks it.
3. **The product is the hero.** Windows, real colour, real form. Graphics serve the product, not the other way round. No generated product shots or "lifestyle" renders: real photography or honest illustration (`../nazar-core/references/ai_tells.md` §4).
4. **Front of pack: less.** Brand → product name → variant → one key benefit. Everything else goes on the back or side.
5. **Keep known assets on a refresh.** Don't throw away what shoppers recognise (Tropicana's 2009 redesign was reportedly reversed after a sales drop) [SRC].
6. **The printer and converter are the final authority.** Get their spec before final artwork.
7. **Legal text comes from the client.** Never invent claims, certifications or nutrition data.
8. **No AI renders, no fake photography.** Concepts are flat dielines and spec sheets; realistic visuals use licensed mockups or real prototype photos.

## Workflow
| Phase | Do | Output |
|---|---|---|
| 1 | Intake (`references/intake.md`) | `SPEC.md` |
| 2 | Shelf research: store visits or photos, the competitor shelf, category codes (`references/shelf.md`) | `research/pack/` |
| 3 | Range architecture and the information hierarchy (`references/system.md`) | architecture sheet |
| 4 | Concepts: 3 routes drafted on a real dieline with the `nazar-dieline` engine (art mode), shown flat, folded and in a shelf line-up (core `ideation.md`) | route boards |
| 5 | Structure and substrate choice with the converter (`references/structure.md`, `../nazar-dieline/`) | structure spec |
| 6 | Artwork: front, back, sides, mandatory panels (`references/system.md` §4). Hand-drawn art and lettering: draw, then trace with `../nazar-core/engine/trace.py` (`../nazar-logo/references/trace.md`), multi-tone with `--levels` | artwork files |
| 7 | Production: colour, finishes, preflight, proofs (`references/production.md`) | print-ready PDFs |
| 8 | Prototype and test: a physical mock-up, the shelf test, a scan test (`references/qa.md`) | test notes |
| 9 | Press check, handover, the range template for future SKUs | `assets/packaging/` |

## Files
- `references/intake.md`: questions in 3 rounds
- `references/shelf.md`: shelf research, category codes, findability vs visibility
- `references/system.md`: range architecture, front-of-pack hierarchy, variant systems, back of pack and mandatory panels
- `references/structure.md`: formats, substrates, sustainability, structural ideas
- `references/production.md`: colour management, CMYK and Pantone, finishes, dielines, preflight, proofing, press check
- `references/qa.md`: packaging QA and tests
