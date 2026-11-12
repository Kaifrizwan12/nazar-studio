# AI tells: what makes work look machine-made, and how not to

Every kit runs this before Kaif sees anything. "It looks AI" is the fastest way to lose a client's trust, and it's now the first thing audiences and art directors check for. Treat the tells as a **cluster**: one alone proves nothing, but three together and people stop trusting the piece. [SRC: Lovart; Mika Reyes; Pangram; see Sources]

The root cause is the same everywhere: generators and unbriefed designers fall back on the **statistical average** of what they've seen. Purple gradients, Inter, teal-and-orange and "elevate" are all just the most common choices in the training data, fed back in as more of the internet copies them. [SRC: prg.sh "Why your AI keeps building the same purple gradient website"; Flitto DataLab "orange-and-teal bias"; Sam Goree "Why does AI art look like that" (2025)] **The cure is a specific decision traced to this brand**, not a different default.

## 1. Colour and light
| Tell | Why it reads as AI | Do instead |
|---|---|---|
| Purple-to-blue / indigo gradients, gradient text | The best-known AI fingerprint in UI and brand work | The brand's own flat colours; at most one gradient, reserved for one job |
| Teal-and-orange grading, glossy HDR saturation | The "Midjourney look", baked in from film and Instagram grading | Grade from the brand's palette, or keep photos natural |
| Soft glows, radial blooms behind type, light from nowhere | Decoration that means nothing: "lit from within" | Flat fills. Light only where a real light source would be |
| Neon on near-black, everywhere | The default "premium tech" mood | Choose dark or light for a reason, and let one colour be loud |
| The "anti-AI default": warm cream + terracotta, or black + one acid green | What you get when you ask an AI to look *less* AI. It's already a cliché. | Colour that comes from the brand's own research (`research_path.md`) |

## 2. Layout and composition
| Tell | Do instead |
|---|---|
| Everything centred, evenly spaced, the same weight: no hierarchy, no focal point | One clear focal point. Deliberate imbalance. Space used unevenly on purpose. |
| The same skeleton every time (centred hero → three rounded cards with icons and soft shadows) | Compose each piece for its medium. A book's grid is for the book; films, posts and campaigns vary frame by frame. |
| Glassmorphism, frosted panels, rounded-everything, drop shadows on every card | Edges and materials the brand actually owns (paper, print, signage, a cut, a rule) |
| Too many competing details and styles in one piece (script + brush + block fonts) | Fewer elements. Remove before adding (`masters.md`). |
| Uniform detail everywhere, with nothing sharp and nothing rough | Contrast of finish: some parts precise, some parts with a hand in them |

## 3. Type
| Tell | Do instead |
|---|---|
| Inter / Roboto / system sans by default; Poppins and Montserrat headlines | A typeface chosen for this brand, with a reason written in `SPEC.md` |
| Garbled, warped or inconsistent lettering in images (the most reliable single tell in generated images) | Set all type as real type. Never let an image generator draw letters. |
| Pill badges ("New", "Beta") above headlines, emoji as icons | Real labels in the brand's label style; drawn icons on one grid |

## 4. Images
| Tell | Do instead |
|---|---|
| Waxy, poreless skin; perfect symmetry; extra or fused fingers | Real photography of real people, shot or licensed (`nazar-art-direction`) |
| Inconsistent shadows; foreground and background in different light | One light direction per scene, matched across a set |
| Broken repeats (tiles, bricks, windows); near-identical background faces | Real places. Check edges and backgrounds, where artefacts hide. |
| Smeared, melted edges where objects meet | Objects with clean separation |
| No credit and no maker | Credit the photographer or illustrator. Provenance is part of trust. |

## 5. Copy
| Tell | Do instead |
|---|---|
| "Delve", "elevate", "seamless", "leverage", "robust", "tapestry", "unlock", "journey" | Plain, specific words in the brand's voice |
| "It's not just X, it's Y" / "More than just…" | Say what it is |
| Everything in threes | Vary the rhythm. Use two, or four, or one. |
| Em dashes everywhere | Use punctuation for its purpose, not as a habit |
| Placeholder names (John Doe, Acme, Lorem) left in | Real or clearly marked sample content |
| A line that could belong to any brand | Kaif's rule: if you could swap the logo and it still works, it's dead |

## 6. Process (where the look comes from)
- **Unbriefed defaults.** Most AI looks are what happens when no decision was made. Write the decision down: the colour from where, the type for what, the composition because of what.
- **No reference trail.** Human work can say where an idea came from. Keep the research log (`research_path.md`) and point to it.
- **Polish without a point.** If an effect can't be explained in one sentence about the brand, remove it.
- **Over-specific filler.** Fake precision (timestamps, coordinates, stats nobody asked for) makes a piece read generated. Stay high level unless the brief is about the detail.

## The 30-second test (run on every deliverable)
1. Squint: is there one focal point, or is everything the same weight?
2. Cover the logo: could this belong to any brand? If yes, fail.
3. Find the gradient and the glow: does each have a reason? If not, flatten.
4. Read the copy aloud: any word from the list in §5? Rewrite.
5. Zoom into edges, hands, backgrounds and any lettering in images.
6. Ask "where did this come from?" for the colour, the type and the main graphic. Each needs an answer from the research.
Two or more fails is a P1 (`qa_design.md` §R).

## Sources
- Lovart, "How to detect AI-generated design" (text as the most reliable indicator; uniform detail; flaws becoming obsolete as a test)
- Mika Reyes, "How to spot AI-made graphic design and posters" (inconsistent competing details, mixed fonts)
- UX Planet, "How to spot AI-generated design" (ultra-conventional skeletons)
- superdesign.dev, "Why AI design looks generic"; 925 Studios, "AI slop fonts and gradients"; noqta.tn, "AI design slop: overused UI patterns" (purple gradients, Inter, glassmorphism, centred hero + three cards)
- prg.sh, "Why your AI keeps building the same purple gradient website" (training-data feedback loop)
- Flitto DataLab, "Orange-and-teal bias in AI art"; Sam Goree, "Why does AI art look like that" (2025)
- Sightengine, Clutch, Digital Camera World, PopSci: image artefacts (hands, skin, lighting, repeats, provenance)
- Pangram, "Signs of AI writing" (vocabulary rates, "not just X but Y", triads; vendor data, so treat as indicative); Wikipedia's "Signs of AI writing" guide via Beutler Ink
- Caveat: most of this comes from practitioner blogs, not controlled studies. Use it as a checklist of signals, not proof.
