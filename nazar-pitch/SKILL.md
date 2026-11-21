---
name: nazar-pitch
description: Nazar Studio's client process kit. Use for discovery calls, scoping, proposals and value-based pricing (three options), contracts and terms (deposit, revisions, kill fee, IP transfer), timelines, presenting work, handling feedback, change requests, handover and the case-study / Behance write-up.
---

# Kaif pitch (client process)

Read `../nazar-core/SKILL.md` first. Good process protects the work: a clear scope, a fair price, a signed agreement and a decision-maker make better design possible. This kit isn't legal advice. Contracts should be reviewed by a lawyer in the client's jurisdiction.

## Rules
1. **A value conversation before the price** (Blair Enns): understand what the outcome is worth to the client before proposing [SRC].
2. **Three options that differ in outcome and approach,** not three sizes of the same deliverables [SRC].
3. **Nothing starts without a signed agreement and a deposit.**
- **Decks and proposals pass the AI test too.** No template slides, gradient title cards or "unlock your potential" copy; clients read them as generated (`../nazar-core/references/ai_tells.md`).
4. **One decision-maker,** named in the agreement.
5. **Revision rounds are limited and defined;** extra work goes through a change request.
6. **IP transfers on full payment;** licensed elements (fonts, images, music) are listed separately.
7. **Present with reasoning and a recommendation;** never ask "do you like it?"

## Workflow
| Phase | Do | Output |
|---|---|---|
| 1 | Discovery call (`references/discovery.md`) | call notes |
| 2 | Proposal with 3 options (`references/proposal.md`) | proposal PDF (built with the core engine) |
| 3 | Agreement and deposit (`references/contract.md`) | signed agreement |
| 4 | Kick-off: timeline, approvals, access, inputs | kick-off notes, `SPEC.md` |
| 5 | Presentations and feedback rounds (`references/presenting.md`) | decisions recorded |
| 6 | Handover and close (`references/handover.md`); package it with `engine/handover.py` (dry run first) | versioned client / portfolio / press folders with README, checksums and zips; invoice; case study |

## Files
- `references/discovery.md`: the discovery call questions and red flags
- `references/proposal.md`: proposal structure, value-based three-option pricing, timelines
- `references/contract.md`: the key terms to include (from the AIGA Standard Form of Agreement and common practice)
- `references/presenting.md`: presenting work, feedback, change requests
- `references/handover.md`: handover pack, closing the project, case study and Behance write-up
- `engine/deck.py`: the deck engine (SVG pages, outlined type, fit-or-fail and overlap guards, compose helpers, PDF, contact sheet, Behance panels + covers); `engine/example_deck.py` is a 6-page demo. Case-study sequencing lives in `../nazar-story/`
- `engine/handover.py`: the delivery packager. A JSON manifest (groups, items, and targets: client / portfolio [Behance, Dribbble, site] / press / social) becomes:
  - versioned folders (`v02_YYYY-MM-DD`) with clean, numbered names that are safe on Windows, macOS and Linux
  - covers at each platform's sizes
  - `README.txt`: contents, formats, colour, fonts and licences, concept vs press-ready, AI disclosure
  - `SHA256SUMS.txt`, and a zip with a size report

  It fails on missing or stale sources (declared inputs, build marker). It never deletes: changed or removed files go to `_parked/<timestamp>/`. `--dry-run` prints what would be added, changed or parked, and which panels to re-upload. `diff` compares two releases. Self-check: `python engine/handover.py --selftest`, or `python engine/test_handover.py`
- `examples/handover_manifest.json`: a generic manifest; it runs on the deck demo's output. `examples/handover_manifest_demo_bagh.json` is DEMO ONLY: it reproduces one real job's client and Behance folders
- `references/research_handover.md`: dated sources (2026-11-21): handover practice, file naming and path limits, zip UTF-8 names, Behance and Dribbble specs, PDF/X-4, font licences, AI disclosure
- `LESSONS.md`: what real jobs taught this kit
