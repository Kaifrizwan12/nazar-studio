#!/usr/bin/env python3
"""
nazar-social/engine/social_lint.py: the slop test, as code (stdlib only).

Flags the text tells listed in nazar-core/references/ai_tells.md and the kit's own rules:
  stock phrases    elevate, journey, unlock, seamless, leverage, delve, robust, game-changer,
                   "in today's fast-paced", "take your X to the next level", "dive in"
  structure        "not just X, but Y"; triads ("A, B, and C" three times); a rhetorical
                   question opener; em-dash density; exclamation marks; emoji as bullets
  platform         hashtag count, caption length vs a slide's room
  Roman Urdu       English mixed with Roman Urdu is normal copy here, so Roman Urdu words (roman_urdu.py) are never typos;
                   one word spelt two ways in one piece (nahi ... nahin ... nai) is flagged: pick one spelling and keep it.
                   Sources: references/research_roman_urdu.md.
  typo             only a word that is one inserted, dropped or swapped letter away from another word in the same piece
                   (verify ... verfy), 5+ letters, neither a known Roman Urdu word: there is no dictionary, so it cannot
                   find a typo that appears alone.
It judges the TEXT only. A clean lint is not proof a post is good, and a hit isn't proof it's
machine-written (people write "elevate" too): it's a prompt to rewrite, never a verdict.

    python social_lint.py caption.txt            # or - for stdin
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roman_urdu  # noqa: E402

PHRASES = ["elevate", "journey", "unlock", "seamless", "leverage", "delve", "robust", "game-changer", "game changer",
           "in today's fast-paced", "next level", "dive in", "dive into", "tapestry", "ever-evolving", "fast-paced world",
           "it's important to note", "revolutionize", "supercharge"]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def _one_edit(a, b):
    """True if b is a with one letter inserted or dropped, or two neighbours swapped (not a substitution: share/shake are both words)."""
    if a == b:
        return False
    if len(a) == len(b):
        d = [i for i in range(len(a)) if a[i] != b[i]]
        return len(d) == 2 and d[1] == d[0] + 1 and a[d[0]] == b[d[1]] and a[d[1]] == b[d[0]]
    if abs(len(a) - len(b)) != 1:
        return False
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))


def typos(text):
    words = roman_urdu.tokens(text)
    uniq = sorted(set(w for w in words if len(w) >= 5 and not roman_urdu.is_roman_urdu(w)))
    out = []
    for i, a in enumerate(uniq):
        for b in uniq[i + 1:]:
            if _one_edit(a, b):
                rare, common = sorted((a, b), key=lambda w: words.count(w))
                out.append((rare, common))
    return out


def lint(text):
    t = text.lower()
    hits = []
    for p in PHRASES:
        if p in t:
            hits.append(("phrase", f'"{p}"'))
    if re.search(r"\bnot (?:just|only)\b.{1,60}\bbut\b", t):
        hits.append(("structure", '"not just X, but Y"'))
    triads = re.findall(r"\b[\w' -]{2,24}, [\w' -]{2,24},? (?:and|&) [\w' -]{2,24}", t)
    if len(triads) >= 2:
        hits.append(("structure", f"{len(triads)} triads (A, B and C)"))
    first = text.strip().split("\n")[0]
    if first.endswith("?") and len(text.split()) > 30:
        hits.append(("structure", "opens with a rhetorical question"))
    dashes = text.count("—")
    if dashes >= 2:
        hits.append(("structure", f"{dashes} em-dashes"))
    if text.count("!") >= 2:
        hits.append(("tone", f"{text.count('!')} exclamation marks"))
    if len(EMOJI.findall(text)) >= 3:
        hits.append(("tone", f"{len(EMOJI.findall(text))} emoji"))
    tags = len(re.findall(r"#\w+", text))
    if tags > 5:
        hits.append(("platform", f"{tags} hashtags"))
    for head, forms in roman_urdu.inconsistent(text):
        hits.append(("spelling", f"{head} spelt {len(forms)} ways: " + ", ".join(f"{f} ({c})" for f, c in forms.items()) + "; pick one"))
    for rare, common in typos(text):
        hits.append(("typo", f'"{rare}" next to "{common}": a typo?'))
    words = len(text.split())
    return {"words": words, "roman_urdu_share": roman_urdu.share(text), "hits": hits, "verdict": "clean" if not hits else f"{len(hits)} flag{'s' if len(hits) > 1 else ''}"}


if __name__ == "__main__":
    src = sys.stdin.read() if sys.argv[1] == "-" else open(sys.argv[1], encoding="utf-8").read()
    r = lint(src)
    print(json.dumps(r, indent=1, ensure_ascii=False))
