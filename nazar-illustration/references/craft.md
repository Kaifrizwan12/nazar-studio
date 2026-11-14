# Craft: method, faults, styles, math art, archives

## 1. Method
**Concept lock** (top of every scene script): idea (one sentence), focal point, light direction, eye path, budget (paper + ink + 3–5 flats + one accent; 3 line weights; max objects), and what the image must say about the brand. Generate 2–3 concepts with: **metaphor** (the thing stands for the idea), **gesture** (what a hand does), **mechanism** (show how it works, not the noun — "a handoff chain that weakens at each hop", not "robots at a laptop") [SRC: vpgits/claude-editorial-svg]. Lock one sentence before drawing.

**Composition before detail:** 2–3 thumbnails as rough blocks, checked at 160 px; asymmetric over centred; a big quiet field, one light; paint order = depth order (background → far → figure → surface in front → things on the surface → the focal accent last).

**Construction:** build from simple masses (egg head, tapered box torso, tube limbs) before lines [ARCH: Preston Blair, Loomis]. Silhouette test: fill black; if the pose isn't readable, change the pose. Clothes hang from bodies: shoulder line, lapels, folds from support points, with any hanging sleeve clearly empty. Hands get a clear job (pinch, grip, point); cartoon gloves need separate fingers, a thumb and a cuff, or they read as a light bulb.

**Line weight:** thicker on the outer silhouette, the shadow side and in front; thinner on interior detail and the lit side; taper the ends; break hidden lines at T-junctions [ARCH: Pennell, *Pen Drawing and Pen Draughtsmen*, 1889]. Three weights per piece (≈1.2 / 0.75 / 0.22 at A4 scale).

**Light and tone:** one declared light source; two value groups beat five muddy ones; tone from hatching (nested tones) or stipple, never opacity blur.

**Shape language:** circles friendly, squares stable, triangles dynamic; one dominant shape family, vary sizes.

**Working loop:** render → open the PNG → name the single most visible fault → fix only that → re-render. Stop at 4 rounds [SRC: cloveric/claude-drawing-skill workflow].

## 2. Fault table
Add a row whenever a drawing fails review.

| Symptom | Cause | Fix |
|---|---|---|
| Cute instead of sober | No taste check against the brand register | Ask: does Kaif's register want a wink or a shrug here? Simplify or restrain |
| The picture contradicts the brand message | Drew the reference literally instead of locking the idea first | Lock the concept sentence; check "must say" before drawing |
| A garment reads as a beanbag | Flat slabs with no body inside | Shoulder line, lapels, an empty hanging sleeve, folds from support points |
| A dark limb disappears on a dark torso | Same value, no edge | A lit edge line on the light side; outline clearly |
| A limb's root shows as a loop on the body | The whole limb outline drawn on top | Start the limb under the garment; only stroke the visible edges |
| Gloves read as light bulbs | No fingers or thumb | Palm + 4 rounded fingers + thumb + stitch lines + cuff |
| Colours go muddy / occlusion breaks in the print look | True overprint used on art not designed for it | `riso=True` keeps occlusion; `overprint=True` only for planned overlaps |
| Line work sits on top of things in front of it | Ink layer re-pasted over everything | Never re-composite line art over flats; keep misregistration in the flats' own offsets |
| Boxes look like blobs | Splines through corners | `stroke(..., corners=True)` |
| A kink where a loop closes | An open spline forced shut | Closed loops continue past the start (built into `ink.py`) |
| Everything detailed equally | No focal hierarchy | Give the focal point the accent and the darkest darks; simplify the rest |
| A "shaky filter" look | High-frequency jitter | Low-frequency wobble only; fewer, longer, confident strokes |
| Machine-made circles/symmetry | Pure primitives | Slight asymmetry; overshoot; build ellipses from key points |
| Shadows point different ways | No declared light | One light in the concept lock; derive every hatch from it |
| Identical repeats | Copy-paste | Vary size, angle, spacing per instance (seeded) |
| Glossy gradients, glow, purple-blue | Default "AI look" | Flats + hatch + one accent; see `../../nazar-core/references/ai_tells.md` |

## 3. Style recipes
| Style | Build | Fits |
|---|---|---|
| **Editorial ink + riso (default)** | Pressure line (3 weights), 3–5 misregistered flats, nested hatching, one accent, `save(riso=True)` | Heroes, explainers, pack backs, decks |
| **Pen and ink** | Black + one accent; tone from hatch/stipple only; strong silhouette | Heritage, origin stories, certificates |
| **Flat editorial shapes** | Value-shaped flats, no outlines, hatch sparingly | Covers, posters, calm worlds |
| **Cartoon / mascot** | Construction, squash and stretch, line of action, exaggerate one feature | Mascots (with `nazar-brand-book`), stickers |
| **Patterns and repeats** | One tile, seeded variation, test the repeat at 3×3 | Backgrounds, wraps |
| **Desi vernacular grammar** | Study truck-art borders, ajrak geometry, kashi rhythm, matchbox framing; draw your own motifs, never copy | Pattern and border work |
| **Op-art / trippy (one accent zone)** | Moiré, Riley curves, kaleidoscope folds, colour vibration | Launch moments, one pack variant |
| **True riso overprint** | 2–3 spot inks designed to overlap; `save(overprint=True)` | Zines, posters, merch |

