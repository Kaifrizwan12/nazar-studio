# Lockups, rules and files

## Lockups
- **Primary** (the default), **horizontal**, **stacked**, **symbol only** (the atom), **wordmark only**, a **tagline lockup** (only if a tagline is locked), and a **bilingual** order variant if needed.
- Fixed relationships: the symbol-to-wordmark size ratio, the gap measured in a mark unit (e.g. "the x-height", "one dot"), and the alignment axis. Draw these on a construction sheet.

## Clear space and minimum size
- Clear space measured in a unit **from the mark itself** (cap height, symbol width, a dot), never in mm, so it scales.
- Minimum sizes from the tests, separately for screen (px) and print (mm), per lockup. Below the minimum, switch to the symbol.

## Colour versions
Full colour (on light) · full colour (on dark) · one colour black · one colour white (reversed) · one colour brand colour · special (foil, emboss or gradient), only where allowed.
Colour values: HEX, RGB, CMYK (from the printer's profile when known), and a spot reference if used.

## Misuse page (6–8 tiles)
Stretched · recoloured · rotated · effects (shadow, glow, bevel) · outlined · rearranged lockup · on a busy background without contrast · crowded (clear space broken).

## The export matrix
| Format | Use | Notes |
|---|---|---|
| **SVG** | Web, UI, the master for screen | Outlined text, no hidden layers, clean IDs, tight viewBox |
| **PDF / EPS** | Print and vendors | Vector, with spot colours named if used |
| **PNG** (transparent) | Office, social, quick use | Several widths (e.g. 500, 1000, 2000, 4000 px) |
| **JPG** | Where transparency isn't supported | On white or brand colour |
| **ICO / PNG favicons** | 16, 32, 48, 180 (Apple touch), 192 and 512 (PWA) | Use the symbol, with optical tweaks for tiny sizes |
| **App icon** | iOS and Android sizes and masks | Test against the rounded mask and adaptive-icon safe zone |
| **Social avatars** | Circle crop, 400–1080 px | Symbol centred optically within the circle |
| **Lottie / MP4** | Logo animation (from `nazar-motion`) | |
Each lockup × each colour version × each needed format. Generate them with a script so they're consistent and can be regenerated.

## Naming and folders
`<brand>_logo_<lockup>_<colour>[_<size>].<ext>`, all lowercase, hyphens within words, e.g. `acme_logo_horizontal_full-colour_on-dark.svg`.
```
assets/logo/
  README.md      which file to use where, minimum sizes, clear space, colours, licences
  svg/  pdf/  png/  favicon/  app-icon/  social/
```

## Handover
- The source file (vector, organised and named layers), the construction sheet, the font licence notes, and the trademark first-pass record plus the recommendation to clear it.
- A one-page "logo quick guide" PDF: lockups, clear space, minimum sizes, colours, misuse.
