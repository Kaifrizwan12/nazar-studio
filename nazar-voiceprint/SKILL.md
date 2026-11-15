---
name: nazar-voiceprint
description: Nazar Studio's pattern extractor. Use when someone wants AI to write, script or design like THEM instead of like an AI. They drop their own pre-AI archive (old .docx from an office job, essays, journals, scripts, reel scripts, treatments, a design or illustration portfolio, photos), and the kit builds their pattern across three languages (words, story/script, visuals). It confirms the pattern with them, then outputs THE PATTERN, a portable file that overrides any AI's default style (Claude, ChatGPT, Gemini). Engines: ingest.py (archive intake with a pre-AI date filter), analyze.py (stylometry incl. a Hindi-Urdu baseline, cross-document signature phrases, habit vs. genre), and a visual stack run by portfolio.py: palette and composition, colour grading and effects, illustrator strokes, OCR-free layout and type scale, EXIF camera habits, style modes and recurring elements, editing rhythm from video, and pose. Built for creatives first; works for anyone.
---

# Nazar voiceprint

Read `../nazar-core/SKILL.md` first. **The user's prompt leads; use only the layers the job needs.**

**The idea:** your old work already contains your pattern. Every AI has a pattern too, and it's the one everybody can now smell. This kit pulls *yours* out of your archive, checks it with you, and hands any AI a file that makes your pattern win over its own.

Before a job, read the research it stands on:
- `references/stylometry.md`: what a writing fingerprint actually is.
- `references/ai_conditioning.md`: how to make an AI drop its own voice, and the ceiling.
- `references/screenwriting.md`: script, dialogue and reel pacing.
- `references/visual_design.md` and `references/creative_disciplines.md`: designers, illustrators, photographers, editors.

## Say this first (the honest ceiling)
Research from 2025–26 shows prompted style transfer still leaves a measurable gap from true authorship. **The output is a strong, inspectable approximation that you review, not a clone.** Say it before starting.

## The flow (what a first-time user sees)

### 1. Drop the archive
> "Use nazar-voiceprint. My old work is in `~/Documents/old-work`."

Any mess is fine: hundreds of `.docx`, PDFs, `.txt` and `.md` files, Final Draft `.fdx`, `.fountain`, `.rtf`, images.

### 2. Five intake questions (ask them all at once, with options)
1. Is this **your own** work? (Never profile someone else without their consent.)
2. What will you make with the pattern next? (Memos, a deck, academic writing, a script, reels, posters, illustration.)
3. Which languages are in the archive?
4. Do you know any files that were AI-assisted? (They come out.)
5. Did you write any files yourself after 30 Nov 2022? (They can go back in.)

### 3. Intake (`engine/ingest.py <folder> --out voiceprint/<name>/corpus`)
Report it back in one line, e.g.: *"312 documents and 84,000 words in; 41 held back as dated after 30 Nov 2022 (list shown, tick any you wrote yourself); 9 images to the visual layer; 3 skipped."*
- Re-run with `--include-post-ai`, or move ticked files back, as the person decides.
- **Under about 5,000 words the frequency features get noisy.** Say so and ask for more.

### 4. Analysis: run only the layers that apply

**Words** — all text, both layers:
- `engine/analyze.py corpus/text --lang en` (or another language code). It gives:
  - rhythm (mean *and* spread),
  - punctuation and paragraphing,
  - function words: English, and Hindi-Urdu (Devanagari, Urdu script and Roman spellings, with `--lang hinglish` / `hi` / `ur`). Other languages are skipped and the output says why, never faked,
  - **signature phrases that recur across documents** (openers, pivots, sign-offs),
  - a verdict per feature: **habit** (it's them), **varies**, or **document-driven** (it's the genre).
- Then a qualitative read of discourse (`stylometry.md` §3): how they open, hedge, transition and close.

**Story / script** — scripts, treatments, reels:
- Map turns against the baseline as a percentage of each piece (`screenwriting.md`: Save the Cat beats for features; setup → complication → reversal → button for short pieces).
- Note dialogue cadence and devices (refrains, code-switching, frame breaks, buried fables) and format ratios.
- For reels, take hook placement, reveal rate and ending style **from their own catalogue only**. Industry "3-second rules" are unsourced folklore.

**Visual** — designers, illustrators, photographers, colourists, editors:
- One command for the whole stack: `engine/portfolio.py <images folder>`. A look counts as a **habit** only if it appears in ≥60% of pieces; single images are confounded by their content.
- Or run a single engine:
  - `visual.py`: palette habit (ground, support, accent, with shares), air, symmetry, thirds, weight placement, line weight, tone and warm/cool lean.
  - `grade.py`: colour grading and effects as numbers (look stats, colourfulness, split-toning, faded or crushed blacks, roll-off, palette breadth, vignette, grain, softness, bloom), plus look labels tagged measured vs. folklore. Describe the transform, never a film stock.
  - `strokes.py`: illustrators. Skeleton → strokes: length, straightness, taper, pressure swing, loose ends (sketchy vs. confident).
  - `layout.py`: graphic designers, OCR-free. Alignment, columns, margins, type scale (matched to named modular scales), type vs. image share.
  - `exif_habits.py`: photographers. Focal length, aperture, shutter, flash and orientation distributions.
  - `cluster.py`: whole portfolio. Style modes (most creatives have 2–3) and recurring elements across pieces.
  - `video.py`: editors and directors. Cuts, median and distribution of shot lengths, pace trend, 1/f rhythm, grade across shots. Needs `pip install imageio-ffmpeg`, or a cut list.
  - `pose.py`: how people are posed and framed (facing, contrapposto, hands, crop, headroom). Needs `pip install "onnxruntime==1.23.2" rtmlib`, or exported keypoints.
