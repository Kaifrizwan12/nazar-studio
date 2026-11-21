# Research: Roman Urdu spelling variation (2026-11-21)

Backs `engine/roman_urdu.py` and the Roman Urdu checks in `engine/social_lint.py`. Tags: [SRC] read for this note, [KNOWN] background.

## Findings
- **No standard spelling, many forms per word.** Khan, Karim, Sajjad, Kamiran and Xu show one Urdu word written as zindagi, zindagee, zindagy, zaindagee and zndagi. Roman Urdu has no standard lexicon and no labelled corpus, so they cluster variants rather than look them up. Their gold standard maps about 61,000 variants to 22,700 words; corpora are SMS (159k and 1.99M messages), a web forum (183k) and web text. [SRC] "A Clustering Framework for Lexical Normalization of Roman Urdu", Natural Language Engineering 28 (2022) 93-123, arXiv 2004.00088. https://arxiv.org/abs/2004.00088
- **Where variants come from.** They come from vowels doubled or dropped (ee / i, aa / a), from the "h" of an aspirate being dropped (samajh / samaj), from letters that sound alike (q / k, z / x, w / v, s / sh / c) and from a final nasal "n" that comes and goes (nahin / nahi). The UrduPhone encoding groups these sounds so variants share a key. [SRC] same paper, UrduPhone rules (Table 2)
- **Earlier unsupervised work:** "An Unsupervised Method for Discovering Lexical Variations in Roman Urdu Informal Text", EMNLP 2015. [SRC] https://aclanthology.org/D15-1097
- **Real rates of Hindustani function words** (OpenSubtitles2018 via FrequencyWords, CC-BY-SA-4.0) already sit in `nazar-voiceprint/engine/baselines/hi_ur_function_words.json`, with Roman spellings such as nahin / nahi / nhi. [SRC] that file

## What we took from it
1. **No spell-check against English.** A Roman Urdu word is not misspelt English, so the lint never calls one a typo. The only typo check compares words inside the same piece (verify ... verfy), because there is no dictionary to compare against.
2. **Hand-checked variant groups, not a phonetic key.** A key like UrduPhone merges words that differ in meaning: drop the final nasal and hai ("is") meets hain ("are"); main ("I") meets mein ("in"). For a lint, a false "inconsistent spelling" flag on two different words is worse than a miss, so `roman_urdu.py` keeps narrow groups built from the variant patterns above, and leaves ambiguous forms (kia = kya or kiya) out.
3. **Forms that are also English** (to, he, me, or, ham, bad, sub, do, main, par, log...) don't count as Roman Urdu on their own. A form like "to" counts only beside the clear Roman Urdu form of the same word ("toh").
4. **Consistency in one piece is the rule:** pick one spelling (nahi or nahin) and keep it through the piece. Which one is the brand's call; the archive's own spelling wins (`nazar-voiceprint` voice layer).

## Open
- Grow the groups from real brand copy, adding a spelling only when it has been seen.
- A set-level check (one spelling across a whole carousel) is the next step.
