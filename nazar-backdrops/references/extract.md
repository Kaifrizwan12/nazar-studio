# Extract: from a brand book to tokens

Goal: a `brand.json` (template: `../../nazar-core/templates/brand.json`) where every value has a page reference. Keep the log in `research/backdrops/extraction.md` as `value · source (book p. N) · note`.

## 1. Read the book in this order
1. **Idea pages**: the core idea and tone. The backdrop should feel like this idea, quietly.
2. **Logo**: primary, secondary, mark, on-dark version, clear space, minimum size, the misuse page.
3. **Colour**: names, values, proportions, pairing rules.
4. **Type**: families, weights, hierarchy, a second script, RTL.
5. **Graphic elements**: devices, patterns, frames, icons, textures. The edge device usually comes from here.
6. **Photography / illustration**: crop, grade, subjects (this sets the image-window role).
7. **Applications, especially social**: if the book already shows posts, start from them; don't contradict the book.
8. **Voice**: the handle, sign-offs, how they write a call to action.

## 2. Colour
- **Screen values first.** Use the book's HEX/RGB. If only CMYK or Pantone is given, convert with Pantone's official sRGB values for that library (coated and uncoated differ), then check on a phone. Print values often look dull on screen. [SRC: Pantone Connect; sRGB IEC 61966-2-1]
- Record the **proportions** (e.g. 60/30/10). A backdrop uses the base, the light and at most one accent.
- Check every text/background pair with `contrast()` in `lib.py`: ≥ 4.5:1 for small text, ≥ 3:1 for large text and marks. [SRC: WCAG 2.2, 1.4.3 / 1.4.11]
- An accent that fails on both base and light becomes a graphic colour only (the band, a dot), never text.
- **Dark-mode base:** if the book's black is pure #000, consider a near-black for screens. Material Design's dark theme uses #121212 because pure black smears on OLED when scrolling and makes saturated colours vibrate. [SRC: Material Design, "Dark theme"] Ask before changing a brand colour.

## 3. Type
- Get the real font files and **check the licence covers social graphics**. Desktop licences usually allow static images; some exclude apps or broadcast, and video can count as broadcast. Record it. [SRC: each foundry's EULA]
- Assign roles: `text` (headlines and body), `label` (handle, counter, small caps), `display` only if the book uses one.
- For a second script, test every string with `missing()` in `lib.py`.

## 4. Logo
- Get the **SVG** of every version, including on-dark. Never trace a PDF screenshot.
- Note the clear space and the screen minimum. On a 1080 canvas, a mark under ~90–110 px wide tends to blur after the platform recompresses it; test it.
- Add the on-dark version to `brand.json` as `<name>_on_dark`; the renderer uses it on dark backdrops automatically.

## 5. Devices
- List every device the book allows, with its rules (can it crop, rotate, change colour?).
- Choose **one** for the backdrop. Two devices on a routine frame is noise.

## 6. Gaps
Anything missing (no on-dark logo, no screen colours, no social rules) is logged and raised once, with a recommended answer.