- Each layer reports mean ± spread across the portfolio, plus a plain reading. If there are several style modes, ask which one the pattern is for.
- **Then the VLM pass: this is where you look, because numbers can't find most of a designer's or illustrator's patterns** (a hidden second image in the negative space, hands drawn as mittens, a recurring joke). Follow `references/vlm_protocol.md` exactly:
  1. `engine/views.py <folder> <out>` builds a study sheet per piece (squint, grey, flat colour, edges, five full-detail crops) and a contact sheet. Read the contact sheet first.
  2. Open discovery: list everything that recurs, with no taxonomy.
  3. Run the lenses (Morelli's minor details, Wölfflin, Kress & van Leeuwen, McCloud, Gestalt, plus studio lenses for subject, wink, type-and-image, edges, texture, rhythm, frames).
  4. **A finding counts only with evidence** (piece + crop), in **≥3 pieces**. Counts and measures come from the engines, never by eye. Never attribute to another artist. Describe before interpreting.
  5. Output the table (pattern, lens, seen in, evidence, confidence, maker's why), then confirm each row with the maker. The *why* is theirs to give.
- Motifs, meaning and intent are **not** computable (Gatys 2015; tacit-knowledge literature). They come from step 5.

**Stability:** every layer reports which features hold across the archive. Only habits go into the pattern; genre-driven features go into briefs.

### 5. Confirm loop (what makes it *theirs*)
- **About ten plain statements**, never raw numbers first. *"You put the decision first and the reason second. Deliberate?"* / *"Your frames are mostly air, with one hot accent. Rule or accident?"* They answer yes, no, or "that's the genre".
- **Their never list:** 2–5 things that would feel fake coming from them, each with what they'd do instead. This list outranks any generic AI-tell list.
- **Creatives:** the meaning of recurring motifs, why they crop, cut or break the grid the way they do, and which project or genre the next piece should follow.
- **Register choice:** when the archive holds several voices (academic vs. journal vs. email), which one this pattern is for.

### 6. Output: THE PATTERN (`templates/pattern.md` → `voiceprint/<name>/PATTERN.md`)
- §0 precedence block: this overrides the AI's defaults, and its usual habits count as errors.
- Habits in plain language, signature moves, story and visual layers if relevant.
- 3–5 **real quoted** exemplars.
- The never list with do-instead.
- A backup list of AI tells.
- The plan → draft → check → revise procedure, with re-anchoring on exemplars every 2–3 paragraphs or scenes.
- Honesty line.

### 7. Test drive (always)
- Write a short sample in their next format, then run the **same engine on the sample** and show it beside their numbers and one real exemplar.
- Fix what failed (see `examples/tamasha_pattern.md`: three passes from "flat, even" to matching rhythm).
- They mark anything that's off, and the pattern becomes v2.

### 8. Use it anywhere
- Paste it into Claude project instructions, a ChatGPT custom GPT or a Gemini Gem.
- In this repo, "write this using my pattern" pulls `voiceprint/<name>/PATTERN.md`.
- Re-run when they have more self-written work. Keep versions.

## Don't
- Profile anyone who isn't the person in the room.
- Redistribute copyrighted material from an archive (a famous script, someone else's art). Analyse it, quote briefly, never republish it.
- Skip the confirm loop. An unconfirmed pattern is a guess.
- Promise a clone.

## Files
- `engine/ingest.py`: archive → corpus, pre-AI date filter, manifest.
- `engine/analyze.py`: words layer. 1 file = profile, 2 = diff, 3+ = archive pattern with habit verdicts and cross-document signature phrases.
- `engine/views.py`: study sheets and a contact sheet, so a vision model can see the details. `references/vlm_protocol.md`: the researched protocol for the VLM pass.
- `engine/visual.py`, `grade.py`, `strokes.py`, `layout.py`, `exif_habits.py`, `cluster.py`, `video.py`, `pose.py`: the visual layers; `portfolio.py` runs them all.
- `engine/baselines/`: the Hindi-Urdu function-word baseline (OpenSubtitles2018 via FrequencyWords, CC-BY-SA-4.0) and the script that builds it.
- `templates/pattern.md`: the output.
- `references/`: the research (stylometry, AI conditioning, screenwriting, visual design, creative disciplines, grading/effects/pose).
- `examples/`: Tamasha pattern read; the original 3 AM monologue (draft → pass 4); known-answer test generators for every engine (`make_genre_demos.py`, `make_grade_demo.py`) and the README card renderer.
