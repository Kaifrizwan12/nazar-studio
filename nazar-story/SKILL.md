---
name: nazar-story
description: Nazar Studio's case-study kit. Use to turn finished work (packaging, identity, campaign) into a continuous Behance-style story or a client presentation deck. It runs hook, insight, idea, system, applications, payoff, then the credits/contact page and thank-you, one idea and one layout device per page. Built on nazar-pitch/engine/deck.py, it renders numbered Behance panels and covers or a light PDF. Its guards fail the build on text overflow or overlapping images and warn when a device repeats.
---

# Kaif story (case studies)

Read `../nazar-core/SKILL.md` and `../nazar-core/references/kaif.md` first. The write-up side of a case study (what to say, credits, permissions) is in `../nazar-pitch/references/handover.md`. This kit decides the sequence and composition, and `../nazar-pitch/engine/deck.py` renders it. The research behind every rule is in `references/research.md` (dated sources).

## Intake (one message, options and a pick)
1. **Where will it live?** Behance (panels + cover, recommended) / client PDF / awards cut (8 panels or fewer).
2. **The one idea** in a sentence, and its proof image. Get a yes before page 1.
3. **The product list:** every SKU and format, each front and back, as exact render files. Ask which scene photo, if any, the owner has picked.
4. **Studio facts** for the contact page (name, mark file, founder, email, phone, social), as plain text. Never invent them.

## Rules
1. **The story order:** hook → brief/tension → insight → idea → system → applications → payoff → studio contact → thank-you (`references/sequence.md`). The insight gets its own page; the research comes before the solution.
2. **The first two panels carry the pitch.** 74% of viewing time goes to the first two screenfuls, and a curator gives a project about 5 s. Panel 1 is the hero product, full size, with no paragraph. Panel 2 states the idea or the brief in one line.
3. **One idea per page, readable in about 2 s at phone width:** one image, one line, under about 25 words. Put long argument in the project text, not in the panel.
4. **Every product front AND back is shown, once each.** Tick a SKU × side list. No pack image appears twice.
5. **Never repeat a layout device.** Each page declares its device in `d.page(body, device=...)`, and the build warns on a repeat. Treat a warning as a fail before you show anything.
6. **Vary composition, scale and colour.** Follow the rhythm hero > range > turn over > scale > detail > split > standing > dark. Change the ground colour at least every 3 pages, never put two dense pages side by side, and space out the big visual moments.
7. **Keep pack art clean.** No numbered callouts, arrows or labels on the pack. Explain the rules beside it.
8. **Real product only.** No AI scene photos unless the owner picked that one. Show the packs as true renders with soft, grounded shadows, never cartoon mockups (`../nazar-core/references/ai_tells.md`).
9. **Include a measured flats page:** every structure with its grams and its flat size in mm, and a note that the converter's dieline replaces each concept flat.
10. **The final image mirrors the hook:** the same product or colour, now in context or at a new scale.
11. **The studio contact page comes directly before thank-you,** using owner-supplied facts only. Credit once, at the end, never on every page.
12. **Behance specs:**
    - Panels: same width on every panel, 2880 × 1620 PNG (Behance shows 1400, up to 2800 in lightbox), each 10 MB or less, no folios.
    - Cover: 1616 × 1264, with 808 × 632 and 768 × 576 fallbacks. Use a product image with no text, subject central (Behance crops it), and repeat the cover image as panel 1.
    - GIFs go inside the project only. A film is embedded from a video host for full width.
13. **Show the contact sheet to the owner before shipping.** They flag issues by page number: fix that page, then hunt the same class of problem on every page.
14. English only. Never name other brands in panels or copy.

## Build
```
export PYTHONUTF8=1                      # Windows: also put the cairo DLL folder on PATH
python your_story.py                     # PDF + <name>_contact.jpg
BEHANCE=1 python your_story.py           # behance/<name>_behance_NN.png + 00_COVER_* + _behance_contact.jpg
```
A story script is short:
```python
import sys; sys.path.insert(0, ".claude/skills/nazar-pitch/engine")
from deck import Deck, couple, fan, toss, bleed
d = Deck("tokens.json", "out/story")           # colours, fonts, folio text: no brand hard-coded in the engine
b = d.img(bleed("hero_front.png", d.cache, 1100, 1080, 1250, 560, 560), d.W - 1100, 0, 1100, 1080)
b += d.tx("BRAND", 80, 120, 40)
d.page(b, device="hero bleed", folio=False)
...
d.build(cover="hero_front_on_colour.png")
```
`nazar-pitch/engine/example_deck.py` is a working 6-page demo built from nazar-core's sample assets.

