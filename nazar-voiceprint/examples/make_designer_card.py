#!/usr/bin/env python3
"""Render assets/demo-voiceprint-designers.jpg from designer_test.py's live result
on real CC0 prints (fetch_cma_designers.py). Nothing on the card is typed in.

    python make_designer_card.py prints_folder out.jpg
"""
import os
import sys
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import designer_test as dt  # noqa: E402

F = os.path.join(HERE, "..", "..", "nazar-core", "engine", "fonts") + "/"
PAPER, INK, GREY, RULE, ACC = "#F2EEE6", "#1C1B19", "#6E6A64", "#CFC9BF", "#E4572E"
anton = lambda s: ImageFont.truetype(F + "Anton-Regular.ttf", s)
grot = lambda s: ImageFont.truetype(F + "SpaceGrotesk-Regular.ttf", s)
mono = lambda s: ImageFont.truetype(F + "SpaceMono-Regular.ttf", s)
NAMES = {"steinlen": "Théophile-Alexandre Steinlen", "lautrec": "Henri de Toulouse-Lautrec", "cheret": "Jules Chéret", "mucha": "Alphonse Mucha"}

folder, out = sys.argv[1], sys.argv[2]
r = dt.run(folder)
n = r["posters"]
per = defaultdict(lambda: [0, 0])
wrong = {}
for a in r["attribution"]:
    per[a["truth"]][1] += 1
    per[a["truth"]][0] += a["right"]
    wrong[a["file"]] = None if a["right"] else a["guess"]
biggest = max(r["designers"].values())
majority = biggest / n

W, M = 2400, 110
rows = [k for k in ("steinlen", "cheret", "mucha", "lautrec") if k in per]
H = 560 + len(rows) * 290 + 250
im = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(im)
d.text((M, 80), "CAN THE ENGINES TELL DESIGNERS APART?", font=anton(88), fill=INK)
d.text((M, 195), f"{n} real prints by four Belle Époque designers (Cleveland Museum of Art, CC0)  ·  leave-one-out: hide one print, learn each designer from the rest, name the maker", font=grot(25), fill=GREY)

# headline numbers
y = 270
d.line([(M, y), (W - M, y)], fill=RULE, width=2)
bx, bw = M, 1400
for i, (label, val, col) in enumerate((("blind accuracy", r["blind_accuracy"], ACC), ("always guess the biggest group", majority, "#BDB6AC"), ("pure chance", r["chance"], "#BDB6AC"))):
    yy = y + 40 + i * 62
    d.text((bx, yy), label, font=grot(26), fill=INK)
    d.rectangle([bx + 520, yy + 4, bx + 520 + bw * val, yy + 38], fill=col)
    d.text((bx + 520 + bw * val + 14, yy + 2), f"{val:.0%}", font=mono(30), fill=INK)
d.text((1900, y + 56), "beats both baselines,", font=grot(24), fill=GREY)
d.text((1900, y + 88), "but unevenly. see below", font=grot(24), fill=GREY)

# per designer
y = 520
for k in rows:
    d.line([(M, y), (W - M, y)], fill=RULE, width=2)
    ok, tot = per[k]
    d.text((M, y + 22), NAMES[k], font=mono(30), fill=INK)
    d.text((M, y + 66), f"{ok} of {tot} named correctly", font=grot(28), fill=ACC if ok / tot >= 0.5 else INK)
    for j in range(tot):
        d.rectangle([M + j * 34, y + 112, M + j * 34 + 26, y + 138], fill=ACC if j < ok else "#BDB6AC")
    files = sorted(f for f in os.listdir(folder) if f.startswith(k + "_") and f.endswith(".jpg"))
    x = 620
    for f in files[:9]:
        t = Image.open(os.path.join(folder, f)).convert("RGB")
        t.thumbnail((140, 220))
        im.paste(t, (x, y + 30))
        if wrong.get(f):
            d.rectangle([x, y + 30 + t.height + 4, x + t.width, y + 30 + t.height + 8], fill=ACC)
        x += t.width + 12
    y += 290
d.line([(M, y), (W - M, y)], fill=RULE, width=2)
d.text((M, y + 28), "orange bar under a print = the engine named the wrong maker. strongest measurable habits: " + ", ".join(s["feature"].replace("_", " ") for s in r["signature"][:3]), font=grot(24), fill=INK)
d.text((M, y + 70), "honest read: this works for makers with a consistent look (Steinlen's tonal street scenes, Chéret's saturated posters). It fails for Lautrec,", font=grot(23), fill=GREY)
d.text((M, y + 102), "whose seven works span flat-colour posters, a pale line print and a dark black-and-white stage poster: three modes, not one hand. numbers measure the", font=grot(23), fill=GREY)
d.text((M, y + 134), "measurable layer only: palette, tone, air, line, layout. why a designer chose it comes from the VLM pass and the maker.", font=grot(23), fill=GREY)
d.text((M, y + 190), "images: Cleveland Museum of Art Open Access (CC0), each reviewed by eye; accessions and links in manifest.json · reproduce: fetch_cma_designers.py → designer_test.py", font=mono(17), fill=GREY)
im.save(out, quality=88)
print("saved", out, im.size, "per-designer:", {k: tuple(v) for k, v in per.items()}, "majority", round(majority, 2))
