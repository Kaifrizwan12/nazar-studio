---
name: nazar-core
description: Shared foundation for every Nazar Studio kit (brand book, strategy, logo, packaging, social, OOH, motion, web, art direction, pitch). Holds who Kaif is, the archive-backed research method, the masters' practices, the design QA checklist, sources, and the local SVG→PNG/PDF engine. Load it whenever any nazar-* skill is used.
---

# Kaif core

Every `nazar-*` kit builds on this folder. Read it first, every time.

## The studio rules (all kits)
1. **Read `references/kaif.md`.** It covers who Kaif is, his taste, how he reviews, what he rejects, and the risks to flag.
2. **Ask before building.** Each kit has its own intake: 3 rounds at most, every question with options and a recommended pick first. Facts (names, contacts, prices, legal text) are asked as plain text, never invented.
3. **Research before concept.** Follow `references/research_path.md`. Tag findings [ARCH] / [SRC] / [KNOWN] / [TREND] / [IDEA]. No reference, no decision.
4. **Ideas before looks.** Generate concepts with `references/ideation.md` (at least 3 methods), then cluster them into territories and 3 routes.
5. **Judge like the masters.** `references/masters.md`: meaning, distinctiveness, the blur and shelf tests, remove before adding.
6. **No AI slop.** No AI-generated or stock imagery in deliverables. Build from the brand's own parts, real places, real type and real data. Mockups are spec sheets unless a licensed mockup or real photo is used.
7. **The client's logo is sacred.** Use exact artwork, and never redraw it unless the job *is* the logo (`nazar-logo`).
8. **Lock before you build.** The name, tagline and core idea are locked in writing before production. Changes after that cost a rebuild, so say so.
9. **QA before showing.** `references/qa_design.md` (methods, checks, P1/P2/P3 triage), plus the kit's own QA list. Report what you fixed.
10. **Systems in code.** Grids, tokens and heading positions are set once (in `engine/brand.json`), so fixes are global.
11. **Credit and license.** Fonts, images, archives and maps are all recorded. Nothing non-commercial ships to a client.

## Folder map
| Path | What |
|---|---|
| `references/kaif.md` | Kaif's profile, taste, review habits, risks to flag |
| `references/research_path.md` | The eight research passes, evidence tags, the moodboard rule |
| `references/masters.md` | Practices of the masters, each with how to apply it |
| `references/ideation.md` | Concept methods: reframing, word→image collisions, semiotics, lateral thinking, SCAMPER, matrices, analogy, kill list |
| `references/qa_design.md` | Design QA: 10 ways of looking, ~90 checks, triage |
| `references/sources.md` | Archives and references by topic |
| `references/studio_flow.md` | How every Kaif job runs: brief → research → routes → build → QA → handover |
| `templates/research_log.md` | Research log format |
| `templates/brand.json` | Engine config template |
| `engine/` | The renderer: outlined type (harfbuzz, RTL-safe), exact logos, OSM maps, PNG + PDF + contact sheet |

## Which kit for which job
| Job | Kit |
|---|---|
| Positioning, naming, tagline, architecture, messaging | `nazar-strategy` |
| A new mark, wordmark or refresh | `nazar-logo` |
| The identity system and brand book | `nazar-brand-book` |
| Packs, labels, ranges, print production | `nazar-packaging` |
| Instagram / TikTok / LinkedIn systems and content | `nazar-social` |
| Billboards, transit, vehicles, walls, screens, guerrilla | `nazar-ooh` |
| Logo animation, motion system, video idents | `nazar-motion` |
| Brand websites and landing pages | `nazar-web` |
| Photography, illustration and icon direction | `nazar-art-direction` |
| Proposals, pricing, presenting, feedback, contracts, handover | `nazar-pitch` |
A full identity job usually chains: pitch → strategy → logo → brand book → (packaging / social / OOH / motion / web / art direction) → pitch (handover).
