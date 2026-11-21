# Research behind the composers engine (2026-11-21)

Four passes for `engine/composers.py`: how product groups are composed, size truth (the law on misleading pack size and imagery), shadow physics and compositing, attention on portfolio pages, and blending seams when a plate is extended. Tags follow `../../nazar-core/references/research_path.md`. Every source was accessed 2026-11-21. Brands named in rulings are left out; only the pattern is kept.

## 1. Composition conventions for product groups

- **Hero placement [SRC, trade guides].** Group-shot guides put the hero product "up front or in the center" as the anchor, group items of similar size or shape, and keep every product clearly visible. A packshot is the clean product-only view (front, side, a few standard angles); a lifestyle image adds context.
- **Odd numbers [SRC, photography tutorials].** Flat-lay and still-life guides favour groups of 3 or 5 and split big sets into odd clusters. The sources say there is no real consensus on why. Treat it as a habit, not a law.
- **Rule of thirds and negative space [SRC, tutorials].** Put the main product near a thirds intersection. Empty space around the product steers attention to it. How much empty space varies by source (one food guide says half the frame), so no single number holds.

→ Rules (built in):
- One product leads each group: `couple` puts the front in front; `cascade` makes the first item the largest and nearest.
- `fan`, `row` and `scatter` record an advisory note on groups of 4 or 6 ("3 or 5 usually read calmer"). It is a note, not a fail.
- `scatter` keeps a clear gap between products by default (overlap 0). Use `overlap > 0` only for a deliberate toss.

## 2. Scale truth: never show a small pack as big

Misleading size is regulated almost everywhere a deck's products are sold:

- **US [SRC].** 21 CFR 100.100: a food is misbranded if its container is "so made, formed, or filled as to be misleading". Non-functional slack fill in a container that hides its contents is misleading. Six exemptions count as functional (protection, machine fill, and so on). Intent to mislead does not have to be proved.
- **EU [SRC].** The Packaging and Packaging Waste Regulation (EU) 2025/40 applies from 12 August 2026. It prohibits packaging that increases the perceived volume of the product (double walls, false bottoms) unless protected by a design right or trademark that existed before 11 February 2025. It also caps empty space in grouped, transport and e-commerce packaging at 50%, from 2030 or 36 months after the methodology acts (secondary sources disagree on the date).
- **UK [SRC].** The CMA's unfair commercial practices guidance (CMA207, DMCC Act 2024) covers misleading actions and omissions, packaging and labels included. The ASA's advice says images that exaggerate the size or quality of a product are likely to mislead, judged on the overall impression. Upheld rulings include a bouquet pictured larger than the one sold, a TV ad that overstated a portion, and a box pictured with more items than it held.
- **India [SRC].** The CCPA Guidelines for Prevention of Misleading Advertisements (9 June 2022, Consumer Protection Act 2019) bring misleading visual representation into scope. Penalties go up to INR 10 lakh, and up to 50 lakh for repeats. Net quantity under the Legal Metrology (Packaged Commodities) Rules 2011 excludes the packaging. No slack-fill clause was found.
- **Pakistan [SRC, partial].** The Punjab Consumer Protection Act 2005, s.21, and the Sindh Consumer Protection Act 2014, s.21, cover false, deceptive or misleading representation. The section text was not readable from here. The Competition Commission has acted on copycat packaging.

→ Rules (built in):
- `row`, `grid` and `stack` take `true_scale=True` with each product's real `height_mm` or `width_mm`. One px-per-mm is shared, and the tallest real product gets `height` px.
- Missing millimetres raise an error rather than guessing.
- `check_scale()` proves the ratios.
- On a page that compares sizes (30 g beside 250 g), true scale is mandatory. Elsewhere, products shown at the same height must not be read as the same size (label the sizes).

## 3. Shadows: physics and how pros composite

