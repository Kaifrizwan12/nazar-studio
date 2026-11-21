# Research: flavour-cycle films (platform specs, pacing, loops, flash safety, web formats)

All sources accessed 2026-11-21. Tags: [SRC] = the platform's or standard's own page, [3P] = third-party guide (treat as
unverified; check the platform before a paid placement), [KNOWN] = settled craft knowledge. Where sources disagree,
the engine (`engine/flavour_cycle.py`, `PLATFORMS`) uses the conservative figure and says so here.

## 1. Platform video specs

| Platform | Size / ratio | Length | Codec, rate | Safe zone (t/b/l/r) | Tag |
|---|---|---|---|---|---|
| Instagram feed | 4:5 recommended (1080x1350); ads accept 1.91:1 to 4:5, 1:1 centre crop | ads to 60 min; engine warns past 90 s | MP4/MOV, H.264, 4 GB (ads) | small; 5% margin used | [SRC] Meta dev docs + [3P] |
| Instagram Reels / Stories | 9:16, 1080x1920, 30 fps | sources split: 90 s / 3 min / 15-20 min. Engine: 90 s Reels, 60 s per Story card | MP4/MOV, H.264 | top ~14%, bottom 35% (some say 20%, Meta text guide 40%), sides ~6% | [3P] citing Meta |
| TikTok in-feed ads | 9:16 >= 540x960 (rec. 1080x1920); 16:9 >= 960x540; 1:1 >= 640x640 | up to 10 min | .mp4 .mov .mpeg .3gp .avi; <= 500 MB; >= 516 kbps (TopView >= 2,500 kbps) | depends on ratio and caption length; official template files. Measured: 120 px sides, top 240 px, bottom 660 px | [SRC] + [3P] for the pixels |
| YouTube Shorts | square or vertical | up to 3 min (uploads from 15 Oct 2024) | as YouTube | not published; engine uses a Reels-like zone with a wider right margin | [SRC] |
| YouTube (upload) | as recorded | - | MP4, H.264, 4:2:0, closed GOP, moov atom at front (Fast Start), no edit lists; 1080p SDR 8 Mbps (12 at 48-60 fps); AAC-LC 48 kHz | 5% | [SRC] |
| LinkedIn (ads) | 16:9 1920x1080 (max), 1:1, vertical 9:16 to 16:9 allowed (5% tolerance) | 3 s to 30 min (in-stream 90 s) | MP4, H.264 or VP8, 75 KB-500 MB, "less than 30 fps", AAC | 5% | [SRC] |
| X (API) | 32x32 to 1280x1024; rec. 1280x720, 720x1280, 720x720; ratio 1:3 to 3:1; PAR 1:1 | 0.5 s to 20 min (Premium 125 min); Help Center still says 140 s, engine warns past 140 s | H.264 High, YUV 4:2:0 only, <= 60 fps, progressive, no open GOP, rec. >= 5,000 kbps; AAC-LC (no HE-AAC) | 5% | [SRC] |
| X animated GIF | <= 1280x1080, <= 350 frames, <= 15 MB, <= 300 M pixels total | | | | [SRC] |
| Behance (direct upload) | reported cap 1280 px wide, 1 GB; middle frame becomes the thumbnail; videos stack one per row; staff suggest a video-host embed for full bleed | | | | [3P] community answers |

Sources:
- Meta Instagram media requirements: https://developers.facebook.com/documentation/ads-commerce/instagram/ads-api/reference/media-requirements
- Jon Loomer, aspect ratios by placement: https://www.jonloomer.com/recommended-aspect-ratios-by-placement-for-meta-ad-creative/
- Reels/Stories safe zones [3P]: https://www.socialync.io/tools/safe-zones/instagram-stories , https://billo.app/blog/meta-ads-safe-zones , https://postfa.st/sizes/instagram/reels
- TikTok in-feed ad specs: https://ads.tiktok.com/help/article/video-ads-specifications?lang=en ; TopView: https://ads.tiktok.com/help/article/tiktok-reservation-topview ; measured safe zone [3P]: https://www.manypixels.co/blog/social-media-design/tiktok-ad-specs
- YouTube three-minute Shorts: https://support.google.com/youtube/answer/15424877
- YouTube upload encoding: https://support.google.com/youtube/answer/1722171 ; ffmpeg YouTube guide: https://trac.ffmpeg.org/wiki/Encode/YouTube
- LinkedIn video ads specs: https://www.linkedin.com/help/linkedin/answer/85306 , https://business.linkedin.com/advertise/ads/sponsored-content/video-ads/specs
- X media best practices: https://docs.x.com/x-api/media/quickstart/best-practices ; legacy 140 s: https://help.x.com/en/using-x/premium-longer-videos
- Behance: https://help.behance.net/hc/en-us/articles/204483574-Guide-Uploading-Audio-Video-Files , https://community.adobe.com/questions-606/behance-issue-layout-making-imbeded-and-video-files-tiny-577533

