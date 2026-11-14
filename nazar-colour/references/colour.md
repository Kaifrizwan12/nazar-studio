# Colour reference

Confidence tags: [V] checked at the source, [K] standard knowledge, [UNVERIFIED] check before you rely on it.

## 1. Archive and art-history sources
| Source | What it gives | Rights |
|---|---|---|
| **Sanzo Wada, *Haishoku Sōkan* (1933–34)**: 348 combinations of 159 colours from Japanese dye tradition [V] | Ready combinations of 2–4 colours with a cultural logic | Wada died in 1967, so the plates are public domain in Japan [V]; US status unconfirmed. The 2010 Seigensha book layout is copyrighted. Data: sanzo-wada.dmbk.io (no licence stated), github.com/mattdesl/dictionary-of-colour-combinations (MIT). Hex values are approximate digitisations |
| **Werner's Nomenclature of Colours (1814/1821)** [V] | Naming colours after animals, plants and minerals | Public domain; interactive edition at c82.net/werner |
| **Emily Noyes Vanderpoel, *Color Problems* (1902)** [V] | Proportional 100-square grids reducing an object to its colour areas: a method you can run on a Karachi object | Public domain (Gutenberg; Public Domain Review) |
| **Josef Albers, *Interaction of Color* (1963)** [V] | Colour is relative; make one colour read as two to test a palette | In copyright (Yale); the method is free to use |
| **Itten, *The Art of Color*** [K] | The seven contrasts; **contrast of extension** explains "one accent on a sober ground" | In copyright; use the vocabulary |
| Ostwald, Munsell [K] | Even steps of hue, value and chroma (the ancestors of OKLCH) | — |
| nipponcolors.com [K] | About 250 named Japanese colours | Values approximate |
| Pantone / RAL [K] | Pantone for print spot colours (libraries now need Pantone Connect [UNVERIFIED terms]); **RAL for shopfronts, signage, paint, powder coat** | Proprietary |

## 2. Pakistani and South Asian palettes (strongest for Nazar)
- **Ajrak (Sindh):** indigo, madder red, black, white; resist block print. Few colours, deep meaning: an ideal "sober ground plus one pop" system [K].
- **Truck art (phool patti):** saturated, mirror work, "disco" energy. Karachi style; Sindh favours red and camel-bone ornament. **No documented fixed palette: sample real trucks with calibrated photos** (expert: Durriya Kazi) [V].
- **Kashi-kari tilework** (Wazir Khan Mosque, Lahore; Thatta): cobalt, turquoise, ochre, green [K]. Multani and Hala blue pottery: cobalt and turquoise on white [UNVERIFIED specifics].
- **Mughal miniature pigments:** lapis lazuli, orpiment, cinnabar, gold; later Indian yellow; lac red [V]. Sample from open-access museum images (The Met CC0; Smithsonian NMAA), never by paraphrase.
- Traditional pigments: indigo, kumkum (turmeric + lime), hingul (cinnabar) [V popular source].

## 3. How strong studios build palettes
- Own one colour: Mailchimp's Cavendish Yellow (Collins, 2018); Tiffany Blue; Cadbury purple (fought in court) [K].
- Wide palettes run on pairing rules (Collins for Dropbox, 2017); deliberately abrasive ones break taste on purpose (Wolff Olins, London 2012) [K].
- Pentagram: palettes come from the client's own material (archive, building, product) [K].

## 4. Technical checks
- **OKLCH/OKLab** (Ottosson 2020; CSS Color 4) are perceptually even. Ramps step L at a fixed hue and lower C at the extremes. Tools: oklch.com, Evil Martians' explainer.
- **WCAG 2.2:** 4.5:1 normal text, 3:1 large text (24 px, or 18.66 px bold), 3:1 UI and graphics.
- **APCA** (draft for WCAG 3): Lc 75 or more for body text at 18 px/400, Lc 90 preferred; better for light-on-dark [V].
- **Colour blindness:** about 1 in 12 men, 1 in 200 women. Simulate with Chrome DevTools, Coblis or Sim Daltonism. Never use red/green alone for meaning; check in greyscale.

## 5. Screen → print
- sRGB/P3 are additive; CMYK is subtractive with a smaller gamut, so vivid greens, cyans, oranges and violets drop out.
- Uncoated stock dulls colour: specify Pantone C **and** U. Use the printer's ICC profile (FOGRA39/51, GRACoL). Total ink about 300% or less; rich black only on large areas.
- Pakistan practice [UNVERIFIED]: many printers don't work to profiles. Ask for wet or machine proofs, give Pantone references, press-check the first run. Use spot or fluorescent inks for truck-art saturation.

## 6. AI palette tells and avoidance
Tells:
- purple-to-blue gradients,
- neon cyan or magenta on near-black with glow,
- teal and orange,
- every hue at equal lightness (generator rainbows),
- pure #000/#FFF with one stock "brand blue".

Avoidance:
- start from a named source,
- tint the neutrals,
- use unequal proportions,
- mix lightness and chroma on purpose,
- keep one earthy friction colour,
- use gradients only from a real reference (dye bleed, sky at a stated hour),
- run the Albers relativity test.

## Sources
github.com/mattdesl/dictionary-of-colour-combinations · sanzo-wada.dmbk.io · artplatform.go.jp/artists/A2089 · commons.wikimedia.org/wiki/Template:PD-Japan · c82.net/werner · gutenberg.org/ebooks/77736 · publicdomainreview.org (Vanderpoel charts) · news.yale.edu (Albers app, 2013) · bottosson.github.io/posts/oklab · w3.org/TR/css-color-4 · w3.org/TR/WCAG22 · github.com/Myndex/SAPC-APCA · colourblindawareness.org · color.org · en.wikipedia.org/wiki/Ajrak · en.wikipedia.org/wiki/Truck_art_in_South_Asia · geo.tv (phool patti, 2022) · aramcoworld.com (Pakistani art trucks, 2021) · mapacademy.io (Mughal pigments) · cambridge.org (Shahnamah palette, JRAS) · colourlex.com · metmuseum.org open access · wearecollins.com (Mailchimp, Dropbox)
