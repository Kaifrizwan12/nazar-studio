# 06 · Type

## The system
Usually 3 roles, 4 at most:
| Role | Job | Rule |
|---|---|---|
| **Display** | Logo, tagline, posters, packaging fronts | Never used for sentences. One per brand. |
| **Text** | Everything the brand *says*: titles, lines, body | Light or Regular only. Medium for a rare emphasis. Never Bold for lines. |
| **Label** | Places, times, specs, numbers, page furniture | A mono or a narrow grotesk, small, tracked +5–10% |
| **Script 2** | The second language (Urdu, Arabic, Hindi...) | Its own face, matched for weight and x-height, not a fallback |

A typical set: one characterful display face, one neutral grotesk or serif in light and regular weights for text, and one mono for labels.

## Choosing
1. Start from research pass 5: what has this category and region set before (Fonts In Use, archive scans)? Choose a face that either belongs to that lineage or deliberately breaks it. Write down which, and why.
2. Pair by **contrast of role, harmony of construction**: a geometric display with a humanist text often fights, so match the skeleton or contrast strongly.
3. Check the glyph set: the local currency symbol, diacritics for transliteration (ā ī ū), the brand's own name, numerals (tabular for specs). Space Mono lacks ː ɪ ʒ, so avoid IPA or use plain transliteration.
4. **Licence**: OFL/Google Fonts are free for commercial use. Anything else needs a licence before client use, so record it in `SPEC.md`. Flag non-commercial fonts on day one.

## Bilingual setting (Urdu + Latin, or any pair)
- Urdu has three families: **Nastaliq** (calligraphic, the newspaper voice; Gulzar is the best free modern one and has a matching Latin), **Naskh** (clearer at small sizes) and **Kufic** (geometric, logo-friendly: Reem Kufi, Kuficology).
- Match the visual size, not the point size. Urdu needs a larger size and more leading than Latin.
- Align the two scripts by a shared line (baseline, centre or cap height). Show the rule on the type page.
- A transliterated local language (Roman Urdu, Hinglish, Arabizi…) is upright. No italics, no quotes, no "translated" smell. When the audience is mixed, pair each line with its meaning in the secondary colour.
- Never fake a script in a Latin font, and never outline a script your engine can't shape. The engine uses harfbuzz, so RTL shaping works if the font supports it.

## Scale
A short modular scale, for example 13 · 19 · 28 · 48 · 72 · 160 (dividers). Sub-headings are rarely needed: one title plus one line is the pattern.

## Specimen tricks (choose one for the type pages)
- **Eye chart**: the tagline or name set as a Snellen chart, getting smaller
- **Menu card**: the faces set as a real menu for the brand
- **Ingredient label**: the type scale as a nutrition panel
- **Ticket or receipt**: the label face as a till receipt
- **Sign-painter sheet**: the alphabet as a signboard layout with brush guide lines
- **Telegram**: the voice line set as a telegram, mono

## Rules for the book
- At most one display moment per page.
- Line length 45–75 characters, and text blocks no wider than 6 columns.
- Leading: 1.35 for text, 1.1 for display.
- Tracking: never on lowercase text, +5–10% on mono caps labels.
- Outline the type in the engine so the PDF renders the same everywhere. Keep a live-text copy for the Behance write-up.

## Master practices (see `../nazar-core/references/masters.md`)
- **Vignelli:** few typefaces, used well. Hierarchy comes from size, weight and space.
- **Bringhurst:** measure about 45–75 characters (66 ideal), narrower in columns. Derive `para()` max widths from the measure, not the page.
- **Müller-Brockmann:** set all vertical spacing in multiples of a baseline unit taken from body leading.
- **Crouwel:** a display face or numeral set built from the brand's own grid can be its most ownable asset. Propose one when the scope allows.
