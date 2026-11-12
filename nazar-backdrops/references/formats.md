# Formats, crops and safe zones

Platforms change these without notice. Everything below is [SRC] from platform help pages and ad guides as of 2025–26. **Verify in each app's own preview before the final export**, and date the check in the extraction log. The renderer's `FORMATS` table mirrors this file.

| Engine name | Canvas | Use | What gets cropped or covered |
|---|---|---|---|
| `feed_4x5` | 1080 × 1350 | Instagram / Facebook / LinkedIn portrait post: the default | The profile grid shows a **3:4** crop (≈ 1012 × 1350: ~34 px off each side). Instagram moved the grid to 3:4 previews in January 2025. |
| `feed_3x4` | 1080 × 1440 | Native to the 3:4 grid | Some feeds show it at 4:5: keep key content inside the central 1080 × 1350. |
| `feed_1x1` | 1080 × 1080 | Square posts, LinkedIn, X | The 3:4 grid crops to the central ≈ 810 × 1080. |
| `carousel_*` | 1080 × 1350 | Carousel slides (Instagram allows up to 20 since 2024) | The cover gets the grid crop; later slides don't. |
| `story` | 1080 × 1920 | Stories, WhatsApp status | Meta's guidance: keep ~14% (≈ 250 px) at top and bottom free of text and logos (profile bar, reply bar). |
| `reel_cover` | 1080 × 1920 | Reel / TikTok cover | The grid shows the central 3:4 (1080 × 1440: 240 px off top and bottom). In playback, UI covers roughly the bottom 35% and a right-hand strip of buttons. |
| `linkedin` | 1200 × 1200 | LinkedIn single image (1080 × 1350 also works). Document posts are PDFs: one backdrop per page. | — |
| `x_post` | 1600 × 900 | X in-feed image (16:9) | Mobile can crop toward the centre: no text in the outer ~5%. |
| `yt_thumb` | 1280 × 720 | YouTube thumbnail (16:9, under 2 MB) | The duration stamp covers the bottom-right (~170 × 60 px); hover icons sit top-right. |
| `highlight` | 1080 × 1920 | Instagram highlight cover | Shown as a small circle cut from the centre. Only the centre matters. |
| `avatar` | 1080 × 1080 | Profile picture everywhere | Shown as a circle at 40–110 px. The symbol only, never the full lockup. |

Add these to `FORMATS` if the client posts there: Pinterest 1000 × 1500 (2:3) · X header 1500 × 500 (the avatar overlaps bottom-left on mobile) · LinkedIn banner 1584 × 396 · YouTube channel art 2560 × 1440 (safe centre 1546 × 423) · Facebook cover 851 × 315 (mobile shows a narrower centre).

## Attention budget
People decide fast. Facebook IQ's research found mobile feed content was viewed for ~1.7 s on average (vs 2.5 s on desktop), and that recall was measurable after just 0.25 s. [SRC: Facebook IQ, "Capturing attention in feed", 2016] The backdrop's job is to make the brand register inside that first glance, which is why its anchor never moves.

## Sources
- Instagram Help Centre (image sizes, carousel limits); Instagram's January 2025 announcement of the 3:4 grid
- Meta Business Help Centre / Ads Guide (Stories and Reels safe zones)
- LinkedIn Help (image and document posts); X Help (image specs); YouTube Help (custom thumbnails: 1280 × 720, under 2 MB)
- Facebook IQ (2016), "Capturing attention in feed: the science behind effective video creative"
