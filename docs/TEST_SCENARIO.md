# The test scenario: a real designer, a real archive, blind judges

Back to the [README](../README.md). This is the protocol every result in the README follows. It is written so anyone can rerun it on their own archive.

## 1. The archive
- One brand's finished social pieces (42 here, kept anonymous). Brand assets (logo, backdrops, mascot) are files to place, not pieces to learn from.
- A fixed split: two thirds teach, one third is **held back and never opened** by any run. Pieces with people stay out of every public image.
- The skill learns once and saves a **brand profile**: format, grounds, palette, accent, voice and handle, the devices, the usage rules (which ground carries which content, where the logo and handle sit, which colour goes on which element), and the exact files.

## 2. The person
A designer who knows their brand writes the kind of prompt a designer writes: what to make, which files, how the backdrops are used, what never appears, the voice. The same prompt goes to every condition that is allowed it.

## 3. The skill's questions
The skill runs step 0: it tags the job and the brand, and asks only what the prompt doesn't say (at most four questions, with options and a recommended pick). A fixed answer sheet, written once from the designer's known preferences, answers them, so every run gets the same answers and nothing is invented mid-test. The number of questions asked is reported.

## 4. The briefs (12)
- **Six single posts:** verification is free and takes a minute; partner brands, students are waiting; what "verified student" means; the app launches soon; bring a friend to the next community event; a meme about paying full price.
- **One six-slide carousel:** how verification works (a cover hook, four steps, a takeaway slide).

## 5. The conditions
| | Prompt | Skill | Told to measure and check |
|---|---|---|---|
| A | casual | no | no |
| B | the designer's prompt | no | yes, with its own tools |
| C | the designer's prompt | yes, with step 0 questions | the skill's own checks |

Every run is a fresh agent that has never seen the held-back pieces or another run's output.

## 5b. The feedback round (real use)
Real work is never one shot. After round 1 the designer looks at each run's drafts and writes notes in their own words (or a fixed note sheet
written after seeing them, so every run gets the same kind of notes): what to keep, what to change, what never to do again. The same agent revises
once, and both rounds are judged blind together, so the gain from one round of direction is measured. Results from runs without this round are
labelled "one shot".

## 6. Judging
- **Three blind raters doing real jobs**, each shown the brand's reference pieces and a shuffled mix of the held-back real pieces and every generated slide, labels hidden: a **brand manager** with the brand guidelines (brand-kit compliance, approve / edits / reject, the errors to send back), a **social media lead** (reads on a phone, would post this week) and an **art director** (looks like the designer made it, quality). Each also guesses real or generated.
- **A human pick test** (`nazar-voiceprint/engine/pick_test.py`): the designer picks real from generated, blind.

## 7. What is measured
Brand fit, quality, "called real" rate; clutter (objects per slide against the archive's range) and unfamiliar objects; off-theme pixels; colour-role drift; backdrop match; copy length; contrast; tokens, tool calls and time; the person's prompt words and the questions answered.

## 8. What is shown publicly
Numbers, and cards with the brand's logo and handle blurred, unless the brand owner approves showing them.
