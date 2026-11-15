#!/usr/bin/env python3
"""Render assets/demo-voiceprint-genres.jpg. Every reading on the card is
computed live by the engines from the inputs make_genre_demos.py and
make_grade_demo.py generate; nothing on it is typed in by hand.

    python make_genre_card.py demos_folder out.jpg
"""
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import cluster, exif_habits, grade, layout, pose, strokes, video  # noqa: E402

F = os.path.join(HERE, "..", "..", "nazar-core", "engine", "fonts") + "/"
PAPER, INK, GREY, RULE, ACC = "#F2EEE6", "#1C1B19", "#6E6A64", "#CFC9BF", "#E4572E"
anton = lambda s: ImageFont.truetype(F + "Anton-Regular.ttf", s)
grot = lambda s, w="Regular": ImageFont.truetype(F + f"SpaceGrotesk-{w}.ttf", s)
mono = lambda s: ImageFont.truetype(F + "SpaceMono-Regular.ttf", s)
short = lambda s: re.sub(r"\s*\[[^\]]*\]", "", s).split(":")[0]

root, out = sys.argv[1], sys.argv[2]
W, H, M = 2400, 3400, 110
im = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(im)


def thumb(path, box):
    t = Image.open(path).convert("RGB")
    t.thumbnail(box)
    return t


def section(y, num, title, sub):
    d.line([(M, y), (W - M, y)], fill=RULE, width=2)
    d.text((M, y + 30), f"{num}  {title}", font=mono(28), fill=INK)
    d.text((M, y + 72), sub, font=grot(24), fill=GREY)
    return y + 130


def lines(x, y, items, size=22, col=INK, gap=30, width=None):
    for t in items:
        d.text((x, y), t, font=grot(size), fill=col)
        y += gap
    return y


d.text((M, 80), "ONE ENGINE PER CREATIVE TRADE", font=anton(96), fill=INK)
d.text((M, 205), "each tested blind on original work built with a KNOWN style. orange = what the engine concluded, untouched", font=grot(28), fill=GREY)

# 1 colourist / photographer
y = section(280, "01", "COLOURIST / PHOTOGRAPHER  ·  grade.py", "six grades of one original scene. it has to name each look without being told")
gdir = f"{root}/grade"
gfiles = sorted(os.listdir(gdir))
tw = (W - 2 * M - 5 * 24) // 6
for i, f in enumerate(gfiles):
    x = M + i * (tw + 24)
    t = thumb(f"{gdir}/{f}", (tw, 400)); im.paste(t, (x, y))
    built = f[2:-4].replace("_", " ")
    d.text((x, y + t.height + 14), "built: " + built, font=mono(18), fill=GREY)
    looks = [short(l) for l in grade.analyse(Image.open(f"{gdir}/{f}"))["looks"]] or ["neutral"]
    lines(x, y + t.height + 44, looks[:3], size=20, col=ACC, gap=26)
y += 400

# 2 illustrator
y = section(y, "02", "ILLUSTRATOR  ·  strokes.py", "skeleton → strokes → length, taper, pressure, loose ends. three hands, three tools")
sdir = f"{root}/strokes"
tw = 300
for i, (f, built) in enumerate(zip(sorted(os.listdir(sdir)), ["6 tapered brush strokes", "220 short loose marks", "a ruled technical grid"])):
    x = M + i * 730
    t = thumb(f"{sdir}/{f}", (tw, tw)); im.paste(t, (x, y))
    d.text((x + tw + 24, y), "built: " + built, font=mono(18), fill=GREY)
    r = strokes.analyse(Image.open(f"{sdir}/{f}"))
    lines(x + tw + 24, y + 34, [f"{r['segments']} strokes, taper {r['taper']}"] + [s.split(":")[0].split(" (")[0] for s in strokes.reading(r)[:2]],
          size=20, col=ACC, gap=28)
y += 340

# 3 graphic designer
y = section(y, "03", "GRAPHIC DESIGNER  ·  layout.py", "OCR-free: alignment, columns, margins, type scale")
ldir = f"{root}/layout"
for i, (f, built) in enumerate(zip(sorted(os.listdir(ldir)), ["left · 3 columns · type ×1.5", "centred · type ×1.25"])):
    x = M + i * 1100
    t = thumb(f"{ldir}/{f}", (260, 350)); im.paste(t, (x, y)); d.rectangle([x, y, x + t.width, y + t.height], outline=RULE, width=2)
    r = layout.analyse(Image.open(f"{ldir}/{f}"))
    d.text((x + t.width + 30, y), "built: " + built, font=mono(20), fill=GREY)
    read = [f"{r['dominant_alignment']} · {r['columns'] if r['columns'] >= 2 else 'no'} columns",
            f"type ×{r['type_scale']['median_step']} ({r['type_scale']['nearest_named'].split(' ')[0]} {r['type_scale']['nearest_named'].split(' ')[1]})",
            f"{r['alignment_consistency']:.0%} of elements share an edge"]
    lines(x + t.width + 30, y + 40, read, size=24, col=ACC, gap=36)
