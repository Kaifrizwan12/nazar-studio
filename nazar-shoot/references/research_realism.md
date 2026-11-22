# Research: what makes an image read as real (papers behind the shoot engines)

Pass run 2026-11-22 (web search; papers checked on the authors', publishers' or arXiv pages). Tags as in `../../nazar-core/references/research_path.md`. This complements `research.md` (compositing practice) with peer-reviewed vision science, graphics and forensics.

## Findings and where they went
| Paper | Finding | Became |
|---|---|---|
| Ostrovsky, Cavanagh & Sinha, "Perceiving illumination inconsistencies in scenes", *Perception* 34 (2005) 1301-1314 [SRC] | People are surprisingly insensitive to lighting inconsistencies; detection needs slow, serial search. The visual system does not force its lighting estimates to agree across a scene | Don't trust a first glance at our own composites: check shadows with the eight clues (`../../nazar-study/references/reading_light.md`) and the engines, not by feel. Several small errors together are what trained viewers catch |
| Fleming, Dror & Adelson, "Real-world illumination and the perception of surface reflectance properties", *Journal of Vision* 3(5) (2003) 347-368 [SRC] | People judge gloss and finish accurately only when the illumination has realistic statistics (edges, bright compact sources); unrealistic light makes materials unreadable | Brief real, structured light (a window, a strip, the sky), never "even lighting"; the pack's finish only reads under it. `shotplan.py` names the source's size and shape |
| Xue, Agarwala, Dorsey & Rushmeier, "Understanding and improving the realism of image composites", *ACM TOG* 31(4), SIGGRAPH 2012 [SRC] | Tested which 2D statistics matter for composite realism with human studies; matching luminance, colour temperature, saturation and local contrast of the foreground to the background improves realism | `composite.py` tone match, black lift and saturation; `look.py compare` checks the whole frame against the target in the same terms |
| Zhu, Krähenbühl, Shechtman & Efros, "Learning a discriminative model for the perception of realism in composite images", ICCV 2015 [SRC] | A model trained on real vs composite images predicts human realism judgements and can adjust colour to improve them | Supports colour and tone matching as the first fix; a learned judge is beyond our engines, so we keep measurable checks |
| Debevec, "Rendering synthetic objects into real scenes", SIGGRAPH 1998 [SRC] | Light the inserted object with the scene's measured illumination; differential rendering adds its shadows and bounce to the photo and tolerates approximate local reflectance | The proxy route (`proxy.py`): a stand-in in the scene measures the light at the product's position; our pixels take that shading |
| Kee, O'Brien & Farid, "Exposing photo manipulation with inconsistent shadows", *ACM TOG* 32(3) (2013); "...from shading and shadows", *ACM TOG* 33(5) (2014) [SRC] | Lines from cast-shadow points through the objects that cast them must meet at one light position; combining many weak constraints exposes a fake when no single light fits | Every shadow in a composite must point back to the same key (`camera_pass.md` QA); the plate is rejected when its own shadows disagree |
| Farid, "Lighting (in)consistency of paint by text", arXiv 2207.13744 (2022); "Perspective (in)consistency of paint by text", arXiv 2206.14617 (2022) [SRC] | Text-to-image models have no explicit physical model; their lighting, cast shadows, reflections and perspective can be tested with forensic geometry | Read every generated plate's light and vanishing lines before compositing (`gemini_routes.md` iterate step 3) |
| Sarkar, Mai, Mahapatra, Lazebnik, Forsyth & Bhattad, "Shadows don't lie and lines can't bend! Generative models don't know projective geometry... for now", CVPR 2024 [SRC] | Classifiers using only geometry (perspective fields, line segments, object-shadow relations) detect generated images better than pixel detectors: current generators don't reproduce projective geometry reliably | The planner owns the geometry the model can't: camera height, perspective, shadow direction and length (`shotplan.py`); reject plates whose straight lines converge to more than one point |
| Hunter, Biver & Fuqua (with Reid), *Light: Science & Magic*, 6th ed., Routledge 2021 [SRC, preview pages] | The **family of angles**: a light inside it produces direct (specular) reflection, outside it does not; the family depends on the camera's position; a longer lens shrinks it; a polariser helps when the reflection is polarised | `shotplan.py` samples the pack face and finds glare per light, then searches for the nearest clean position |
| Schlick's approximation of Fresnel reflectance (Schlick 1994) [KNOWN] | Reflectance rises steeply toward grazing angles (R0 about 4% for lacquer, glass, acrylic) | `shotplan.py` floor reflection strength from the camera's height |

## Practice sources added this pass
- Google, *7 tips to get the most out of Nano Banana Pro* (2025-11-20): https://blog.google/products/gemini/prompting-tips-nano-banana-pro/
- Google Cloud, *The ultimate Nano Banana prompting guide* (2026-03-06): https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana

## Links
- Ostrovsky et al.: https://core.ac.uk/download/4384232.pdf
- Fleming et al.: https://persci.mit.edu/pub_pdfs/Fleming_JOV_2003.pdf
- Xue et al.: https://graphics.cs.yale.edu/sites/default/files/2012sig_compositing.pdf
- Zhu et al.: https://ri.cmu.edu/publications/learning-a-discriminative-model-for-the-perception-of-realism-in-composite-images
- Debevec 1998: https://www.pauldebevec.com/Research/IBL/debevec-siggraph98.pdf
- Kee, O'Brien & Farid 2014: https://farid.berkeley.edu/downloads/publications/tog14.pdf ; 2013: https://history.siggraph.org/?p=108529
- Farid 2022: https://arxiv.org/abs/2207.13744 ; https://arxiv.org/abs/2206.14617
- Sarkar et al. 2024: https://arxiv.org/abs/2311.17138
- *Light: Science & Magic*: https://www.routledge.com/Light-Science--Magic-An-Introduction-to-Photographic-Lighting/Hunter-Biver-Fuqua/p/book/9780367860271

## Gaps
- No study measures realism for packaging composites specifically; the rules extend general findings.
- The pouch bend model in `shotplan.py` is a simple left-right curve; real pouches crease irregularly, so treat glare percentages as a guide, not a measurement.
- Zhu et al.'s year and venue are from the CMU page; confirm before quoting in client copy.
