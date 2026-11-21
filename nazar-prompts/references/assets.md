# Assets to attach, the iteration log, disclosure

## Every job
- [ ] Written client approval of AI use (date, signatory), filed with the job
- [ ] Brand palette sheet (hex + words); a style frame or palette reference image
- [ ] Rights confirmed for every attached asset; no third-party IP; releases for any real person
- [ ] References in the **output aspect ratio**, JPEG/PNG, ≥ 1920 px on the long side [studio rule]
- [ ] Products and subjects on plain or segmented backgrounds, no extra subjects (Flow guidance)

## Packaging hero (image)
- [ ] Flat front-label artwork (high-res PNG): "preserve exactly"
- [ ] 1–3 real photos of the physical pack (front, 3/4, top) on a seamless background
- [ ] One lighting or style reference (Pro takes up to 3)
- [ ] Surface and prop references
- [ ] A layout sketch with the copy-safe zone
- [ ] The vector logo, kept for post (not for generation)
- [ ] Output spec: ratio, 2K/4K

## Social reel (9:16)
- [ ] Character sheet: front, 3/4 and profile on a plain background (≤ 3 per character, ≤ 2 characters on Omni)
- [ ] Product references; a location plate with no people
- [ ] Shot list with durations (≤ 8 s Veo, ≤ 15 s Omni); dialogue timed to fit
- [ ] Start and end frames for each transition
- [ ] Music and VO in post unless native audio is approved; Instagram safe-zone overlay

## Product video (16:9 / 9:16)
- [ ] Product turnaround stills (3 asset references, the Veo maximum)
- [ ] First and last frames per shot, made in Nano Banana from those references
- [ ] Storyboard + timestamp breakdown; a style frame
- [ ] End card built in post with the real logo and legal copy
- [ ] Extension note: describe again anything outside the last 10 s

## OOH visual
- [ ] Media spec: size, viewing distance, DPI
- [ ] Generate the closest ratio (21:9, 4:1, 8:1, 1:4, 1:8 available) at 4K, then upscale and retouch in post
- [ ] Product and palette references; bleed and safe template
- [ ] **The headline is never AI-rendered**; disclosure label placed where required

## Iteration log (`research/ai/log.md`, one row per run)
| Date | Tool | Model ID + version | Settings (ratio, size, duration, seed) | Full prompt | Attached files (names + hashes) | Output file | Keep / kill | Why |
|---|---|---|---|---|---|---|---|---|

## Delivery note (disclosure)
"Images/video in this delivery were generated with [tool, model] on [dates] from Nazar's art direction and prompts, then retouched and finished by Nazar. AI use approved by [client signatory] on [date]. Generated content may not be exclusive; provenance metadata (SynthID/C2PA) is preserved."

## Hybrid scenes (AI plate + real pack): rules that held up
- **AI makes only the empty plate.** Never let a model re-light or redraw the pack; it erases print detail.
- **Camera must match the pack render:** top-down or dead straight-on plates only for flat orthographic renders. Oblique plates make pasted packs look fake.
- **Seat the pack, don't paste it:** carry the plate's low-frequency light and colour cast onto the pack, lift the pack's blacks to the plate's black level, drop saturation slightly, add a soft bend falloff and a broad sheen from the key light, an inner edge occlusion, a cast plus tight contact shadow away from the key, and the plate's grain.
- **Shelves:** bag bases tuck behind the shelf lip (re-lay the lip band over the packs), slight lean, overlapping facings.
- **Tool limits:** some connectors return only small previews (unusable as plates); some cap free model runs. Check full-resolution output and quota before promising a set.
- **Owner preference may still be "no hyper-real for now":** keep scenes optional; the designs lead.

### Standing packs in a plate: what stops the "pasted sticker" look
- **The base is not a straight cut.** A stand-up pouch seen from a little above has a gusset: the bottom bows forward into an arc, the side-seal corners pull up, and the film turns under. Warp the bottom 15–20% of a flat front render that way, darken the underside and add a soft crest. A straight bottom edge reads as a card standing on its edge.
- **The shadow lies on the surface.** Project the silhouette onto the ground plane from the base, sheared away from the key and squashed to the camera's height. A translated copy behind the pack reads as a drop shadow. Glossy tops (marble, polished wood) also need a faint, soft, flipped reflection.
- **Stock it like a hand did.** Let tilt, height and spacing drift by about 1%. Perfect repetition reads as generated.
- **Shop graphics are print, not AI.** Header boards and shelf-edge strips are drawn by code with the brand's real type, then lit by the plate's own light map. Ask the image model for a blank header panel and blank strips only.
- **Ceiling:** flat front renders can't turn in perspective. For true 3/4 or lying poses, use a 3D model with the flat art as its texture.
- **Faded packs:** lifting the pack's blacks to the plate's darkest tone washes packs out on white sets (shelving, studio). Keep the lift near 0.1 there, keep full saturation, add local contrast on the print, then grade the whole frame once (gentle S-curve, vignette) so pack and plate share one finish.