## 4. Math and generative art
| Technique | Core idea | Rule |
|---|---|---|
| Flow fields | Angle grid ~50% larger than the canvas; curves follow the nearest angle | Seed with circle packing; quantise angles for a rocky look [SRC: Tyler Hobbs] |
| Watercolour | Recursive midpoint displacement, many low-opacity layers | Hard edges on the focal side [SRC: Hobbs] |
| Sand painting | Scatter near-transparent dots along a moving segment | Accumulate in float32, quantise at the end [SRC: Inconvergent] |
| Lissajous / harmonograph / spirograph | x = A sin(at+δ), y = B sin(bt); damped sums; hypotrochoids | Near-integer ratios drift richly; damping reads as human |
| Moiré | Two gratings 1–5° apart or a slight frequency mismatch | One grating static |
| Riley curves | yₖ(x) = k·gap + A(x)·sin(ωx+φ(k)) | Vary A or φ slowly |
| Weighted Voronoi stipple | Darkness-weighted Lloyd relaxation | Dot count and radius by tone [SRC: Secord 2002] |
| Nested hatching (TAM) | Each darker tone adds a layer | Strokes follow form [SRC: Praun & Hoppe 2001] |

## 5. Archives (study, never copy)
CC0/PD: The Met, Smithsonian, Rijksmuseum, Art Institute of Chicago, Cleveland Museum (incl. a Kalighat album), Biodiversity Heritage Library, Library of Congress (Swann Collection of Caricature & Cartoon), Public Domain Review, pre-1929 cartooning manuals and Pennell on archive.org, Digital Comic Museum / Comic Book Plus, ukiyo-e.org.
Reference only (copyrighted or unclear; grammar not copies): archives.design, Artwork Archive Discovery, Preston Blair / Loomis manuals (status disputed), Pakistani truck art (Folkloristan archive, Durriya Kazi's research), Indian matchbox labels (Tasveer Ghar), hand-painted film posters, Dieline/Pentawards/D&AD galleries.
Log every reference in `research/illustration/refs.md`: URL · maker · year · licence · one-line lesson · tag.

## 6. Creative QA
1. **Blind describer:** show only the PNG, ask what it's a picture of, where the eye goes, the mood, the action, what looks wrong. Run twice; keep only agreement [SRC: jchapuis/drawing-skill].
2. **Silhouette test:** fill black; the pose/object must still read.
3. **Thumbnail test:** 160 px; the idea survives.
4. **Budget check:** colours, weights, object count, light direction.
5. **AI-tell sweep:** no gradients/glow/purple-blue, no perfect symmetry everywhere, no uniform jitter, no identical repeats, no equal detail, shadows consistent.
6. **Meaning check:** does it say the "must say" line, and nothing that contradicts it?
Triage: P1 meaning/legibility/broken occlusion, P2 craft, P3 polish. Fix the most visible P1 first, one per round, stop at 4. If P1s remain, simplify the concept or (with client approval) hand over an image prompt via `../nazar-prompts/`.

## Sources
github.com/steveruizok/perfect-freehand · github.com/rough-stuff/rough · github.com/acamposuribe/p5.brush · mattdesl.svbtle.com/drawing-lines-is-hard · en.wikipedia.org/wiki/Centripetal_Catmull–Rom_spline · hhoppe.com/hatching.pdf · cs.ubc.ca/labs/imager/tr/2002/secord2002b · tylerxhobbs.com/words (flow fields; watercolour) · inconvergent.net/generative · en.wikipedia.org (Twelve basic principles of animation; Line of action; Lissajous curve; Harmonograph; Spirograph; Op art; Risograph; Halftone) · archive.org (Preston Blair; Loomis; Lederer *Cartooning Made Easy* 1923; Pennell *Pen Drawing and Pen Draughtsmen* 1889) · github.com/anthropics/skills (algorithmic-art, canvas-design) · github.com/cloveric/claude-drawing-skill · github.com/jchapuis/drawing-skill · github.com/vpgits/claude-editorial-svg · github.com/Devesh-Shirsath/spotkit · metmuseum.org/hubs/open-access · si.edu/openaccess · rijksmuseum.nl/en/rijksstudio · artic.edu/open-access · clevelandart.org/open-access · biodiversitylibrary.org · loc.gov/free-to-use · publicdomainreview.org · folkloristan.com/designarchive · en.wikipedia.org/wiki/Truck_art_in_South_Asia
