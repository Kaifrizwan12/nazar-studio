# Research behind the shoot rules

Pass run 2026-11-21 (web search plus one page read). Tags as in `../nazar-core/references/research_path.md`: [SRC] a primary or technical source, [KNOWN] consistent practitioner practice across several sources, [IDEA] our own inference. Most compositing advice online is tutorial or vendor content; it is used for consistent practice only, never as numbers.

## Findings and where they went
| Finding | Tag | Became |
|---|---|---|
| Sample the plate's darkest shadow and use it as the inserted element's black point; match darks, mids and highlights per channel | [KNOWN] | Black lift to plate P2; QA check "product P1 >= 90% of plate P1" |
| Light wrap is not uniform: a bright sky wraps an edge differently from dark ground; keep it out of shadowed areas | [KNOWN] | Wrap samples the local plate behind each edge, not one colour; QA check "edge pixels lean toward the room" |
| A hard, aliased or dark edge is the fastest giveaway; dark fringing breaks a shot | [KNOWN] | Pre-blur, wrap, QA check "no dark fringe outside the silhouette" |
| Contact shadow and cast shadow are separate: a small tight dark under the product, not a band round the silhouette; the cast shadow follows the light | [KNOWN] | `_contact` ellipse + projected `_ground_shadow`; QA "base 25% darker", "falls away from the key" |
| Cast shadows are darkest and sharpest at the contact point, softer and lighter with distance; a default drop shadow reads fake | [KNOWN] | Penumbra grows with distance (blur blend by row) and fades; QA "darkest at the base" |
| Ambient-occlusion-only contact shadows lack direction | [KNOWN] | Contact plus directional cast shadow, never one alone |
| Grain is several properties (amount, size, level dependence, channel): heavier in blacks and blue on digital; CG renders are too clean | [KNOWN] | Grain measured from the plate's flattest third, added to the product only; QA "0.6-1.6x" |
| Common fake tells: wrong lighting, weak shadows, mismatched scale, exposure and colour cast, focus/depth of field, missing grain, floating | [KNOWN] | By-eye QA list in `camera_pass.md` |
| Lateral CA is expressed as % of distance from the image centre: < 0.04 insignificant, 0.04-0.08 low, 0.08-0.15 moderate, > 0.15 strong; visible on tangential edges near the corners, not on radial edges, not measurable near the centre | [SRC] | `lateral_ca` radial R/B magnification, off by default, cap 0.12%, CLI `--ca`; self-test checks centre = 0, edge outward, within cap |
| Halation: strong light passes the emulsion, reflects off the base and re-exposes the red layer, so the glow is red-orange and appears only where light exceeds latitude; obvious around tungsten, barely visible around LEDs | [SRC] / [KNOWN] | Warm halation only above a highlight threshold, low strength, guidance in `camera_pass.md` |
| Frosted or satin translucent products: front light reveals surface texture; colour reads truest lit from the front; angled light shows finish; a flat front-lit shot makes plastic featureless; backlight through a diffuser for glow | [KNOWN] | Plate brief asks for one angled key; sheen is broad and soft; frosted-film behaviour (contact clarity, milky veil) stays in the pack render, not the plate |
| Match light direction, colour, grain and edge quality across layers matters more than any single effect | [KNOWN] | The self-test reports every check together; one PASS is not "real" |
| Our own job: pale ghost shadows, floating packs and creaseless film were rejected as "AI slop" | [ARCH] owner reviews | Owner rules in `SKILL.md`, `LESSONS.md` |

## Sources (accessed 2026-11-21)
- Lens-test documentation on lateral chromatic aberration, measurement and severity scale: https://imatest.com/docs/sfr_chromatic
- Chromatic aberration overview with measured example: https://www.imatest.com/imaging/chromatic-aberration/
- Chromatic aberration recovery on arbitrary images (thesis, LCA magnitudes up to ~10 px on a zoom lens): https://arxiv.org/pdf/2110.04030
- Compositing tips (black levels, matching plates): https://www.oocities.org/tokyo/fuji/8010/fxguide/compositingTips.html
- Techniques for photorealism in compositing a 3D element: https://studiodaily.com/2006/04/techniques-for-photorealism-in-compositing
- Advanced integration in VFX (O'Reilly chapter): https://www.oreilly.com/library/view/digital-visual-effects/9780133812664/ch06.html
- Light wrap course note: https://www.lynda.com/Nuke-tutorials/How-apply-light-wrap-your-comp/450278/547276-4.html
- Three compositing tips (grain, light wrap): https://nofilmschool.com/2015/03/basic-tips-make-after-effects-compositing-look-better
- How to properly judge composites: https://fstoppers.com/composite/how-properly-hate-composites-and-visual-effects-works-277438
- Realistic compositing checklist: https://junoschool.pages.dev/article/realistic-compositing-checklist-after-effects/
- Why CGI ads look fake, a quality checklist: https://dev.to/maverickframe/why-cgi-ads-look-fake-a-practical-quality-checklist-for-brands-3iol
- Realistic cast shadow (shape, blur, blend): https://photoshopcafe.com/tutorials/cast_shadow/cast_shadow.htm
- Very realistic shadows (fade with distance): https://photoshopcafe.com/how-to-make-very-realistic-shadows-in-photoshop/
- Cast shadow vs drop shadow: https://www.photoshopessentials.com/?p=378
- Product scene scale and contact shadows: https://dreamina.capcut.com/ai-image/product-scene-scale-contact-shadows
- Halation, physics and simulation: https://blog.dehancer.com/articles/halation/
- Understanding halation: https://www.cined.com/chasing-the-glow-understanding-halation-and-why-filmmakers-keep-coming-back-to-it/
- Emulating film halation in grading: https://mixinglight.com/color-tutorial/emulating-film-halation-in-davinci-resolve
- Shooting translucent products on white with two lights: https://www.diyphotography.net/?p=179431
- Backlighting translucent objects: https://digital-photography-school.com/backlight-translucent-objects-dramatic-effect/comment-page-1
- Photographing flat plastic samples (surface and transparency): https://www.uniquephoto.com/community/qa/how-can-i-photograph-flat-plastic-samples-so-their-surface-and-transparency-are-visible

## Gaps
- No primary study measured "what makes a composite read as fake" for packaging; the list is consistent practice, not evidence.
- Translucent-film lighting advice found online is thin; the frosted-film model in the owner's pouch renders (contact clarity, milky veil, coloured shadow) remains our own [IDEA], validated by owner review, not by a source.
