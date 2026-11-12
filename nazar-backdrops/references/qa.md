# Backdrops QA

Run with `../../nazar-core/references/qa_design.md` and the 30-second test in `ai_tells.md`.

## Skeleton
- [ ] The logo sits in the same corner, at the same relative size, on every format and mode.
- [ ] The margin and edge device are identical (as a ratio of the short side) across formats.
- [ ] Dark and light versions are pixel-identical in layout; only colours differ.
- [ ] The centre is empty on every clean backdrop.
- [ ] The backdrop covers ≤ ~15% of the canvas.

## Safe zones
- [ ] 4:5 and 1:1 covers: logo, handle and swipe cue survive the 3:4 grid crop.
- [ ] Story: nothing static inside the top ~250 px or bottom ~250 px.
- [ ] Reel cover: logo and title zone inside the central 1080 × 1440.
- [ ] Avatar and highlight: the symbol is optically centred and fits the circle with air.
- [ ] YouTube: nothing in the bottom-right timestamp corner.

## Brand fidelity
- [ ] Exact logo files (SVG), the on-dark version on dark, the book's clear space respected.
- [ ] Every colour and font traces to the extraction log; font licences cover social use.
- [ ] Contrast passes for every text element (the renderer's warnings are cleared).
- [ ] One accent per backdrop.

## Phone test
- [ ] Viewed on a real phone in dark and light mode, at full size and grid size.
- [ ] Handle and counter readable at arm's length; nothing shimmers or fringes after the platform's compression (post to a private test account if possible).

## Not the AI look
- [ ] No glows, gradients behind type, glass panels or centred-everything.
- [ ] Every part (band, corner, counter style) has a one-line reason from the brand book.

## Files
- [ ] Clean + guide for every backdrop; names follow `brand_format_role_mode`.
- [ ] Editable templates delivered and tested by someone on the client team.
- [ ] Usage sheet included, with the date the specs were verified.
