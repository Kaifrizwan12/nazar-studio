# Scenarios: how a real person uses the skill

A person with a mind doesn't say "use the skill". They say what they have, what they want, which kits matter, what to follow and what never to do, and leave the rest to Claude. Each scenario below is written that way, with its status on the evidence so far.

**Status key:** *tested* = run end to end on real work; *engines tested* = the engines ran on real public files, the full scenario hasn't; *untested* = built, not yet run on real files.

## 1. A designer keeps one brand's look across AI tools — *tested*
**They hand over:** 30+ finished pieces for one brand, plus the exact backdrop and logo files.
**Their prompt:**
> Learn how I work from the 28 pieces in this folder with nazar-voiceprint, then make four new slides for these briefs. Exact backdrop and logo files, placed as they are. Check the headline font with nazar-type and contrast with nazar-colour, write the copy with nazar-social, and QA before you show me. Don't add anything my work doesn't use.
**Runs:** voiceprint (format, grounds, palette, accent, devices) → type (`font_match.py`) → colour (contrast) → backdrops (exact files) → social (copy lint) → core (QA, `chain_check.py`).
**Comes back:** slides, a pattern file, a QA line per slide, and what it doesn't know (the font is a near match).
**They must supply:** the archive, the exact files, the headline style they know by eye, and the voice.
Result: the README case study.

## 2. An agency inherits a client's archive — *tested (pattern and held-out check)*
**They hand over:** 60 posts the previous designer made, no brand book.
**Their prompt:**
> Here are the client's last 60 posts. Tell me what the system is: formats, grounds, accent, what they never do, and where the pieces split into modes. Hold back a third and show me the habits hold on those. Then draft a launch carousel that follows the system without copying any post.
**Runs:** voiceprint (`portfolio.py`, `score_pattern.py --build`, held-out score, photo mode, device check) → backdrops (rebuild the static layer from the book's real parts).
**Comes back:** a measured system, which habits are real (held-out score), and a prompt block (`score_pattern.py --prompt`) the whole team can reuse.
**They must supply:** the posts, and a person who knows the brand to confirm every line.

## 3. A writer or scriptwriter wants AI to write like them — *engines tested*
**They hand over:** years of their own documents: essays, scripts, memos, reel scripts.
**Their prompt:**
> This is my own writing from before 2023, plus a few things I wrote since that I want in. Build my pattern with nazar-voiceprint. Don't flatten me into a standard AI voice. Then write this memo the way I would, and tell me where you are guessing.
**Runs:** voiceprint (ingest with the person's word on authorship, stylometry, signature phrases, habit vs genre, Hindustani baseline) → confirm loop → PATTERN.md.
**Comes back:** a portable pattern file, a draft, and the honest ceiling: a strong approximation, not a clone.
**Status:** the engines ran on public-domain genres and a Hindustani baseline. A full personal archive and the Gutenberg authorship test are still to do.

## 4. An illustrator wants spot art in their own line — *engines tested*
**They hand over:** 40 pen or brush drawings, scanned large (about 2400 px across).
**Their prompt:**
> These are my line drawings. Read how my line behaves: loose or confident, tapered or even, which way it leans. Then draw a spot illustration of a market stall in that line, in code, no AI imagery.
**Runs:** voiceprint (`portfolio.py --line`, `strokes.py`) → illustration (drawing in code, `trace.py --fine`).
**Comes back:** a line reading with a resolution warning if the scans are too small, and an SVG.
**Status:** tested on public-domain prints. A real portfolio hasn't been run.

## 5. A bilingual packaging job — *engines tested*
**They hand over:** a snack pack brief, English and Urdu, a 90 mm label, legal text.
**Their prompt:**
> Urdu and English snack pack, 90 mm label. Pick typefaces that cover both, check small legal text reaches 1.2 mm x-height, build the dieline and check the safe areas. Nothing that is a template font.
**Runs:** type (`type_check.py`, `font_match.py`) → colour (print-safe, contrast) → dieline → packaging QA.
**Comes back:** font recommendations with licences and coverage, a dieline with art placed, and a QA list.
**Status:** tested on public fonts and a public-domain carton. A real client pack and real Urdu print are untested.

## 6. A photographer or editor wants their framing and pace read — *untested*
**They hand over:** years of shoots and cuts.
**Their prompt:**
> Read my camera habits and how I frame and cut: focal lengths, headroom, how long my shots run. Describe it, then brief a second shooter in my style.
**Runs:** voiceprint (`exif_habits.py`, `pose.py`, `video.py`).
**Status:** built and unit-tested, not run on real files (the pose model isn't installed yet).

## 7. A non-creative person: memos and emails — *untested at scale*
**They hand over:** old work emails and memos.
**Their prompt:** *Here are my emails from the last five years. Write my reply to this client the way I would.*
**Runs:** voiceprint (words layer).
**Status:** same engines as scenario 3.

## What every scenario shares
1. The person states what to reference, follow and avoid. The kit never overrides that.
2. Claude runs the engines instead of guessing, and says what it measured and what it couldn't.
3. Held-back work checks the pattern, and the QA runs before anything is shown.
4. Whatever fails is logged in the kit's `LESSONS.md` and patched with the owner's okay (`improve.md`).
