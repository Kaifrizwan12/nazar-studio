# Shoot lessons

- 2026-11-21: Hybrid rule. AI made only the empty plate; the packs were our renders, so type stayed sharp. Every AI output carried the disclosure stamp. Engine: `engine/composite.py`.
- 2026-11-21: The owner called floating packs, pale ghost shadows and creaseless film "AI slop". Fix the physics, not the strength: a tight contact shadow at the base, a projected cast shadow that softens with distance, the plate's black level and colour cast on the pack.
- 2026-11-21: Packs standing behind a shelf lip need the plate's lip band pasted back over their bases (`--relay`). Without it they read as stickers.
- 2026-11-21: Hyper-real scenes are parked unless the owner asks. AI scene photos were dropped from the deck; only a flat-lay the owner picked stayed.
- 2026-11-21: No "chic slop" plates (palm shadows, travertine, beige plinths). Brief real local places with one named light.
- 2026-11-21: Building the self-test showed that a flat-topped projected shadow reads like a cut-out slab. The penumbra must widen and fade toward the tip, and the near edge needs room to blur below the base.
- 2026-11-21: Never mirror a pack render to fake a second unit. The type reads backwards. Use another SKU's render.
- 2026-11-21: A soft drop shadow alone melted the pouch's seal teeth and notches into a blur. Add a tight contact shadow under the soft one, in films and in every composite.
- 2026-11-21: Cinematic films: a wide feathered wipe ghosted two packs into each other (doubled type). A crisp edge with a light glow reads as a light leak and never blends packs. Show stills of the start, mid-shot, mid-wipe and the next shot before rendering video.
- 2026-11-21: The flavour-cycle film was a one-brand script. It is now `engine/flavour_cycle.py`, driven by a JSON job (any range, any aspect, platform presets with safe zones, cinematic or snap, loop, beat sync, optional music). Tint `auto` samples the pack's dominant print colour.
- 2026-11-21: Vertical presets (Reels, Stories, TikTok, Shorts) shrink the pack to fit the safe zone instead of letting the UI cover the pack's type. Check the stills sheet: the safe zone is drawn on the mid-shot.
- 2026-11-21: Flash safety is measured on every render (WCAG 2.3.1 general and red flashes over 11.1% of the frame). Shots are never shorter than fps/3 frames, and the wipe glow is capped at +48 levels on a thin band, so a range that swings dark to light tints stays at 1.5 flashes a second or less. The self-test shows the meter fails a real strobe.
- 2026-11-21: For a loop, the last frame is a pixel-exact copy of the first (no hero repeat); the tests compare them byte for byte.
