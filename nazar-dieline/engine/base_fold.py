"""ENGINE NOTE (generic copy of a worked example, BAGH).
Needs the project `art` module (tokens T, FONT, W/HP/G page sizes in mm, SS, HERE) and out/<sku>_print-art.png
(flat print art with 3 mm bleed: front panel, gusset strip, back panel). Edit SKU, TINT and the paths to reuse.
The logic is in references/flexibles_labels.md ("Doypack base: in, then out").
"""
"""How the D1 pouch base works: the gusset folds IN, then back OUT, and that W is what lets it stand.
Code-drawn from the real print art (no AI). Three views: the printed flat, a side cut (empty vs filled), the base from below.
    python base_fold.py [sku]   -> out/<sku>_base-fold.png
"""
import os, io, sys, base64
import cairosvg
from PIL import Image, ImageDraw
import art

T = art.T; FONT = art.FONT; W, HP, G, SS = art.W, art.HP, art.G, art.SS
SKU = next(s for s in T["skus"] if s["id"] == (sys.argv[1] if len(sys.argv) > 1 else "mango"))
TINT = SKU["tint"]; INK = "#1E1A17"; MUTE = "#6F665E"; BG = "#F3EEE5"; BLUE = "#00AEEF"
OUT = os.path.join(art.HERE, "out"); CW, CH = 2400, 1350


def tx(s, x, y, cap, wght=800, anchor="start", fill=INK, track=0.0):
    g, _ = FONT.path(s, x, y, cap / FONT.cap(100, wght), 100, wght, track=track, anchor=anchor, fill=fill); return g


def uri(im):
    b = io.BytesIO(); im.save(b, "PNG"); return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


flat = Image.open(os.path.join(OUT, f"{SKU['id']}_print-art.png")).convert("RGB")
k = flat.height / (2 * HP + G + 6)                                   # px per mm in the print art (3 mm bleed each side)
gus = flat.crop((int(3 * k), int((3 + HP) * k), int((3 + W) * k), int((3 + HP + G) * k)))

s = [f'<rect width="{CW}" height="{CH}" fill="{BG}"/>',
     tx("HOW THE BASE WORKS", 80, 92, 18, 800, fill=MUTE, track=0.16),
     tx("In, then out. That fold is the foot.", 80, 160, 52, 900)]

# 1. the printed flat: front, base gusset, back on one web
fh = 1000; fw = fh * flat.width / flat.height; fx, fy = 110, 250
s.append(f'<image href="{uri(flat.resize((int(fw * 1.5), int(fh * 1.5))))}" x="{fx}" y="{fy}" width="{fw:.0f}" height="{fh}"/>')
mm = fh / (2 * HP + G + 6)
gy0, gy1, gmid = fy + (3 + HP) * mm, fy + (3 + HP + G) * mm, fy + (3 + HP + G / 2) * mm
lx = fx + fw + 26
for y, lab in ((fy + (3 + HP / 2) * mm, "FRONT"), (gmid, "BASE GUSSET"), (fy + (3 + HP + G + HP / 2) * mm, "BACK")):
    s.append(f'<line x1="{lx}" y1="{y}" x2="{lx + 30}" y2="{y}" stroke="{INK}" stroke-width="2"/>' + tx(lab, lx + 40, y + 7, 18, 800))
s.append(f'<path d="M{lx},{gy0} h14 V{gy1} h-14" fill="none" stroke="{INK}" stroke-width="2"/>')
s.append(tx("blue dash = the fold", lx + 40, gmid + 36, 15, 600, fill=BLUE))
s.append(tx("1  One printed web", fx, 1310, 22, 900))

# 2. side cut: empty (W folded up inside) and filled (W opens into a floor)
def cut(ox, oy, sc, filled):
    o = []
    if not filled:
        d, pk = 26, G / 2                                               # pouch flat: walls close, gusset tucked up inside
        fr = f"M{ox},{oy - 150 * sc} L{ox},{oy}"; bk = f"M{ox + d * sc},{oy - 150 * sc} L{ox + d * sc},{oy}"
        gu = f"M{ox},{oy} L{ox + d / 2 * sc},{oy - pk * sc} L{ox + d * sc},{oy}"
    else:
        d = 62
        fr = f"M{ox + 8 * sc},{oy - 150 * sc} C{ox - 6 * sc},{oy - 90 * sc} {ox - 4 * sc},{oy - 20 * sc} {ox},{oy}"
        bk = f"M{ox + (d - 8) * sc},{oy - 150 * sc} C{ox + (d + 6) * sc},{oy - 90 * sc} {ox + (d + 4) * sc},{oy - 20 * sc} {ox + d * sc},{oy}"
        gu = f"M{ox},{oy} Q{ox + d / 2 * sc},{oy - 14 * sc} {ox + d * sc},{oy}"
        body = f"M{ox + 8 * sc},{oy - 120 * sc} C{ox - 6 * sc},{oy - 80 * sc} {ox - 4 * sc},{oy - 20 * sc} {ox},{oy} Q{ox + d / 2 * sc},{oy - 14 * sc} {ox + d * sc},{oy} " \
               f"C{ox + (d + 4) * sc},{oy - 20 * sc} {ox + (d + 6) * sc},{oy - 80 * sc} {ox + (d - 8) * sc},{oy - 120 * sc} Z"
        o.append(f'<path d="{body}" fill="{TINT}" opacity="0.35"/>')
    o.append(f'<line x1="{ox - 60}" y1="{oy + 2}" x2="{ox + d * sc + 60}" y2="{oy + 2}" stroke="{MUTE}" stroke-width="2" stroke-dasharray="6 6"/>')
    o.append(f'<path d="{fr}" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/><path d="{bk}" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>')
    o.append(f'<path d="{gu}" fill="none" stroke="{TINT}" stroke-width="9" stroke-linejoin="round" stroke-linecap="round"/>')
    return "".join(o), d