## 2. Pacing and easing

- **Slow in, slow out** (Disney, Thomas and Johnston, *The Illusion of Life*, 1981): more frames near the start and
  end of a move, fewer in the middle. The push-in uses a cosine ease; the snap pop uses ease-out (fast start, soft
  landing). https://en.wikipedia.org/wiki/Twelve_basic_principles_of_animation [KNOWN]
- **Timing** = frames per action: more frames read smoother and slower, fewer read crisper and faster.
  https://en.wikipedia.org/wiki/Timing_(animation) [KNOWN]
- **Material motion** (UI scale, still useful as an anchor): typical transition ~300 ms, large full-screen ~375 ms,
  entering ~225 ms, leaving ~195 ms, over 400 ms feels slow for UI; standard curve cubic-bezier(0.4, 0, 0.2, 1),
  deceleration (0, 0, 0.2, 1) for entering, acceleration (0.4, 0, 1, 1) for leaving.
  https://m1.material.io/motion/duration-easing.html [SRC]. The 12-frame (400 ms) wipe sits at the top of that UI
  range: a deliberate, filmic transition, not a UI snap.
- **Readable hold**: subtitle guidance is 160-180 words a minute (about 3 words a second, ~0.33 s a word); Netflix
  adult 200 wpm / 17 cps, children 160 wpm. https://clevercast.com/bbc-subtitling-guidelines ,
  https://backlothelp.netflix.com/hc/en-us/articles/216787938-Portuguese-Timed-Text-Style-Guide [3P/SRC].
  Engine rule: a shot needs >= 0.5 s + words / 3 s; it warns otherwise.

## 3. Seamless loops

- The seam is what matters: the last frame must match the first (design the end, then set the start to it).
  https://larryjordan.com/articles/create-a-seamless-animated-video-loop-in-apple-motion/ [3P]
- Audio encoder delay and padding shift the seam even when frames match; fade audio out at the boundary.
  https://www.capcut.com/create/seamless-loop-videos-continuity-techniques [3P]
- Engine: `loop: true` drops the hero repeat and wipes the end card into a pixel-exact copy of frame 0 (frozen
  marquee and grain for that one target frame), so a GIF or muted autoplay loop has no jump.

## 4. Flash safety

- **WCAG 2.3.1 (A)**: no more than three general flashes and/or three red flashes in any one second, or flashes
  below the thresholds. General flash = a pair of opposing changes in relative luminance of 10% or more of max, where
  the darker state is below 0.80. Red flash = opposing transitions involving saturated red (R/(R+G+B) >= 0.8).
  Area threshold: 0.006 sr (25% of any 10-degree field), estimated as 341x256 px on a 1024x768 screen (11.1% of it).
  https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html [SRC]
- **Ofcom / Harding**: the Harding FPA implements the UK regulator's guidance (Graham Harding's research). Legacy ITC
  note: a flash is potentially harmful when the brighter image is above ~20 cd/m2 and the two differ by >= 20 cd/m2;
  regular patterns are flagged above 25% of the screen. https://en.wikipedia.org/wiki/Harding_test ,
  https://www.ofcom.org.uk/__data/assets/pdf_file/0021/16248/gn_flash.pdf (403 to automated fetch; quoted via
  search), gap analysis https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11872230/ [SRC/3P]
- Engine: `FlashMeter` tracks luminance extremes per cell on a 48-wide grid, counts transitions in every one-second
  window over the worst 11.1% of the frame, and fails above 3 flashes/s; red transitions are counted separately.
  A shot is never shorter than fps/3 frames (<= 3 cuts/s, so <= 1.5 flashes/s even between dark and light tints).
  The wipe glow peaks at +48 levels on a band ~5% of the frame, once per wipe. A guard, not certification: run a
  Harding/PEAT pass for broadcast.

## 5. GIF vs MP4 vs animated WebP (web, README, decks)

- web.dev: a 3.7 MB GIF became a 551 KB MP4 and a 341 KB WebM; use `<video autoplay loop muted playsinline>` to act
  like a GIF; a video without a poster is not an LCP candidate. https://web.dev/articles/replace-gifs-with-videos [SRC]
- GIF: 8-bit palette (256 colours max per frame), 1-bit transparency; dithering adds noise that compresses badly.
  Animated WebP: 24-bit colour, 8-bit alpha, smaller files (Google cites ~64% smaller for lossy, with visible loss).
  https://developers.google.com/speed/webp/faq , https://en.wikipedia.org/wiki/WebP [SRC/3P]
- Rule: MP4 is the master and the embed wherever video plays (decks, sites, social). GIF only where video cannot play
  (a README, email, some chat tools): 15 fps, 540 px, ~160 colours, bayer dither, under 15 MB and 350 frames.
  Animated WebP when the target page supports it and size matters.
