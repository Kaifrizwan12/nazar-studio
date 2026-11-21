# Research: what predicts how good a layout is rated (2026-11-21)

Backs the HABIT score in `engine/score_pattern.py` (`--rank`). Tags: [SRC] read for this note, [KNOWN] background.

## Findings
- **Layout measures from geometry.** Ngo, Teo and Byrne defined fourteen aesthetic measures for screen layouts (balance, equilibrium, symmetry, sequence, unity, proportion and others), each a 0 to 1 number computed from where the objects sit. They tie users' sense of aesthetics to perceived usability. [SRC] "Modelling interface aesthetics", Information Sciences 152 (2003) 25-46, doi 10.1016/S0020-0255(02)00404-8. https://www.academia.edu/11749849/Modelling_interface_aesthetics
- **Screenshot metrics explain part of the ratings, not all.** Miniukovich and De Angeli measured visual clutter, symmetry, contour density, figure-ground contrast and colour variability straight from screenshots. Six metrics explained up to 51% of aesthetics ratings in one study and 36% in a second one (desktop pages and phone apps). Half the variance is left over, so a pixel score can order work roughly but can't replace a look. [SRC] https://iris.unitn.it/handle/11572/101632 ; https://www.academia.edu/11396872/Quantification_of_Interface_Visual_Complexity
- **Human preference data is scarce and expensive.** DesignSense-10k (10,235 human preference pairs for graphic layouts) was built because no large layout-preference set existed. Design-o-meter avoids human ratings because they cost so much. AesthetiQ trains a multimodal model on layout preferences. [SRC] arXiv 2602.23438 ; arXiv 2411.14959 ; arXiv 2503.00591
- **A model as judge, by principle.** PRISM has a vision-language model score designs on named principles (such as coherence) from 0 to 1, so each score comes with a reason. [SRC] arXiv 2606.00592
- **Our own tests.** The gate passed every good slide (it saturates). FIT and TYPICAL could not separate real held-out pieces (0.92) from generated ones (0.89 to 0.95). Blind judges named generated slides by tidy, formulaic sets, invented devices and invented layouts. [SRC] `../LESSONS.md`, `../../docs/CASE_STUDY.md`
- **AI tells as a cluster:** gradients and glows with no reason, everything centred, a centred hero over three rounded cards, pill badges above headlines, stock copy. [SRC] `../../nazar-core/references/ai_tells.md` and its sources

## What we took from it
1. Rank against the designer's own habits (their devices, their alignment, their lines per piece), not general beauty. Reasons: the research shows general metrics explain at most about half of ratings, and our blind tests failed generated work for breaking the archive's habits, not for low "beauty".
2. Penalise AI tells only when the designer's own archive doesn't carry them. A brand whose real backdrops have a gradient isn't penalised for that gradient (lesson 2026-11-16, gradients rule vs brand practice).
3. Every score comes with its reasons (`why`), as PRISM does, so a person can disagree with a line instead of a number.
4. Weights (0.30 gate, 0.20 typical/fit, 0.25 devices, 0.25 range, minus 0.12 per tell) are a first guess, tuned only on synthetic fixtures (`engine/test_habit_rank.py`). They need fitting to real picks: run `pick_test.py` with the designer, then check whether HABIT orders the pieces the way they do.

## Open
- Add balance and symmetry measures (Ngo) as range habits, measured from the archive and not as fixed ideals.
- Fit the weights to a real designer's picks, and report rank agreement (Kendall tau) next to the score.
