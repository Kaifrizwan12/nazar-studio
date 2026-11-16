#!/usr/bin/env python3
"""
nazar-core/engine/studio.py: the fast path. Two commands cover a brand-asset job (social slides, posts, banners).

  learn   measure a folder of the person's finished pieces and write the pattern:
              python studio.py learn train_folder out_folder [exact_asset_files...]
          writes out_folder/pattern.json and out_folder/prompt.md, and prints: the measured habits
          (format, grounds, palette, accent, layout), the held-in score, and the prompt block to work from.
  check   check finished slides against the pattern, in one pass:
              python studio.py check slides_folder copy.json pattern.json [sheet.jpg]
          prints per slide: pattern score, contrast of text and accent type on their own ground (with a darker
          suggestion for NEW type only), language, copy lint, and the QA measurements (edges, margins, gaps,
          small text); writes the QA sheet (full size, squint, phone size). Then look at the sheet.
It runs the engines in nazar-voiceprint, nazar-core and nazar-colour; it adds no judgement of its own.
One call each replaces about ten, so a job reads less and calls less. Everything else (concept, copy, the font
question via nazar-type/engine/font_match.py) is still yours.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PY = sys.executable
run = lambda args: subprocess.run([PY, *args], capture_output=True, text=True)


def learn(train, out, assets):
    os.makedirs(out, exist_ok=True)
    pj = os.path.join(out, "pattern.json")
    print(run([f"{ROOT}/nazar-voiceprint/engine/portfolio.py", train]).stdout.strip())
    r = run([f"{ROOT}/nazar-voiceprint/engine/score_pattern.py", "--build", train, pj, *assets])
    if r.returncode:
        sys.exit(r.stderr)
    print("\nHeld-in score:", run([f"{ROOT}/nazar-voiceprint/engine/score_pattern.py", pj, train]).stdout.strip())
    block = run([f"{ROOT}/nazar-voiceprint/engine/score_pattern.py", "--prompt", pj]).stdout.strip()
    open(os.path.join(out, "prompt.md"), "w").write(block + "\n")
    print("\nPrompt block (also in prompt.md):\n" + block)
    print(f"\npattern.json: {pj}")


def check(slides, copy, pattern, sheet):
    print(run([f"{ROOT}/nazar-core/engine/chain_check.py", slides, copy, pattern]).stdout.strip())
    print("\nQA measurements:")
    r = run([f"{ROOT}/nazar-core/engine/qa_views.py", slides, sheet])
    print(r.stdout.strip() or r.stderr.strip())


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if a[0] == "learn" and len(a) >= 3:
        learn(os.path.abspath(a[1]), os.path.abspath(a[2]), [os.path.abspath(x) for x in a[3:]])
    elif a[0] == "check" and len(a) >= 4:
        sheet = os.path.abspath(a[4]) if len(a) > 4 else os.path.join(os.path.abspath(a[1]), "qa_sheet.jpg")
        check(os.path.abspath(a[1]), os.path.abspath(a[2]), os.path.abspath(a[3]), sheet)
    else:
        sys.exit(__doc__)
