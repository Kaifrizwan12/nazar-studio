# Delivery

## 1. Export matrix
| Output | Spec | Use |
|---|---|---|
| MP4 (H.264 / H.265) | 1080 × 1920, 1080 × 1350, 1920 × 1080, 3840 × 2160 as needed; 25/30 fps (or as the platform requires) | Social, presentations, screens |
| MOV with alpha (ProRes 4444) | For overlays | Editors, video production |
| GIF / animated WebP | Small, short loops | Email, messaging, stickers |
| **Lottie (JSON)** | Vector, small, scalable | Web and apps (keep shapes simple; check feature support in the player) |
| CSS / JS tokens | Easing and durations | Product and web |
| Static end frames | PNG | Thumbnails, fallbacks |
| Sound files | WAV master + MP3/AAC | Sonic logo, beds |
Name as `<brand>_motion_<piece>_<ratio>_<duration>s.<ext>`.

## 2. Handoff
- The project files (After Effects or similar) organised and named, with fonts listed and licensed for video use.
- A motion spec PDF: the behaviour idea, easing curves (with values), the duration palette, entrance and transition patterns, logo animation variants, do and don't, and reduced-motion rules.
- Templates for editors (title card, lower third, end card, caption style), with editable text fields and locked brand elements.

## 3. Motion QA (on top of core `qa_design.md`)
- [ ] The behaviour expresses the brand idea (you can say what the motion means in one line)
- [ ] One signature easing used consistently; durations from the palette only
- [ ] Hierarchy in time is correct; the end frame holds long enough to read
- [ ] Text is readable at phone size; reading time is sufficient; captions present
- [ ] Works muted and looped; safe zones respected for each platform
- [ ] No flashing above safe thresholds; a reduced-motion alternative is provided
- [ ] Logo geometry is exact in every frame (no distortion, colours correct)
- [ ] Music and fonts are licensed for this use; records kept
- [ ] Lottie files tested in the target player; file sizes reasonable
- [ ] Exports match the matrix, are named correctly, and play on real devices
