# Research path: the full-proof method

Kaif's rule: **no reference, no decision.** Research runs between intake rounds 1 and 2, and it's what makes the round-2 options credible. Use WebSearch (several queries in parallel) and fetch the real pages. Save everything to `research/` in the brand repo.

## Tag every finding
| Tag | Meaning | Weight |
|---|---|---|
| **[ARCH]** | Primary archive material: a scanned manual, label, poster, map, pigment record or museum object | Strongest. You can base a decision on it. |
| **[SRC]** | Secondary web source: an article, case study or interview | Good for context and facts; cite the URL |
| **[KNOWN]** | Established design knowledge (Albers, Itten, Vignelli, Swiss grid...) | Fine, but name it |
| **[TREND]** | Trend blogs and "2026 trends" lists, often vendor content | Context only, never the reason for a decision |
| **[IDEA]** | Our own move built on top of the above | Must point to the [ARCH]/[SRC] it grows from |

## The eight passes (do all eight, briefly)
Each pass produces 5–15 findings in `research/0N_*.md` with links, plus what it suggests for the book.

1. **The category's own archive.** How has this category looked for 100 years? Find old packaging, labels, ads and manuals for it.
 - Food and produce: fruit-crate and can labels (LAPL on Calisphere, UC Davis Lug & Can Labels, Boston Public Library on Digital Commonwealth, the State Library of Florida), Cooper Hewitt packaging, old grocer ads.
 - Tech: corporate identity manuals (IBM, Braun, Lufthansa, NASA, NYCTA), Unit Editions' *Manuals 1 & 2*, Standards Manual reissues, early computer manuals.
 - Fashion and beauty: magazine archives, old label and swing-tag collections.
 - Services and institutions: transit manuals, airline identities, municipal signage.
 → Find what's *always* been done (a cliché to avoid or subvert) and one forgotten thing worth reviving.
2. **The place.** Where does the brand live or come from? Real maps (OpenStreetMap via Overpass), street names, local materials (limewash, terrazzo, jute, steel), local signage and lettering, vernacular art (hand-painted signs, vehicle art, posters, matchbox and calendar art), local colour names. Find the region's own design archive, national archive and visual-culture books (`sources.md` lists some by region).
3. **The material or ingredient.** What is it made of? Photograph-free studies: cross-sections, botanical plates (Biodiversity Heritage Library), mineral and pigment records, process diagrams. Dried fruit → orchard maps, drying racks, botanical plates of apricot and fig, old Gilgit-Baltistan trade routes.
4. **Colour sources.** Build palettes from evidence, not pickers: Sanzo Wada's *Dictionary of Color Combinations* (348 plates; browse the digitised plates, check against the Seigensha book), *Werner's Nomenclature of Colours* (1814/1821; Nicholas Rougeux's interactive edition), historic pigments (lapis, malachite, orpiment, lac, hingul, ramraj), the place's own surfaces, and period printing (riso inks, two-colour litho, newspaper spot colours). Method in the kit's colour reference (e.g. `nazar-brand-book/references/05_colour.md`).
5. **Type sources.** Fonts In Use (what's been set in this category and region), Letterform Archive's online archive, the local script's history (for Urdu: Nastaliq vs Naskh vs Kufic, newspaper Nastaliq, hand-painted signage). Check every font's licence.
6. **Identity systems to learn from.** Pick 3 strong systems and write one line on *why* each works: a strict system (transit or agency manuals), a flexible system (an identity that changes with its content), a character system (a mascot with rules), and a format reference for the book itself. Choose systems that fit this brand's problem, not the most famous ones. Use `masters.md` for the principles behind them.
7. **Competitors and the shelf.** Find 6–10 direct competitors. Plot them on 2 axes (for example sober↔loud, heritage↔modern) as a simple diagram in `research/`. The brand must sit somewhere empty. For an existing brand, also list its current distinctive assets and test each one for fame (do people know it?) and uniqueness (does it point to this brand only?).
8. **Mascot and character precedent** (only if a mascot is on the table): see `nazar-brand-book/references/08_mascots.md`.

## The moodboard rule
Collect real references in `research/moodboard/` (downloaded archive scans, with the source in the filename: `archive-name_19931_apricot.jpg`). Never put AI images in a moodboard. Reference images are for study and are **never placed in the book** unless they're public domain or licensed. Check the rights statement on every archive item; Artvee, the Public Domain Review and the Internet Archive are good starting points, but verify each item.

## Output
- `research/00_inventory.md`: what's in the repo
- `research/01_category.md` … `research/08_mascot.md`: one per pass
- `research/sources.md`: every URL, grouped and tagged
- `research/summary.md`: **one page**: the 5 findings that matter most, the cliché to avoid, the forgotten thing to revive, the empty spot on the competitor map, and 3 concept seeds. This is what round 2 is built from.

## Rules of evidence
- Prefer primary documents (the actual manual PDF, the museum record) over articles about them.
- When sources disagree (dates, counts, attributions), say so and use the most authoritative one (the museum, the publisher, the original document).
- Don't present a reference as yours: the credits page lists the archives used.
- Search the web in parallel batches of 4–6 queries. Use extended search only for niche or very recent facts.
