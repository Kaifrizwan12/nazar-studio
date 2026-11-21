# Handover and close

## Handover pack
- Final files in the agreed structure (each kit's deliverables section), with a **README** saying what to use where
- Source files (if included in scope)
- Brand guidelines (PDF) and any quick guides
- A licence list: fonts, images, music, with who holds each licence
- The trademark first-pass record, with the recommendation for legal clearance
- Contacts for future work, and a support window if agreed (e.g. 30 days for small fixes)

## Close the project
- Final invoice, sent once the files are ready (and files released on payment, per the agreement)
- A short close call: what worked, what to improve, what's next (packaging, social, web, a retainer)
- Ask for a testimonial and permission to publish
- Archive the project: final files, `SPEC.md`, research, correspondence

## Case study / Behance write-up
Short paragraphs, in this order: the client and the problem → the insight from research → the idea (one sentence) → the mark and system → the applications → the outcome (real results if available) → credits (team, photographers, typefaces, archives used).
Images: the strongest single image first, then the system, then applications in use (real photos where possible), then details. Label concept or fictional work honestly. Respect confidentiality and the launch timing.

## Client deck and Behance: what works (owner-tested)
- **Visual-first, one short title per page.** Kicker + a title under ~30 characters; the pack fills the page. Paragraphs belong in the call, not on the slide.
- **A width guard on every text line:** measure each line against its box, shrink to a floor, two lines for narrow columns, and **fail the build** if anything still overflows. Look at a contact sheet of every page before sending.
- **Never crop the product at a page edge** by accident (slice crops cut pack tops). Fit packs whole; crop only on purpose (a macro cover).
- **Cover: one pack, very close** (frost, product, the name filling the frame) reads modern. A flood colour plus a row of packs reads like a catalogue.
- **Close on the best range photo under a tinted gradient with a thank-you** in the brand's voice.
- **Behance = the same pages in case-study order,** no folios, no client to-do page. Keep the PDF light (render pages to JPEG; vector-embedded photos blew one deck past 100 MB).
- **Client folder:** a root folder with only the PDF, pack images, film and one range photo, friendly file names, no tech files.
- **End the client deck with "How far are we":** Done / Next / Need from you, short bullets.


## Review wall (comments that reach Claude)
Use `nazar-core/engine/review_wall.py` and follow `nazar-core/references/review_wall.md`: one command builds the page, one publish puts it live, and notes sent to Claude come back to the chat.

## Packaging the delivery (engine/handover.py)
One manifest (`../examples/handover_manifest.json`) declares every output, and the engine builds the folders, so nothing is hand-copied. The dated sources are in `research_handover.md`.
```
python engine/handover.py mark  manifest.json              # at the START of a render run
python engine/handover.py build manifest.json --dry-run    # what would be added / changed / parked + panels to re-upload
python engine/handover.py build manifest.json              # folders + README.txt + SHA256SUMS.txt + covers + zips
python engine/handover.py diff  OLD_FOLDER_or_zip NEW      # what changed between two releases, by content
```

**Manifest keys:**
- **Top level:** `project`, `slug`, `version`, `date` (ISO 8601), `source_root`, `release_root`, and optionally `build_marker`.
- **`groups`:** each has a `number` and a `label`.
- **`targets`:** any name. Each target has a `kind` (client / portfolio / press / social), a `platform` (behance / dribbble / site / social), a `folder` template, `naming` (human or safe), `cover`, `zip`, `readme` and `checksums`.
- **`items`:**
  - `src`: a glob template for the source files.
  - `name`: a template. Fields: `{group} {label} {line} {size} {sku} {view} {nn} {stem} {v} {stamp}`, plus anything set in `for` / `rows` / `with` / `match` / `map`. Filters: `|cap |title |upper |lower |words`.
  - Optional: `status` (concept / press-ready), `ai`, `inputs`, `static`, `optional`.
- **`handover`:** studio, contact, colour, fonts, stock, ai, support.

**Rules it enforces (each from the research):**
- **Version and date in every folder name** (`CLIENT_<SLUG>_v02_YYYY-MM-DD`). Numbered file names sort in reading order, with leading zeros. Never call a file "final".
- **Names that are safe everywhere:**
  - No `< > : " / \ | ? *`, no control characters, and no trailing space or period.
  - Device names (CON, NUL, COM1, COM¹ ...) get a `_` prefix.
  - NFC Unicode.
  - A name is 120 characters or fewer. Folder plus name is 200 or fewer, so it fits Windows' 260 after unzipping into Downloads.
  - Names must differ beyond case, because Windows and macOS ignore case.
  - Client folders use human names (spaces allowed). Portfolio, press and social folders use ASCII `A-Z 0-9 . _ -` only.
- **Fail loudly, all problems at once.** It fails on a missing source, a duplicate name, a path that is too long, a file over the platform's hard limit, or a **stale** source. A source is stale if it is older than a declared input (re-render it), or older than the build marker (it was not re-rendered in the last run; mark photos `static`). `--allow-stale` turns stale failures into warnings, for a deliberate partial release.
- **Never delete.** A changed or removed file, and an old zip, are moved to `<release_root>/_parked/<timestamp>/<folder>/` before the new one lands. The delivery folder stays clean.
- **SHA-256 for every file** (`SHA256SUMS.txt`, which works with `sha256sum -c`). The client or printer can prove nothing changed in transit, and the next release diff is exact.
- **README.txt in every folder**, covering:
  - what is inside: per file, the group, format, pixels, colour mode and ICC profile, PDF/X version, size and status
  - formats and colour
  - **fonts and licences**: who holds each one, and whether the font files are included
  - stock
  - **concept vs press-ready**
  - the **AI disclosure**, when any item is `ai: true`
  - how to check the checksums, and support
- **Covers at platform sizes** from one source (centre crop, Lanczos); a source already at the exact size is shipped byte for byte. Sizes:
  - Behance: 1616×1264 and 808×632. The minimum is 808×632, it shows at 202×158, and a GIF cannot be the cover.
  - Dribbble: 1600×1200.
  - Site: 1200×630.
  - Social: 1080×1350 and 1080×1080.
- **Platform checks:**
  - Behance: a warning over 2800 px wide or 10 MB; a failure over 50 MB.
  - Dribbble: at least 1600 px wide; images 10 MB or less; video 20 MB or less.
  - Press: a warning on any PDF that is not PDF/X.
- **A zip that comes out the same every time**, beside each folder: entries sorted, a fixed date, media stored, text compressed, and the UTF-8 name flag for non-ASCII names. If an existing zip has the same contents (names and CRC), it is kept.
- **The dry run is the re-upload list.** Run it after any fix: it names each changed portfolio panel number (`re-upload panels: 03, 07`), so you replace only those on Behance. `diff` between two releases gives the same list after the fact.

**Before sending:**
- [ ] The dry run is clean: no missing or stale sources, and every warning read and accepted
- [ ] Read the README once as the client would: fonts, licences, AI line and status are all true
- [ ] Open the zip on another machine (Windows and macOS if possible): accented names intact, no path too long
- [ ] Press files: PDF/X-4 per the printer's spec, bleed as they ask, fonts embedded or outlined, a proof requested
- [ ] Licences: if OFL font files ship, their licence file goes with them. Never ship commercial font files; the client buys their own. List stock with its licence holder
- [ ] Portfolio: the cover has no text and a central subject; upload in name order, and re-upload only the panels the dry run names