y += 380

# 4 editor
y = section(y, "04", "EDITOR / DIRECTOR  ·  video.py", "a cut with 11 known shot lengths. grey = what was cut, orange = what was detected")
fps, n, det, mids = video.detect(f"{root}/video/edit.mp4")
true = [3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8, 0.6, 6.0, 9.0, 7.5]
span = W - 2 * M
for row, (vals, col) in enumerate(((true, "#BDB6AC"), (det, ACC))):
    x = M
    for v in vals:
        wpx = span * v / sum(true)
        d.rectangle([x, y + row * 60, x + wpx - 4, y + row * 60 + 44], fill=col)
        d.text((x + 6, y + row * 60 + 10), f"{v:.1f}", font=mono(18), fill=INK if row == 0 else PAPER)
        x += wpx
rr = video.rhythm(det)
d.text((M, y + 130), f"median shot {rr['median_s']} s · mean {rr['mean_ASL_s']} s · " + " · ".join(video.reading(rr)[:2]), font=grot(24), fill=INK)
y += 190

# 5 portfolio modes + reuse
y = section(y, "05", "WHOLE PORTFOLIO  ·  cluster.py", "10 pieces, two hidden modes, one original mark reused on 6 of them")
res = cluster.run(f"{root}/cluster")
x = M
for md in res["style_modes"]["modes"]:
    for p in md["pieces"][:6]:
        t = thumb(f"{root}/cluster/{p}", (120, 120)); im.paste(t, (x, y)); x += 130
    d.text((x - 130 * min(6, len(md['pieces'])), y + 132), f"mode {md['mode']}: " + ", ".join(md["sets_it_apart"]), font=grot(20), fill=ACC)
    x += 60
rec = res["recurring_elements"][0]
d.text((M, y + 180), f"recurring mark found in {rec['count']} pieces (built: 6)  ·  re-saved version caught: {res['near_duplicates'][0]['pieces']}", font=grot(24), fill=INK)
y += 240

# 6 camera + pose
y = section(y, "06", "CAMERA HABITS + POSE  ·  exif_habits.py, pose.py", "a 20-shot set with known settings; three skeletons with known poses")
h = exif_habits.habits(f"{root}/exif")
lines(M, y, ["built: 70% at 35mm · 65% at f/1.8 · 35% flash · mostly vertical"], size=20, col=GREY)
lines(M, y + 36, exif_habits.reading(h), size=24, col=ACC, gap=36)
kp = json.load(open(f"{root}/pose/kp.json"))
labels = [("frontal,", "arms at sides"), ("3/4, contrapposto,", "hand on hip"), ("profile,", "cropped above knees")]
bones = [(5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)]
for i, k in enumerate(kp):
    x0 = 1180 + i * 400
    sc = 0.32
    for a, b in bones:
        if k[a][2] > 0.3 and k[b][2] > 0.3 and k[a][1] < 1000 and k[b][1] < 1000:
            d.line([(x0 + (k[a][0] - 400) * sc, y + k[a][1] * sc - 40), (x0 + (k[b][0] - 400) * sc, y + k[b][1] * sc - 40)], fill=INK, width=4)
    if k[0][2] > 0.3:
        cx, cy = x0 + (k[0][0] - 400) * sc, y + k[0][1] * sc - 40
        d.ellipse([cx - 14, cy - 18, cx + 14, cy + 10], outline=INK, width=4)
    p = pose.person(k, (1000, 1000))
    d.text((x0 - 60, y + 250), "built: " + labels[i][0], font=mono(16), fill=GREY)
    d.text((x0 - 60, y + 272), "       " + labels[i][1], font=mono(16), fill=GREY)
    d.text((x0 - 60, y + 302), p["facing"] + (" · weight shift" if p.get("weight_shift") else ""), font=grot(20), fill=ACC)
    d.text((x0 - 60, y + 328), ", ".join(p["hands"]), font=grot(20), fill=ACC)
    d.text((x0 - 60, y + 354), p["crop"], font=grot(20), fill=ACC)
y += 410

d.line([(M, y), (W - M, y)], fill=RULE, width=2)
d.text((M, y + 30), "regenerate: python examples/make_genre_demos.py demos && python examples/make_grade_demo.py demos/grade && python examples/make_genre_card.py demos out.jpg", font=mono(19), fill=GREY)
im = im.crop((0, 0, W, min(H, y + 90)))
im.save(out, quality=90)
print("saved", out, im.size)
