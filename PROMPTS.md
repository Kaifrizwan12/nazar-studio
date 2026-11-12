# Prompts

Paste one of these into Claude in the client repo, after filling the `<…>` parts. Each prompt calls the right kit and sets how Kaif works. Delete lines that don't apply.

---

## 0. Start any project (Claude picks the kits)
```
Use nazar-core and the right nazar-* kits for this job.
Client: <name>. They sell <product/service> in <city/markets> to <audience>.
The job: <e.g. strategy + logo + brand book + social launch>.
Nuances: <anything special: languages, nevers, competitors, mood, budget>.
Deadline: <date>.

Work the Kaif way: read the repo first, then ask me every intake question up front with options and your recommendation (facts as plain text, don't guess). Research from archives and primary sources and log it in research/. Generate concepts with at least 3 ideation methods, then show me 3 routes (one sharp, one bold, one unorthodox, and one route that turns up my taste dial: pop culture, desi, cinematic or Insta-savvy, if the brand can carry it) with a recommendation. Lock the idea in one sentence before building. QA everything against qa_design.md before showing me. Keep it sober, graphics-heavy, specific, never generic.
```

## 1. Strategy (nazar-strategy)
```
Use nazar-strategy. Client: <name>, <what they sell>, <where>, <who buys>.
I need: positioning (onlyness statement + tension + beliefs), <naming? tagline? architecture?>.
Competitors: <list>. What customers say about them: <quotes if any>.
Run intake round 1, research (category archive, competitor map with visual codes, audience), then show me 2–3 options at each fork with your pick. Taglines: give me 20, keep the 3 with an edge, savvy and specific, no generic lines. First-pass trademark and handle checks on any name, with the lawyer caveat. End with a 12–20 page strategy deck and a locked one-sentence brand idea.
```

## 2. Logo (nazar-logo)
```
Use nazar-logo. Client: <name> (spelling in each script: <…>). New mark / refresh / redraw: <…>.
Brand idea (from strategy): <one sentence>. Must work hardest on: <avatar / shelf / signage / embroidery / motion>.
Off-limits: <colours, symbols>. Nice classes: <…>.
Do the competitor marks wall and archive research, then a real concept session (reframe the brief, word→image collisions, the name holds the mark, semiotic choice, random entry or provocation) with 50–100 thumbnails clustered into territories. Show me territories first, then 3 routes at equal finish with construction drawings, test sheets (blur, 16 px, one colour, reversed, material tests) and a trademark first pass. Recommend one. After I pick: lockups, clear space in a mark unit, minimum sizes, and the full export matrix named to convention.
```

## 3. Brand book (nazar-brand-book)
```
Use nazar-brand-book. Client: <name>. Logo files are in <path> (exact artwork, never redraw).
Locked idea: <one sentence>. Tagline: <…>. Languages: <…>.
Ask me all 3 intake rounds first. Propose 2–3 complete anatomies (narrative device + format + modules), at least one that isn't a dark-grid deck. Build palettes from evidence (place, material, archive plates, pigments) with local-language names and measured contrast. Pick 2–4 unorthodox devices that grow from the idea, with a reveal page. Applications as spec sheets, never cartoon mockups. Build with the engine section by section, show me contact sheets, and QA every page (alignment, gaps, text starts, contrast, glyphs) before I see it. Deliver PDF + PNGs + asset pack + Behance text.
```

## 4. Packaging (nazar-packaging)
```
Use nazar-packaging. Product: <…>, format: <pouch/carton/bottle/…>, range: <SKUs now and in 2 years>.
Sold in: <retail channels, online?>. Printer/converter: <name or TBD>.
Legal text, certifications, barcodes and nutrition data will come from the client, so ask, never invent.
Do shelf research and a category-codes sheet (keep / break / own), then range architecture options on a shelf line-up, then 3 concept routes on the real dieline. Test at 2–3 m in greyscale among competitors, and as an online thumbnail. Then production: get the printer's spec, colour strategy (CMYK / spot / white ink), finishes for meaning, preflight, proofs on the real substrate, press check notes. Hand over a range template for future SKUs.
```

