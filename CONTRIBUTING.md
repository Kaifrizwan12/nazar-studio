# Contributing

Thanks for helping. The skill gets better from real work, so the most useful contributions are honest reports.

## Report what failed on a real job
Open an issue with the **Kit lesson** template: the kit, what happened, the evidence (a measurement, a check's output, a screenshot with private
details removed) and the change you propose. This is the same format as each kit's `LESSONS.md`.

## Change an engine
1. Keep it plain Python (numpy, Pillow; nothing heavier without a reason).
2. Add a known-answer test: a case where the right answer is known, run before you trust the engine.
3. Run `python3 nazar-core/engine/selftest.py` and `python3 nazar-core/engine/test_draw.py /tmp/sheet.png`; both must pass.
4. Describe what the engine measures and what it cannot, in its docstring and the kit's `SKILL.md`.

## Rules that never bend
No client names, faces or private files in the repo without the owner's written okay. A client's logo is never redrawn or recoloured. AI imagery
only with the client's written yes. Results are reported as they are, including the ones that don't flatter the skill.
