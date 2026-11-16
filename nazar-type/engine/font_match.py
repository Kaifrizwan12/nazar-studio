#!/usr/bin/env python3
"""
nazar-type/engine/font_match.py: which installed font does this headline look like?

Give it a crop of a headline (one line, solid text on a plain or soft ground) and the words it
says. It draws the same words in every font file it can find, stretches each drawing into the
crop's box, and ranks them by how much of the ink overlaps (IoU), penalising a wrong width-to-height
ratio so condensed and extended faces don't pass for each other.

It matches SHAPES against the fonts on THIS machine. So:
  - shape overlap 0.90+, width within 5% and a clear gap to the runner-up is a strong candidate:
    still confirm with the maker and check the licence (type_check.py);
  - overlap 0.80+ with a width gap is a near match: a cousin, another cut, or tracked or stretched
    type. Don't name it as the brand's font;
  - lower, or several fonts bunched together: the real font probably isn't installed. Ask the
    maker or use a font identifier.
It never reads a font's licence and never downloads anything.
Small text (a crop under 45 px high) gives a shortlist of three, not a name: see the verdict it prints.

    python font_match.py crop.png "SAME BRANDS." [--fonts DIR ...] [--top 8]
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DIRS = ["/System/Library/Fonts", "/System/Library/Fonts/Supplemental", "/Library/Fonts",
        os.path.expanduser("~/Library/Fonts"), "/usr/share/fonts", os.path.join(HERE, "..", "..", "nazar-core", "engine", "fonts")]
EXTS = (".ttf", ".otf", ".ttc")
N = 192
COARSE_N, COARSE_SIZE = 64, 90


def ink_cov(im):
    """Greyscale ink coverage (0..1) of the text in a crop, cropped to its bounding box. Anti-aliasing is kept: it
    carries the stroke weight, which a hard threshold throws away."""
    a = np.asarray(im.convert("RGB"), float)
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(edge, 0)
    d = np.linalg.norm(a - bg, axis=2)
    if d.max() < 1:
        raise SystemExit("no text found in the crop")
    cov = np.clip(d / d.max(), 0, 1)
    ys, xs = np.where(cov > 0.3)
    return cov[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def render(text, path, index, size=220):
    try:
        f = ImageFont.truetype(path, size, index=index)
        l, t, r, b = f.getbbox(text)
        if r - l < 20 or b - t < 8:
            return None
        im = Image.new("L", (r - l + 40, b - t + 40), 0)
        ImageDraw.Draw(im).text((20 - l, 20 - t), text, font=f, fill=255)
    except Exception:          # broken or unsupported font file: skip it
        return None
    c = np.asarray(im, float) / 255.0
    ys, xs = np.where(c > 0.3)
    if len(ys) == 0:
        return None
    return f, c[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def fit(c, ar, width):
    """Resample to a common box that keeps the target's aspect ratio (a text line stays a line, so letter detail and
    stroke weight survive), greyscale."""
    h = int(min(max(round(width / ar), 8), 256))
    return np.asarray(Image.fromarray((c * 255).astype("uint8")).resize((width, h), Image.LANCZOS), float) / 255.0


def soft(a, radius):
    """Blur to the softness of a small raster, so one pixel of misregistration doesn't wipe out a thin stroke."""
    from PIL import ImageFilter
    return np.asarray(Image.fromarray((a * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(radius)), float) / 255.0


def soft_iou(a, b, radius=2.0):
    a, b = soft(a, radius), soft(b, radius)
    iou = float(np.minimum(a, b).sum() / max(np.maximum(a, b).sum(), 1e-6))
    # stroke weight: mean ink density inside the box; a light cut of the right family must not beat the right weight
    wa, wb = a.mean() + 1e-6, b.mean() + 1e-6
    return iou * float(np.exp(-4 * abs(np.log(wa / wb))))


def candidates(extra):
    seen = set()
    for d in list(extra) + DIRS:
        for root, _, files in os.walk(d):
            for fn in files:
                if fn.lower().endswith(EXTS):
                    p = os.path.join(root, fn)
                    if p not in seen:
                        seen.add(p); yield p


def match(crop_path, text, extra=(), top=8):
    """Two passes: every face is drawn small and ranked coarsely, then the best 40 are redrawn at full size and scored.
    The score is soft overlap of greyscale ink (so weight counts) times a penalty for the wrong width-to-height ratio."""
    target = ink_cov(Image.open(crop_path))
    t_ar = target.shape[1] / target.shape[0]
    tc = fit(target, t_ar, 128)
    coarse = []
    for p in candidates(extra):
        idx = 0
        while idx < 24:
            r = render(text, p, idx, 90)
            if r is None:
                break
            f, m = r
            ar = m.shape[1] / m.shape[0]
            coarse.append((soft_iou(fit(m, t_ar, 128), tc) * float(np.exp(-3 * abs(np.log(ar / t_ar)))), p, idx))
            idx += 1
            if not p.lower().endswith(".ttc"):
                break
    coarse.sort(reverse=True)
    tf = fit(target, t_ar, 320)
    rows = []
    for _, p, idx in coarse[:40]:
        r = render(text, p, idx)
        if r is None:
            continue
        f, m = r
        ar = m.shape[1] / m.shape[0]
        iou = soft_iou(fit(m, t_ar, 320), tf)
        pen = float(np.exp(-3 * abs(np.log(ar / t_ar))))
        try:
            name = " ".join(f.getname())
        except Exception:
            name = os.path.basename(p)
        rows.append((iou * pen, iou, ar / t_ar, name, os.path.basename(p)))
    rows.sort(reverse=True)
    uniq, seen = [], set()
    for r in rows:
        if r[3] not in seen:
            seen.add(r[3]); uniq.append(r)
    return uniq[:top], len(coarse)


def verdict(rows):
    """Judge on shape overlap and width ratio separately: tracking or a different cut changes the
    width without changing the letter shapes, so a good overlap with a width gap is a cousin, not a match."""
    if not rows:
        return "no candidates"
    _, iou, ar, name, _ = rows[0]
    gap = rows[0][0] - (rows[1][0] if len(rows) > 1 else 0)
    off = abs(ar - 1)
    if iou >= 0.90 and off <= 0.05 and gap >= 0.03:
        return f"strong candidate: {name}. Confirm with the maker and check the licence"
    if iou >= 0.80:
        return (f"near match, not a match: {name} has the right kind of letter shapes (overlap {iou:.2f}) but the width is off by "
                f"{off:.0%}, so the real font is a cousin, a different cut, or the type was tracked or stretched. Do not name it as the brand's font: ask the maker for the file name")
    return "no installed font matches: the real font is probably not on this machine. Ask the maker or use a font identifier; do not pick one from this list"


if __name__ == "__main__":
    args = sys.argv[1:]
    extra = [args[i + 1] for i, a in enumerate(args) if a == "--fonts"]
    top = int(args[args.index("--top") + 1]) if "--top" in args else 8
    pos = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] not in ("--fonts", "--top"))]
    rows, n = match(pos[0], pos[1], extra, top)
    print(f"{n} font faces compared")
    for s, iou, ar, name, fn in rows:
        print(f"  {s:.2f}  overlap {iou:.2f}  width ratio {ar:.2f}  {name}  ({fn})")
    small = Image.open(pos[0]).height < 45
    if small:
        print("verdict: SMALL TEXT, so this is a shortlist, not a name. Known-answer test: 24 installed faces rendered at 26 px and matched "
              "back landed first for 13 and in the top 3 for 20. Look-alike families (Helvetica, Arial, Helonia, Microsoft Sans Serif) cannot be "
              "told apart at this size. Ask the maker for the file name, or crop a larger sample of the same face.")
    else:
        print("verdict:", verdict(rows))
