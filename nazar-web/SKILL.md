---
name: nazar-web
description: Nazar Studio's brand website kit. Use for brand sites, landing pages, portfolio and case-study sites, and the web expression of an identity: sitemap and page structure, content-first wireframes, design tokens, responsive type scales, art direction on the web, motion, accessibility, performance basics and developer handoff.
---

# Kaif web

Read `../nazar-core/SKILL.md` first. A brand site is the identity *in use*: it should feel unmistakably like the brand, load fast, work for everyone, and make the next step obvious.

## Rules
1. **Content first.** Real copy and real images drive the layout. No lorem ipsum in reviews. Never the default AI site: no purple/indigo gradients, no Inter-by-default, no centred hero plus three icon cards, no glassmorphism, no "New" pill badges (`../nazar-core/references/ai_tells.md` §1–3).
2. **One job per page.** Every page has one primary action.
3. **Tokens, not one-offs.** Colour, type, spacing, radius and motion live as tokens shared with the brand system [SRC].
4. **Accessible by default:** WCAG 2.2 AA contrast, keyboard use, focus states, alt text, reduced motion.
5. **Fast:** optimised images, few fonts and weights, no heavy effects without a reason.
6. **Art-directed, not templated.** One or two signature moments (a hero interaction, a scroll story, a cinematic section) that only this brand would do.

## Workflow
| Phase | Do | Output |
|---|---|---|
| 1 | Intake (`references/intake.md`) | `SPEC.md` |
| 2 | Audit and research: current site, competitors, analytics if available, user goals | `research/web/` |
| 3 | Structure: sitemap, user journeys, page outlines (`references/structure.md`) | sitemap, outlines |
| 4 | Content-first wireframes (low fidelity, real copy) | wireframes |
| 5 | Visual system on the web: tokens, type scale, grid, components (`references/system.md`) | design tokens, UI kit |
| 6 | High-fidelity design: 3 key pages, then the rest; the signature moments | designs |
| 7 | Handoff and QA (`references/handoff.md`) | spec, assets, QA report |

## Files
- `references/intake.md`: questions
- `references/structure.md`: sitemap, page types, landing page anatomy, copy rules
- `references/system.md`: tokens, responsive type, grid and breakpoints, components, art direction, motion on the web
- `references/handoff.md`: accessibility, performance, SEO basics, developer handoff, QA
