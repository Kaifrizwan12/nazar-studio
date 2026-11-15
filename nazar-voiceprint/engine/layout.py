#!/usr/bin/env python3
"""
nazar-voiceprint/engine/layout.py: a graphic designer's layout habits, OCR-free
(numpy + Pillow only).

  1. ink mask -> run-based connected components (union-find on row runs)
  2. merge glyphs into text lines (horizontal closing), lines into blocks
  3. per piece: alignment consistency (share of element edges on a line shared
     with another element, the idea in LayoutRectifier, Shen, Shamir & Igarashi,
     arXiv 2508.11177), dominant alignment (left / centre / right), column
     count and gutter, margins, type scale (distinct text-line heights and the
     ratio between them, matched to named modular scales), text vs. image share

No OCR, so it measures text *lines* by shape, not words. Font names aren't
guessed (DeepFont manages ~80% top-5, not reliable enough to state): ask the
designer which typefaces they use.

    python layout.py image_or_folder [--json]
"""
import json
import os

import numpy as np
from PIL import Image

EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
SCALES = {"minor third 1.2": 1.2, "major third 1.25": 1.25, "perfect fourth 1.333": 1.333,
          "augmented fourth 1.414": 1.414, "perfect fifth 1.5": 1.5, "golden 1.618": 1.618, "octave 2.0": 2.0}


def _otsu_levels(g):
    hist = np.bincount(g.ravel(), minlength=256).astype(float)
    w = np.cumsum(hist); mu = np.cumsum(hist * np.arange(256))
    with np.errstate(divide="ignore", invalid="ignore"):
        between = (mu[-1] * w - mu * w[-1]) ** 2 / (w * (w[-1] - w))
    return int(np.nanargmax(between[:-1]))


def ink(im, side=1300):
    im = im.convert("L")
    im.thumbnail((side, side))
    g = np.asarray(im, np.uint8)
    t = _otsu_levels(g)
    bg = np.median(np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]]))
    return (g <= t) if bg > t else (g > t)


def dilate_x(m, k):
    out = m.copy()
    for s in range(1, k + 1):
        out[:, s:] |= m[:, :-s]; out[:, :-s] |= m[:, s:]
    return out


def dilate_y(m, k):
    out = m.copy()
    for s in range(1, k + 1):
        out[s:] |= m[:-s]; out[:-s] |= m[s:]
    return out


def components(mask):
    """Union-find over horizontal runs; returns bounding boxes (x0, y0, x1, y1, area)."""
    parent = []

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i

    runs_prev, runs_all = [], []
    for y, row in enumerate(mask):
        d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
        starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
        runs_cur = []
        for s, e in zip(starts, ends):
            idx = len(parent); parent.append(idx)
            for ps, pe, pidx in runs_prev:
                if ps < e and s < pe:   # overlap (4-connected)
                    a, b = find(idx), find(pidx)
                    if a != b:
                        parent[a] = b
            runs_cur.append((s, e, idx)); runs_all.append((y, s, e, idx))
        runs_prev = runs_cur
    boxes = {}
    for y, s, e, idx in runs_all:
        r = find(idx)
        b = boxes.get(r)
        if b is None:
            boxes[r] = [s, y, e, y + 1, e - s]
        else:
            b[0] = min(b[0], s); b[1] = min(b[1], y); b[2] = max(b[2], e); b[3] = max(b[3], y + 1); b[4] += e - s
    return [tuple(b) for b in boxes.values()]


def cluster_1d(vals, tol):
    vals = sorted(vals)
    groups = []
    for v in vals:
        if groups and v - groups[-1][-1] <= tol:
            groups[-1].append(v)
        else:
            groups.append([v])
    return groups


