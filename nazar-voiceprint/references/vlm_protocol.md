# The VLM pass: how Claude finds the patterns the engines can't

Confidence tags: [V] confirmed in sources, [K] standard design practice, not separately sourced, [UNVERIFIED].

The engines measure (palette, grading, strokes, layout, camera, cuts, pose). They can't tell you that a designer always hides a second image in the negative space, draws hands as three-fingered mittens, or ends every composition with one off-register accent. A vision-language model (you, looking) can. But a VLM left to free-associate invents. This protocol points the looking at researched lenses, gates every claim behind evidence, and hands counting and measuring to the engines.

## Why a protocol, and what the research says
- **VLMs are weak at fine perception.** "Vision language models are blind" (Rahmanzadehgervi et al., ACCV 2024, arXiv 2407.06581) found they struggle to count line intersections and overlapping shapes; later work (MIRAGE, arXiv 2505.10604) finds counting and spatial failures persist [V]. **So the model never counts or measures.** The engines do, and their numbers go in as evidence.
- **Art attribution by VLMs works above chance, but trails dedicated classifiers** (KU Leuven, arXiv 2409.03521), and connoisseur-level diagnosis is near chance on CArtBench [V, secondary]. **So never attribute ("this is by X"). Name patterns.**
- **Free-form reasoning about art invites invented opinions; decomposing into sub-tasks with concrete formal-analysis language reduces them** (ArtCoT, arXiv 2501.09012) [V; gain figures vary by source]. **So describe formally first, interpret last, and ask the maker for the why.**
- **Crops and multi-resolution views help fine-detail questions** (CropVLM, arXiv 2511.19820; Dragonfly, arXiv 2406.00977), and detector outputs fed to the VLM improve counting (GroundCount, arXiv 2603.10978) [V; no head-to-head comparison exists]. **So `engine/views.py` prepares crops, and the engines supply the numbers.**
- [UNVERIFIED] I found no study showing that forcing the model to cite regions reduces hallucination. The evidence rule below is a sound discipline, not a proven fix.

## Step 0: prepare the views
```
python engine/views.py <portfolio folder> <out folder>
```
One study sheet per piece (original, squint, greyscale, 4-colour flat, edge map, five full-detail crops) plus `contact.jpg`, the whole body of work at once. Read the contact sheet first, then the sheets. Each view answers one question: squint = hierarchy and focal point; grey = value structure; flat = figure-ground and palette logic; edges = line vs. mass, where detail lives; crops = the habitual minor details.

## Step 1: open discovery (the "many, many other patterns" pass)
Before any lens, look at `contact.jpg` and list **everything that recurs**, in plain words, with no taxonomy: shapes, subjects, gestures, compositions, devices, jokes, materials, a certain kind of corner. Write each as a candidate with the pieces it appears in. This is where patterns no checklist anticipated show up. Then carry every candidate through the same tests as the lens findings in steps 3–4.

## Step 2: the lenses
Each lens is a question answered by looking. **Evidence required** is what makes a finding count.