px = 760
s.append(tx("Empty, flat", px, 330, 24, 900))
g, d = cut(px + 120, 860, 3.2, False); s.append(g)
s.append(tx("IN", px + 100, 780, 20, 900, "end") + tx("OUT", px + 228, 780, 20, 900))
s.append(tx("base tucked up inside:", px, 920, 17, 600, fill=MUTE) + tx("in, then back out", px, 946, 17, 600, fill=MUTE))
s.append(tx("Filled, standing", px + 400, 330, 24, 900))
g, d = cut(px + 450, 860, 3.2, True); s.append(g)
s.append(tx("weight opens the fold:", px + 400, 920, 17, 600, fill=MUTE) + tx("the gusset becomes a floor", px + 400, 946, 17, 600, fill=MUTE))
s.append(tx("front", px + 120 - 70, 860 - 150 * 3.2 + 20, 15, 700, fill=MUTE) + tx("back", px + 120 + 26 * 3.2 + 14, 860 - 150 * 3.2 + 20, 15, 700, fill=MUTE))
s.append(tx("2  Side cut", px, 1310, 22, 900))

# 3. from below: the opened gusset as an eye-shaped foot, its hidden line readable
bx, by, bw, bd = 1560, 620, 620, 280
lens = f"M{bx},{by} Q{bx + bw / 2},{by - bd} {bx + bw},{by} Q{bx + bw / 2},{by + bd} {bx},{by} Z"
s.append(f'<defs><clipPath id="L"><path d="{lens}"/></clipPath></defs>')
s.append(f'<ellipse cx="{bx + bw / 2 + 10}" cy="{by + 14}" rx="{bw / 2}" ry="{bd / 2.2}" fill="#000" opacity="0.10"/>')
s.append(f'<image href="{uri(gus)}" x="{bx}" y="{by - bd / 2}" width="{bw}" height="{bd}" preserveAspectRatio="none" clip-path="url(#L)"/>')
s.append(f'<path d="{lens}" fill="none" stroke="{INK}" stroke-width="3"/>')
s.append(f'<line x1="{bx + 6}" y1="{by}" x2="{bx + bw - 6}" y2="{by}" stroke="{INK}" stroke-width="2" stroke-dasharray="10 6" opacity="0.55"/>')
for cx_, sg in ((bx, 1), (bx + bw, -1)):                              # side-seal corners: where front, back and gusset meet
    s.append(f'<path d="M{cx_},{by} l{sg * 70},-34 l0,68 Z" fill="{INK}" opacity="0.25"/>')
s.append(tx("FRONT EDGE", bx + bw / 2, by - bd / 2 - 24, 15, 800, "middle", fill=MUTE) + tx("BACK EDGE", bx + bw / 2, by + bd / 2 + 40, 15, 800, "middle", fill=MUTE))
s.append(tx("crease", bx + bw / 2, by - 14, 14, 700, "middle", fill=MUTE))
s.append(tx("corners: side seals hold the fold", bx, by + bd / 2 + 110, 17, 600, fill=MUTE))
s.append(tx("tip it up: “Khatam? Phir se.”", bx, by + bd / 2 + 138, 17, 600, fill=MUTE))
s.append(tx("3  From below", bx, 1310, 22, 900))
s.append(tx("Schematic from the print art · converter dieline governs · Nazar Studio", CW - 80, 92, 14, 600, "end", fill=MUTE))

svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{CW}" height="{CH}" viewBox="0 0 {CW} {CH}">{"".join(s)}</svg>'
p = os.path.join(OUT, f"{SKU['id']}_base-fold.png")
Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert("RGB").save(p)
print(p)
