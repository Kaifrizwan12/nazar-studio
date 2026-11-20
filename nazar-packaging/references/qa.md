# Packaging QA and tests (on top of core `qa_design.md`)

## Tests
- [ ] **Shelf line-up:** among 6–10 real competitors at true size, at 2–3 m, in greyscale, in a 2-second glance. Brand found, variant clear.
- [ ] **Online thumbnail:** 150–300 px on white; brand and variant readable.
- [ ] **Full range sheet:** every current and planned SKU side by side; no colour collisions; the brand block consistent.
- [ ] **Physical mock-up:** printed, cut, folded or sealed. Fit, window position, readability, opening experience.
- [ ] **Substrate proof:** colours checked on the real material (kraft, film, metal).
- [ ] **Barcode and QR scan** from the proof, with several phones and a retail scanner if possible.

## Design
- [ ] Front-of-pack hierarchy: brand → name → variant → one benefit. Nothing extra fighting.
- [ ] The product is visible or truthfully represented (no misleading imagery or scale).
- [ ] Back-of-pack story in the brand voice; the giggle placed where it rewards a closer look.
- [ ] Every language fits at or above the legal minimum type size.

## Compliance (the client confirms; you check that it's present)
- [ ] All mandatory information is present, in the client-approved wording, for each market
- [ ] Claims and certification marks are only those the client has proven
- [ ] Allergens are emphasised as required
- [ ] The variable-data zone is placed and sized as the converter specified
- [ ] Recycling marks are correct for the actual structure

## Production
- [ ] The preflight checklist in `production.md` passes
- [ ] The converter's dieline is used unaltered; the artwork respects seals, folds and the glue area
- [ ] Spot colours, finishes and white ink are on correctly named layers
- [ ] Contract or substrate proof approved and signed; press check done on the first run

## Handover
- [ ] Print-ready PDFs, live masters, the range template for future SKUs, a colour spec sheet, the approved proof references, and a README for reorders

## Render and family QA (learned the hard way)
- [ ] **Look at fronts AND backs sheets**, every line together. Back-only faults (a signature on a band line, a wrong-colour mark) hide in a fronts-only sheet.
- [ ] **Render-only zones get clearance too:** no ink within 3 mm of a gusset, base band, fold or seal curve drawn on the render, not just on the dieline. Automate it; don't trust the eye alone.
- [ ] **Copy must be true per line.** A family line ("just fruit", "orchard") pasted onto a different product line (vegetables, herbs) is a false claim. Keep the device shared, write the words per line. Same for the lock-up descriptor.
- [ ] **Never name other products or brands** in pack copy or decks (no competitor names, no unrelated snack words). Scan strings automatically.
- [ ] **One-ink marks route to one layer.** A studio signature or small icon gets one ink (white on tinted film), never a caller-supplied dark that prints black by accident.
- [ ] **Multi-packs are built from the real single-pack renders,** never redrawn side profiles (they read as slop).