- **Contact vs cast [SRC, compositing guides].** These are separate layers. The contact shadow is the darkening where the object meets the surface, and it signals support. The cast shadow spreads where the object blocks the light. One big blurred blob for both makes a product float.
- **Ambient occlusion as a small, controlled pass [SRC, render docs].** Render AO with a small radius for seams and contact. Set its strength in the composite, multiplied over the background, and keep it off the direct light. Real studio shadows are often lighter than people expect (opinion source).
- **Soft-shadow research [SRC, CVPR 2021].** Soft shadows and an AO map are predicted from the object mask and the light, and give realistic shading near contact points. The silhouette drives the shadow.
- **One light direction [SRC, perception studies].** People assume light comes from above and a little to the left. One study measured the bias at about −22° from vertical, present from age 5. The prior gives way to real lighting cues such as cast shadows. A page whose shadows disagree breaks the cue.

→ Rules (built in):
- One shared `Light` (default −30°, from above-left) drives every composer, so all shadows on a page and across a deck fall down and to the right. The self-test checks every shadow offset and every measured shadow centroid for the same sign.
- Every product gets a soft shadow (thrown by its height, blurred about 3% of its height) plus a contact shadow drawn from its exact silhouette (about 0.6% offset, about 0.2% blur). Tear notches, seal teeth and caps stay readable at the ground line. The self-test checks the notch and teeth in the shadow mask.
- `cast` adds a ground-plane shadow trailing away from the light, fading from the base.
- Shadows are laid back to front, so a front product's shadow lands on the item behind it. In `row(on_top="auto")` the item nearer the light sits on top, so each tuck casts onto its neighbour and reads as depth.
- Flat-lays (`scatter`) throw shadows half as far, because the products lie on the surface.

## 4. Attention on portfolio and case-study pages

- **F, layer-cake and spotted patterns [SRC, NN/g].** The F-pattern still shows on poorly structured text (flipped in right-to-left languages). Layer-cake scanning (headings only) is the most effective. Strong hierarchy breaks the F.
- **Z-pattern [SRC, secondary].** On sparse, image-led pages the eye runs top-left → top-right → diagonal → bottom-left → bottom-right. It suits one-message pages and is a loose tendency, not a path.
- **Left half and top [SRC, academic eye-tracking].** Fixations drop as users scroll, and most time is spent on the left half of the page. Faces pull attention but can distract from key information above the fold.
- **Scroll attention [SRC, NN/g 2018, in research.md].** 57% of viewing time goes above the fold, 74% to the first two screenfuls.

→ Rules:
- Put the line (the one idea) top-left, where the F and the Z both start.
- Put the product group on the opposite side, or the lower right of the Z.
- On a hero bleed, bleed off the right or bottom edge, so the cut-off product points the eye on into the scroll.
- Don't put a busy group under the headline's first fixation.

## 5. Extending a plate: seam blending

- **Multiresolution spline [SRC, Burt & Adelson 1983].** The width of a seam's transition should match the wavelength of the image's lowest prominent frequency: too narrow shows a step, too wide shows a ghost band. Pyramid blending does this per frequency band.
- **Photoshop practice [SRC, Adobe help and tutorial].** Feather the selection before filling (a few px for detail), extend the selection a little into the area to match, and retry when a seam shows. Content-Aware Crop extends a boundary from nearby pixels.

→ Rules (built in):
- `extend_canvas` repeats the edge's own colour profile, smoothed along the edge, and adds grain matched to the edge's own texture (a flat strip reads fake).
- It carries the edge's light falloff on and eases it flat (`trend=True`). Without this, a flat fill beside a gradient showed a visible Mach band at the seam on the first contact sheet.
- It feathers the seam over about 4% of the photo (smoothstep).
- Only even surfaces (table, wall, sky) can be extended. An object cut by the edge is never continued: reshoot, or move the layout instead.