def analyse(im):
    m = ink(im)
    h, w = m.shape
    if m.mean() < 0.001:
        return None
    lines = [b for b in components(dilate_x(m, max(3, w // 90))) if b[4] > 12]
    # text-like: wide, not too tall, moderately filled
    text = [b for b in lines if (b[2] - b[0]) > 2.2 * (b[3] - b[1]) and (b[3] - b[1]) < h * 0.12]
    other = [b for b in lines if b not in text and (b[2] - b[0]) * (b[3] - b[1]) > 0.002 * w * h]
    elems = text + other
    if not elems:
        return None
    tol = max(2, w // 100)
    shared = 0
    align_votes = {"left": 0, "centre": 0, "right": 0}
    for name, key in (("left", lambda b: b[0]), ("centre", lambda b: (b[0] + b[2]) / 2), ("right", lambda b: b[2])):
        groups = cluster_1d([key(b) for b in elems], tol)
        on_shared = sum(len(g) for g in groups if len(g) >= 2)
        align_votes[name] = on_shared
        shared = max(shared, on_shared)
    dominant = max(align_votes, key=align_votes.get)
    # columns only mean something on a left/right axis; centred lines' left edges
    # line up by coincidence
    lefts = cluster_1d([b[0] for b in elems], tol) if dominant != "centre" else []
    cols = [g for g in lefts if len(g) >= 3]
    col_x = sorted(np.mean(g) for g in cols)
    gutters = [b - a for a, b in zip(col_x, col_x[1:])]
    x0, y0 = min(b[0] for b in elems), min(b[1] for b in elems)
    x1, y1 = max(b[2] for b in elems), max(b[3] for b in elems)
    # type size from the x-height band (dense core rows), not the line box: a box
    # grows with whatever ascenders/descenders that line happens to contain
    # type size = ascender top to baseline: ignores descenders (g, p, y), which
    # are the main reason line boxes differ within one size
    heights = []
    for b in text:
        prof = m[b[1]:b[3], b[0]:b[2]].sum(1)
        if prof.max() > 0:
            dense = np.where(prof > 0.45 * prof.max())[0]
            top = np.where(prof > 0.04 * prof.max())[0][0]
            heights.append(int(dense[-1] - top + 1))
    if heights:   # drop slivers (rules, broken fragments) far below the typical line
        floor = max(6, 0.4 * float(np.median(heights)))
        heights = [x for x in heights if x >= floor]
    # cluster in log space: a type scale is a ratio, so "same size" is a % band
    levels = [float(np.exp(np.median(g))) for g in cluster_1d(list(np.log(heights)), np.log(1.09))] if heights else []
    levels = [l for l in levels if l >= 4]
    ratios = [b / a for a, b in zip(levels, levels[1:]) if a > 0]
    scale = None
    if ratios:
        r = float(np.median(ratios))
        name = min(SCALES, key=lambda k: abs(SCALES[k] - r))
        scale = {"median_step": round(r, 3), "nearest_named": name if abs(SCALES[name] - r) < 0.08 else "none close"}
    text_area = sum((b[2] - b[0]) * (b[3] - b[1]) for b in text)
    other_area = sum((b[2] - b[0]) * (b[3] - b[1]) for b in other)
    return {
        "elements": len(elems), "text_lines": len(text),
        "alignment_consistency": round(shared / len(elems), 3),
        "dominant_alignment": dominant,
        "columns": len(cols),
        "gutter_ratio": round(float(np.median(gutters)) / w, 3) if gutters else None,
        "margins": {"left": round(float(x0) / w, 3), "right": round(float(w - x1) / w, 3), "top": round(float(y0) / h, 3), "bottom": round(float(h - y1) / h, 3)},
        "type_levels": len(levels),
        "type_scale": scale,
        "text_share_of_content": round(float(text_area) / max(text_area + other_area, 1), 3),
    }


def reading(r):
    if not r:
        return ["no layout found"]
    out = [f"{r['dominant_alignment']}-aligned; {r['alignment_consistency']:.0%} of elements share an edge with another"]
    out.append(f"{r['columns']}-column structure" if r["columns"] >= 2 else
               "single centred axis" if r["dominant_alignment"] == "centre" else "single axis, no column grid")
    m = r["margins"]
    if min(m.values()) > 0.08:
        out.append("generous margins all round")
    if abs(m["left"] - m["right"]) > 0.05:
        out.append("asymmetric side margins")
    if r["type_scale"] and r["type_scale"]["nearest_named"] != "none close":
        out.append(f"type steps ~{r['type_scale']['median_step']} ({r['type_scale']['nearest_named']}) across {r['type_levels']} sizes")
    out.append("type-led" if r["text_share_of_content"] > 0.6 else "image/shape-led" if r["text_share_of_content"] < 0.3 else "balanced type and image")
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    files = [a.path] if os.path.isfile(a.path) else sorted(
        os.path.join(a.path, f) for f in os.listdir(a.path) if os.path.splitext(f)[1].lower() in EXTS)
    res = {}
    for f in files:
        r = analyse(Image.open(f))
        res[os.path.basename(f)] = {"layout": r, "reading": reading(r)}
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for k, v in res.items():
            print(f"\n{k}\n  {v['layout']}")
            for line in v["reading"]:
                print("  -", line)
