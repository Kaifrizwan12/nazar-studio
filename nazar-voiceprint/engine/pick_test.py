#!/usr/bin/env python3
"""
nazar-voiceprint/engine/pick_test.py: the human pick test. Can the maker tell their own pieces from the AI's?

A habit score measures habits, not quality, and good runs all score about the same. The test that ranks good work is a
person who knows the brand picking real from generated, blind. This builds that test and scores it.

    python pick_test.py build real_folder generated_folder out_folder [--n 12] [--seed 7]
        Mixes n pieces (half real, half generated, drawn at random) into numbered quiz sheets in out_folder.
        The answer key is saved as out_folder/KEY_do_not_open.json: the person taking the test must not open it.
    python pick_test.py score out_folder answers.json
        answers.json: {"A1": "real", "A2": "generated", ...}, and optionally {"best": ["A3", "A7"]} for the slides they would post.
        Prints their accuracy, the generated pieces they took for real (the AI that passed), and the real ones they doubted.

Reading it: accuracy near 50% means they can't tell, which is the goal. Near 100% means the generated pieces still show.
With few pieces the result is rough; say so when you report it. Pieces with people in them are the maker's call to include.
"""
import json
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

EXTS = (".png", ".jpg", ".jpeg", ".webp")


def pick(folder, n, rng):
    fs = sorted(f for f in os.listdir(folder) if f.lower().endswith(EXTS))
    rng.shuffle(fs)
    return [os.path.join(folder, f) for f in fs[:n]]


def build(real, gen, out, n=12, seed=7):
    rng = random.Random(seed)
    half = n // 2
    items = [("real", p) for p in pick(real, half, rng)] + [("generated", p) for p in pick(gen, n - half, rng)]
    rng.shuffle(items)
    os.makedirs(out, exist_ok=True)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40, index=1)
    except OSError:
        font = ImageFont.load_default()
    key, tiles = {}, []
    for i, (kind, path) in enumerate(items, 1):
        bid = f"A{i}"
        key[bid] = {"truth": kind, "file": path}
        im = Image.open(path).convert("RGB"); im.thumbnail((430, 540))
        tile = Image.new("RGB", (450, 600), "white"); tile.paste(im, (10, 50))
        ImageDraw.Draw(tile).text((12, 4), bid, font=font, fill=(0, 0, 0))
        tiles.append(tile)
    for s in range(0, len(tiles), 6):
        sheet = Image.new("RGB", (1350, 1200), "white")
        for j, t in enumerate(tiles[s:s + 6]):
            sheet.paste(t, ((j % 3) * 450, (j // 3) * 600))
        sheet.save(os.path.join(out, f"quiz_{s // 6 + 1}.jpg"), quality=88)
    json.dump(key, open(os.path.join(out, "KEY_do_not_open.json"), "w"), indent=1)
    json.dump({k: "real or generated" for k in key} | {"best": []}, open(os.path.join(out, "answers_template.json"), "w"), indent=1)
    print(f"{len(items)} pieces in {len(tiles) // 6 + (1 if len(tiles) % 6 else 0)} sheet(s) in {out}. Open quiz_*.jpg, fill answers_template.json, then score it.")


def score(out, answers_path):
    key = json.load(open(os.path.join(out, "KEY_do_not_open.json")))
    ans = json.load(open(answers_path))
    rows = [(k, v["truth"], ans.get(k)) for k, v in key.items() if ans.get(k) in ("real", "generated")]
    if not rows:
        sys.exit("no answers found: use 'real' or 'generated' for each id")
    right = sum(1 for _, t, a in rows if t == a)
    fooled = [k for k, t, a in rows if t == "generated" and a == "real"]
    doubted = [k for k, t, a in rows if t == "real" and a == "generated"]
    print(f"accuracy {right}/{len(rows)} = {right / len(rows):.0%}   (50% means they cannot tell)")
    print(f"generated pieces taken for real: {len(fooled)} {fooled}")
    print(f"real pieces taken for generated: {len(doubted)} {doubted}")
    best = ans.get("best") or []
    if best:
        hit = [b for b in best if key.get(b, {}).get("truth") == "generated"]
        print(f"of the {len(best)} they would post, {len(hit)} are generated: {hit}")
    for k in fooled:
        print(f"  passed as real: {k} -> {key[k]['file']}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if a[0] == "build" and len(a) >= 4:
        n = int(a[a.index("--n") + 1]) if "--n" in a else 12
        seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 7
        build(a[1], a[2], a[3], n, seed)
    elif a[0] == "score" and len(a) >= 3:
        score(a[1], a[2])
    else:
        sys.exit(__doc__)
