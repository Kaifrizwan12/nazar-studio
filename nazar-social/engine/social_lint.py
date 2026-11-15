#!/usr/bin/env python3
"""
nazar-social/engine/social_lint.py: the slop test, as code (stdlib only).

Flags the text tells listed in nazar-core/references/ai_tells.md and the kit's own rules:
  stock phrases    elevate, journey, unlock, seamless, leverage, delve, robust, game-changer,
                   "in today's fast-paced", "take your X to the next level", "dive in"
  structure        "not just X, but Y"; triads ("A, B, and C" three times); a rhetorical
                   question opener; em-dash density; exclamation marks; emoji as bullets
  platform         hashtag count, caption length vs a slide's room
It judges the TEXT only. A clean lint is not proof a post is good, and a hit isn't proof it's
machine-written (people write "elevate" too): it's a prompt to rewrite, never a verdict.

    python social_lint.py caption.txt            # or - for stdin
"""
import json
import re
import sys

PHRASES = ["elevate", "journey", "unlock", "seamless", "leverage", "delve", "robust", "game-changer", "game changer",
           "in today's fast-paced", "next level", "dive in", "dive into", "tapestry", "ever-evolving", "fast-paced world",
           "it's important to note", "revolutionize", "supercharge"]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


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
    words = len(text.split())
    return {"words": words, "hits": hits, "verdict": "clean" if not hits else f"{len(hits)} flag{'s' if len(hits) > 1 else ''}"}


if __name__ == "__main__":
    src = sys.stdin.read() if sys.argv[1] == "-" else open(sys.argv[1]).read()
    r = lint(src)
    print(json.dumps(r, indent=1, ensure_ascii=False))
