#!/usr/bin/env python3
"""Render assets/demo-colour.jpg: a palette taken from real archive photographs
(The Met Open Access, CC0) and checked by palette_check.py. All numbers and
verdicts are computed live.

    python make_colour_card.py images_folder out.jpg [--k 5]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import palette_check as pc  # noqa: E402

F = os.path.join(HERE, "..", "..", "nazar-core", "engine", "fonts") + "/"
PAPER, INK, GREY, RULE, ACC = "#F2EEE6", "#1C1B19", "#6E6A64", "#CFC9BF", "#E4572E"
anton = lambda s: ImageFont.truetype(F + "Anton-Regular.ttf", s)
grot = lambda s, w="Regular": ImageFont.truetype(F + f"SpaceGrotesk-{w}.ttf", s)
mono = lambda s: ImageFont.truetype(F + "SpaceMono-Regular.ttf", s)

folder, out = sys.argv[1], sys.argv[2]
k = int(sys.argv[sys.argv.index("--k") + 1]) if "--k" in sys.argv else 5
r = pc.run(folder, k)
pal, pairs = r["palette"], r["pairs"]
files = sorted(f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in pc.EXTS)

W, M = 2400, 110
H = 1660
im = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(im)
d.text((M, 80), "A PALETTE FROM REAL ARCHIVE WORK, THEN CHECKED", font=anton(84), fill=INK)
d.text((M, 190), f"{r['n_images']} public-domain cyanotypes (The Met, CC0)  ·  OKLab k-means  ·  WCAG 2 contrast  ·  colour-blind simulation (Machado 2009)", font=grot(26), fill=GREY)

# source strip
d.line([(M, 250), (W - M, 250)], fill=RULE, width=2)
d.text((M, 275), "01  SOURCE", font=mono(26), fill=INK)
x = M
for f in files[:10]:
    t = Image.open(os.path.join(folder, f)).convert("RGB"); t.thumbnail((150, 190))
    im.paste(t, (x, 325)); x += t.width + 14

# palette
y = 570
d.line([(M, y), (W - M, y)], fill=RULE, width=2)
d.text((M, y + 25), "02  PALETTE, BY SHARE", font=mono(26), fill=INK)
x, total = M, W - 2 * M
raw = [max(230, total * p["share"]) for p in pal]
scale = total / sum(raw)
for p, w0 in zip(pal, raw):
    w = w0 * scale
    d.rectangle([x, y + 75, x + w - 8, y + 245], fill=p["hex"])
    L, C, Hh = p["oklch"]
    d.text((x, y + 258), p["hex"], font=mono(24), fill=INK)
    d.text((x, y + 290), f"OKLCH {L:.2f} {C:.2f} {Hh}°", font=grot(20), fill=GREY)
    d.text((x, y + 346), f"{p['share']*100:.0f}% of pixels", font=grot(20), fill=GREY)
    d.text((x, y + 318), p["role"], font=grot(20), fill=ACC)
    x += w

# pairs that pass, with real sample text
y = 985
d.line([(M, y), (W - M, y)], fill=RULE, width=2)
d.text((M, y + 25), "03  WHICH PAIRS CAN CARRY TEXT?", font=mono(26), fill=INK)
d.text((M, y + 66), "foreground on background, ratio computed, verdict applied: 4.5:1 normal text · 3:1 large text and UI", font=grot(22), fill=GREY)
best = sorted(pairs, key=lambda p: -p["contrast"])[:4]
x = M
for p in best:
    a, b = p["a"], p["b"]
    # darker colour as text on the lighter one
    fg, bg = (a, b) if pc.luminance(_ := [int(a[i:i + 2], 16) / 255 for i in (1, 3, 5)]) < pc.luminance([int(b[i:i + 2], 16) / 255 for i in (1, 3, 5)]) else (b, a)
    d.rectangle([x, y + 115, x + 500, y + 300], fill=bg)
    d.text((x + 24, y + 135), "Cyanotype", font=grot(46, "Medium"), fill=fg)
    d.text((x + 24, y + 205), "sun-printed, iron-blue, 1843", font=grot(24), fill=fg)
    d.text((x, y + 312), f"{p['contrast']}:1", font=mono(30), fill=INK)
    verdict = p["wcag"]
    d.text((x + 120, y + 318), verdict, font=grot(22), fill=ACC if verdict == "fails" else INK)
    x += 560

# colour-blind + greyscale
y = 1365
d.line([(M, y), (W - M, y)], fill=RULE, width=2)
d.text((M, y + 25), "04  WHAT BREAKS FOR SOME VIEWERS", font=mono(26), fill=INK)
coll = [p for p in pairs if p["collapses_for"]]
close = [p for p in pairs if p["grey_gap_L"] < 0.08]
lines = [f"{len(pairs)} pairs checked, {sum(1 for p in pairs if p['contrast'] >= 4.5)} pass WCAG AA for text, {sum(1 for p in pairs if 3 <= p['contrast'] < 4.5)} only for large text/UI, {sum(1 for p in pairs if p['contrast'] < 3)} fail"]
lines.append(f"colour-blind simulation: {len(coll)} pairs collapse for a protan, deutan or tritan viewer" + (": " + "; ".join(f"{p['a']} / {p['b']} ({', '.join(c.split(' ')[0] for c in p['collapses_for'])})" for p in coll[:2]) if coll else " (a single-hue palette keeps its lightness steps)"))
lines.append(f"greyscale: {len(close)} {'pair sits' if len(close) == 1 else 'pairs sit'} within 0.08 L of each other, so {'it depends' if len(close) == 1 else 'they depend'} on hue alone to separate")
for i, t in enumerate(lines):
    d.text((M, y + 75 + i * 44), t, font=grot(26), fill=INK)
d.text((M, y + 225), "images: The Met Open Access (CC0)  ·  nazar-colour/engine/palette_check.py  ·  APCA deliberately not used: its WCAG 3 status is unresolved (Apr 2026)", font=mono(18), fill=GREY)
im.save(out, quality=90)
print("saved", out, im.size)
