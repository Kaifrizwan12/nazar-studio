# Flavour-cycle loops

A short loop that cuts through every SKU on the beat: for a client PDF, a case study and the feed. Proven on the owner's five-flavour pouch range (4:5, 30 fps). Detailed motion systems live in `../nazar-motion/`.

## Structure
| Part | Spec |
|---|---|
| Frame | 1080 x 1350 (4:5), 30 fps |
| Ground | Each SKU's own tint, with its own flat print art or flavour name set huge, tone on tone, behind the pack |
| Pack | The real front render, centred a little low (about 51% of height, 72% of frame height) with a soft drop shadow |
| Cut | Hard cut per flavour, about 14 frames (~0.47 s) in round one; round two 4 frames faster so it accelerates |
| Push-in | The pack pops from 96.5% to 100% scale on each cut, ease-out cubic |
| Continuity | Background marquee rows drift on a global frame counter, so motion carries across the cuts instead of restarting |
| Land | Hold on the hero SKU for about 1 s, then an end card (about 1.3 s): brand, range line, tint bar, small studio signature |
| Texture | Film grain cycled over 4 frames and a soft vignette, same as the stills |

## Exports
- MP4: H.264, yuv420p, CRF 18, faststart.
- GIF: 15 fps, 540 px wide, palette of about 160 colours, bayer dither.
- Strip: one frame per flavour plus the end card, for the contact sheet.

## Rules
- Every SKU gets the same device and the same timing (all-or-none). If one SKU's art changes, re-render the loop.
- The pack is the real render; never an AI video of the pack. AI video plates follow the same stamp rule as stills.
- No text on the moving frames beyond what is on the pack; the words live on the end card.
