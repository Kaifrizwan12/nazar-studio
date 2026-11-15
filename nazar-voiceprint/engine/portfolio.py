#!/usr/bin/env python3
"""
nazar-voiceprint/engine/portfolio.py: point the whole visual stack at a
portfolio folder and get one reading, layer by layer.

Runs: palette + composition (visual.py), grading and effects (grade.py),
line and stroke (strokes.py), layout and type (layout.py), camera habits
(exif_habits.py), style modes and recurring elements (cluster.py), and pose
(pose.py, only if rtmlib is installed).

A single image's look is confounded by its content (a white sky looks like
"desaturated highlights"; a scene with no blacks looks "faded"). So a look only
becomes a HABIT when it appears in at least 60% of pieces; 30-60% is "sometimes";
below that it's left out. Feature values are reported as mean +/- spread.

    python portfolio.py folder [--json]
"""
import json
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cluster  # noqa: E402
import exif_habits  # noqa: E402
import grade  # noqa: E402
import layout  # noqa: E402
import strokes  # noqa: E402
import visual  # noqa: E402

EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def tally(lists, n):
    c = Counter(x for l in lists for x in set(l))
    return {"habit": [k for k, v in c.items() if v / n >= 0.6],
            "sometimes": [k for k, v in c.items() if 0.3 <= v / n < 0.6]}


def run(folder):
    files = sorted(os.path.join(folder, f) for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in EXTS)
    if not files:
        sys.exit(f"no images in {folder}")
    imgs = []
    for f in files:
        im = Image.open(f).convert("RGB")
        im.thumbnail((1300, 1300))
        imgs.append((os.path.basename(f), im))
    n = len(imgs)
    small = [(nm, im.copy()) for nm, im in imgs]
    for _, im in small:
        im.thumbnail((256, 256))

    pal = visual.palette(small)
    comps = [dict(file=nm, **visual.composition(im), line=visual.line_quality(im), tone=visual.tone(im)) for nm, im in small]
    comp_summary = visual.summarise(comps)
    grades = [grade.analyse(im) for _, im in imgs]
    stroke_rows = [strokes.analyse(im) for _, im in imgs]
    layout_rows = [layout.analyse(im) for _, im in imgs]
    stroke_ok = [r for r in stroke_rows if r]
    layout_ok = [r for r in layout_rows if r]

    report = {
        "n_pieces": n,
        "palette": pal,
        "composition": visual.read_plain(comp_summary, pal),
        "grading": tally([g["looks"] for g in grades], n),
        "line": tally([strokes.reading(r) for r in stroke_ok], max(len(stroke_ok), 1)) if stroke_ok else None,
        "layout": tally([layout.reading(r) for r in layout_ok], max(len(layout_ok), 1)) if layout_ok else None,
        "camera": exif_habits.reading(exif_habits.habits(folder)),
        "modes_and_reuse": cluster.run(folder) if n >= 3 else None,
    }
    try:
        import rtmlib  # noqa: F401
        import pose
        report["pose"] = pose.reading(pose.summarise(pose.detect_folder(folder)))
    except ImportError:
        report["pose"] = ['skipped: pip install "onnxruntime==1.23.2" rtmlib to read pose habits']
    return report


def show(r):
    print(f"\n{r['n_pieces']} pieces\n")
    print("PALETTE:", ", ".join(f"{p['hex']} {p['share']*100:.0f}% {p['role']}" for p in r["palette"]))
    print("\nCOMPOSITION & TONE:"); [print("  -", x) for x in r["composition"]]
    for layer in ("grading", "line", "layout"):
        t = r.get(layer)
        if not t:
            continue
        print(f"\n{layer.upper()}:")
        for x in t["habit"]:
            print("  HABIT     ", x)
        for x in t["sometimes"]:
            print("  sometimes ", x)
        if not t["habit"] and not t["sometimes"]:
            print("  no consistent habit (changes piece to piece)")
    print("\nCAMERA:"); [print("  -", x) for x in r["camera"]]
    m = r.get("modes_and_reuse")
    if m and m["style_modes"]:
        sm = m["style_modes"]
        print(f"\nSTYLE MODES: {sm['n_modes']}")
        for md in sm["modes"]:
            print(f"  mode {md['mode']} ({len(md['pieces'])} pieces): {', '.join(md['sets_it_apart'])}")
        for e in m["recurring_elements"][:3]:
            print(f"  recurring element in {e['count']} pieces")
    print("\nPOSE:"); [print("  -", x) for x in r["pose"]]
    print("\nConfirm every line with the maker. Motifs, meaning and intent come from them, not from this.")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = run(a.folder)
    if a.json:
        print(json.dumps(r, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    else:
        show(r)
