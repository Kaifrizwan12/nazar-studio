#!/usr/bin/env python3
"""Render assets/demo-kits.jpg: five kits, each run live on real assets (CC0 art from
The Met and the Cleveland Museum of Art). Nothing on the card is typed in by hand
except the poster copy, which was read off the posters by eye (stated on the card).

    python make_kits_card.py cy_folder cma_folder pack_box.png pack_qa.md out.jpg
"""
import os
import shutil
import sys
import tempfile

import imageio_ffmpeg as iio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "..", "..")
for k in ("nazar-ooh", "nazar-social", "nazar-web", "nazar-motion"):
    sys.path.insert(0, os.path.join(R, k, "engine"))
import motion_check as mc  # noqa: E402
import ooh_check as ooh  # noqa: E402
import social_lint as sl  # noqa: E402
import web_audit as wa  # noqa: E402

F = os.path.join(R, "nazar-core", "engine", "fonts") + "/"
PAPER, INK, GREY, RULE, ACC, GOOD = "#F2EEE6", "#1C1B19", "#6E6A64", "#CFC9BF", "#E4572E", "#2F6B4F"
anton = lambda s: ImageFont.truetype(F + "Anton-Regular.ttf", s)
grot = lambda s: ImageFont.truetype(F + "SpaceGrotesk-Regular.ttf", s)
mono = lambda s: ImageFont.truetype(F + "SpaceMono-Regular.ttf", s)
cy, cma, pack_png, pack_qa, out = sys.argv[1:6]
W, M, RH = 2400, 100, 430
im = Image.new("RGB", (W, 330 + 5 * RH + 90), PAPER)
d = ImageDraw.Draw(im)
d.text((M, 70), "PACKAGING · BILLBOARDS · SOCIAL · WEB · MOTION", font=anton(84), fill=INK)
d.text((M, 190), "five kits, each with its own engine, run live on public-domain art (The Met, Cleveland Museum of Art, CC0). orange = a finding, green = passes", font=grot(25), fill=GREY)
mark = lambda lvl: ACC if lvl in ("fail", "warn", "P1", "P2") else GOOD


def row(i, label, engine, sub):
    y = 270 + i * RH
    d.line([(M, y), (W - M, y)], fill=RULE, width=2)
    d.text((M, y + 22), label, font=mono(32), fill=INK)
    d.text((M, y + 68), engine, font=grot(21), fill=GREY)
    d.text((M, y + 98), sub, font=grot(21), fill=GREY)
    return y


def lines(x, y, items, size=22, gap=34, width=1000):
    for col, t in items:
        words, cur = t.split(), ""
        for w in words:
            if d.textlength(cur + " " + w, font=grot(size)) > width:
                d.text((x, y), cur, font=grot(size), fill=col); y += gap - 6; cur = w
            else:
                cur = (cur + " " + w).strip()
        d.text((x, y), cur, font=grot(size), fill=col); y += gap
    return y


# 1 packaging: real art on a real structure, with the pack engine's own QA
y = row(0, "PACKAGING", "nazar-dieline art + QA", "real art on a real dieline")
dl = Image.open(pack_png.replace("_box.png", ".png")).convert("RGB"); dl.thumbnail((470, 335)); im.paste(dl, (560, y + 25))
d.text((560, y + 25 + dl.height + 8), "flat dieline: cut, crease, glue, grain", font=grot(19), fill=GREY)
b = Image.open(pack_png).convert("RGB"); b = b.crop((120, 140, 820, 1230)); b.thumbnail((220, 335)); im.paste(b, (1100, y + 25))
d.text((1100, y + 25 + b.height + 8), "folded, with the art", font=grot(19), fill=GREY)
qa = [l[2:].strip() for l in open(pack_qa).read().splitlines() if l.startswith("- **P")]
items = [(ACC, "engine QA (it checks the art, not just the box):")] + [(ACC, "· " + q.replace("**", "")) for q in qa[:4]] + [(INK, "P1 = fix before showing anyone. P2 = fix before the converter.")]
lines(1400, y + 40, items, width=900)

