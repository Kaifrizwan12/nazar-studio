# Flavour-cycle loops

A short loop that cuts through every SKU on the beat: for a client PDF, a case study and the feed. Proven on the owner's five-flavour pouch range (4:5, 30 fps). Detailed motion systems live in `../nazar-motion/`.

## Structure
| Part | Spec |
|---|---|
| Frame | 1080 x 1350 (4:5), 30 fps |
| Ground | Each SKU's own tint, with its own flat print art or flavour name set huge, tone on tone, behind the pack |
| Pack | The real front render, centred a little low (about 51% of height, 72% of frame height) with a soft shadow **plus** a tight contact shadow (blur about 3 px per 1000 px of pack) so the seal teeth and notches still read |
| Pace | Two styles. **Snap:** hard cut every 14 frames (~0.47 s), round two 4 frames faster. **Cinematic** (the owner's pick for portfolio films): 36 frames (1.2 s) per flavour, one round |
| Push-in | Snap: 96.5% to 100% pop, ease-out cubic. Cinematic: 93% to 100% over the whole shot, cosine ease, plus a sway of about 1.2 degrees |
| Depth and light | Cinematic only: the marquee type is blurred about 2 px per 1080 px (shallow focus) and drifts slowly; a soft diagonal light band crosses the pack's film once per shot, at most 20% strength, masked to the pack |
| Transition | Cinematic: a crisp diagonal wipe of about 12 frames with a soft light glow on the edge. **Never a wide feathered blend between two packs**: inside the feather both packs show at once and the type doubles ("APPGO"). Fade the last shot into the end card over about 12 frames |
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

## Engine
`engine/flavour_cycle.py` renders all of the above for any range from a plain JSON job (items with pack PNG, tint or
`auto`, marquee label; brand title, tagline, sign, fonts, paper and ink; options). `--stills` first (start, mid-shot,
mid-wipe, next shot, end card, safe zone drawn), then the film. Every render writes `<name>_qa.json` with timing,
platform warnings and the flash check. `--selftest` and `engine/test_flavour_cycle.py` guard it.

## Platform rules (dated sources in `research_flavour_cycle.md`, 2026-11-21)
| Use | Preset | Size | Notes |
|---|---|---|---|
| Client PDF, feed | `instagram-feed` | 1080x1350 (4:5) | the default |
| Reels, Stories, TikTok, Shorts | `instagram-reels`, `instagram-stories`, `tiktok`, `youtube-shorts` | 1080x1920 | pack, title and tagline stay inside the safe zone (top ~14%, bottom ~35%, sides 6-11%); the pack gets smaller, never under the UI |
| Case study, Behance | `behance` (1280x720 direct upload) or `--aspect 16:9` for a video-host embed | | Behance takes the middle frame as the thumbnail: make sure mid-film is a clean shot |
| LinkedIn | `linkedin` / `linkedin-square` | 1920x1080 / 1080x1080 | 30 fps cap |
| X | `x`, `x-portrait`, `x-square` | <= 1280x1024 | H.264 High, 4:2:0, >= 5,000 kbps; GIF <= 350 frames, 15 MB |
- Every MP4: H.264 High, yuv420p, even dimensions, closed GOP, moov at the front (faststart), no edit list, audio
  (if any) AAC-LC 48 kHz. Silent by default; `music` pads or trims to the film and fades the last 0.5 s.
- Keep films under the platform limit the engine checks (Reels 90 s, Story card 60 s, Shorts 180 s, X 140 s).

## Timing rules
- Readable hold: at least 0.5 s + (words / 3) s for any words on a shot (subtitle pace, about 3 words a second).
- Never more than 3 cuts a second (a shot is at least fps/3 frames), whatever the BPM.
- Beat sync (`bpm`): each shot is a whole number of beats nearest the style's own length; cinematic wipes are
  centred on the beat; boundaries are computed from the start (no drift).
- Slow in, slow out on every move (cosine for the push, ease-out cubic for the snap pop). Change fps and the seconds
  stay the same.

## Loops
- `loop`: no hero repeat; the end card (or last shot) wipes home to a pixel-exact copy of frame 0, so a GIF or a
  muted autoplay loop has no jump. Fade any audio at the seam.

## Flash safety (WCAG 2.3.1)
- No more than 3 general or 3 red flashes in any second over 25% of a 10-degree field (11.1% of the frame).
- The wipe glow is a light, capped at +48 levels on a band about 5% of the frame, once per wipe; the light sweep is
  capped at 20% and masked to the pack. Hard cuts between a dark and a light tint are transitions: the 3-cuts rule
  keeps them at 1.5 flashes a second or less.
- The engine's check is a guard; for broadcast, run a Harding or PEAT pass as well.

## Web formats
- MP4 is the master and the embed (`<video autoplay loop muted playsinline>` with a poster). GIF only where video
  cannot play (README, email): 15 fps, 540 px, about 160 colours. Animated WebP (`webp: true`) when supported:
  24-bit colour and real alpha, smaller than GIF.
