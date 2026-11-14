# Type reference

Confidence tags: [V] checked at the source, [K] standard knowledge, [UNVERIFIED] check before you rely on it. **Read the live EULA before advising a client.**

## 1. Where to source, and what the licence allows
| Source | Licence | Notes |
|---|---|---|
| Google Fonts, fonts.google.com | Nearly all SIL OFL 1.1, a few Apache 2.0 [K] | Uneven quality; the best are commissioned (Noto, Gulzar, Markazi, Fraunces, Newsreader). Analytics at fonts.google.com/analytics show what's overused |
| Fontshare (ITF), fontshare.com | ITF Free Font Licence (not OFL): commercial use allowed; no redistribution, may restrict modification [V via licenseorg]. **Logo use not explicit [UNVERIFIED]: read it first** | Satoshi, General Sans, Clash, Switzer: good, but common in startup work |
| Velvetyne, velvetyne.fr | Mostly OFL; some fonts carry other terms (e.g. "CUTE Conditions" restricting big companies) [V] | Experimental display; check each LICENSE |
| Collletttivo, collletttivo.it/licensing | OFL; credit asked [V] | Contemporary grotesks and display |
| Open Foundry, uncut.wtf, Use & Modify, League of Moveable Type | Mostly OFL; per-font licences [K/V] | Curated free faces; check each |
| Fontsource, Bunny Fonts | Packaging / privacy-friendly hosting of OFL fonts [K/V] | For web builds; Bunny avoids Google's IP logging (a GDPR concern) |
| Adobe Fonts | Included with Creative Cloud; logos and print OK; **no sending files to clients or printers, no app embedding** [K] | Don't build a long-term client identity on it unless the client licenses directly |
| Paid foundries: Klim, Commercial Type, Grilli Type, Dinamo, Pangram Pangram, Displaay, Colophon, Production Type, **Typotheque** (strong non-Latin: Arabic, Indic), Lineto | Split by medium: desktop (print, packaging, logos), web (page views), app, ePub, broadcast; logo or trademark clauses vary [K] | Trials for pitching only |

## 2. SIL OFL in plain terms (openfontlicense.org/ofl-faq) [V]
- **Logos:** yes. The logo artwork is yours, but you get no exclusive rights in the font.
- **Packaging, print, commercial products:** yes. Only the font files stay under the OFL.
- **Embedding** in PDFs and apps: yes. Apps must include the licence text.
- **Modify:** yes, but rename the font if it has Reserved Font Names. Outlined wordmarks count as artwork, not a font.
- **Sell the font on its own:** no.

## 3. South Asian scripts and bilingual pairing
| Need | Fonts | Notes |
|---|---|---|
| Urdu Nastaliq (display, brand) | **Gulzar** (OFL, typographic Nastaliq with a matching Latin; best bilingual default) [V]; Noto Nastaliq Urdu (OFL, calligraphic, tall) [K]; Nafees Nastaleeq (MIT) [V]; Awami Nastaliq (SIL OFL; test rendering) [K] | **Jameel Noori Nastaleeq: licence unclear ("free for Urdu lovers"), so not for commercial work** [V] |
| Urdu, Sindhi, Arabic Naskh (small text, packaging) | Noto Naskh Arabic, Lateef (SIL, built for Sindhi and Urdu), Scheherazade New, Amiri, Markazi Text [K] | Sindhi is set in Naskh and needs ڄ ڃ ڇ ڏ ڙ ڪ ڻ: check every glyph |
| Devanagari / Gurmukhi | Mukta, Hind, Tiro Devanagari, Noto Sans/Serif Devanagari; Noto Gurmukhi, Mukta Mahee, Baloo Paaji 2 [K] | |

