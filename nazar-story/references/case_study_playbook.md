# Case-study playbook: from teardown to published project

`sequence.md` decides the pages; this decides everything around them: the teardown before, the written project text, the fields Behance asks for, the checks before publishing. Research: `research.md`, `research_behance_2026.md`.

## 1. Tear down before you plan (30 minutes, every new category)
Run `../../nazar-study/references/teardown.md` §3 on 6-10 strong projects in the same category (featured on Behance, award winners, the best studio case pages). Write in `research/case_teardown.md`:
- the 5 moves that recur in the strongest (for packaging this has held: hero first, idea in a line before the system, the system as rules, the range together once, one page per format, macro detail, one real-world moment, a calm studio close);
- the 3 moves that recur in weak ones (one template for every panel, cartoon mockups, callouts over the product, process dumped as a wall of sketches);
- the gap our story can own (a measured flats page, a film, a print-ready proof, a local idea).
Optional: `look.py set` on their panels for the palette, empty space and text density they use.

## 2. The flatplan (before any page)
Follow `sequence.md`. Add two checks the teardown usually surfaces:
- **Thinking is visible.** At least one page shows how the decision was made: the insight with its evidence, the system measured, a road to print. A curator looks for "innovative, polished, thoughtful, well-crafted" work [SRC: Behance curation team]. Process means a decision with its reason, not a dump of sketches.
- **Outcome is stated** where one exists (shelf, launch, numbers). If there is none yet, say what stage it is at ("concept for client review", "press-ready concept") rather than implying it shipped.

## 3. The written project text (Behance description, client email, awards form)
Short, specific, in the brand's voice; no paragraph appears on a panel (`SKILL.md` rule 3). Fill this, then cut by a third:
1. **Title:** brand + what it is, plain ("BAGH: a dried-fruit pack system").
2. **One line:** the idea in under 15 words.
3. **The brief / tension (2 sentences):** what was asked, what made it hard.
4. **The insight (1-2 sentences):** the one finding the design rests on, with its evidence.
5. **The idea and system (3 sentences):** what the design does, and the rules that make it a family.
6. **The craft (2 sentences):** the specific thing done properly (measured dielines, ink plates, a film).
7. **Status and honesty (1 sentence):** concept / client review / in production; stand-in name if it is one; AI disclosure if any plate is generated.
8. **Credits:** client (only with permission), studio, roles. Credit once.
Then the fields:
- **Creative fields:** up to 3, the closest ones (for packs: Packaging, Branding, Graphic Design) [KNOWN: Behance editor; check the live form].
- **Tags:** about 10, specific (product category, structure, material, place, method), never generic praise words.
- **Tools used:** list the real ones (Behance uses tools for its tool galleries) [SRC: Behance curation team].
- **Co-owners and credits:** every collaborator [SRC: Behance curation team].
- **Copyright / licence and visibility:** as the client contract allows.

## 4. Media
- Panels at one width (2880 px source; Behance shows 1400) (`SKILL.md` rule 12). Cover with no text, reads at thumbnail.
- Films: a video-host embed for full width; a direct upload uses the middle frame as its thumbnail, so make mid-film a clean shot (`../../nazar-shoot/references/motion.md`).
- GIFs only inside the project.

## 5. Before publishing (curators review a project once, at first publish [SRC: research.md])
- [ ] Teardown written; the flatplan answers its gap
- [ ] Build passes (no overflow, overlap or device repeat); contact sheet seen by the owner
- [ ] **Measured consistency:** `python ../../nazar-study/engine/look.py set <panels> -o <qa>`: no panel clips highlights on the product (`clip_highlights_pct` near 0 on pack pages), no panel's black point far outside the set's range unless it is the planned dark page
- [ ] Project text filled (title, one line, the seven blocks, fields, tags, tools, credits); stand-in names and AI use disclosed
- [ ] Cover at 202 x 158 still reads
- [ ] Every claim in the text is true today (no implied launch, no invented numbers)
