# Spawning the researcher

Never write the researcher's prompt by hand: a hand-written angle list narrows the scope (real case: the kit profiles were replaced, and the dataset came back without the category's real products). Generate it:

```
python .claude/skills/nazar-research/engine/dataset.py spawn <research_dir> "<brief one paragraph>" \
    --kit packaging,logo,shoot,... --deliverables <research_dir>/deliverables.txt --formats "<format>; <format>"
```

It carries: the kit profiles as the floor; every product format with a minimum; every deliverable with every world it touches; the owner's references (`dataset/owner_refs/README.md`); write-as-you-go; `progress.md` after every round; the balance rules (≤25% one brand per kind, ≥3 sites per kind, largest rendition); stop reasons per kind; the finish line `dataset.py report --strict` (or every remaining key written in gaps.md).

Mid-run: read `progress.md` instead of asking. If the owner changes scope, send ONE consolidated instruction that replaces the earlier ones.
