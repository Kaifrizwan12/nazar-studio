# Grading, effects and pose

Confidence tags: [V] confirmed in sources, [K] standard technique, [F] practitioner folklore (a hint, never a fact). Engines: `grade.py`, `pose.py`.

## Describe the transform, never the film stock
- **Steve Yedlin, Display Prep Demo (ASC)** [V]. After one fixed transform, viewers couldn't tell film from digital capture; he argues a "look" is display-prep maths applied in post. He published no measurement data and didn't reveal which shots were film.
- **Rule:** write a person's look as measured parameters (lifted floor at L 0.30, warm highlights, grain σ 0.013), never as "Portra" or "Fuji". No measured source separates stocks [F].

## Grading: what's measurable
| Feature | Computation (OKLab unless noted) | Source |
|---|---|---|
| Look stats | Mean and std of L, a, b over all pixels | Reinhard et al., "Color Transfer between Images" (2001): mean+std in lαβ is the whole transferable look [V] |
| Look as a stored object | Normalise, then stylise; styles kept as presets | Ke et al., "Neural Preset", CVPR 2023, pp. 14173–14182 [V]; GPU-only, cited not built |
| Colourfulness | rg = R−G, yb = ½(R+G)−B; √(σrg²+σyb²) + 0.3√(μrg²+μyb²), on 0–255 RGB | Hasler & Süsstrunk, SPIE 2003; r > 0.9 against observers [V] |
| Split-toning | Mean a/b of the darkest and brightest 20% **by rank** (a threshold fails when a crush puts 20% of pixels at one value); split when both chroma > 0.02 and hues sit > 60° apart | [K] |
| Faded / matte blacks | P1 of L ≥ 0.22 with contrast < 0.6. OKLab L is perceptual, so even true black reads ~0.12 | [K], calibrated in `examples/make_grade_demo.py` |
| Crushed blacks | Share of pixels with L < 0.06 above 3% | [K] |
| Highlight roll-off | Slope P90→P99, clipped share | [K] |
| Saturation by lightness band | Mean chroma in five L bands. **Portfolio level only:** in one image a white sky looks the same as rolled-off highlights | [K] |
| Palette breadth | Chroma-weighted hue histogram, 12 bins; mono = mean C < 0.012; duotone = top-2 bins > 95% and ≤ 2 families | [K] |
| Vignette | **Every** corner darker than the centre (max corner ratio < 0.85). A dark floor or bright sky alone doesn't count | [K]; robust fits: Microsoft US 8,577,140; Zheng et al. radial gradients [V] |
| Grain | Immerkær (1996) noise σ on the flattest third of 8×8 blocks; grain is correlated and level-dependent, so measure on flat patches | [V]; Liu, Tanaka & Okutomi TIP 2013 |
| Softness | Variance of the Laplacian | [K] |
| Halation / bloom | Brighter **and** warmer ring around clipped highlights; a blurred white edge alone isn't halation | [K] |
| Chromatic aberration | R/B displacement against G at strong edges, growing with radius | US 8,965,118 [V]; built as an optional camera-pass step (off by default, capped at 0.12% of centre-to-corner) with a measurement for its self-test: `nazar-shoot/engine/composite.py` (`lateral_ca`, `measure_ca`) |
| Film-colour history | FilmColors (Flueckiger, University of Zurich, ERC 670446, 2015–21) and the Timeline of Historical Film Colors | [V]; no published "taxonomy of colour aesthetics" found |

## Look labels (`grade.py looks()`)
| Label | Rule | Status |
|---|---|---|
| Monochrome | Mean C < 0.012 | measured |
| Duotone / limited | Top-2 hue share > 0.95, ≤ 2 families | measured |
| Split-toned | Shadow and highlight chroma > 0.02, hue gap > 60° | measured |
| Teal & orange | Split with shadows at 160–250° and highlights at 30–100° | measured split, folklore name. The mechanism (skin on the orange side, opposite hues) is practitioner lore; Pixflow notes it was tuned for lighter skin [F] |
| Faded / matte | P1 ≥ 0.22, contrast < 0.6 | measured |
| Bleach-bypass-like | Chroma 0.012–0.05, contrast > 0.7, crushed > 1% | measured mechanism (see `nazar-art-direction` photography §1b) |
| Vignette, grain, soft, bloom | Rules above | measured |
| Cross-processed-like | Colourfulness > 80, contrast > 0.8, clipped > 2% | folklore; varies by stock and lab |

Known-answer test: `examples/make_grade_demo.py` renders one original scene in 6 grades, and the engine names all 6 blind (README genre card, panel 01).

## Pose from 2D keypoints (COCO-17)
- **Precedent:** Impett & Moretti, "Totentanz: Operationalizing Aby Warburg's Pathosformeln", Stanford Literary Lab Pamphlet 16 / *NLR* II/107 (2017) [V]. No study yet classifies a photographer's pose habits; the formulas below are [K].

| Feature | Formula |
|---|---|
| Facing | Shoulder width ÷ torso length (shoulder mid to hip mid). Adults run ~0.7 face-on and ~0.45 at a 50° turn: frontal > 0.45, three-quarter 0.18–0.45, profile below |
| Tilts | Shoulder line and eye line angles |
| Contrapposto | Shoulder angle − hip angle; weight shift when they tilt opposite ways by > 6° |
| Openness | Convex-hull area of the keypoints ÷ torso²; arm extension = shoulder→wrist ÷ (upper arm + forearm) |
| Asymmetry | Mean offset between left and mirrored-right keypoints ÷ torso |
| Hands | Raised (above shoulders); on hip (wrist within 0.35 torso of a hip **and** arm bent, extension < 0.85); at sides (straight arm, below mid-torso); else chest/gesturing |
| Gaze proxy | Nose x minus eye midpoint, ÷ inter-eye distance |
| Framing | Crop point (ankles / knees / waist out of frame), headroom, subject scale, camera-height proxy (head-to-torso ratio; approximate) |

**Install on this Mac (Intel, Python 3.12):**
- MediaPipe ships no Intel-Mac wheel, and current torch is arm64-only.
- Use `pip install "onnxruntime==1.23.2" rtmlib`. That's the last onnxruntime with a cp312 x86_64 wheel (19 MB), and rtmlib is pure Python; models download on first use.
- Without them, `pose.py --keypoints` takes keypoints from any tool.

## Sources
arXiv 2204.13339 (Reinhard overview) · openaccess.thecvf.com (Neural Preset, CVPR 2023) · infoscience.epfl.ch/record/33994 · cordis.europa.eu/project/id/670446 · digitalhumanities.org/dhq/vol/14/4/000500 · yedlin.net (Display Prep Demo) · theasc.com · patents.google.com/patent/US8577140B2 · eecis.udel.edu (Zheng radial gradient vignetting) · cse.buffalo.edu/~siweilyu/papers/mmsec10.pdf · USPTO 8213500 · patents.google.com/patent/US8965118 · pixflow.net (teal and orange) · newleftreview.org/issues/ii107 · pypi.org/project/mediapipe · pypi.org/project/onnxruntime · pypi.org/project/rtmlib
