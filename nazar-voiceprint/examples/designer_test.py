#!/usr/bin/env python3
"""How a person designs: can the visual engines tell designers apart?

Input: a folder of posters named <designer>_<objectID>.jpg (fetch_met_designers.py).
For every poster the engines measure palette and tone, air, symmetry, thirds,
edge density, line weight variation, angularity, line vs fill, alignment,
columns and text share. Then:

  1. SIGNATURE: per feature, between-designer variance / within-designer
     variance (an F-style ratio). High = that feature is a designer's habit
     (stable within, different between). Low = it varies by poster, not by person.
  2. BLIND TEST: leave-one-out. Hide one poster, build each designer's centroid
     from the rest (standardised, using the habit-weighted features), and name
     the nearest. Report accuracy against chance (1 / number of designers).

This is the same habit-vs-genre logic the archive analyser uses on words, applied
to design. It measures the *measurable* layer; why a designer chose it comes
from the confirm loop.

    python designer_test.py posters_folder [--json]
"""
import json
import os
import sys
from collections import defaultdict

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import grade  # noqa: E402
import layout  # noqa: E402
import visual  # noqa: E402

FEATURES = ["lightness", "colourfulness", "contrast", "hue_families", "negative_space", "symmetry", "thirds_pull",
            "edge_density", "weight_x", "weight_y", "line_variation", "angularity", "line_vs_fill",
            "align_consistency", "text_share", "ink_coverage"]
EXTS = {".jpg", ".jpeg", ".png"}


def measure(path):
    im = Image.open(path).convert("RGB")
    im.thumbnail((700, 700))
    g = grade.analyse(im.copy())
    c = visual.composition(im)
    ln = visual.line_quality(im) or {"line_weight_variation": 0, "angularity": 0, "line_vs_fill": 0}
    lay = layout.analyse(im) or {"alignment_consistency": 0, "text_share_of_content": 0}
    return [g["look_stats"]["L_mean"], g["colourfulness"], g["contrast_total"], g["hue_families"],
            c["negative_space"], c["lr_symmetry"], c["thirds_pull"], c["edge_density"],
            c["weight_centre"][0], c["weight_centre"][1],
            ln["line_weight_variation"], ln["angularity"], ln["line_vs_fill"],
            lay["alignment_consistency"], lay["text_share_of_content"], 1 - c["negative_space"]]


def run(folder):
    by = defaultdict(list)
    for f in sorted(os.listdir(folder)):
        if os.path.splitext(f)[1].lower() in EXTS:
            by[f.split("_")[0]].append((f, measure(os.path.join(folder, f))))
    names = sorted(by)
    X = np.array([v for n in names for _, v in by[n]], float)
    y = np.array([n for n in names for _ in by[n]])
    files = [f for n in names for f, _ in by[n]]
    mu, sd = X.mean(0), X.std(0)
    sd[sd < 1e-9] = 1
    Z = (X - mu) / sd

    # 1 signature strength: between / within variance per feature
    F = []
    grand = Z.mean(0)
    for j, feat in enumerate(FEATURES):
        within = np.mean([Z[y == n, j].var() for n in names if (y == n).sum() > 1])
        between = np.mean([(Z[y == n, j].mean() - grand[j]) ** 2 for n in names])
        F.append({"feature": feat, "ratio": round(float(min(between / max(within, 1e-6), 99.0)), 2)})
    F.sort(key=lambda r: -r["ratio"])

    # 2 blind leave-one-out, using every feature weighted by its ratio (capped)
    w = np.array([min(r["ratio"], 6.0) for r in sorted(F, key=lambda r: FEATURES.index(r["feature"]))])
    correct, rows = 0, []
    for i in range(len(Z)):
        mask = np.ones(len(Z), bool); mask[i] = False
        # weights come only from the training posters, never the hidden one
        Zt, yt = Z[mask], y[mask]
        g_t = Zt.mean(0)
        ws = []
        for j in range(Z.shape[1]):
            within = np.mean([Zt[yt == n, j].var() for n in names if (yt == n).sum() > 1])
            between = np.mean([(Zt[yt == n, j].mean() - g_t[j]) ** 2 for n in names])
            ws.append(min(between / max(within, 1e-6), 6.0))
        ws = np.array(ws)
        cents = {n: Zt[yt == n].mean(0) for n in names}
        guess = min(names, key=lambda n: float(((Z[i] - cents[n]) ** 2 * ws).sum()))
        ok = guess == y[i]
        correct += ok
        rows.append({"file": files[i], "truth": y[i], "guess": guess, "right": bool(ok)})
    res = {"designers": {n: len(by[n]) for n in names}, "posters": len(Z), "signature": F,
           "blind_accuracy": round(correct / len(Z), 3), "chance": round(1 / len(names), 3), "attribution": rows}
    return res


if __name__ == "__main__":
    r = run(sys.argv[1])
    if "--json" in sys.argv:
        print(json.dumps(r, indent=2))
    else:
        print(f"{r['posters']} posters, designers: {r['designers']}")
        print(f"blind attribution: {r['blind_accuracy']:.0%} correct (chance {r['chance']:.0%})\n")
        print("strongest habits (between/within):")
        for s in r["signature"][:6]:
            print(f"  {s['feature']:20} {s['ratio']}")
        print("weakest (vary poster to poster):")
        for s in r["signature"][-3:]:
            print(f"  {s['feature']:20} {s['ratio']}")
        for a in r["attribution"]:
            print(("  ok  " if a["right"] else "  MISS"), a["file"], "->", a["guess"])