Pairing rules (practitioner starting points [UNVERIFIED as fixed numbers]):
1. Match visual size, not point size. Start Urdu at 115–130% of the Latin size.
2. Leading: Nastaliq ≈ 1.8–2.2×, Latin 1.3–1.5×. Never share one line-height token between them.
3. Match stroke contrast: Gulzar with its own Latin, or a low-contrast humanist sans. Nastaliq has no real bold, so build hierarchy with size or colour.
4. Set right to left on its own grid; use `dir` and `lang="ur"` on the web. Urdu digits are U+06F0–06F9.
5. Test Nastaliq shaping in the actual tool (InDesign World-Ready composer; Figma [UNVERIFIED]).

Pakistani packs: labels must be in English and/or Urdu (Punjab Food Authority) [V]. Nutrient text is cited at 3 mm or more (1 mm under 25 cm²) [V secondary; confirm PFA/PSQCA]. Export benchmark: EU 1169/2011 Art. 13, x-height of 1.2 mm or more (0.9 mm if the largest surface is under 80 cm²) [V].

## 4. Pairing and selection
- Bringhurst: suit the text's character; aim for 45–75 characters per line (66 ideal). Lupton: pair by clear contrast and use few families. Butterick: body text first, with 120–145% line spacing [K].
- **Fonts In Use** (fontsinuse.com): check the font's track record in the category, and who already uses it. Typewolf: pairings and alternatives [K].

| Medium ↓ / mood → | Sober, heritage | Contemporary, cultural | Warm, desi, pop | Technical |
|---|---|---|---|---|
| Pack front | Old-style or transitional serif / custom wordmark; Gulzar | Grotesk with character | Expressive display + Nastaliq as a feature | Neo-grotesk, mono |
| Pack legal | Large-x-height humanist sans + Naskh | same | same | same |
| Signage at distance | Open-aperture sans or slab, no hairlines | Wide grotesk | Bold condensed | DIN-like |
| Screen UI | Neutral sans with tabular figures | Grotesk with optical sizes | Humanist or rounded sans | Grotesk or mono |
| Editorial | Text serif + sans captions | Serif with italics + grotesk | Display + calm text serif | Sans + mono |

Thresholds: screen body 16 px or more (WCAG text spacing); signage cap height grows with viewing distance (ADA 703; a rule of thumb is about 1 inch per 10 ft [UNVERIFIED]).

## 5. Font QA checklist
- [ ] Coverage: every language (Urdu, Sindhi, Pashto, Shahmukhi), ₨/Rs, © ® ™ %, fractions, Urdu digits, transliteration diacritics (ā ī ū). Tools: FontDrop, Wakamai Fondue, Font Bakery
- [ ] Kerning and spacing at final size: AVATAR, Ty, LT, all caps; Urdu joining and nuqta collisions
- [ ] Licence file and invoice stored; the font comes from the official source; every use in the brief is covered
- [ ] Embedding (OS/2 fsType) allows PDF and app embedding; outline type in logos and print artwork
- [ ] Variable fonts: named instances for print apps; export static or outline if the printer's RIP is unsure
- [ ] Web: subset (pyftsubset), WOFF2, `font-display: swap`; subset large Nastaliq files

## Sources
openfontlicense.org/ofl-faq · fonts.google.com/analytics · licenseorg.com/guide/fonts/fontshare · collletttivo.it/licensing · helpx.adobe.com/fonts/using/font-licensing.html · github.com/googlefonts/Gulzar · fonts.googleblog.com/2023/03/why-are-there-so-few-digital-nastaliq.html · fontlibrary.org/en/font/nafees-nastaleeq · software.sil.org (Awami, Lateef, Scheherazade) · amirifont.org · unicode.org/charts/PDF/U0600.pdf · brecorder.com/news/amp/4588683 · cdn.georgeinstitute.org (Pakistan fact sheet 2024) · food.ec.europa.eu (FIC language and presentation) · fontsinuse.com · typewolf.com · practicaltypography.com · thinkingwithtype.com · w3.org/TR/WCAG22 · fontdrop.info · wakamaifondue.com · github.com/fonttools/fontbakery
