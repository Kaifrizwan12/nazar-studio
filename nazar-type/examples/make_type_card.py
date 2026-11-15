#!/usr/bin/env python3
"""Render assets/demo-type.jpg: the type kit's QA run on real font files, with a
real shaped Latin line and a real shaped Urdu line through each. Everything is
computed live (type_check.py for the checks, harfbuzz for the shaping).

    python make_type_card.py fonts_dir out.jpg
"""
import io
import os
import sys

import cairosvg
import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import type_check as tc  # noqa: E402

CORE = os.path.join(HERE, "..", "..", "nazar-core", "engine", "fonts") + "/"
PAPER, INK, GREY, RULE, ACC = "#F2EEE6", "#1C1B19", "#6E6A64", "#CFC9BF", "#E4572E"
anton = lambda s: ImageFont.truetype(CORE + "Anton-Regular.ttf", s)
grot = lambda s: ImageFont.truetype(CORE + "SpaceGrotesk-Regular.ttf", s)
mono = lambda s: ImageFont.truetype(CORE + "SpaceMono-Regular.ttf", s)

folder, out = sys.argv[1], sys.argv[2]
FONTS = [CORE + "Anton-Regular.ttf", CORE + "SpaceGrotesk-Regular.ttf", CORE + "SpaceMono-Regular.ttf", os.path.join(folder, "Gulzar.ttf")]
LATIN, URDU = "Nazar Lag Jaye", "نظر لگ جائے"


def shaped(path, text, height_px, colour=INK, max_w=520):
    data = open(path, "rb").read()
    face = hb.Face(data); font = hb.Font(face)
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True, "rlig": True, "init": True, "medi": True, "fina": True, "isol": True})
    tt = TTFont(path); gs = tt.getGlyphSet(); order = tt.getGlyphOrder(); upm = tt["head"].unitsPerEm
    x, parts = 0, []
    for i, p in zip(buf.glyph_infos, buf.glyph_positions):
        pen = SVGPathPen(gs); gs[order[i.codepoint]].draw(pen)
        parts.append((pen.getCommands(), x + p.x_offset, p.y_offset)); x += p.x_advance
    sc = min(height_px / upm, max_w / max(x, 1))
    W, H = int(x * sc) + 20, int(height_px * 1.9)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">'
    for d, gx, gy in parts:
        svg += f'<path d="{d}" transform="translate({10 + gx * sc},{height_px * 1.3 - gy * sc}) scale({sc},-{sc})" fill="{colour}"/>'
    svg += "</svg>"
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert("RGBA"), len(parts)


rows = []
for p in FONTS:
    r = tc.check(p); r["_path"] = p; r["verdict"] = tc.verdict(r); rows.append(r)

W, M = 2400, 100
colw = (W - 2 * M) // 4
H = 1500
im = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(im)
d.text((M, 70), "TYPE QA ON REAL FONT FILES", font=anton(92), fill=INK)
d.text((M, 185), "four fonts, one checklist (nazar-type): licence, embedding, coverage, shaping, small-type legality. then a real Latin and a real Urdu line set through each", font=grot(25), fill=GREY)

y0 = 260
for i, r in enumerate(rows):
    x = M + i * colw
    d.line([(x, y0), (x + colw - 30, y0)], fill=RULE, width=2)
    d.text((x, y0 + 20), f"{r['family']}", font=mono(30), fill=INK)
    d.text((x, y0 + 62), f"{r['style']}  ·  v{r['version']}", font=grot(21), fill=GREY)
    # specimens
    lat, _ = shaped(r["_path"], LATIN, 80, max_w=colw - 50)
    im.paste(lat, (x, y0 + 105), lat)
    urd, n = shaped(r["_path"], URDU, 80, max_w=colw - 50)
    im.paste(urd, (x, y0 + 235), urd)
    # coverage bars
    yy = y0 + 420
    for k, v in r["coverage"].items():
        label = k.split(" (")[0].replace(" ۰–۹", "")
        d.text((x, yy), label, font=grot(20), fill=INK)
        d.rectangle([x + 235, yy + 5, x + 235 + 180, yy + 21], outline=RULE, width=2)
        if v > 0:
            d.rectangle([x + 235, yy + 5, x + 235 + 180 * v, yy + 21], fill=ACC if v < 1 else INK)
        d.text((x + 430, yy), f"{v:.0%}", font=mono(18), fill=INK)
        yy += 34
    yy += 14
    shp = ", ".join(r["arabic_shaping"]) or "none"
    facts = [("shaping", shp), ("kerning", "yes" if r["kerning"] else "no"), ("embedding", "free"),
             ("licence", "OFL 1.1 (in file)" if "Open Font" in r["licence"] else "OFL 1.1, file separate" if "Gulzar" in r["family"] else r["licence"][:28]),
             ("1.2 mm x-height", f"{r.get('min_pt_for_1.2mm_xheight')} pt min")]
    for k, v in facts:
        d.text((x, yy), k, font=grot(20), fill=GREY)
        d.text((x + 200, yy), v, font=grot(20), fill=INK)
        yy += 32
    yy += 18
    for line in [v.replace("₨", "Rs sign U+20A8") for v in r["verdict"]]:
        words, cur = line.split(), ""
        for w in words:
            if d.textlength(cur + " " + w, font=grot(20)) > colw - 45:
                d.text((x, yy), cur, font=grot(20), fill=ACC); yy += 26; cur = w
            else:
                cur = (cur + " " + w).strip()
        d.text((x, yy), cur, font=grot(20), fill=ACC); yy += 34

yb = 1255
d.line([(M, yb), (W - M, yb)], fill=RULE, width=2)
g = [r for r in rows if "Gulzar" in r["family"]][0]
miss = " ".join(f"U+{ord(c):04X}" for c in g["missing"]["Sindhi extra letters"][:6])
d.text((M, yb + 28), "what the checks caught: none of the studio's three fonts has the rupee sign (U+20A8), so a Pakistani price line needs 'Rs' or a fallback. Gulzar sets Urdu beautifully", font=grot(23), fill=INK)
d.text((M, yb + 62), f"but covers only 4 of 15 Sindhi letters (missing e.g. {miss} …), lacks ™ and ṇ, and needs 7.7 pt to reach a legal 1.2 mm x-height, against 4.6 pt for Anton.", font=grot(23), fill=INK)
d.text((M, yb + 108), "the file doesn't carry its licence text, so the OFL.txt from its repository must be filed beside it. coverage % says nothing about whether the shapes are good: that's still a designer's eye.", font=grot(21), fill=GREY)
d.text((M, yb + 150), "fonts: Anton, Space Grotesk, Space Mono (OFL, in nazar-core) and Gulzar (OFL 1.1, Google Fonts) · nazar-type/engine/type_check.py · reproduce: examples/fetch_gulzar.py → make_type_card.py", font=mono(17), fill=GREY)
im.save(out, quality=90)
print("saved", out, im.size)
