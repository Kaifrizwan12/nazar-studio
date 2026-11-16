#!/usr/bin/env python3
"""
nazar-core/engine/qa_views.py: the design QA's looking-and-measuring methods, as a tool.

For a folder of finished slides it writes one QA sheet (full size, squinted greyscale, phone size) and measures what
qa_design.md says to check by eye:
  edges      how many distinct left edges the text sits on (3+ is "almost aligned": a fault)
  margins    the smallest gap from text to the canvas edge, as % of width (under 4% is crowded; text near the edge may clip)
  gaps       vertical gaps between text blocks against the block above (under 25% of its height is cramped)
  phone      the smallest text height when the slide is shown 360 px wide (under 9 px is hard to read)
It cannot judge concept, taste or hierarchy, and it cannot see lines that collide so completely they merge into one block (tight headline stacks look the same): look at the sheet. Findings are P2 (fix) or P3 (note); P1 needs eyes.

    python qa_views.py slides_folder [sheet.jpg | out_folder]     (default: slides_folder/qa_sheet.jpg)
"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "nazar-voiceprint", "engine"))
import layout  # noqa: E402


def measure(im):
    m = layout.ink(im); h, w = m.shape
    # merge words into lines (wide horizontal dilation); drop specks (dot-grid textures, grain) by size
    def tight(b):      # the merge pads each box; measure the ink itself
        sub = m[b[1]:b[3], b[0]:b[2]]; ys, xs = np.where(sub)
        return (b[0] + int(xs.min()), b[1] + int(ys.min()), b[0] + int(xs.max()) + 1, b[1] + int(ys.max()) + 1, b[4]) if len(ys) else b
    raw = [tight(b) for b in layout.components(layout.dilate_x(m, max(6, w // 28)))]
    lines = sorted([b for b in raw if (b[2] - b[0]) > 0.12 * w and 0.012 * h < (b[3] - b[1]) < 0.2 * h
                    and (b[2] - b[0]) > 1.6 * (b[3] - b[1])], key=lambda b: b[1])
    tiny = [b for b in raw if (b[2] - b[0]) > 0.08 * w and 0.006 * h < (b[3] - b[1]) <= 0.012 * h and (b[2] - b[0]) > 2 * (b[3] - b[1])]
    if not lines:
        return {"findings": [("P3", "no text found")]}
    out = []
    lefts = sorted(b[0] for b in lines)
    axes = [lefts[0]]
    for x in lefts[1:]:
        if x - axes[-1] > w * 0.02:
            axes.append(x)
    if len(axes) >= 3:
        out.append(("P2", f"text lines start on {len(axes)} different left edges ({', '.join(str(a) for a in axes[:5])} px): align to one axis or make the break deliberate"))
    body = [b for b in lines if (b[3] - b[1]) > 0.03 * h] or lines     # footers and handles are meant to sit low
    near = min(min(b[0], w - b[2], b[1], h - b[3]) for b in body) / w
    if near < 0.04:
        out.append(("P2", f"text comes within {near:.1%} of the canvas edge: crowded, and it may clip in a crop"))
    for a, b in zip(lines, lines[1:]):
        if b[1] < a[3] - 0.02 * h and not (b[0] >= a[2] or a[0] >= b[2]):
            out.append(("P1", f"text lines overlap by {a[3] - b[1]}px near y={b[1]}: a collision"))
            break
    for a, b in zip(lines, lines[1:]):      # a big block over a much smaller one is headline over subline
        ha, hb = a[3] - a[1], b[3] - b[1]
        if ha > 1.8 * hb and 0 <= b[1] - a[3] < 0.5 * hb:
            out.append(("P3", f"only {b[1] - a[3]}px between a {ha}px headline block and the {hb}px line under it: cramped"))
            break
    small = min(b[3] - b[1] for b in lines + tiny) * 360 / w
    if small < 9:
        out.append(("P2" if small < 7 else "P3", f"smallest text line is {small:.1f}px tall at phone width (360 px): hard to read"))
    return {"findings": out, "axes": len(axes), "min_edge_pct": round(near * 100, 1), "min_phone_px": round(small, 1)}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    folder = sys.argv[1]
    files = sorted(glob.glob(folder + "/*.png") + glob.glob(folder + "/*.jpg"))
    T = 300
    sheet = Image.new("RGB", (len(files) * T, int(T * 1.25) * 3), "white")
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB")
        h = int(T * 1.25)
        sheet.paste(im.resize((T, h)), (i * T, 0))
        sheet.paste(ImageOps.grayscale(im).filter(ImageFilter.GaussianBlur(im.width / 64)).convert("RGB").resize((T, h)), (i * T, h))
        ph = im.resize((180, int(180 * im.height / im.width)))
        sheet.paste(ph, (i * T + 60, 2 * h + 10))
        r = measure(im)
        print(os.path.basename(f))
        for lvl, msg in r["findings"] or [("ok", "no measurable faults")]:
            print(f"   [{lvl}] {msg}")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(folder, "qa_sheet.jpg")
    if os.path.isdir(out):          # a folder was given: write qa_sheet.jpg inside it
        out = os.path.join(out, "qa_sheet.jpg")
    sheet.save(out, quality=82)
    print("sheet:", out, "(rows: full size, squint greyscale, phone size). Look at it: hierarchy and concept are yours to judge.")
