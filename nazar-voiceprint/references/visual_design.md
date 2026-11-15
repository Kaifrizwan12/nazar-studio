# Visual and design language

Confidence tags: [V] checked at the source, [S] secondary sourcing, [UNVERIFIED].

## 1. What computers can actually extract about visual style
- **Neural style transfer (Gatys, Ecker & Bethge, arXiv 1508.06576, 2015; CVPR 2016)** [V].
  - *Content* is the feature responses in higher CNN layers, which keep spatial layout.
  - *Style* is Gram matrices: correlations between feature maps, averaged over space, so spatial layout is thrown away on purpose. In this technical sense, "style" means texture and colour statistics.
  - The authors themselves concede that "content and style cannot be completely disentangled".
  - **Takeaway:** texture, colour fields and brushwork-like statistics are extractable. Composition, subject choice and intent are not.
- **Computational connoisseurship (C. Richard Johnson Jr., Cornell; Don H. Johnson, Rice)** [V]. Weave-density maps of canvas thread counts matched *Sunset at Montmajour* to the same canvas roll as a known Van Gogh. The Van Gogh Museum authentication was published in the *Burlington Magazine*, Oct 2013. A related brushstroke-classification project trained on 101 high-resolution scans, 23 of them confirmed authentic [S, news coverage only]. The real lesson: attribution works on *physical, measurable* traces, not on "feel".

## 2. Design-specific research (thin, but real)
- **Lin & Martelaro, "Learning Personal Style from Few Examples" (PseudoClient, DIS 2021, arXiv 2105.14457)** [V]. Models a person's design *taste* from as few as 5 positive and negative examples, at 79.4% accuracy. It's the closest real analogue to a design signature, but it models preference, not the person's own output.
- **Named designer "signatures" are mostly unsourced repetition.**
  - The one directly sourced Paul Rand line is "the principal role of the logo is to identify" (*Design, Form, and Chaos*).
  - Most other "documented habits" of Rand or Bass circulating online have no primary citation.
  - Don't cite them as evidence; describe the person in front of you instead.

## 3. Implementable techniques (what `engine/visual.py` does)
- **Palette:** k-means on pixel colours, with the centroids as the palette. Run it in a *perceptual* space (OKLab here), because Euclidean distance has to track perceived difference. Use k-means++ initialisation and several seeds, keeping the lowest-error result [V, standard method].
- **Palette roles:**
  - a large, low-chroma share = ground;
  - a small, high-chroma share = accent;
  - everything else = support.
  - This turns a palette into a *habit* ("one small hot accent on a pale ground"), not just a swatch list.
- **Composition:** rule-of-thirds pull, left-right symmetry, negative-space share, edge density and visual-weight centre. These rules are enumerated in composition-analysis literature, e.g. US patent 10,277,806 [V]. No single tool combines palette and composition, so this script combines two standard techniques.
- **Across a body of work:** mean ± spread per feature. A low spread is a habit. A high spread probably moves with the project, so ask before treating it as voice.

## 4. Where extraction stops (say this out loud)
- Design-research writing on tacit knowledge says it "presents a particular challenge to design research" (*Design Issues*, 2012). Vaughn Tan's line translates directly: newcomers "can recite the style guide but still produce work that feels wrong" [V].
- A 2024 cs.HC review of tacit knowledge in graphic design proposes ways to capture it in tools. Read it before citing it further.
- **So:** the engine briefs the measurable layer (palette habit, air, symmetry, weight placement, density). The **why** comes from the confirm loop and is written into the pattern in the person's own words:
  - why this crop;
  - what a recurring motif means to them;
  - what they'd never do;
  - the idea behind a piece.

## Signal types for a visual pattern
| Layer | Source | Example |
|---|---|---|
| Palette habit | `visual.py` | "pale warm ground ~85%, one hot accent under 3%" |
| Air and density | `visual.py` | "most of the frame empty; low edge density" |
| Balance | `visual.py` | "asymmetric by habit; weight sits left" |
| Texture | qualitative (or a Gram-matrix pass, if ever built) | "grain, slight misregistration, no gradients" |
| Motifs and meaning | confirm loop only | "the eye shows up as a hidden detail; it means 'look twice'" |
| Intent | confirm loop only | "sober page, one wink" |

## Sources
arXiv 1508.06576 · bethgelab.org · news.cornell.edu (canvas weave, 2013) · people.ece.cornell.edu/johnson/ComputationalConnoisseurship.pdf · arXiv 2105.14457 · USPTO 10277806 · Design Issues 28(2), 2012 · vaughntan.org/learnwhatmatters · Ottosson, OKLab (2020)
