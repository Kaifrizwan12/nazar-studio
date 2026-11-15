# Pattern extraction across creative disciplines

Confidence tags: [V] confirmed in sources, [K] standard technique, [UNV] unverified. "In engine" means `engine/visual.py` computes it today. Everything else is a documented method for a future engine build, or for the qualitative read.

## The principle (why the method holds for any medium)
- **Style is consistent choices across a body of work, and the maker confirms the intent.**
- Nelson Goodman, "The Status of Style", *Critical Inquiry*, June 1975, reprinted in *Ways of Worldmaking* (1978), rejects the idea that "subject is what's said, style is how it's said" [V opening].
- Herbert Simon, "Style in Design" (Design Research Association; cited as 1971 or 1975) is the design-side framing [V exists].
- Cite both as framing only. The method stays the same in every medium:
  1. measure choices,
  2. test which choices hold across the whole archive,
  3. hand the *why* back to the maker.

## Illustrators: line quality
| Feature | How | Source | In engine |
|---|---|---|---|
| Stroke width and line-weight variation | Min of horizontal/vertical ink runs per pixel (cheap stand-in for the Stroke Width Transform) | Epshtein, Ofek & Wexler, CVPR 2010 [V] | yes |
| Stroke direction / hatching habit | Gradient-angle histogram on ink edges; concentration = 1 − normalised entropy | [K] | yes |
| Line-led vs. fill-led | Edge pixels ÷ ink pixels | [K] | yes |
| Per-stroke length, curvature and orientation histograms | Skeletonise, split at junctions, measure segments | Shaheen et al., "Stroke Authorship Recognition", CGF 2016 [V abstract] | no (needs skimage) |
| Stroke-level attribution | Segment and classify strokes; 70–90% per stroke, >80% per drawing on Picasso/Matisse/Schiele | Elgammal et al., AAAI 2018 [V abstract] | no |
| Taper at stroke ends | Width sampled along the skeleton near endpoints vs. mid-stroke | [K] | no |

- **Tacit (confirm loop only):** why a line breaks, and what a mark means.
- **Tested on real prints (Dürer woodcuts vs. Rembrandt etchings, CC0):** `strokes.py` needs roughly **2400 px or more** to read line. On web-sized images (a few hundred px) a fine line is 1–2 px wide and taper and pressure swing read identically for everything. At full resolution, **loose ends per 1k px and straightness separate the media** (woodcut 14–27 and 0.81–0.89; etching 30–38 and 0.80–0.84), but **taper and pressure swing still don't**: a carved or etched line has no pen pressure. So it answers *how continuous is the line*, not *how hard was it pressed*. It also can't read tonal lithographs or colour prints (it measures paper grain). Use it on line art.

## Shape language
| Feature | How | Source | In engine |
|---|---|---|---|
| Angular vs. rounded | Share of edge pixels whose direction turns more than 50° against neighbours | [K] | yes |
| Corner sharpness and curvature distribution | Contour polygon vertex angles (OpenCV) | [K] | no |
| Edge complexity | Box-counting fractal dimension | Taylor's Pollock work is **contested**: Jones-Smith & Mathur, *Nature* 444 (2006), found random scribbles also pass. Use only as "busy vs. calm", never for attribution [V] | no |

## Graphic design layout
| Feature | How | Source | In engine |
|---|---|---|---|
| Air, balance, thirds, symmetry, density | Pixel statistics | see `visual_design.md` | yes |
| Grid estimate and alignment consistency | Cluster element-box edges; share of edges on shared lines | Shen, Shamir & Igarashi, LayoutRectifier, arXiv 2508.11177 [V] | no (needs OCR boxes) |
| Visual importance | Predicted importance map | Bylinskii et al., UIST 2017, arXiv 1708.02660 [V] (design count reported inconsistently: check before quoting) | no |
| Type-size scale, margins, text vs. image share | OCR boxes plus non-text regions | [K] | no |

- **Tacit:** why the grid breaks, and hierarchy as an argument.

## Type and lettering
- Font identification works but isn't reliable. DeepFont (Wang et al., ACM MM 2015) reports >80% **top-5** on real images; top-1 is roughly 60–70% [V via mirror]. So *ask* which typefaces the person uses rather than guessing.
- **Measurable habits** (from OCR boxes) [K]:
  - x-height / cap-height ratio,
  - share of all-caps,
  - tracking (gap ÷ glyph width),
  - weight (ink ÷ box).
- **Tacit:** hand-lettering intent and custom glyphs.

## Photographers
| Feature | How | Source | In engine |
|---|---|---|---|
| Tone curve: shadows, mids, highlights, contrast | OKLab L percentiles | [K] | yes |
| Colour lean (warm/cool, green/magenta) and chroma | Mean OKLab b / a, mean chroma | [K] | yes |
| Lens habits: focal length, aperture, shutter, ISO distributions | EXIF (`Pillow getexif`), compared with a baseline where ~50% of shots are normal to slightly wide | UCSB EXIF thesis; Image Engineering large-scale stats [V] | no |
| Horizon placement, subject size | Hough lines; saliency or person box ÷ frame | [K] | no |

- Photographer identification is an open problem. Style is "much more subtle than in painting" (arXiv 1508.05038) [V].
- **Tacit:** what they wait for, and what they refuse to shoot.

## Video editors and directors
| Feature | How | Source | In engine |
|---|---|---|---|
| Cuts | PySceneDetect `AdaptiveDetector` | docs [V]; weak on sports footage [V] | no |
| Shot length: **median and distribution**, not just the mean | From the cut list | Salt (1974); Tsivian's Cinemetrics (2005). Redfern shows the mean (ASL) alone is statistically weak [V] | no |
| Cutting rhythm | Log-log slope of the shot-length power spectrum (1/f) | Cutting, DeLong & Nothelfer, *Psych Science* 2010: 150 films, 1935–2005 [V] | no |

- **Tacit:** why a cut lands where it does.

## Across disciplines: embeddings
- **CLIP/DINO embeddings** per piece → cluster the portfolio into "modes" and find recurring motifs by cosine similarity [K].
- **Evidence:** frozen CLIP plus an MLP reaches about 72.8% artist accuracy over 372 artists; WikiArt 27-style state of the art is about 71%. VLMs make errors experts reject (KU Leuven, arXiv 2409.03521) [V].
- **Use embeddings to group and find motifs, never to judge identity.**

## Build order (most signal per line of code)
1. ✅ Palette habit, air, balance (`visual.py`).
2. ✅ Line weight, line variation, direction, line vs. fill, angularity.
3. ✅ Tone curve and colour lean.
4. ✅ Skeleton strokes: Zhang–Suen thinning, crossing-number junctions, spur pruning, taper, pressure swing, loose ends (`strokes.py`, numpy only).
5. ✅ Alignment, columns, margins, type scale from x-height to baseline, OCR-free (`layout.py`).
6. ✅ EXIF lens, aperture, shutter, flash and orientation habits (`exif_habits.py`).
7. ✅ Cuts, median and distribution of shot lengths, pace trend, 1/f slope, grade across shots (`video.py`, ffmpeg via imageio-ffmpeg).
8. ✅ Style modes (k-means plus silhouette over all features) and recurring elements (256-bit tile dHash) (`cluster.py`). Embedding-based motifs remain optional.
9. ✅ Deep grading and effects with look labels (`grade.py`; see `grading_effects_pose.md`).
10. ✅ Pose habits from keypoints (`pose.py`; detection via rtmlib, optional).

Every engine has a known-answer test in `examples/` (README genre card).
