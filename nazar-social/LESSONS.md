# Lessons from real work (nazar-social)
Format: date, what happened, evidence, change made. Generic on purpose: no client names or private data.

- 2026-11-21 · Copy lint was English-only · Roman Urdu and mixed lines went unchecked, and any spelling check would have called them typos. · New `engine/roman_urdu.py` (hand-checked variant groups, `references/research_roman_urdu.md`): Roman Urdu is never a typo, one word spelt two ways in a piece (nahi / nahin / nai) is flagged, generic-copy flags kept; tests in `engine/test_social_lint.py`.
