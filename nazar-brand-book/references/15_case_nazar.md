# 15 · Worked example: Nazar (2026, 65 pages)

Use this to calibrate quality and density, not as a template to copy.

## The brand
Nazar (نظر, "sight, gaze") is a Karachi creative studio that **syncs street (analogue) and screen (digital) marketing**, so a client's brand is wherever you look: the hoarding, the rickshaw back, the in-car tablet, the concert stage, and the reel you open after. It is NOT about counting eyeballs.

## The idea, carried everywhere
- **Found in the logo:** نظر has two x-shaped nuqtas (dots). One is the street's eye and the other is the screen's eye. The concept: "Do Aankhen, Har Taraf" (two eyes, everywhere you look).
- **Tagline:** HAR GALI, HAR NAZAR (every street, every gaze), in Anton, tucked under the logo's baseline bar from the ط's serif axis to the mark's edge.
- **Atom:** the two nuqtas. They're used alone as the avatar and favicon, never beside the full mark.
- **Journey:** one day across Karachi on ten real OSM-mapped streets (Tariq Road at 9 am → DHA Phase 2 Ext at 2:30 am). The pages darken from Chuna to Raat.
- **Dividers:** split scenes, with the street map on the left and the same place on a phone on the right, joined by one Ember sync line.
- **Hidden devices:** a sync stamp on every page (both eyes · a line · place · hour), and two low-opacity eyes hidden on every page, revealed on a "Where the eyes were" page.
- **Voice device:** every line has two halves, a street half (Chuna) and a screen half (Ember). "Nazar uthao. Phir phone dekho." "Park ho gaye? Hum nahi."

## The system
| | |
|---|---|
| Palette | Raat `#0E0D12` (base) · Chuna `#F3EFE6` (light) · Ember `#F2742E` (accent, taken from the logo's orange stop) · Dhuan `#A6A2AE` (secondary; Dhuan-dark `#6B6773` on Chuna). The chrome gradient `#FFC24B → #FF8A3D → #FF3D7A → #E4237A` is used on the logo only. |
| Type | PAK23 Black (the mark; licence is non-commercial, so it's not shipped) · Anton (tagline) · Space Grotesk Light/Regular (text) · Space Mono (labels) |
| Textures | Halftone at 18° (from the logo) = street; pixels = screen |
| Page | 1920×1080, margin 120, running head y 92, kicker 152, title 212, subtitle 254 |

## Section list
00 cover · dictionary page (har gali, har nazar) · contents · how to read → 01 divider · the note · the problem · the name · the idea · what we do · har taraf (8 places, each with its screen twin) · beliefs → 02 primary mark · with tagline · mark and eyes · anatomy (exploded letters) · clear space · misuse → 03 palette · day/night · chrome · pairings → 04 the faces · scale · two scripts · eye chart → 05 the nuqta system · two textures · maps and pins · the sync mark → 06 how we sound · one line, two halves · ads → 07 social playbook for @nazar.pk (profile, pillars, templates, reels, captions, launch, the slop test) → 08 client formats as spec sheets (hoarding, rickshaw back, in-car tablet, wall/slip/box, concert, stationery, merch, a Kona café concept campaign) → 09 say salaam · where the eyes were · sources and credits · back cover.

## What went wrong (and the fix that became a rule)
| Problem | Rule now |
|---|---|
| Cartoon object mockups were called "AI slop" | Spec sheets only (`10_applications.md`) |
| The concept was misread as eyeball counting | Restate the idea in one line and get a yes (`02_intake.md` Q5) |
| Bold display type used for sentences | Light/Regular only (`06_type.md`) |
| The tagline changed three times after the build | Lock the tagline in round 2 and warn about the cost |
| Dhuan blended into Raat | Contrast checks for every pair (`05_colour.md`) |
| Uneven gaps under the headings across 73 calls | The heading system is in code (`../nazar-core/engine/lib.py` `heading()`) |
| Phones vanished against dark maps | A solid device body with an outline, and the map knocked out behind it |
| The map credit appeared on every page | Credit once on the sources page |
| The section 08 formats were unclear (whose brand?) | Tag each sheet as a client format or own format |
| A non-commercial font was used in the mark | Check licences in research pass 5 |

## Files (in the Nazar repo)
`NAZAR_BRAND_BOOK.md` (spec) · `v2/07_brand_book/engine/` (the full engine this kit's engine is derived from) · `v2/07_brand_book/exports/` · `v2/assets/` (the asset pack layout used in `13_deliverables.md`) · `internetfinds/` (the research dump layout).