### Core lenses (sourced)
| Lens | Question | Evidence required | Source |
|---|---|---|---|
| Minor-detail habit | How do they draw hands, eyes, ears, corners, stroke ends? | The same treatment in ≥3 crops from different pieces | Morelli; Ginzburg, "Clues" (1979) [V] |
| Signature and lettering quirks | Any recurring signature, letterform or numeral oddity? | A crop of each instance | Morelli [V] |
| Linear vs. painterly | Do edges dominate, or masses and soft boundaries? | Name two edges | Wölfflin, *Principles of Art History* (1915) [V] |
| Plane vs. recession | Parallel layers, or depth into the page? | Point to the overlap cues | Wölfflin [V] |
| Closed vs. open form | Contained by the frame, or running off it? | Which edges are cropped | Wölfflin [V] |
| Multiplicity vs. unity | Independent parts, or one subordinated whole? | The dominant element | Wölfflin [V] (critics call this pair and the next redundant) |
| Given / New, Ideal / Real | What sits left vs. right, top vs. bottom, centre vs. margin? | An element-by-zone list | Kress & van Leeuwen, *Reading Images* [V] |
| Salience hierarchy | What wins attention 1st, 2nd, 3rd, and by what means (size, contrast, focus)? | An ordered list with the cause; confirm on the squint view | Kress & van Leeuwen [V] |
| Gaze and distance | Do figures look at the viewer (demand) or past (offer)? Intimate or far, high or low angle? | A per-figure note | Kress & van Leeuwen [V] |
| Abstraction position | Where on realistic ↔ iconic ↔ abstract? Faces generic or specific? | Compare two pieces | McCloud, *Understanding Comics* (his own triangle's corners are disputed in sources) [V, partly] |
| Closure habit | What is left out for the viewer to complete? | Name the missing part | McCloud [V] |
| Figure-ground play | Does negative space form a second image? | State both readings | Gestalt practice [V] |
| Grouping logic | Proximity, similarity or continuity: which organises it? | Which elements group | Gestalt practice [V] |
| Three levels | What is drawn, what it signifies, why this choice? | Levels 1–2 from the image; **level 3 only from the maker** | Panofsky, *Studies in Iconology* (1939); Schapiro [V] |

Dondis's visual elements (*A Primer of Visual Literacy*, 1973: dot, line, shape, direction, value, hue, saturation, texture, scale, dimension, motion) give a checklist for texture and motion questions [V, secondary].

### Studio lenses (design and illustration practice [K], held to the same evidence rules)
| Lens | Question | Evidence required |
|---|---|---|
| Subject choice | What do they draw again and again, and what do they never draw? | Tally across pieces |
| The wink | Is there a hidden joke, second reading or Easter egg, and where does it sit? | A crop, and the maker's confirmation |
| Type and image | Is lettering part of the image, set against it, or hidden in it? | A crop of the type |
| Edge treatment | How do edges end: ragged, ruled, bled off, vignetted, deckled? | A crop of an edge |
| Material and texture | What material is being imitated or avoided (paper, print, grain, brush)? | A crop of the texture |
| Light and shadow | One declared light direction? Cast shadows, hatch, none? | The shadow side, on the grey view |
| Rhythm and repetition | What repeats, at what interval, and where is the repeat broken? | Mark the repeats and the break |
| Scale contrast | Is there one huge element against many small ones, or an even scale? | The ratio, measured by an engine if possible |
| Border and frame devices | Rules, frames, panels, corner marks, folios? | A crop |
| Narrative moment | Which moment of the story is drawn: before, during or after? | One sentence per piece |
| Cultural and period references | What visual traditions are quoted, in the maker's own words? | Maker only |
| Colour roles | Which colours do which jobs (ground, ink, accent, shadow)? | The flat view plus the engine's palette |

## Step 3: the evidence rules (a finding without these doesn't count)
1. **Name the piece and the place.** Every claim cites a piece and a crop or region, e.g. "poster 4, bottom-right crop".
2. **Recurrence threshold:** a habit needs **≥3 pieces**. Two is "possible". One is an observation, not a pattern.
3. **Counts and measures go to the engines.** Never count objects, intersections or alignment by eye. Ask `visual.py`, `layout.py`, `strokes.py` or `grade.py`, and quote their numbers.
4. **Crop, don't glance.** Check detail claims on the full-resolution crops, not the thumbnail.
5. **Describe before interpreting.** Write the formal description first. Meaning comes last.
6. **Never attribute.** Don't say "this resembles Rand". Name the pattern itself.
7. **Mark confidence:** *seen* (visible in crops), *likely* (consistent but not isolated), *unsure*. Never invent detail in stylised images (a mitten hand is a finding, not a mistake to correct).
8. **The why is the maker's.** Level 3 (intent, meaning, reference) is asked in the confirm loop and written in their words.

## Step 4: the output table
Fill one row per pattern. This table is what goes into the pattern file (§4, "Recurring devices").

| Pattern | Lens | Seen in | Evidence (crop / engine number) | Confidence | Maker's why |
|---|---|---|---|---|---|
| hands drawn as three-fingered mittens | minor-detail habit | 5 of 8 pieces | crops: p2 bottom-left, p4 centre, p6 bottom-right | seen | "I never learned fingers, it became the joke" |

## Step 5: confirm
Read the table back in plain words. For each row, ask: *deliberate, or accident? always, or only on this kind of job?* A pattern the maker calls an accident goes in the "never lean on this" list. A pattern they call a rule goes into the pattern file with their wording.

## Sources
arXiv 2407.06581 · arXiv 2505.10604 · arXiv 2409.03521 · arXiv 2501.09012 · arXiv 2511.19820 · arXiv 2406.00977 · arXiv 2603.10978 · Ginzburg, "Clues: Roots of an Evidential Paradigm" (1979; JHU Press) · Wölfflin, *Kunstgeschichtliche Grundbegriffe* (1915) · Panofsky, *Studies in Iconology* (1939) · Schapiro, "Style" (1953; his exact wording unverified) · Kress & van Leeuwen, *Reading Images: The Grammar of Visual Design* · McCloud, *Understanding Comics* (1993) · Dondis, *A Primer of Visual Literacy* (1973) · DeSantis Breindel, visual brand audit (brand-audit practice only; no source documents reverse-engineering one designer's habits)
