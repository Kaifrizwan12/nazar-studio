#!/usr/bin/env python3
"""
nazar-colour/engine/palette_check.py: archive images -> palette -> checked.

Implements the colour kit's own rules (numpy + Pillow only):
  1. extract a palette from real source material: k-means in OKLab (perceptual),
     k-means++ init, several seeds, best kept; each colour gets hex, OKLCH, share
     and a role (ground = large and low-chroma, accent = small and high-chroma)
  2. WCAG 2.x contrast ratio for every pair (4.5:1 normal text, 3:1 large text/UI)
  3. colour-blind check: simulate protan / deutan / tritan (Machado, Oliveira &
     Fernandes 2009, severity 1.0, applied in linear RGB) and report any pair that
     collapses (OKLab distance under 0.04) for that viewer
  4. greyscale check: pairs whose lightness gap is too small to read without hue

APCA is deliberately not used: as of April 2026 its place in WCAG 3 is unresolved,
so WCAG 2.2 stays the compliance check (see references/colour.md section 4).

    python palette_check.py image_or_folder [--k 6] [--json]
"""
import json
import os
import sys

import numpy as np
from PIL import Image

EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
M_OK1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
M_OK2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
M_OK2I = np.array([[1.0, 0.3963377774, 0.2158037573], [1.0, -0.1055613458, -0.0638541728], [1.0, -0.0894841775, -1.2914855480]])
M_OK1I = np.array([[4.0767416621, -3.3077115913, 0.2309699292], [-1.2684380046, 2.6097574011, -0.3413193965], [-0.0041960863, -0.7034186147, 1.7076147010]])
# Machado et al. 2009, severity 1.0, linear RGB
SIM = {
    "protan (no red)": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
    "deutan (no green)": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
    "tritan (no blue)": np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]),
}


def to_linear(rgb):
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def from_linear(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def oklab(rgb):
    return np.cbrt(to_linear(np.asarray(rgb, float)) @ M_OK1.T) @ M_OK2.T


def from_oklab(lab):
    return from_linear((np.asarray(lab, float) @ M_OK2I.T) ** 3 @ M_OK1I.T)


def hexof(rgb):
    return "#%02X%02X%02X" % tuple(int(round(float(v) * 255)) for v in np.clip(rgb, 0, 1))


def luminance(rgb):
    r, g, b = to_linear(np.asarray(rgb, float))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def kmeans(x, k, seed, iters=30):
    rng = np.random.default_rng(seed)
    c = [x[rng.integers(len(x))]]
    for _ in range(1, k):
        d2 = np.min(((x[:, None] - np.array(c)[None]) ** 2).sum(-1), 1)
        c.append(x[rng.choice(len(x), p=d2 / d2.sum())])
    c = np.array(c)
    for _ in range(iters):
        lab = np.argmin(((x[:, None] - c[None]) ** 2).sum(-1), 1)
        new = np.array([x[lab == i].mean(0) if np.any(lab == i) else c[i] for i in range(k)])
        if np.allclose(new, c, atol=1e-5):
            break
        c = new
    return c, lab, ((x - c[lab]) ** 2).sum()


def load(path, side=200, per=3000):
    files = [path] if os.path.isfile(path) else sorted(os.path.join(path, f) for f in os.listdir(path) if os.path.splitext(f)[1].lower() in EXTS)
    rng = np.random.default_rng(0)
    px = []
    for f in files:
        im = Image.open(f).convert("RGB"); im.thumbnail((side, side))
        a = np.asarray(im, np.float32).reshape(-1, 3) / 255
        px.append(a[rng.choice(len(a), min(per, len(a)), replace=False)])
    return np.concatenate(px), len(files)


def palette(pixels, k=6):
    lab = oklab(pixels)
    c, lab_i, _ = min((kmeans(lab, k, s) for s in range(4)), key=lambda r: r[2])
    share = np.bincount(lab_i, minlength=k) / len(lab_i)
    out = []
    for i in np.argsort(-share):
        L, a, b = c[i]
        rgb = from_oklab(c[i])
        ch = float(np.hypot(a, b))
        out.append({"hex": hexof(rgb), "rgb": [float(v) for v in np.clip(rgb, 0, 1)], "share": round(float(share[i]), 3),
                    "oklch": [round(float(L), 3), round(ch, 3), round(float(np.degrees(np.arctan2(b, a)) % 360))],
                    "role": "ground" if share[i] > 0.3 and ch < 0.08 else "accent" if ch > 0.1 and share[i] < 0.15 else "support"})
    return out


def checks(pal):
    n = len(pal)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            a, b = pal[i], pal[j]
            cr = contrast(a["rgb"], b["rgb"])
            row = {"a": a["hex"], "b": b["hex"], "contrast": round(cr, 2),
                   "wcag": "AA text" if cr >= 4.5 else "large text / UI only" if cr >= 3 else "fails",
                   "grey_gap_L": round(abs(a["oklch"][0] - b["oklch"][0]), 3), "collapses_for": []}
            for name, M in SIM.items():
                sa, sb = from_linear(to_linear(np.array(a["rgb"])) @ M.T), from_linear(to_linear(np.array(b["rgb"])) @ M.T)
                if float(np.linalg.norm(oklab(sa) - oklab(sb))) < 0.04 <= float(np.linalg.norm(oklab(a["rgb"]) - oklab(b["rgb"]))):
                    row["collapses_for"].append(name)
            pairs.append(row)
    return pairs


def run(path, k=6):
    px, n = load(path)
    pal = palette(px, k)
    return {"n_images": n, "palette": pal, "pairs": checks(pal)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path"); ap.add_argument("--k", type=int, default=6); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = run(a.path, a.k)
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        print(f"{r['n_images']} images")
        for p in r["palette"]:
            print(f"  {p['hex']}  {p['share']*100:5.1f}%  OKLCH {p['oklch']}  {p['role']}")
        print("pairs:")
        for p in sorted(r["pairs"], key=lambda p: -p["contrast"])[:8]:
            print(f"  {p['a']} on {p['b']}: {p['contrast']}:1 {p['wcag']}" + (f"  COLLAPSES for {', '.join(p['collapses_for'])}" if p["collapses_for"] else ""))
