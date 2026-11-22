# Kit profiles: what each kit needs researched

Every kit's research runs through this kit. Pick the profile for the job (a job can use several), run its angles (numbers from `angles.md`) and build its dataset. `engine/dataset.py plan <dir> "<brief>" --kit <name>` writes the tree with that profile's angles and dataset kinds.

| Kit | Angles | Dataset (real, sourced, reference only) | Target |
|---|---|---|---|
| nazar-strategy | 01 02 05 06 08 09 12 | competitors' sites, ads, claims and price points; category ads past and present | 80 |
| nazar-logo | 01 02 03 05 06 07 | competitor marks, the category's visual codes, local lettering and signage, marks by masters in the field, trademark lookalikes | 150 |
| nazar-brand-book | 01 03 05 06 07 10 | identity manuals and brand books (archive and current), competitor systems, the place's colours and materials | 120 |
| nazar-packaging | 04 05 06 07 10 11 | every relevant real pack: competitors (front, back, side, shelf), category leaders worldwide, award winners, heritage packs, the local shelf, app tiles | 250 |
| nazar-dieline | 04 06 07 10 | structures: pouches, cartons, tins, closures, windows, displays; converter catalogues; flat dielines where public | 100 |
| nazar-shoot / nazar-art-direction | 03 04 07 10 | product photographs of the category by the best photographers, real-life shots of the product in use, lighting references, the place | 150 |
| nazar-study | 07 | the 20-40 best pieces to measure (look.py), chosen from the other datasets | 30 |
| nazar-social | 01 06 08 09 10 | the brand's and competitors' feeds (posts, reels, stories), best category accounts worldwide, local meme and language formats | 200 |
| nazar-backdrops | 01 10 | the brand's own routine posts, platform safe-zone specs | 40 |
| nazar-ooh | 03 06 07 09 10 | street media in the place (billboards, rickshaw backs, walls, shop signs), award-winning OOH, local hand-painted signage | 150 |
| nazar-motion | 07 10 | idents, logo animations and title sequences in the category; platform video specs | 80 |
| nazar-web | 06 07 08 10 | competitor and leader sites (full-page captures), checkout and product-page patterns | 80 |
| nazar-type | 03 05 07 | lettering in the place and the category, Fonts In Use entries, archive specimens, script history | 120 |
| nazar-colour | 03 04 05 | the place's surfaces, the product's real colours, archive pigments and palettes, competitor colour codes | 120 |
| nazar-illustration | 03 05 07 | regional craft and vernacular art, botanical and archive plates, illustrators in the category | 120 |
| nazar-prompts | 07 10 | real photographs that set the target for any plate (never AI images as targets) | 40 |
| nazar-voiceprint | 01 08 09 | the person's or brand's own pre-AI work (from the user), plus how the audience talks | as given |
| nazar-story / nazar-pitch | 01 06 07 08 | best case studies in the field (Behance, studio sites), pitch decks made public, the client's market numbers | 60 |

Every profile also writes `research/summary.md` and `gaps.md`. When a later kit starts and its profile hasn't been run for this project, run just the missing angles and dataset kinds, and add to the same `research/` folder (one folder per project, growing).
