# Study lessons

- 2026-11-22: Kit created. `look.py` passes its known-answer tests (light falloff side, warm cast, grain sigma within 25%, clipping share, weight centroid, empty space, compare flags). Pillow cannot Gaussian-blur float ("F") images; the engine uses its own three-pass box blur.
- 2026-11-22: On a real 26-panel Behance cut, `clip_highlights_pct` counted any channel at 250+, so flat brand-yellow pages read as 21% 'clipped'. Now `clip_highlights_pct` = near-white blowout (all channels 250+) and `channel_clip_pct` = one channel 254+ (often an intended flat colour). Test added.
