# Anatomy of a backdrop

## Why a static layer works (the research)
- **Distinctive assets need consistency to build memory.** A colour, a corner, a band only becomes "the brand" through repeated, consistent exposure, and changing it resets the memory. [SRC: Jenni Romaniuk, *Building Distinctive Brand Assets*, 2018; Byron Sharp, *How Brands Grow*, 2010 (Ehrenberg-Bass Institute)]
- **Fame × uniqueness.** An asset is worth using when people link it to this brand (fame) and to no other (uniqueness). An accent band in a colour three competitors also use is neither. [SRC: Romaniuk's distinctive-asset grid]
- **Fluency.** Familiar, consistent features are processed faster and liked more; distinctive recurring devices are among the strongest drivers of long-term effect in advertising. [SRC: Orlando Wood, *Lemon* (IPA, 2019) and *Look Out* (IPA, 2021), System1 data]
- **A programme, not a page.** Design the rules that produce the posts, not each post. [ARCH: Karl Gerstner, *Designing Programmes*, 1964]
- **A grid is a discipline, not a style.** It holds the skeleton steady so the content can vary. [ARCH: Josef Müller-Brockmann, *Grid Systems in Graphic Design*, 1981; Massimo Vignelli, *The Vignelli Canon*, 2010]

## Precedents from the archive (static frames that carried thousands of variations)
- **Penguin Books' horizontal grid (1935, revised by Jan Tschichold 1947–49):** three bands, colour-coded by genre. Every title fits the same frame. [ARCH: Penguin archive, University of Bristol]
- **National Geographic's yellow border:** one rectangle made the magazine recognisable from across a room for decades.
- **Blue Note Records (Reid Miles, 1950s–60s):** a fixed typographic attitude and photo treatment, endlessly varied inside it.
- **The Criterion Collection spine numbers:** a counter as a collectible device. The same thinking applies to carousel counters and post numbers.
- **Swiss and Stedelijk posters (Wim Crouwel):** one grid, one type system, a season of posters that read as a set.
Use these as structural lessons. Don't copy their looks.

## The parts (in render order)
| Part | Job | Defaults (1080 canvas) |
|---|---|---|
| **Background** | The mode: dark, light or accent | Flat brand colour. Texture only if the book has one. |
| **Margin** | Holds everything off the edges and out of the crops | ≈ 6.5% of the short side (~70 px). Never less than the grid crop. |
| **Edge device** | The distinctive asset that survives every crop | A band ≈ 1–1.5% of the short side, on one edge (asymmetric) |
| **Logo slot** | Says who, in the first 0.25 s | ≈ 14–18% of the short side wide, in the anchor corner, at least the book's clear space from everything |
| **Handle** | Says where to find them | Label font, ≈ 2.4–2.8% of the short side, opposite corner to the logo |
| **Counter** (carousels) | Pace and position | `01/05` in the label font, opposite the handle |
| **Swipe cue** (cover) | Tells people there's more | A small arrow or line next to the counter |
| **Continuity line** (optional) | A line that joins up when slides sit side by side, rewarding the swipe | Same y on every slide; it touches the edge on inner slides |
| **Image window** (image role) | Where a real photo goes | A fixed rectangle with a defined ratio. Photos get cropped to it, never stretched. |
| **Content zones** (guide only) | Title, body, CTA areas for whoever fills it | Drawn only on the `_guide` versions |

## Skeleton rules
1. **The anchor never moves** between formats or modes. A story and a square post put the logo in the same corner at the same relative size.
2. **Scale from the short side**, so a 1:1, a 4:5 and a 9:16 feel related.
3. **RTL brands mirror the skeleton** (logo top-right, band on the right edge), not the logo itself.
4. **Leave the centre empty.** The middle belongs to the content.
5. **One loud thing.** If the accent is on the band, it's not also on the handle and the counter.
