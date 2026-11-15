#!/usr/bin/env python3
"""Regenerate every known-answer test input for the README genre demos.
All inputs are original and synthetic (no one's photos, art or footage), each
built with a KNOWN style, so the engines can be checked against the truth.

    python make_genre_demos.py out_folder

Writes:
  strokes/   A_brush (6 tapered strokes), B_sketch (short loose marks), C_technical (ruled grid)
  layout/    A_swiss_grid (left, 3 columns, type ratio 1.5), B_centred_poster (centred, ratio 1.25)
  cluster/   5 "client" pieces + 4 "personal" pieces, an eye mark on 6 of them, 1 re-saved version
  exif/      20 shots: 70% at 35mm, 65% at f/1.8, 35% flash, mostly vertical; 2 stripped exports
  video/     edit.mp4 with shots of 3.0 2.5 2.0 1.5 1.2 1.0 0.8 0.6 6.0 9.0 7.5 s (needs imageio-ffmpeg)
  pose/      kp.json: frontal arms at sides; 3/4 contrapposto hand on hip; profile cropped above knees
And grades via make_grade_demo.py.
"""
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "nazar-core", "engine", "fonts")
SHOTS = [3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8, 0.6, 6.0, 9.0, 7.5]


def strokes(out):
    random.seed(1)
    im = Image.new("L", (512, 512), 245); d = ImageDraw.Draw(im)
    for k in range(6):
        pts = [(40 + i * 8, 80 + k * 60 + 30 * math.sin(i / 9 + k)) for i in range(55)]
        for i in range(len(pts) - 1):
            d.line([pts[i], pts[i + 1]], fill=20, width=int(1 + 7 * math.sin(math.pi * i / (len(pts) - 1))))
    im.save(f"{out}/A_brush.png")
    im = Image.new("L", (512, 512), 245); d = ImageDraw.Draw(im)
    for _ in range(220):
        x, y, a, L = random.uniform(40, 470), random.uniform(40, 470), random.uniform(0, math.pi), random.uniform(8, 30)
        d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=30, width=2)
    im.save(f"{out}/B_sketch.png")
    im = Image.new("L", (512, 512), 245); d = ImageDraw.Draw(im)
    for k in range(10): d.line([(40, 50 + k * 42), (470, 50 + k * 42)], fill=10, width=4)
    for k in range(6): d.line([(60 + k * 80, 40), (60 + k * 80, 470)], fill=10, width=4)
    im.save(f"{out}/C_technical.png")


def layout(out):
    words = "form follows the brief and the brief follows the street".split()
    line = lambda n, k: " ".join(words[(k + i) % len(words)] for i in range(n))
    f = lambda w, s: ImageFont.truetype(os.path.join(FONTS, f"SpaceGrotesk-{w}.ttf"), s)
    W, H = 1200, 1600
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    d.text((100, 120), "STREET FIRST", font=f("Medium", 81), fill="black")
    d.text((100, 260), line(5, 1), font=f("Medium", 54), fill="black")
    for c, x in enumerate((100, 460, 820)):
        d.text((x, 420), line(2, c), font=f("Medium", 36), fill="black")
        for r in range(14):
            d.text((x, 500 + r * 40), line(3, r + c), font=f("Regular", 24), fill="black")
        d.rectangle([x, 1150, x + 280, 1450], fill=(40, 40, 40))
    im.save(f"{out}/A_swiss_grid.png")
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    y = 200
    for size, n in ((92, 2), (74, 3), (59, 3), (47, 4), (37, 5), (30, 6), (24, 7)):
        t = line(n, size); tw = d.textlength(t, font=f("Regular", size))
        d.text(((W - tw) / 2, y), t, font=f("Regular", size), fill="black"); y += int(size * 1.9)
    im.save(f"{out}/B_centred_poster.png")


