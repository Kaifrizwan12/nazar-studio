# Design QA (before Kaif sees anything)

QA isn't a final skim. It's a set of **methods** (ways of looking) plus **checks** (what to look for), run on every page and then on the whole book. Kaif reviews by page number and catches alignment, gaps and clutter, so catch them first.

## A. Methods: look at each page in all these ways
| Method | How | Catches |
|---|---|---|
| **Fresh build first** | Delete the old output, rebuild, confirm the build exited cleanly and the file's timestamp is new, then look | Reviewing a stale file after a failed build and calling it fixed |
| **Full size** | Open each PNG at 100% | Overlaps, glyphs, kerning, small type |
| **Contact sheet** | `exports/sheet.png`, as Kaif sees it | Rhythm, consistency, odd pages out, empty or crowded pages |
| **Squint / blur** | Blur the page heavily (or squint) | Hierarchy: is the focal point clear? Do things that look alike belong together? [NN/g squint test] |
| **Greyscale** | Desaturate | Contrast and hierarchy that rely on hue alone |
| **Flip** | Mirror horizontally | Balance and symmetry problems your eye has learned to ignore |
| **Grid overlay** | Overlay columns, margins and baselines | Elements off the grid, inconsistent text starts |
| **Side by side** | Pages of the same type next to each other | Heading drift, inconsistent spacing, style mismatch |
| **Five seconds** | Glance at the page for 5 s, look away, and say what it was about | Whether the one idea lands |
| **Real size** | View at the size of use (phone for social, A4 printout, shelf distance for packs) | Legibility, minimum sizes, scale mistakes |
| **Fresh eyes** | Re-check after other work, last of all | Everything you stopped seeing |