**What the engine guards:**
- `fit()` shrinks a line to its box, never below 50%. A line still too wide fails the build.
- `para()` wraps by measured width. An optional `maxh` fails the build if the paragraph runs taller.
- `img()` flattens PNG alpha onto the page colour as a cached JPEG. It fails the build on any image off the page or overlapping another.
- Compose overlaps with `couple`, `fan`, `toss` and `bleed`, so each group lands on the page as one picture.

**The composers engine** (`engine/composers.py`, generic, any product: pouches, bottles, cans, boxes, cosmetics, books, devices) is the fuller version of those helpers. Each call returns one RGBA plus metadata (per-product box, scale, mask; px/mm when true scale) and its device name:
```python
sys.path.insert(0, ".claude/skills/nazar-story/engine")
from composers import Item, Light, DeviceLog, fan, couple, row, cascade, stack, bleed_hero, grid, scatter, extend_canvas
c = row([Item("30g.png", height_mm=140), Item("250g.png", height_mm=260)], 520, overlap=-0.1, true_scale=True)
b += d.img(c.save(os.path.join(d.cache, "sizes.png")), 960, 260, 880, 700); d.page(b, device=c.device)
```
- `fan` hand of cards · `couple` front over back (overlap fraction, rise, tilt) · `row` overlap/standing/scale lineup on one baseline (`true_scale` by real mm) · `cascade` · `stack` (a pile that rests on its own silhouettes) · `bleed_hero` (exact box, one edge cut by a requested fraction) · `grid` specimen · `scatter` seeded flat-lay (no touching, or a capped overlap) · `extend_canvas` (edge-colour extension, matched grain, eased falloff, feathered seam).
- Shadows: one shared `Light` (default from above-left) gives every composer the same direction. Each product gets a soft shadow plus a tight contact shadow from its own silhouette (notches and seal teeth survive), with an optional ground-plane `cast` shadow.
- Devices: `DeviceLog().add(page, comp)` / `.add_deck(d)` / `.report()` warns when a device repeats across pages. `check_scale()` proves true-scale ratios.
- `python nazar-story/engine/composers.py --selftest` (all guarantees on synthetic products) · `... sheet` (writes `examples/composers_sheet.jpg`) · `... compose row a.png b.png -o out.png --mm 120,200` · `... extend photo.jpg -o out.jpg --left 300` · `... demo <folder of *front*.png>` (an optional demo on real renders, labelled demo).

## QA before showing
- [ ] The build passes with no overflow, overlap or device-repeat warning
- [ ] Every product group comes from one `Light`; size comparisons use `true_scale` with real mm
- [ ] The SKU × side list is all ticked, and no pack image appears twice
- [ ] At phone width, every panel's line reads in about 2 s (look at `_behance_contact.jpg` at 480 px)
- [ ] The flatplan check in `references/sequence.md` passes
- [ ] The cover reads at 202 × 158
- [ ] The contact sheet has been shown to the owner and their notes are applied

## Files
- `references/sequence.md`: the beats, the application rhythm, device names, the flatplan checklist
- `references/research.md`: story structure, award and gallery patterns, scroll-attention data, Behance specs, sources
- `references/research_composers.md`: dated research behind the composers (composition, scale truth and misleading-size law, shadow physics, F/Z attention, seam blending)
- `engine/composers.py`: product-group composers (one RGBA each), shared Light, contact shadows, true scale, device registry; `engine/test_composers.py` (`python` or `pytest`)
- `examples/composers_sheet.jpg`: every composer on synthetic stand-in products; `examples/composers_demo_bagh.jpg`: the same on the BAGH demo pack renders (demo only)
- `LESSONS.md`: what real jobs taught; add to it after every story
