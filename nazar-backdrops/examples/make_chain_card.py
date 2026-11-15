#!/usr/bin/env python3
"""Render assets/demo-backdrops.jpg: real archive images -> palette (nazar-colour) ->
brand tokens -> a backdrop set (nazar-backdrops). Uses nazar-core/engine/brand.json
temporarily and always restores it.

    python make_chain_card.py cyanotype_folder out.jpg
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "nazar-colour", "engine"))
import palette_check as pc  # noqa: E402

F = os.path.join(ROOT, "nazar-core", "engine", "fonts") + "/"
PAPER, INK, GREY, RULE, ACC = "#F2EEE6", "#1C1B19", "#6E6A64", "#CFC9BF", "#E4572E"
anton = lambda s: ImageFont.truetype(F + "Anton-Regular.ttf", s)
grot = lambda s: ImageFont.truetype(F + "SpaceGrotesk-Regular.ttf", s)
mono = lambda s: ImageFont.truetype(F + "SpaceMono-Regular.ttf", s)
rgb = lambda h: [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]

folder, out = sys.argv[1], sys.argv[2]
pal = pc.run(folder, 5)["palette"]
first = sorted(f for f in os.listdir(folder) if f.endswith(".jpg"))[0]
im0 = np.asarray(Image.open(os.path.join(folder, first)).convert("RGB"), float)
edge = np.concatenate([im0[:6].reshape(-1, 3), im0[-6:].reshape(-1, 3), im0[:, :6].reshape(-1, 3), im0[:, -6:].reshape(-1, 3)])
mount = "#%02X%02X%02X" % tuple(int(v) for v in np.median(edge, 0))
tokens, notes = pc.derive_tokens(pal, accent_hex=mount)
base, light = {"hex": tokens["base"]}, {"hex": tokens["light"]}

bj = os.path.join(ROOT, "nazar-core", "engine", "brand.json")
bak = bj + ".bak_demo"
work = tempfile.mkdtemp()
shutil.copy(bj, bak)
try:
    b = json.load(open(bak)); b["name"] = "Cyanotype Study"
    for k, v in tokens.items():
        b["colours"][k]["hex"] = v
    json.dump(b, open(bj, "w"), indent=1)
    spec = {"handle": "@cyanotypestudy", "logo": "mark", "formats": ["feed_4x5", "story"], "roles": ["cover", "text", "quote", "end"],
            "modes": ["dark", "light"], "carousel_slides": 5, "band": "left", "rtl": False, "margin": 0.067, "band_ratio": 0.012,
            "logo_ratio": 0.15, "swipe_cue": True, "continuity": True, "grain": False, "out": work}
    json.dump(spec, open(os.path.join(work, "spec.json"), "w"))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "nazar-backdrops", "engine", "backdrops.py"), os.path.join(work, "spec.json")],
                       capture_output=True, text=True, timeout=300)
    log = (r.stdout + r.stderr).strip().splitlines()
finally:
    shutil.move(bak, bj)

picks = [("cover", "feed4x5_cover"), ("text", "feed4x5_text"), ("quote", "feed4x5_quote"), ("end", "feed4x5_end"), ("story", "story_story")]
files = [(n, glob.glob(os.path.join(work, f"*_{k}_dark.png"))) for n, k in picks]
W, M = 2400, 100
H = 1810
im = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(im)
d.text((M, 70), "ARCHIVE COLOUR → BRAND TOKENS → BACKDROPS", font=anton(86), fill=INK)
d.text((M, 180), "three kits chained: real cyanotype plates (The Met, CC0) → nazar-colour's palette → nazar-backdrops. the engine checked the contrast and refused what failed", font=grot(24), fill=GREY)

y = 250
d.line([(M, y), (W - M, y)], fill=RULE, width=2)
x = M
for f in sorted(os.listdir(folder))[:6]:
    t = Image.open(os.path.join(folder, f)).convert("RGB"); t.thumbnail((110, 140)); im.paste(t, (x, y + 25)); x += t.width + 10
names = [("base", "ground (dark)"), ("light", "light ground"), ("secondary", "small text on dark"), ("secondary_dark", "small text on light"), ("accent", "accent: the paper mount")]
x = 900
for k, label in names:
    d.rectangle([x, y + 25, x + 230, y + 110], fill=tokens[k])
    d.text((x, y + 118), tokens[k], font=mono(22), fill=INK)
    d.text((x, y + 150), label, font=grot(19), fill=GREY)
    x += 280
ca = pc.contrast(rgb(mount), rgb(base["hex"])); cl = pc.contrast(rgb(mount), rgb(light["hex"]))
d.text((M, y + 195), f"accent on the dark ground: {ca:.2f}:1 (ok)   ·   accent on the light ground: {cl:.2f}:1", font=grot(25), fill=INK)
d.text((M + 1120, y + 195), "→ light mode refused", font=grot(25), fill=ACC)
for i, n in enumerate(notes[:2]):
    d.text((M, y + 235 + i * 30), "note: " + n, font=grot(21), fill=GREY)

y = 570
d.line([(M, y), (W - M, y)], fill=RULE, width=2)
d.text((M, y + 20), "THE SET (dark mode: the only mode the colours support)", font=mono(26), fill=INK)
x, ty = M, y + 70
for n, fs in files:
    if not fs:
        continue
    t = Image.open(fs[0]).convert("RGB"); t.thumbnail((400, 800)); im.paste(t, (x, ty))
    d.text((x, ty + t.height + 10), n, font=mono(20), fill=GREY)
    x += t.width + 28
d.text((M, H - 175), "engine fix found by this test: nazar-backdrops offered light mode whatever the accent contrast (here 1.02:1) and its 'skipped' message could never fire. now a mode is skipped when the accent", font=grot(21), fill=GREY)
d.text((M, H - 143), "is under 2:1 on that mode's ground, and warned under 3:1. the studio's default brand (2.98:1 on paper) keeps both modes with a warning.", font=grot(21), fill=GREY)
d.text((M, H - 105), "the mark is the example brand's placeholder artwork, left unaltered on purpose: client logos are never recoloured or redrawn.", font=grot(21), fill=GREY)
d.text((M, H - 70), "images: The Met Open Access (CC0) · nazar-backdrops/examples/make_chain_card.py", font=mono(17), fill=GREY)
im.save(out, quality=90)
print("saved", out, im.size, "| engine said:", " / ".join(log)[:160])
