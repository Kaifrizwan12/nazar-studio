#!/usr/bin/env python3
"""Known-answer test for engine/grade.py. Renders one original procedural scene
(no photos, nobody's work), applies five grades with known recipes, and saves
them. grade.py then has to name each look without being told.

    python make_grade_demo.py out_folder
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

rng = np.random.default_rng(7)
W, H = 640, 400


def scene():
    y = np.linspace(0, 1, H)[:, None]
    sky = np.stack([0.55 + 0.35 * y, 0.62 + 0.25 * y, 0.80 - 0.05 * y], -1) * np.ones((H, W, 1))
    im = Image.fromarray((np.clip(sky, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.ellipse([430, 70, 500, 140], fill=(255, 244, 214))
    for k, (base, col) in enumerate([(250, (92, 112, 86)), (290, (64, 84, 60)), (330, (44, 58, 40))]):
        pts = [(x, base + 25 * math.sin(x / (90 - k * 15) + k)) for x in range(0, W + 10, 10)]
        d.polygon(pts + [(W, H), (0, H)], fill=col)
    d.rectangle([150, 210, 162, 320], fill=(46, 34, 26))
    d.ellipse([110, 150, 205, 235], fill=(38, 62, 34))
    # a lit facade in the middle: warm highlights, a true-black doorway, a red sign,
    # so the neutral version has the full tonal range and colour in the highs
    d.rectangle([250, 170, 420, 340], fill=(236, 214, 178))
    d.rectangle([310, 240, 352, 340], fill=(6, 6, 8))
    d.rectangle([265, 190, 300, 220], fill=(20, 22, 28)); d.rectangle([370, 190, 405, 220], fill=(20, 22, 28))
    d.rectangle([262, 150, 408, 170], fill=(196, 52, 38))
    d.rectangle([0, 340, W, H], fill=(58, 56, 54))
    d.rectangle([300, 300, 340, 360], fill=(176, 120, 92))          # a warm, skin-ish block
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    a = np.asarray(im, np.float32) / 255
    return np.clip(a + rng.normal(0, 0.006, a.shape), 0, 1)


def lum(a):
    return (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2])[..., None]


def teal_orange(a):
    l = lum(a)
    shadow, high = np.clip(1 - l * 1.8, 0, 1), np.clip((l - 0.45) * 1.8, 0, 1)
    a = a + shadow * np.array([-0.10, 0.03, 0.10]) + high * np.array([0.12, 0.03, -0.12])
    return np.clip((a - 0.5) * 1.15 + 0.5, 0, 1)


def faded_film(a):
    a = 0.14 + a * 0.78                                   # lifted black, lowered white
    l = lum(a)
    a = l + (a - l) * (1 - 0.6 * np.clip((l - 0.6) * 2.5, 0, 1))   # highlights lose chroma
    a = a + np.array([0.03, 0.01, -0.03]) * np.clip(l - 0.4, 0, 1)
    return np.clip(a + rng.normal(0, 0.035, a.shape[:2])[..., None], 0, 1)


def bleach_bypass(a):
    l = lum(a)
    a = l + (a - l) * 0.35                                # desaturate
    a = (a - 0.5) * 1.9 + 0.45                            # hard contrast
    return np.clip(np.where(a < 0.12, a * 0.3, a), 0, 1)  # dense, crushed shadows


def mono(a):
    return np.repeat(lum(a), 3, -1)


def vignette_grain(a):
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)) / math.sqrt(2)
    a = a * (1 - 0.55 * r ** 2)[..., None]
    return np.clip(a + rng.normal(0, 0.04, a.shape[:2])[..., None], 0, 1)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "grade_demo"
    os.makedirs(out, exist_ok=True)
    base = scene()
    for name, f in [("0_neutral", lambda a: a), ("1_teal_orange", teal_orange), ("2_faded_film", faded_film),
                    ("3_bleach_bypass", bleach_bypass), ("4_mono", mono), ("5_vignette_grain", vignette_grain)]:
        Image.fromarray((f(base.copy()) * 255).astype(np.uint8)).save(f"{out}/{name}.png")
    print("wrote 6 graded versions to", out)