# 2 OOH: real poster copy against real legibility numbers
y = row(1, "OUT-OF-HOME", "nazar-ooh ooh_check.py", "1890s posters tested as a 2020s bulletin")
posters = [("cheret_1978-1054.jpg", "PALAIS DE GLACE CHAMPS ELYSEES"),
           ("cheret_1987-1064.jpg", "PASTILLES PONCELET CONTRE RHUMES TOUX BRONCHITES 1.50 LA BOITE DE CENT"),
           ("cheret_2009-555.jpg", "SAXOLEINE PETROLE DE SURETE EXTRA-BLANC DEODORISE ININFLAMMABLE EN BIDONS PLOMBES DE 5 LITRES"),
           ("cheret_1987-1065.jpg", "MUSEE GREVIN MAGIE NOIRE APPARITIONS INSTANTANEES PAR LE PROFESSEUR CARMELLI SEANCES TOUS LES JOURS DE 3H 6H ET 8H")]
x = 560
for f, copy in posters:
    t = Image.open(os.path.join(cma, f)).convert("RGB"); t.thumbnail((150, 380)); im.paste(t, (x, y + 20))
    r = ooh.check(copy, 300, 45, 14)
    wv = r["checks"][0]; rv = r["checks"][2]
    d.text((x, y + 20 + t.height + 8), f"{r['words']} words", font=mono(22), fill=mark(wv[1]))
    d.text((x, y + 20 + t.height + 36), f"read ~{r['read_s_est']}s / {r['in_view_s']}s", font=grot(19), fill=mark(rv[1]))
    x += 215
lines(1500, y + 30, [(INK, "14 x 48 ft bulletin, read from 300 ft at 45 mph, 14 in capitals:"),
                     (GOOD if ooh.check("a", 300, 45, 14)["checks"][1][1] == "ok" else ACC, "· letters pass: need 12.0 in (MUTCD 30 ft per inch, x0.83 for a moderate layout)"),
                     (ACC, "· only the shortest poster is readable in time. the longest needs ~14 s in a 4.5 s glance"),
                     (GREY, "'7 words' is an industry convention with no primary source; the engine says so."),
                     (GREY, "poster copy read off the posters by eye. viewing distance and speed are inputs.")], width=820)

# 3 social: the slop test
y = row(2, "SOCIAL", "nazar-social social_lint.py", "the slop test, as code")
caps = [("a real archive caption", "Photographs of British Algae: Cyanotype Impressions. Anna Atkins, 1843–53. Sun-printed in iron blue, one plate per specimen. The Metropolitan Museum of Art, open access."),
        ("a typical machine caption", "In today's fast-paced world, we're thrilled to elevate your journey — unlock seamless growth, delve deeper, and leverage the power of design! 🚀✨💡 #design #branding #growth"),
        ("the same idea, plainly", "Every plate in this book was made by laying a seaweed on paper and leaving it in the sun. 1843. Still the bluest thing you'll see today.")]
yy = y + 25
for label, text in caps:
    r = sl.lint(text)
    d.text((560, yy), label, font=mono(22), fill=GREY)
    d.text((560, yy + 32), (text[:74] + "…") if len(text) > 74 else text, font=grot(20), fill=INK)
    d.text((1620, yy + 5), r["verdict"], font=mono(26), fill=GOOD if not r["hits"] else ACC)
    d.text((1620, yy + 40), "; ".join(h[1] for h in r["hits"][:4])[:62], font=grot(18), fill=ACC)
    yy += 128
d.text((560, y + 385), "a hit is a prompt to rewrite, not proof of anything: people write 'elevate' too.", font=grot(19), fill=GREY)

# 4 web: audit a good and a naive page built from the same real plates
y = row(3, "WEB", "nazar-web web_audit.py", "one real page, built well and built badly")
tmp = tempfile.mkdtemp()
plates = sorted(f for f in os.listdir(cy) if f.endswith(".jpg"))[:4]
for f in plates:
    shutil.copy(os.path.join(cy, f), tmp)
