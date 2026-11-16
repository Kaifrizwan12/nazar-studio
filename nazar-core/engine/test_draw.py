#!/usr/bin/env python3
"""test_draw.py: draw every draw.py helper onto one sheet and assert basic facts. Usage: python3 test_draw.py [sheet.png]"""
import os, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw import *

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "draw_sheet.png")
BG, INK, ACC = "#F4EFE6", "#14141C", "#2F5BFF"
cv = Canvas(1200, 1500, BG)
H = font("Anton-Regular.ttf", 120); B = font("SpaceGrotesk-Medium.ttf", 34); sm = font("SpaceGrotesk-Regular.ttf", 28)
fails = []

def check(name, ok, info=""):
    print(("PASS " if ok else "FAIL ") + name, info)
    if not ok: fails.append(name)

# ink-aligned text at the margin
M = 90
box = ink_text(cv, M, 60, "Jumping", H, INK)
check("ink_text left edge == margin (bbox)", abs(box[0] - M) <= 2, box)
c1 = cv.result()
a = np.asarray(c1.crop((0, 60, 600, 200)).convert("L")); cols = np.where((a < 100).any(0))[0]
check("ink_text left edge == margin (pixels)", abs(cols.min() - M) <= 2, f"first ink col {cols.min()}")
box_l = ink_text(cv, M, 230, "Lamp wrap", B, INK)
for i, ln in enumerate(wrap("A short line of body text that has to wrap to a given width nicely", sm, 480)):
    ink_text(cv, M, 300 + i * 40, ln, sm, INK)
check("wrap keeps lines within width", all(sm.getlength(l) / S <= 480 for l in wrap("A short line of body text that has to wrap to a given width nicely", sm, 480)))

# strike-through crosses the middle of the text and stays level
tb = ink_text(cv, 640, 60, "Was 500", font("Anton-Regular.ttf", 100), INK)
sb = strike(cv, tb, "#E5322D", 7)
ys = np.asarray(cv.result().crop((640, 40, 1000, 220)).convert("RGB")).astype(int)
red = (ys[..., 0] > 190) & (ys[..., 1] < 90) & (ys[..., 2] < 90)
rr = np.where(red.any(1))[0]; red_c = rr.mean() + 40; tc = (tb[1] + tb[3]) / 2
check("strike centre within 15% of text centre", abs(red_c - tc) <= 0.15 * (tb[3] - tb[1]), f"strike {red_c:.1f} text {tc:.1f} h {tb[3]-tb[1]:.0f}")
check("strike stays level (rows spanned <= width+4)", (rr.max() - rr.min()) <= 7 + 4, f"{rr.max()-rr.min()+1} rows")

wb = ink_text(cv, 640, 230, "circle me", B, INK); ring(cv, wb, ACC)
arrow(cv, (900, 330), (700, 300), INK, 5)

# cards, bubble, ticket
card(cv, (90, 480, 560, 760), 30, "white")
ink_text(cv, 130, 520, "Rounded card", B, INK)
bubble(cv, (640, 480, 1100, 660), "bl", 34, ACC, shadow=True)
ink_text(cv, 680, 540, "Chat bubble", B, "white")
ticket(cv, (90, 840, 600, 1030), 24, "#FFD84A", INK, 4)
ink_text(cv, 270, 915, "TICKET", font("Anton-Regular.ttf", 60), INK)
pill(cv, (640, 760), "Swipe", B, INK, "white")
pill(cv, (900, 760), "Tag", B, ACC, "white", arrow_glyph=False)

# stars, doodles, dashed
star(cv, 700, 950, 62, INK, 7)
star(cv, 880, 950, 50, INK, 0, fill="#FFD84A", rot=12)
star(cv, 1030, 950, 40, ACC, 6, rot=-10)
wobble_line(cv, (640, 1040), (1100, 1040), ACC, 6, amp=5)
dashed(cv, (90, 1100), (1100, 1100), INK, 3)

# cutout: a synthetic "mascot" on white paper and a "logo"
art = Image.new("RGB", (300, 300), "white"); d = ImageDraw.Draw(art)
d.ellipse((60, 60, 240, 240), fill="#FF6B3D"); d.ellipse((120, 120, 140, 140), fill="white")
td = tempfile.mkdtemp(); ap = os.path.join(td, "m.png"); art.save(ap)
cutout(cv, "mascot", ap, 90, 1150, 200)
cutout(cv, "logo", ap, 400, 1150, 120)
r = cv.result()
check("cutout mascot drops the paper (box corner stays ground)", r.getpixel((92, 1152)) == r.getpixel((20, 1152)), r.getpixel((92, 1152)))
check("cutout mascot keeps its colour", r.getpixel((190, 1250))[0] > 230 and r.getpixel((190, 1250))[2] < 100, r.getpixel((190, 1250)))
cv.save(out); print("sheet:", out)
im = Image.open(out); check("saved at 1x", im.size == (1200, 1500), im.size)
print("FAILED" if fails else "all draw tests passed"); sys.exit(1 if fails else 0)