## Sources (all accessed 2026-11-21)
- 21 CFR 100.100 Misleading containers: https://www.law.cornell.edu/cfr/text/21/100.100 ; FDA NLEA dates: https://www.fda.gov/important-nlea-dates ; slack-fill lawsuits overview: https://www.packworld.com/leaders-new/materials/containers/article/22184735/reducing-risk-for-slackfill-packaging-lawsuits-part-one
- EU PPWR 2025/40 summary: https://eur-lex.europa.eu/EN/legal-content/summary/packaging-and-packaging-waste-from-2026.html ; KPMG alert: https://assets.kpmg.com/content/dam/kpmgsites/es/pdf/2025/02/legal.alert-ingles-reglamento-2025-envases-residuos.pdf ; empty-space cap: https://www.packaging-gateway.com/news/eu-sets-50-empty-space-cap-for-e-commerce-packaging/
- CMA207 Unfair commercial practices guidance: https://www.gov.uk/government/publications/unfair-commercial-practices-cma207/unfair-commercial-practices ; ASA misleading advertising advice: https://www.asa.org.uk/advice-online/misleading-advertising.html ; ASA bouquet ruling: https://www.asa.org.uk/rulings/prestige-gifting-ltd-a13-222629.html ; portion-size ruling report: https://marketinglaw.osborneclarke.com/advertising-regulation/birds-eye-ad-banned-exaggerating-size-portions/
- India CCPA guidelines press release: https://pib.gov.in/PressReleasePage.aspx?PRID=1832906 ; analysis: https://www.lkslaw.com/insights/articles/prevention-of-misleading-advertisements-analysis-of-guidelines-issued-by-central-consumer-protection-authority ; Legal Metrology (Packaged Commodities) Rules: https://consumeraffairs.nic.in/organisation-and-units/division/legal-metrology/updated-package-commodity-rule
- Punjab Consumer Protection Act 2005: https://www.courtkutchehry.com/bare-acts/punjab-consumer-protection-act-2005 ; Sindh Consumer Protection Act 2014: https://sja.gos.pk/assets/Updated_Laws/Sindh%20Consumer%20Protection%20Act,%202014.pdf ; Competition Commission order: https://cc.gov.pk/home/vieworders/28
- Contact vs cast shadow: https://dreamina.capcut.com/ai-image/product-scene-scale-contact-shadows ; V-Ray AO for contact shading: https://novedge.com/blogs/design-news/v-ray-tip-using-v-ray-ambient-occlusion-for-controlled-contact-shading ; AO in compositing: https://derekflood.powweb.com/renderdocsDir/pipeline/compFGBG.html ; mental ray AO: https://help.autodesk.com/cloudhelp/2016/ENU/mental-ray-docs/mr_docs/shaders/production/prod_mattecamera.html ; floor shadows in product CGI: https://www.coohom.com/article/how-floor-shadow-elements-are-used-in-product-visualization-and-cgi ; Soft Shadow Network (CVPR 2021): https://www.cs.purdue.edu/homes/bbenes/papers/Sheng21CVPR.pdf
- Light-from-above prior and left bias: https://pmc.ncbi.nlm.nih.gov/articles/PMC3066057 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC2941312 ; https://research.birmingham.ac.uk/files/18225439/Mazzilli_and_Schofield.pdf ; https://www.nature.com/articles/s41598-018-33625-2 ; https://pure.eur.nl/en/publications/the-human-visual-systems-assumption-that-light-comes-from-above-i/
- Composition: https://www.squareshot.com/post/product-group-shot-guide-expert-tips-for-success ; https://www.photoroom.com/blog/product-photography-types-for-ecommerce ; https://www.diyphotography.net/?p=312226 (rule of odds) ; https://en.canon-cna.com/get-inspired/tips-and-techniques/flat-lay-photography-tips/ ; https://www.expertphotography.com/product-photography-composition
- Attention: https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/ ; https://nngroup.com/articles/text-scanning-patterns-eyetracking/ ; https://www.nngroup.com/articles/scrolling-and-attention/ ; https://www.creativebloq.com/web-design/design-jargon-explained-z-pattern-71515717 ; https://aisel.aisnet.org/thci/vol4/iss3/2
- Seams: https://persci.mit.edu/pub_pdfs/spline83.pdf ; https://helpx.adobe.com/photoshop/using/content-aware-fill.html ; https://www.adobe.com/learn/photoshop/in-app/extend-a-photo-boundary-with-content-aware-crop

**Gaps:**
- The text of Pakistan's s.21 and of India's slack-fill position (if any) was not readable.
- The EU 50% empty-space start date differs between secondary sources.
- The odd-number and negative-space conventions rest on tutorials, not studies.
- No eye-tracking study of Behance panels specifically was found.
- None of this is legal advice: when a case study is also used as an ad, the client's counsel checks the size claims.