def eye(d, cx, cy, s, ink):
    d.ellipse([cx - s, cy - s // 2, cx + s, cy + s // 2], outline=ink, width=max(2, s // 8))
    d.ellipse([cx - s // 3, cy - s // 3, cx + s // 3, cy + s // 3], fill=ink)


def cluster(out):
    random.seed(5)
    for i in range(5):
        im = Image.new("RGB", (512, 512), (242, 238, 230)); d = ImageDraw.Draw(im)
        for k in range(4):
            y = 120 + k * 70 + random.randint(-10, 10)
            d.line([(80, y), (300 + random.randint(0, 80), y + random.randint(-20, 20))], fill=(30, 28, 26), width=2)
        d.rectangle([380, 380, 410, 410], fill=(228, 87, 46))
        if i < 3: eye(d, 64, 448, 40, (30, 28, 26))
        im.save(f"{out}/client_{i}.png")
    for i in range(4):
        im = Image.new("RGB", (512, 512), (18, 16, 30)); d = ImageDraw.Draw(im)
        for _ in range(40):
            x, y, r = random.randint(0, 512), random.randint(0, 512), random.randint(10, 60)
            d.ellipse([x - r, y - r, x + r, y + r], fill=random.choice([(240, 60, 120), (40, 200, 220), (250, 210, 40)]))
        if i < 2:
            d.rectangle([0, 384, 128, 512], fill=(242, 238, 230)); eye(d, 64, 448, 40, (30, 28, 26))
        im.save(f"{out}/personal_{i}.png")
    Image.open(f"{out}/client_0.png").resize((500, 500)).resize((512, 512)).save(f"{out}/client_0_v2.png")


def exif(out):
    random.seed(3)
    for i in range(20):
        ex, sub = Image.Exif(), {}
        f = 35 if i < 14 else random.choice([24, 50, 85]); ap = 1.8 if i < 13 else random.choice([4.0, 5.6, 8.0])
        sub[0xA405] = f; sub[0x920A] = (f * 10, 10); sub[0x829D] = (int(ap * 10), 10)
        sub[0x829A] = (1, random.choice([60, 125, 250, 500])); sub[0x8827] = random.choice([200, 400, 800])
        sub[0x9209] = 1 if i % 3 == 0 else 0; sub[0xA434] = "35mm f/1.8 prime" if i < 14 else "zoom"
        ex[0x010F] = "DemoCam"; ex[0x0110] = "X1"; ex[0x8769] = sub
        Image.new("RGB", (400, 600) if i < 15 else (600, 400), (120, 110, 100)).save(f"{out}/shot_{i:02d}.jpg", exif=ex)
    for i in range(2):
        Image.new("RGB", (500, 500), (90, 90, 90)).save(f"{out}/export_{i}.jpg")


def video(out):
    import imageio_ffmpeg as iio
    rng = np.random.default_rng(2); W, H, FPS = 320, 180, 24
    w = iio.write_frames(f"{out}/edit.mp4", (W, H), fps=FPS, macro_block_size=1, quality=8); w.send(None)
    for k, L in enumerate(SHOTS):
        base = rng.uniform(40, 200, 3)
        for t in range(int(round(L * FPS))):
            y = np.linspace(0, 1, H)[:, None, None]
            fr = base * (0.6 + 0.6 * y) * np.ones((H, W, 3))
            cx = int((t * 3 + k * 37) % W); fr[60:120, max(0, cx - 20):cx + 20] = 255 - base
            w.send(np.clip(fr + rng.normal(0, 3, fr.shape), 0, 255).astype(np.uint8))
    w.close()


def pose(out):
    c = 1.0
    frontal = [[500,200,c],[515,190,c],[485,190,c],[530,195,c],[470,195,c],[560,280,c],[440,280,c],[575,380,c],[425,380,c],[580,470,c],[420,470,c],[540,500,c],[460,500,c],[540,650,c],[460,650,c],[540,800,c],[460,800,c]]
    contra = [[510,205,c],[522,195,c],[500,196,c],[530,200,c],[490,202,c],[545,275,c],[470,290,c],[640,385,c],[455,385,c],[548,500,c],[450,470,c],[530,505,c],[475,490,c],[525,650,c],[480,650,c],[520,800,c],[485,800,c]]
    profile = [[540,300,c],[530,290,c],[528,291,0.1],[515,295,c],[0,0,0],[505,380,c],[495,382,c],[560,450,c],[0,0,0.1],[620,450,c],[0,0,0.1],[500,600,c],[492,602,c],[505,1150,c],[495,1150,c],[505,1400,c],[495,1400,c]]
    json.dump([frontal, contra, profile], open(f"{out}/kp.json", "w"))


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "genre_demos"
    for name, fn in (("strokes", strokes), ("layout", layout), ("cluster", cluster), ("exif", exif), ("video", video), ("pose", pose)):
        os.makedirs(f"{root}/{name}", exist_ok=True)
        try:
            fn(f"{root}/{name}")
            print("ok  ", name)
        except ImportError as e:
            print("skip", name, f"({e})")