## B. Concept and meaning
- [ ] The page says **one** thing, and that thing serves the locked idea.
- [ ] Every element earns its place (Vignelli's semantics). Remove anything decorative that means nothing.
- [ ] Remove before adding (Rams): nothing can be taken away without loss.
- [ ] The page would make sense to someone who wasn't in the room.
- [ ] Words, visuals and the section title agree. No line could belong to any brand.

## C. Hierarchy
- [ ] One clear focal point, which survives the squint test.
- [ ] Reading order is obvious: 1st, 2nd, 3rd. No two elements compete for first place.
- [ ] Hierarchy comes from size, weight, colour, space and position. No more than two of these used at once for a single level.
- [ ] The accent colour marks the most important thing only.

## D. Composition (Gestalt and CRAP)
- [ ] **Proximity:** related items are grouped, and labels sit closer to their object than to anything else.
- [ ] **Similarity / repetition:** things that look alike *are* alike; the same element is styled the same way across pages.
- [ ] **Alignment:** every element shares an edge or axis with something. No "almost aligned" (off by a few px reads as a mistake).
- [ ] **Contrast:** differences are decisive (if two sizes differ, make them clearly different).
- [ ] **Figure / ground:** text over images, maps or textures is clearly readable. Knock out or darken the background where needed.
- [ ] **Continuity:** leaders, routes and arrows guide the eye without crossing text or each other.
- [ ] **Balance:** visual weight is deliberate. Symmetrical pages are truly symmetrical (measured), and asymmetrical pages are balanced by a clear counterweight.
- [ ] Negative space is intentional, not left over. No quadrant looks unfinished.
- [ ] **Collisions are cleared or made deliberate.** A glyph running through a rule, text sitting on a line, a tail touching a label: either give it air, or make the break intentional (a knockout gap in the rule).
- [ ] **Paired figures share one layout** (before/after, A/B, then/now), so the only thing that changes is the point being made.
- [ ] Graphics, lines and their labels stay inside their own column or frame, and each label sits at the thing it names.

## E. Grid and alignment
- [ ] Every block starts on the margin or a column line, and the same kind of block starts at the same x on every page.
- [ ] The heading block sits at the project's heading positions (brand.json → page.heading).
- [ ] Margins are equal (or deliberately asymmetric for binding). Nothing crosses them except deliberate full bleeds.
- [ ] Baselines across adjacent columns line up.
- [ ] **Optical corrections:** round and pointed shapes overshoot slightly; logos and icons are centred on their visible mass, not their box; punctuation and quotes hang outside the text edge; text in boxes has visually equal padding (cap height to baseline, not the box edge).

## F. Spacing and rhythm
- [ ] Spacing uses a small set of values (multiples of the baseline unit), never arbitrary.
- [ ] The gap under the heading fits the content: no dead band and no cramming.
- [ ] Equal items have equal gaps (measured, not eyeballed). Labels are centred under their items.
- [ ] Padding inside boxes, chips, slips and tiles is equal on all sides.
- [ ] Page density is consistent across the book, with deliberate breathing pages.

## G. Typography: macro
- [ ] Only the agreed families and weights. No bold for sentences, and display faces only for logo, tagline and posters.
- [ ] Measure 45–75 characters (narrower in columns) [Bringhurst]. Leading suits the measure.
- [ ] The type scale follows the system: no one-off sizes.
- [ ] Sentence case for titles, caps only in tracked labels. Lowercase is never tracked.
- [ ] Line breaks follow sense: break titles by phrase, not where the box ends.

## H. Typography: micro (check on near-final pages, at full size)
- [ ] No widows (one word alone on a last line) or orphans (a stranded first or last line) in titles or short paragraphs.
- [ ] Good rag: no deep holes, no shapes (wedges, steps) in ragged text. No more than 2 hyphens in a row (ladders), and no hyphenated names.
- [ ] No rivers of white in justified text (avoid justifying short measures at all).
- [ ] Kerning is even in display sizes and the logo-adjacent type. Fix any default kerning that gaps (T, V, W, Y, quote marks).
- [ ] Real typographic characters: curly quotes and apostrophes (check all-caps and display lines too; uppercasing in code keeps straight quotes), en dash for ranges (9–5), em dash or spaced en dash for breaks, × for dimensions, real ellipsis, proper minus.
- [ ] Figures: tabular figures in tables and specs, consistent figure style.
- [ ] No missing glyphs or tofu. Run `missing(role, text)` on unusual strings (diacritics, IPA, currency symbols, arrows).
- [ ] Small text meets the minimum (about 12 px on screen pages; check print minimums with the printer).

## I. Bilingual and second script
- [ ] The second script shapes correctly: joined, right-to-left, no broken ligatures or wrong forms.
- [ ] Visual sizes match across scripts (not point sizes), and they align on the agreed shared line.
- [ ] A transliterated local language is set upright, with no italics or quotes, and is spelled consistently across the book (keep a spelling list in `SPEC.md`).
- [ ] RTL layouts mirror where they should (reading direction, arrows), and numbers stay left-to-right.

## J. Colour and accessibility
- [ ] Only palette colours, used in the stated shares. The accent is at most ~10% of the page.
- [ ] Text contrast ≥ 4.5:1 (≥ 7:1 ideal for body), and large text ≥ 3:1 [WCAG 1.4.3].
- [ ] Meaningful graphics, icons and UI parts ≥ 3:1 against **every** adjacent colour [WCAG 1.4.11].
- [ ] Colour is never the only signal: add a label, pattern or icon [WCAG 1.4.1].
- [ ] Pairs that carry meaning are checked in a protan and deutan simulation.
- [ ] Greyscale check: the roles still separate.
- [ ] Gradients only where allowed, with grain on large ones and no banding.
- [ ] Light and dark versions of a page use the light and dark token sets (e.g. the darker secondary colour on light backgrounds).

## K. Logo and core assets
- [ ] The exact supplied artwork. Never redrawn, recoloured, stretched, outlined or effected unless the rules allow it.
- [ ] Clear space and minimum size respected on every page and application.
- [ ] The right lockup for the context (the mark alone by default). The atom or symbol is used alone at small sizes, never beside the full mark.
- [ ] The mark survives the blur test, 16 px, one colour and reversed (shown on the logo pages).
- [ ] Each core asset is distinctive (it points to this brand only), not just different [Sharp & Romaniuk].

## L. Graphics, imagery and texture
- [ ] No AI images, no stock, no cartoon mockups.
- [ ] Icons share one grid, stroke, corner and angle, and they're optically balanced as a set.
- [ ] Textures are subtle (grain felt, not seen), at native resolution, with no visible tile seams and one halftone angle.
- [ ] Maps are real, styled by road class, with a true-scale bar. Private coordinates are rounded. The credit appears once.
- [ ] Diagrams use the house style (1 px lines, dotted leaders, mono labels). There are no 3D or pie charts.
- [ ] Placeholders are clearly labelled ("PHOTO: …") and none remain in the final book.
- [ ] **The AI-look pass.** Run the 30-second test in `ai_tells.md`. No soft glows or radial gradients behind type, no neon on near-black, no default fonts, and not everything centred and evenly spaced. Two or more fails is a P1.
- [ ] **Every graphic argues its own point.** Cover the text and ask what the graphic says. If it could sit next to any paragraph, or only repeats one element many times, replace it. It sits where its point comes up in the reading order.
- [ ] **The grid fits the medium.** A strict, symmetric grid is for the book; campaign pieces, films and social posts vary their composition frame by frame.

## M. Copy and content
- [ ] Proofread every word, then read it once more backwards (word by word) for typos.
- [ ] The brand name, tagline and product names are spelled the same everywhere. After any tagline change, search the whole book.
- [ ] Voice matches the voice page. No filler words ("elevate", "seamless", "curated").
- [ ] Numbers are real or marked "sample". Fictional businesses are labelled fictional.
- [ ] Contacts, URLs and handles are correct and current.
- [ ] No line is repeated on the same page unless the repeat adds something. On short pieces a pull quote usually just echoes the body.
- [ ] Supplied copy matches the source exactly, including paragraph breaks. Diff it against the original.

## N. Consistency across the book
- [ ] Contents page numbers match (run the build twice), and any "see page N" reference is right.
- [ ] The section order matches the anatomy locked in `SPEC.md`.
- [ ] Repeated components (furniture, kickers, labels, tables, swatches, spec title blocks) are identical everywhere.
- [ ] The light/dark rhythm and pacing feel intentional; no two dense pages in a row without a breather.
- [ ] Hidden devices appear wherever the rule says, and the reveal page matches.
- [ ] Applications carry the right tags (client format / own format) and consistent title blocks and dimensions.

## O. Applications and spec sheets
- [ ] True proportions, real dimensions with units, and a complete title block.
- [ ] Safe areas and bleed are shown; logo placement and clear space are correct on each format.
- [ ] Shelf or feed test done at real size, among competitors, in greyscale.
- [ ] Social templates respect the platform's safe zones (profile crop circles, UI overlays on stories and reels).

## P. Truth, rights and safety
- [ ] Every font and image licence is recorded, and no non-commercial asset is in the client pack.
- [ ] Archive references are used only where public domain or licensed, and credited on the sources page.
- [ ] No private addresses or personal details that weren't approved.
- [ ] No invented certifications, awards, claims or client logos.

## Q. Files and export
- [ ] PDF page count, order and size are correct, and the file opens in more than one viewer.
- [ ] PNGs are at full resolution and named `NN_<pid>.png`.
- [ ] The asset pack matches the kit's deliverables file naming, and the README is updated.
- [ ] `SPEC.md` matches the built book.
- [ ] When replacing an already-published image (README, website, CDN), give it a new filename (`-v2`). Caches keep serving the old file under the old name.

## R. Triage and report
Rate each issue, fix all **P1** and **P2** before showing, and list any P3s you chose to leave.
| Level | Meaning | Examples |
|---|---|---|
| **P1 · Broken** | Wrong, unreadable or unsafe | Redrawn logo, missing glyph, wrong contact, contrast failure, overlap, off-brand idea |
| **P2 · Visible** | A pro would notice | Off-grid text start, uneven gaps, widow in a title, inconsistent heading, cramped page |
| **P3 · Polish** | Fine-tuning | Kerning pair, a 2 px optical nudge, a slightly better line break |

When showing work, report it like this: "QA done on pages 12–20: fixed 3 P1s (…) and 6 P2s (…); P3s left: …".
**When Kaif flags one issue, search every page for the same class of issue before replying.**

## Sources
CRAP principles (UW–Madison Design Lab): https://designlab.wisc.edu/resources/design-tips-and-tricks/crap-principles/ · Gestalt (IxDF): https://www.ixdf.org/literature/topics/gestalt-principles · Squint test (NN/g): https://www.nngroup.com/videos/squint-test/ · Squint test (Polypane): https://polypane.app/blog/debug-your-visual-hierarchy-with-the-squint-test/ · Typographic checklist (CreativePro): https://creativepro.com/check-please-typographic-checklist/ · Fonts.com typographic checklist: https://www.fonts.com/content/learning/fyti/typefaces/typographic-checklist · Hanging punctuation: https://www.fonts.com/content/learning/fontology/level-4/fine-typography/hanging-punctuation · Optical vs mathematical alignment: https://pangrampangram.com/blogs/journal/optical-vs-mathematical-alignment · Alignment tips: https://learnui.design/blog/3-pro-tips-on-alignment.html · WCAG non-text contrast: https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast · WebAIM contrast: https://webaim.org/articles/contrast/ · Bringhurst's measure: https://webtypography.net/2.1.2
