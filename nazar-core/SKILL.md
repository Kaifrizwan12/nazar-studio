---
name: nazar-core
description: Shared foundation for every Nazar Studio kit (brand book, strategy, logo, packaging, dieline, illustration, type, colour, prompts, social, OOH, motion, web, art direction, pitch). Holds who Kaif is, the archive-backed research method, the masters' practices, the design QA checklist, sources, and the local SVG→PNG/PDF engine. Load it whenever any nazar-* skill is used.
---

# Kaif core

Every `nazar-*` kit builds on this folder. Read it first, every time.

## Fast path for a brand-asset job (social slides, posts, banners)
Two commands replace about ten, so a job reads less and calls less:
```
python nazar-core/engine/studio.py learn <their finished pieces folder> <out folder> [exact backdrop and logo files...]
python nazar-core/engine/studio.py check <your slides folder> <copy.json> <out folder>/pattern.json [sheet.jpg]
```
`learn` measures the archive (format, grounds, palette, accent, layout), writes the pattern and a prompt block. `check` runs contrast (on the accent type actually used), language, layout, copy lint, the pattern score and the QA measurements, and writes the QA sheet. `copy.json` is `{"slide.png": "all its text"}`. Then look at the sheet: concept and hierarchy are yours. The font question is `nazar-type/engine/font_match.py <one tight headline crop> "the words"`. To place the exact files, use `nazar-core/engine/place_asset.py` (backdrop to a format, logo on white paper with multiply): don't rewrite it. Skip any intake question the prompt already answered.

## The studio rules (all kits)
0. **The user's prompt leads.** Kits are add-ons: pull the pieces that serve the request (a rule, a checklist, an engine), skip the rest, and never let a kit's workflow override what was asked. If a kit and the prompt disagree, follow the prompt and mention the trade-off in one line.
1. **Read `references/kaif.md`.** It covers who Kaif is, his taste, how he reviews, what he rejects, and the risks to flag.
2. **Ask before building, but only for what the prompt doesn't already say.** If the person has given the brief, the files and the constraints, skip those questions and ask only what is missing. Each kit has its own intake: 3 rounds at most, every question with options and a recommended pick first. Facts (names, contacts, prices, legal text) are asked as plain text, never invented.
3. **Research before concept.** Follow `references/research_path.md`. Tag findings [ARCH] / [SRC] / [KNOWN] / [TREND] / [IDEA]. No reference, no decision.
4. **Ideas before looks.** Generate concepts with `references/ideation.md` (at least 3 methods), then cluster them into territories and 3 routes.
5. **Judge like the masters.** `references/masters.md`: meaning, distinctiveness, the blur and shelf tests, remove before adding.
6. **No AI slop, and no AI look.** No stock imagery; AI-generated imagery only with the client's written approval (disclosed, licences checked), and for complex scenes Claude may hand over a ready image prompt as an alternative to code drawing. Build from the brand's own parts, real places, real type and real data. Mockups are spec sheets unless a licensed mockup or real photo is used. Run the 30-second test in `references/ai_tells.md` on everything: no unexplained gradients or glows, no default fonts, no centred-everything skeletons, no "elevate".
7. **The client's logo is sacred.** Use exact artwork, and never redraw it unless the job *is* the logo (`nazar-logo`).
8. **Lock before you build.** The name, tagline and core idea are locked in writing before production. Changes after that cost a rebuild, so say so.
9. **QA before showing.** `references/qa_design.md` (methods, checks, P1/P2/P3 triage), plus the kit's own QA list. Report what you fixed.
10. **Systems in code.** Grids, tokens and heading positions are set once (in `engine/brand.json`), so fixes are global.
11. **Credit and license.** Fonts, images, archives and maps are all recorded. Nothing non-commercial ships to a client.
12. **Improve the kit from the work.** Every job is a test of the kit. Follow `references/improve.md`: when a rule, engine or checklist failed on real work, log it in `LESSONS.md` beside the kit, fix the kit itself only with the user's okay, and never put client names or private data in either.

## Folder map
| Path | What |
|---|---|
| `references/kaif.md` | Kaif's profile, taste, review habits, risks to flag |
| `references/research_path.md` | The eight research passes, evidence tags, the moodboard rule |
| `references/masters.md` | Practices of the masters, each with how to apply it |
| `references/ideation.md` | Concept methods: reframing, word→image collisions, semiotics, lateral thinking, SCAMPER, matrices, analogy, kill list |
| `references/qa_design.md` | Design QA: 10 ways of looking, ~90 checks, triage |
| `references/ai_tells.md` | What makes work look AI-made (colour, layout, type, images, copy, process), the 30-second test, sources |
| `references/sources.md` | Archives and references by topic |
| `references/improve.md` | How any Claude improves a kit from real work: what to log, when to patch, what never to record |
| `references/studio_flow.md` | How every Kaif job runs: brief → research → routes → build → QA → handover |
| `templates/research_log.md` | Research log format |
| `templates/brand.json` | Engine config template |
| `engine/` | The renderer: outlined type (harfbuzz, RTL-safe), exact logos, OSM maps, PNG + PDF + contact sheet |
| `engine/studio.py` | The fast path: `learn` (measure the archive, write the pattern and prompt block) and `check` (chain check and QA in one call) |
| `engine/place_asset.py` | Place exact files: a backdrop to a format (crop, never scale; a square to 4:5 is a labelled resample) and a logo on white paper (thresholded crop, multiply) |
| `engine/chain_check.py` | Run the engines in order on finished slides: colour (the accent type actually used, against its own ground), language, layout, copy lint, pattern score |
| `engine/qa_views.py` | The QA's measurable methods as a tool: sheet (full, squint, phone size), left edges, margins, headline-to-subline gaps, smallest text at phone width |
| `references/scenarios.md` | Seven scenarios, each with the prompt a real person writes, which kits run, and what is tested |
| `engine/trace.py` | Sketch → vector: hand drawings and lettering to clean Bézier SVG (variants, compare sheet, multi-tone `--levels`) for logos and package art |

## Which kit for which job
| Job | Kit |
|---|---|
| Positioning, naming, tagline, architecture, messaging | `nazar-strategy` |
| A new mark, wordmark or refresh | `nazar-logo` |
| The identity system and brand book | `nazar-brand-book` |
| Packs, labels, ranges, print production | `nazar-packaging` |
| Pack structure, dielines, board, windows, flexibles, MVP drafts on the dieline | `nazar-dieline` |
| Instagram / TikTok / LinkedIn systems and content | `nazar-social` |
| Static backdrops for routine posts (dark/light, every format) from a brand book | `nazar-backdrops` |
| Billboards, transit, vehicles, walls, screens, guerrilla | `nazar-ooh` |
| Logo animation, motion system, video idents | `nazar-motion` |
| Brand websites and landing pages | `nazar-web` |
| Photography, illustration and icon direction | `nazar-art-direction` |
| Drawing in code: spot illustrations, icons, patterns, pen-and-ink, math art | `nazar-illustration` |
| Choosing, sourcing and QA-ing typefaces (incl. Urdu/Nastaliq bilingual) | `nazar-type` |
| Building a palette (archive-sourced, print-safe, contrast-checked) | `nazar-colour` |
| AI image/video prompts, only with written client approval | `nazar-prompts` |
| Someone's own pattern (words, story, visual) from their pre-AI archive, to make any AI write/script/design like them | `nazar-voiceprint` |
| Proposals, pricing, presenting, feedback, contracts, handover | `nazar-pitch` |
A full identity job usually chains: pitch → strategy → logo → brand book → (packaging + dieline / social / OOH / motion / web / art direction) → pitch (handover).