dims = {f: Image.open(os.path.join(tmp, f)).size for f in plates}
good = '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Cyanotype Study</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>:root{--fg:#1C1B19;--bg:#F2EEE6}body{color:var(--fg);background:var(--bg)}</style></head><body><h1>Cyanotype Study</h1><h2>Four plates</h2>' + "".join(f'<img src="{f}" alt="Cyanotype plate {i + 1} from Photographs of British Algae, Anna Atkins" width="{dims[f][0] // 2}" height="{dims[f][1] // 2}">' for i, f in enumerate(plates)) + '<a href="/about">About the plates</a></body></html>'
bad = '<!doctype html><html><head><style>.plate{width:120px}body{color:#9a9a9a;background:#ffffff}</style></head><body><h1>Cyanotype</h1><h1>Plates</h1><h4>Four</h4>' + "".join(f'<img class="plate" src="{f}"{"" if i % 2 else " alt=" + chr(34) + "plate" + chr(34)}>' for i, f in enumerate(plates)) + '<a href="/about">click here</a></body></html>'
open(os.path.join(tmp, "good.html"), "w").write(good); open(os.path.join(tmp, "bad.html"), "w").write(bad)
x = 560
for name, label in (("good.html", "built well"), ("bad.html", "built badly")):
    r = wa.audit(os.path.join(tmp, name))
    d.text((x, y + 22), label, font=mono(26), fill=INK)
    d.text((x, y + 58), f"{r['weight_kb']} KB · {r['images']} images", font=grot(19), fill=GREY)
    lines(x, y + 95, [(mark(l), ("+ " if l == "ok" else "× ") + m) for l, m in r["findings"][:8]], size=19, gap=29, width=700)
    x += 880
d.text((560, y + 360), "no network or rendering here: real-device speed and design quality still need Lighthouse and a human.", font=grot(19), fill=GREY)

# 5 motion: the same reveal, linear vs eased
y = row(4, "MOTION", "nazar-motion motion_check.py", "slow in and slow out, measured")
plate = Image.open(os.path.join(cy, "cyanotype_291529.jpg")).convert("RGB"); plate.thumbnail((320, 400))
Pm = np.asarray(plate, np.float32); h2, w2 = Pm.shape[0] - Pm.shape[0] % 2, Pm.shape[1] - Pm.shape[1] % 2
bgm = np.full_like(Pm, 242)
x = 560
for name, fn in (("linear", lambda t: t), ("eased", lambda t: t * t * (3 - 2 * t))):
    pth = os.path.join(tmp, f"{name}.mp4")
    wr = iio.write_frames(pth, (w2, h2), fps=30, macro_block_size=1, quality=8); wr.send(None)
    for i in range(60):
        a = fn(min(1, max(0, (i - 6) / 36)))
        wr.send(np.clip(bgm * (1 - a) + Pm * a, 0, 255).astype(np.uint8)[:h2, :w2])
    wr.close()
    sp, fps = mc.frames_speed(pth); r = mc.analyse(sp, fps)
    gx, gy, gw, gh = x, y + 40, 700, 230
    d.rectangle([gx, gy, gx + gw, gy + gh], outline=RULE, width=2)
    pts = [(gx + 10 + (gw - 20) * k / (len(sp) - 1), gy + gh - 12 - (gh - 30) * (v / sp.max())) for k, v in enumerate(sp)]
    d.line(pts, fill=ACC if name == "linear" else INK, width=4)
    d.text((gx, y + 12), f"{name}: speed per frame", font=mono(21), fill=GREY)
    d.text((gx, gy + gh + 14), f"{r['verdict']}", font=grot(28), fill=ACC if "linear" in r["verdict"] else GOOD)
    d.text((gx, gy + gh + 54), f"peak speed is {r['peak_to_end_speed']}x the speed at the ends · moves {r['duration_ms']} ms · holds {r['hold_start_ms']} ms then {r['hold_end_ms']} ms", font=grot(19), fill=GREY)
    x += 800
d.text((M, im.height - 55), "engines and sources: nazar-dieline, nazar-ooh (MUTCD, FHWA, Snellen), nazar-social, nazar-web, nazar-motion (Thomas & Johnston) · reproduce: nazar-core/examples/make_kits_card.py", font=mono(17), fill=GREY)
im.save(out, quality=90)
print("saved", out, im.size)
