# A VLM pass on real work: ten public-domain cyanotypes

**Source:** ten CC0 cyanotypes from The Met (nine plates from Anna Atkins's *Photographs of British Algae*, one landscape by Henry P. Bosse). Object IDs are in `met_credits.json`.
**Views:** `python engine/views.py <folder> <out>` gave a contact sheet and a study sheet per piece. I read the contact sheet first, then study sheets, and applied `references/vlm_protocol.md`: evidence per claim, ≥3 pieces for a habit, counts left to engines, no attribution, no inferred "why".
**Honest scope:** I looked closely at the contact sheet and one full study sheet (the *Enteromorpha* plate). Claims that need a crop of another piece are marked *likely*, not *seen*.

## Step 1: open discovery (everything that recurs, no taxonomy)
Isolated white specimens on a flat blue field · a small caption at the bottom centre · a lot of empty ground · the plates photographed as bound-book spreads with a grey surround · a few plates with several specimens spread out · two text pages in white script.

## Step 4: the pattern table
| Pattern | Lens | Seen in | Evidence | Confidence |
|---|---|---|---|---|
| One specimen (or a loose few) isolated on a flat field, with much of the plate left empty | Closed form · multiplicity vs. unity · salience | 6 plates (the *Bangia*, *Sphacelaria*, *Grateloupia*, *Ptilota*, *Nostoc* and *Enteromorpha* plates) | contact sheet; squint view of *Enteromorpha* leaves only a pale diagonal against flat blue | seen |
| A small, light caption at the bottom centre, in a handwritten script, sitting on a faintly lighter rectangle | Type and image · framing | 6 plates | *Enteromorpha* bottom-left crop shows the lettering ("Ente…") inside a lighter patch; the same placement is visible on the contact sheet | seen (crop for 1; placement for the rest) |
| Several specimens set apart with generous spacing, hand-arranged rather than packed | Rhythm and repetition · grouping (proximity) | 3 plates (*Grateloupia*: scattered fragments; *Ptilota*: loose cluster; *Nostoc*: a ring of eight) | contact sheet | seen |
| Hair-fine filaments with sharp, thread-thin edges | Minor-detail habit | 1 confirmed in a crop (*Enteromorpha*, centre) | centre crop shows individual white filaments | likely for the others; needs crops |
| White script on blue for contents pages | Type and image | 2 pages | contact sheet | **possible only** (the threshold is 3) |

## What is *not* a habit (and the protocol is there to stop me claiming it)
- **The white-on-blue look is the cyanotype process.** A photogram makes the object pale against Prussian blue. That's the medium, so it can't be attributed to the maker's taste. The pattern worth asking about is *what they chose to lay down*, not that it's light on dark.
- **The grey surround, the visible book edge and the page-turn shadow come from how the museum photographed the album.** It's in 8 of the 10 images, and it's a capture artefact, not a design decision.
- **The tenth image (Bosse) is a different maker.** An oval vignette, a cream mount and a calm horizon. A style-modes pass (`cluster.py`) would put it in its own group, and a pattern built from all ten would describe nobody.

## Step 5: what I'd ask the maker (I can't infer these)
1. Are the specimens placed to a plan, or as they came?
2. Is the caption's lighter rectangle deliberate (a label), or an artefact of how it was printed?
3. Does a contents page count as "your work" or as an index?
4. Level 3 (why this subject, this arrangement): theirs to answer, never mine.

## What this shows about the method
Numbers alone would have called this "blue, single-hue, soft" and stopped (see the real-photo card). Looking added the arrangement, the caption convention and the spacing, and the evidence rules removed three things a free-form description would have confidently said: the process look, the museum's photography, and a style that was really two makers.
