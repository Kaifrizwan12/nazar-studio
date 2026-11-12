# Handoff: templates the team will actually use

A folder of PNGs drifts within a month. Hand off **locked backdrops plus editable content layers** in the tool the team uses (intake Q8).

## Canva (most small teams)
- Set up a **Brand Kit** (colours, fonts, logos) from the extraction.
- Build each backdrop as a **Brand Template**: the backdrop is an image or element group that's **locked**; the title, body and photo frames are unlocked text boxes and frames.
- One template per format, with pages for each role and mode (Canva templates can hold several pages).
- Note: uploaded fonts need a Canva plan that allows brand fonts, and the font's licence must allow it.

## Figma
- One component per format with **variants**: `mode = dark | light | accent`, `role = single | cover | text | image | end | quote | stat`.
- Backdrop layers in a locked group; content in auto-layout frames with text styles bound to the tokens.
- Colour and type as **variables/styles** named the way `brand.json` names them, so a palette change updates everything.
- Publish as a library; the social team instances it.

## Layered files (Photoshop / Affinity)
- One file per format, layer groups `BACKDROP (locked)` / `CONTENT` / `GUIDE (hidden)`. Smart objects for photos.

## Video (CapCut / Premiere)
- Reel cover and end card as templates, with the logo and handle locked and the title as an editable caption.

## The usage sheet (1–2 pages, `exports/backdrops-usage.pdf`)
1. The skeleton in one sentence, plus the guide image.
2. Which role for which kind of post (from `set.md`).
3. Do / don't, six each: e.g. don't move the logo, don't add a second accent, don't put text in the UI zones, don't use AI images on the image role.
4. The grid rhythm (dark/light pattern).
5. File list and naming.
6. Who to ask, and the date the specs were last verified.

## Naming
`brand_format_role_mode[_guide].png` · templates named the same · version in the folder name (`backdrops_v1`), never in each file.
