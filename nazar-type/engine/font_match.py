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


def ink_mask(im):
    a = np.asarray(im.convert("RGB"), float)
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(edge, 0)
    d = np.linalg.norm(a - bg, axis=2)
    m = d > max(40, 0.35 * d.max())
    ys, xs = np.where(m)
    if len(ys) == 0:
        raise SystemExit("no text found in the crop")
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def render(text, path, index):
    try:
        f = ImageFont.truetype(path, 220, index=index)
        l, t, r, b = f.getbbox(text)
        if r - l < 20 or b - t < 20:
            return None
        im = Image.new("L", (r - l + 40, b - t + 40), 0)
        ImageDraw.Draw(im).text((20 - l, 20 - t), text, font=f, fill=255)
    except Exception:          # broken or unsupported font file: skip it
        return None
    m = np.asarray(im) > 128
    ys, xs = np.where(m)
    if len(ys) == 0:
        return None
    return f, m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def fit(m):
    return np.asarray(Image.fromarray((m * 255).astype("uint8")).resize((N, N), Image.BILINEAR)) > 128


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
    target = ink_mask(Image.open(crop_path))
    t_ar = target.shape[1] / target.shape[0]
    tf = fit(target)
    rows = []
    for p in candidates(extra):
        idx = 0
        while idx < 24:
            r = render(text, p, idx)
            if r is None:
                break
            f, m = r
            ar = m.shape[1] / m.shape[0]
            g = fit(m)
            iou = float((g & tf).sum() / max((g | tf).sum(), 1))
            pen = float(np.exp(-3 * abs(np.log(ar / t_ar))))
            try:
                name = " ".join(f.getname())
            except Exception:
                name = os.path.basename(p)
            rows.append((iou * pen, iou, ar / t_ar, name, os.path.basename(p)))
            idx += 1
            if not p.lower().endswith(".ttc"):
                break
    rows.sort(reverse=True)
    uniq, seen = [], set()
    for r in rows:
        if r[3] not in seen:
            seen.add(r[3]); uniq.append(r)
    return uniq[:top], len(rows)


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
    print("verdict:", verdict(rows))
