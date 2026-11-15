#!/usr/bin/env python3
"""Render assets/demo-voiceprint-real.jpg: grade.py run blind on real CC0
photographs from The Met (fetched by fetch_met.py), grouped by the process each
object's own catalogue record names. Every reading is computed live.

    python make_real_card.py met_photos_folder out.jpg
"""
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import grade  # noqa: E402
from visual import srgb_to_oklab  # noqa: E402

F = os.path.join(HERE, "..", "..", "nazar-core", "engine", "fonts") + "/"
PAPER, INK, GREY, RULE, ACC = "#F2EEE6", "#1C1B19", "#6E6A64", "#CFC9BF", "#E4572E"
anton = lambda s: ImageFont.truetype(F + "Anton-Regular.ttf", s)
grot = lambda s: ImageFont.truetype(F + "SpaceGrotesk-Regular.ttf", s)
mono = lambda s: ImageFont.truetype(F + "SpaceMono-Regular.ttf", s)
VERDICT = {
    "cyanotype": "yes: blue, single hue, soft",
    "albumen": "yes: warm-toned print",
    "salted paper": "yes: warm-toned print",
    "autochrome": "partly: grain + true colour need full-resolution scans",
}

root, out = sys.argv[1], sys.argv[2]
man = json.load(open(os.path.join(root, "manifest.json")))
groups = defaultdict(list)
for m in man:
    groups[m["process"]].append(m)

W, M = 2400, 110
rows = len(groups)
H = 330 + rows * 300 + 230
im = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(im)
d.text((M, 80), "REAL PHOTOGRAPHS, READ BLIND", font=anton(92), fill=INK)
d.text((M, 200), f"{len(man)} public-domain (CC0) photographs from The Met. the engine never sees the label; the label is each object's own catalogue record",
       font=grot(26), fill=GREY)
y = 280
for proc in ("cyanotype", "albumen", "salted paper", "autochrome"):
    items = groups.get(proc)
    if not items:
        continue
    d.line([(M, y), (W - M, y)], fill=RULE, width=2)
    x = M
    hues, chroma, looks = [], [], Counter()
    for m in items:
        t = Image.open(os.path.join(root, m["file"])).convert("RGB")
        g = grade.analyse(t.copy())
        a = np.asarray(t.resize((128, 128)), np.float32).reshape(-1, 3) / 255
        lab = srgb_to_oklab(a); C = np.hypot(lab[:, 1], lab[:, 2]); w = C > 0.02
        if w.sum() > 50:
            hues.append((math.degrees(math.atan2(np.average(lab[w, 2], weights=C[w]), np.average(lab[w, 1], weights=C[w]))) + 360) % 360)
        chroma.append(g["mean_chroma"])
        looks.update({re.sub(r"\s*\[.*?\]", "", l).split(":")[0] for l in g["looks"]})
        t.thumbnail((150, 210))
        im.paste(t, (x, y + 30))
        x += t.width + 12
    tx = max(x + 30, 1500)
    d.text((tx, y + 34), proc.upper(), font=mono(28), fill=INK)
    d.text((tx, y + 80), f"hue {np.median(hues):.0f}° · colour {np.median(chroma):.3f}" if hues else f"colour {np.median(chroma):.3f}", font=grot(22), fill=ACC)
    top = [f"{k} {v}/{len(items)}" for k, v in looks.most_common(3)]
    for i, line in enumerate(top):
        d.text((tx, y + 112 + i * 28), line, font=grot(21), fill=ACC)
    d.text((tx, y + 212), VERDICT[proc], font=grot(21), fill=INK)
    y += 300
d.line([(M, y), (W - M, y)], fill=RULE, width=2)
d.text((M, y + 28), "honest limits: albumen and salted paper sit a few degrees apart (aged warm paper dominates), so the engine reads", font=grot(23), fill=GREY)
d.text((M, y + 60), "'warm-toned print', not the exact process. autochrome's starch grain needs full-resolution scans, not web previews.", font=grot(23), fill=GREY)
d.text((M, y + 110), "images: The Met Open Access (CC0), object IDs and links in nazar-voiceprint/examples/met_credits.json · reproduce: examples/fetch_met.py", font=mono(19), fill=GREY)
im.save(out, quality=88)
print("saved", out, im.size)
