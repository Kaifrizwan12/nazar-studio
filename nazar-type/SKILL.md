---
name: nazar-type
description: Nazar Studio's typography kit. Use to choose, source, license, pair and QA typefaces for brands, packaging, signage, screens and editorial, including Urdu Nastaliq, Naskh, Sindhi, Arabic, Devanagari and Gurmukhi bilingual systems, small legal packaging text, and avoiding overused defaults. Covers free/open sources and paid foundries, the SIL OFL in plain terms, licence checks, glyph coverage and kerning QA.
---

# Nazar type

Read `../nazar-core/SKILL.md` first. **The user's prompt leads; use the parts the job needs.**

## Rules
1. **List the uses before choosing a font:** packaging, signage, web, app, social video, broadcast, logo. Pick a font whose licence covers all of them (`references/type.md` §1).
2. **The client owns the licence.** The client buys it, or it's transferred to them. Store the EULA or LICENSE file and the invoice with the font files. Trial fonts are for pitches only.
3. **OFL is the safe default for identities:** no expiry, no seat audits, logos and apps allowed. It isn't exclusive, so get distinctiveness from a custom wordmark (§2).
4. **No template fonts as brand faces.** If a font sits in the Google Fonts top 30 or is all over the competitors, it's out except as a fallback (Inter, Poppins, Montserrat).
5. **Bilingual systems are designed, not appended.** Match visual size (Urdu ≈ 115–130% of the Latin size), give Nastaliq its own leading (≈ 1.8–2.2×), and use Naskh, not Nastaliq, for small text (§3).
6. **Small legal packaging text:** design to an **x-height of 1.2 mm or more** in every script (the EU benchmark; Pakistan rules to be confirmed with PFA/PSQCA). Use a large x-height, open-aperture sans.
7. **QA every font:** glyph coverage for every language and symbol (₨, Urdu digits, diacritics), kerning at final size, the licence, embedding bits, Nastaliq rendering in the target app (§5).

## Workflow
| Phase | Do | Output |
|---|---|---|
| 1 | Uses and media list; scripts and languages; budget for paid licences | type brief |
| 2 | Long list from sources (§1), filtered by licence and coverage | 8–12 candidates |
| 3 | Specimens in real use: headline, body, packaging legal text, signage at distance, Urdu pairing | specimen sheet |
| 4 | Pick 1–2 families with a recommendation; check Fonts In Use for category clashes | type decision |
| 5 | QA (§5), licence filed, tokens in `nazar-core/engine/brand.json` | fonts + LICENSE in the brand folder |

## Files
- `references/type.md`: sources and licences, OFL plain terms, South Asian scripts and pairing, which-font-when matrix, QA checklist, sources