## 5. Social (nazar-social)
```
Use nazar-social. Brand: <name>. Platforms: <IG / TikTok / LinkedIn>. Who posts: <…>. Capacity: <posts/week, video yes/no>.
Audit our accounts, 5–10 competitors and 5 accounts our audience loves outside the category. Give me 3–4 pillars with witty names, grid logic options as 12-post previews, and one dial-up route (pop culture, desi, cinematic or meme-native, grammar only, no protected assets). Build 3 templates + story and reel kits checked in the 3:4 grid crop and the 9:16 safe zones. Write 10 hooks per idea and keep the sharpest; captions specific and local, never generic. Design the 9-post launch grid, and write the team playbook with the slop test.
```

## 6. OOH (nazar-ooh)
```
Use nazar-ooh. Brand: <name>. Media plan: <sites/formats/sizes, or "recommend">. Dates: <…>. Area languages: <…>.
Research the sites (roads, speed, sightlines, neighbourhood). Give me 3 routes, each with its screen twin (the photo people take, a reel, geo-ads or a QR worth scanning), including one bold dial-up route with local wit or cinematic scale. One idea per board, about 6–7 words for fast roads, letter heights checked against viewing distance (use the generous rule), tested at thumbnail size and on site photos, day and night. Re-compose for each format, don't scale. Guerrilla only if legal and safe. Files to the media owner's spec, plus an install spec and a case-study plan.
```

## 7. Motion (nazar-motion)
```
Use nazar-motion. Brand: <name>. Logo files (layered vector): <path>. Where motion lives: <social / web / screens / film>.
Start from behaviour: 3 ways the brand could move, from its idea. Storyboard the logo animation (full ident 1–2 s, sting, loop, end frame) as engine-rendered frames with timing and easing notes. Define the motion system (one signature easing, a 3–4 step duration palette, an entrance pattern, a transition from the brand's geometry) and export it as CSS/JSON tokens with reduced-motion rules. Offer a cinematic treatment (title cards, credits, letterbox, grain) if the brand fits. Deliver the export matrix (MP4, ProRes alpha, GIF/WebP, Lottie, sound) and a motion spec PDF.
```

## 8. Web (nazar-web)
```
Use nazar-web. Brand: <name>. Site purpose: <…>. The one primary action: <…>. Platform: <…>. Who maintains it: <…>.
Audit, then sitemap and journeys, then content-first wireframes with real copy. Build web tokens (base + semantic) from the brand system, a fluid type scale with clamp(), a grid and the components in every state. Design 3 key pages first, with 1–2 signature moments only this brand would do (a scroll story, a cinematic section, the brand's giggle). WCAG 2.2 AA throughout, fast on a mid-range phone. Hand off tokens, components, designs at 3 breakpoints, and a motion spec, and QA the build.
```

## 9. Art direction (nazar-art-direction)
```
Use nazar-art-direction. Brand: <name>. Needed: <photography / illustration / icons>. Uses: <…>. Production level: <…>.
Give me 3 one-line points of view, each with references where you name the exact qualities (light, grade, crop, composition), including one cinematic option. Write the style rules, then the shoot brief, shot list (with layout purpose and ratios) and call sheet. For illustration, a style guide anyone can extend; for icons, a 24 px grid with keylines, one stroke and optical balance. No stock, no AI images, and a rights and releases log for everything.
```

## 10. Pitch and client process (nazar-pitch)
```
Use nazar-pitch. Prospect: <name>. What they asked for: <…>. Notes from our call: <…>.
Write the discovery summary, then a proposal with 3 options that differ in outcome (core / strategic / comprehensive), priced on value with a sanity check against cost, with clear scope, rounds, exclusions, client inputs, timeline and payment schedule (deposit first). Draft the key agreement terms from the AIGA-style structure (IP on full payment, revisions, change requests, kill fee, licences, portfolio rights), flagged for a lawyer to review. Design the proposal like a small brand book.
```

## 11. Fix after review (any kit)
```
Review notes by page/number: <e.g. "14 logo too big, 22 gap under heading, 31 text overlaps line">.
Fix exactly these, then search every other page or file for the same class of problem and fix those too. Re-run QA and report: what you fixed (P1/P2), what you left (P3) and why. Show me the updated contact sheet.
```
