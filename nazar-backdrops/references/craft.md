# Craft: making backdrops survive phones and platforms

## Legibility
- A 1080 px canvas is shown about 375–430 pt wide on a phone, roughly a third of its size. So **40 px on the canvas ≈ 13–14 pt on screen**, about the smallest comfortable body size. Handles and counters can go to ~26–30 px (≈ 9–10 pt) because they're glanced at, not read. [SRC: Apple Human Interface Guidelines, typography; device logical widths]
- Test at real size: AirDrop or send the PNG to a phone and look at arm's length, then at grid size, with a thumb over the bottom.
- Labels in a mono or small-caps face need tracking (+5–10%) at small sizes.

## Contrast
- Text ≥ 4.5:1, large text and marks ≥ 3:1 (WCAG 2.2, 1.4.3 / 1.4.11). Check with `contrast()` in `lib.py`; the renderer warns on failures.
- Colour can't be the only cue (WCAG 1.4.1): a counter in accent colour also needs its number.

## Dark mode and dark backdrops
- Most people browse Instagram in dark mode. A dark backdrop on a dark UI loses its edge, so give it an edge device or a light element near the border.
- Avoid pure #000 with saturated accents: it smears on OLED while scrolling and makes the colours vibrate. Near-black (Material Design uses #121212) is calmer. [SRC: Material Design, "Dark theme"]
- A pure-white light backdrop glares in dark mode. The brand's off-white usually reads better.

## Compression (the platform will recompress everything)
- Upload at the exact canvas size (1080 wide). Bigger files get downscaled by the app, often worse than you'd do it.
- Export **sRGB**. Other profiles get converted and colours shift.
- JPEG-style compression halves colour resolution (4:2:0 chroma subsampling), so **saturated red/orange text and thin coloured lines on dark backgrounds fringe and blur**. Keep accent lines ≥ 2–3 px and accent text large. [SRC: JPEG/JFIF chroma subsampling]
- Flat colour compresses cleanly; smooth gradients band. If a gradient is unavoidable, add 2–4% noise (the engine's `grain_uri()`).
- Hairlines under 2 px can disappear or shimmer. Use at least 2 px.

## Export
- `brand_format_role_mode.png` (e.g. `acme_feed4x5_cover_dark.png`), plus `_guide.png`.
- PNG for the backdrop masters (lossless); the team's posting tool will make the JPEG.
- Keep the SVG masters next to the PNGs. They're the source of truth.
