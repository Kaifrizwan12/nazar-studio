# Teaching an AI someone else's voice (and making it drop its own)

Confidence tags: [V] checked at the source, [P] practitioner evidence (anecdotal, not studied), [UNVERIFIED].

## 1. The ceiling, stated first
- **"Catch Me If You Can? Not Yet" (arXiv 2509.14543, 2025)** [V]. Advanced prompting and personalised fine-tuning both improve alignment with an author's style, and both still fall short in real-world use.
- **A 2026 preprint (arXiv 2604.26460, venue unverified)** found that four inference-time personalisation methods *all* failed to produce text stylistically faithful to target authors on the Blog Authorship Corpus.
- **So:** promise a close, inspectable approximation that the person corrects. Never promise a clone.

## 2. Separate extraction from generation
- **STRAP (Krishna, Wieting & Iyyer, EMNLP 2020, DOI 10.18653/v1/2020.emnlp-main.55)** [V]. First paraphrase to a neutral form, then re-stylise with a style-specific "inverse paraphraser". This beat direct transfer because separating content from form stops the model confusing *what's said* with *how it's said*.
- **Applied here:** don't ask a model to "write like X" in one step. Give it the confirmed profile, let it plan the content, generate, then check the draft against the profile.
- **LLM-era follow-ups:**
  - Liu, Diddee & Ippolito (2024) customise an LLM's idiolect per user with LoRA fine-tuning.
  - Shao et al. (2024) augment data with neutral↔styled pairs, which beats in-context prompting when examples of a rare style are scarce.

## 3. Rules and examples together
- Anthropic's prompting docs treat examples (multishot prompting) as one of the most reliable levers for tone, format and structure. Read docs.anthropic.com directly for current guidance on how many examples to use and where to put them; secondary sources disagree (1–3 vs. 2–8).
- No study compares stated rules against shown examples head to head. Shao et al. is the closest evidence: for distinctive styles, augmented examples beat scarce in-context demos.
- **Hence the profile carries both:** stated features in plain language, *and* 3–5 real quoted passages [inference, not a tested finding].

## 4. The AI's own fingerprint (what to suppress)
- **Juzek & Ward (COLING 2025)** [V]: 21 "focal words" that GPT-3.5 overuses in scientific writing (e.g. *delve*). They test an RLHF-causation hypothesis but don't confirm it.
- **Yakura et al. (arXiv 2409.01754)** [V]: *delve, comprehend, boast, swift, meticulous* spiked in human usage after ChatGPT. A follow-up found about 75% of AI-associated words rose in 22.1M words of *spoken* conversation after 2022. The contamination runs both ways.
- **Cadence:** human writing varies sentence rhythm more than an AI's default even cadence. GPTZero's perplexity/burstiness framing is a useful mental model, but GPTZero itself moved to a deep-learning classifier in late 2023, so don't present it as how current detectors work.
- **Caveat researchers raise:** word frequency alone can't prove AI authorship. It also false-flags non-native English writers, who already lean on common vocabulary.
- So **build the suppression list from the person's own contrasts first**, and use a generic AI-tell list only as a backup.

## 5. Suppression that actually holds
These are mostly practitioner reports, not rigorous studies [P]:
- A prompt-only banned-word list cut flagged words from 11 occurrences to 1 across five outputs, but 2 of the 5 outputs lost or changed information. **Negative constraints work, and they risk meaning drift.**
- **Pair every "don't" with a "do instead".** Models given only prohibitions reportedly break them under generation pressure.
- **Verify in code after generation.** Claude's API has no logit_bias for hard token-level bans, and practitioners report models using banned words despite instructions.
- **Two passes, two calls:** draft, then a separate check-and-revise pass against the profile.

## 6. Drift over long documents
- Persona fidelity measurably degrades over long sessions (100+ turns) and reverts toward the model's default. It gets worse under task pressure (arXiv 2512.12775) [V].
- ContextEcho (arXiv 2605.24279, May 2026) finds the same drift in long agentic sessions and mitigates it by **periodically re-asserting the persona** [V].
- **Warning:** naive context summarisation can bake already-drifted style in as the new baseline.
- **Applied here:** the profile tells the model to re-read itself every section or two on long pieces, and to re-anchor on the original exemplars rather than on its own earlier output.

## Synthesis: what the skill does
1. Extract, then generate, then check, as three separate steps.
2. Stated features *and* real quoted exemplars.
3. A suppression list from the person's own "never" list first, generic AI tells second.
4. A positive alternative for every prohibition.
5. Two-pass generation (draft → check against the profile → revise).
6. Periodic re-assertion on long documents, anchored to the original exemplars.
7. Honest framing: an approximation the person corrects.

## Sources
github.com/martiansideofthemoon/style-transfer-paraphrase · arXiv 2509.14543 · arXiv 2604.26460 · Liu, Diddee & Ippolito 2024 · Shao et al. 2024 · docs.anthropic.com (prompt engineering: multishot) · Juzek & Ward, COLING 2025 · arXiv 2409.01754 · gptzero.me support docs · arXiv 2512.12775 · arXiv 2605.24279
