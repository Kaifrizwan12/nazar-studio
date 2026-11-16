# Case study: run it on your own archive

This is the test that touches the real scenario: a designer with a real archive, an AI, and directions only the designer can give. Repeat it on any brand folder. About 15 minutes.

## 1. Set up
- Put 30+ finished pieces for one brand in a folder. Put brand assets (logo, backdrops, mascot, badges) somewhere else: they are files to place, not pieces to learn from.
- Remove or set aside anything you don't want analysed (people, other clients).
- Split by hand or by rule: about two thirds `train/`, one third `held/`. Held-out pieces never touch the pattern.

## 2. Measure and build (training pieces only)
```
python nazar-voiceprint/engine/portfolio.py train/                 # format, grounds, palette, accent, layout
python nazar-voiceprint/engine/score_pattern.py --build train/ pattern.json
python nazar-voiceprint/engine/score_pattern.py pattern.json held/  # do the habits hold on pieces it never saw?
python nazar-type/engine/font_match.py headline_crop.png "THE WORDS"  # closest installed font, never named by eye
```
The held-out score is your benchmark. A new piece cannot reasonably beat the real work it is meant to match.

## 3. The prompt a real designer writes
Write what you would really say. A good prompter names the canvas, the exact files, the headline style, the subline, what never to add, the voice, and two or three reference pieces. This is the prompt used in the README case study:

```text
Format is 4:5. Make each slide by cropping, not resizing, the top 900x1125 pixels of a story
backdrop: light <file>, dark <file>. Logo <file> on light slides only, top-left, blended with
multiply, never redrawn or recoloured.
Headline: heavy condensed grotesque, ALL CAPS, 2 or 3 lines, left-aligned, black on light and
off-white on dark, the last line in the brand blue. Under it, one short sentence in a plain sans
at about a quarter of the headline size, with clear space between them. Small handle bottom-left.
Do not add buttons, pills, icons, arrows, badges, mascots, faces, stock imagery, your own
gradients or glows. It must not look AI-made.
Voice: short, direct, English mixed with Roman Urdu. No invented numbers or facts.
References: <two or three real slides>. Match their feel, not their words.
Briefs: 1) <...> 2) <...> 3) <...> 4) <...>
```

Run it twice: once with the kit (the pattern file, the exact-assets rule, the engines), and once with a fresh agent that has the same prompt and no kit.

## 4. Check the slides, in order
```
python nazar-core/engine/chain_check.py slides/ copy.json pattern.json   # copy.json: {"slide.png": "all its text"}
python nazar-core/engine/qa_views.py slides/ sheet.jpg                   # sheet + edges, margins, gaps, small text
```
The chain: contrast of the text and of the accent type actually used on its own ground, Hindustani share of the copy, layout, copy lint, and the pattern score (shape, ground, palette, accent, no device the archive never uses). Photo-led posts are scored on shape only. Then look at the QA sheet yourself: hierarchy and concept are yours to judge.

Build the pattern with the exact asset files so the palette is theirs: `python nazar-voiceprint/engine/score_pattern.py --build train/ pattern.json backdrop1.jpg backdrop2.jpg`.

## 5. Read it honestly
- Held-out score against the in-sample score: do the habits generalise?
- Kit run against no-kit run: say what the gap is made of. If it is one check (say, the canvas), that is what the kit added.
- Look at the slides. The score is habits, not quality.
- Log every failure in the kit's `LESSONS.md` and patch the kit with the owner's okay (`nazar-core/references/improve.md`).
