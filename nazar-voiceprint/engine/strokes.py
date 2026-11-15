#!/usr/bin/env python3
"""
nazar-voiceprint/engine/strokes.py: skeleton-based stroke analysis for
illustrators (numpy + Pillow only).

Follows the per-stroke descriptor idea in Shaheen et al., "Stroke Authorship
Recognition" (CGF 2016): skeletonise the ink, split at junctions, measure every
stroke segment, and describe the drawing by the distributions.

  - Zhang & Suen (1984) thinning -> one-pixel skeleton
  - endpoints (1 neighbour) and junctions (3+) -> segments between them
  - per segment: length, straightness (chord / path), orientation,
    width profile along the stroke (min horizontal/vertical ink run at each
    skeleton pixel, a cheap stand-in for the Stroke Width Transform),
    taper (end width / middle width) and pressure swing (width CV along it)

What it says about a hand: many short, broken segments with lots of endpoints
= sketchy, searching line; long continuous segments = confident line; taper
< 1 = pressure-sensitive pen or brush; flat taper and low swing = technical
pen or vector stroke.

    python strokes.py image_or_folder [--json]
"""
import json
import os
import sys
from collections import deque

import numpy as np
from PIL import Image

EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
N8 = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]  # P2..P9 clockwise


def _otsu(g):
    hist = np.bincount((g * 255).astype(np.uint8).ravel(), minlength=256).astype(float)
    w = np.cumsum(hist); mu = np.cumsum(hist * np.arange(256))
    with np.errstate(divide="ignore", invalid="ignore"):
        between = (mu[-1] * w - mu * w[-1]) ** 2 / (w * (w[-1] - w))
    return np.nanargmax(between[:-1]) / 255


def ink_mask(im, side=512):
    im = im.convert("L")
    im.thumbnail((side, side))
    g = np.asarray(im, np.float32) / 255
    bg = np.median(np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]]))
    gi, ti = np.rint(g * 255), round(_otsu(g) * 255)   # compare whole levels: float32 vs float64 at k/255 misfires
    return (gi <= ti) if bg > 0.5 else (gi > ti)


def _neighbours(b):
    p = np.pad(b, 1)
    h, w = b.shape
    return [p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dy, dx in N8]


def zhang_suen(mask):
    """Zhang & Suen (1984), vectorised."""
    img = mask.copy().astype(np.uint8)
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            P = _neighbours(img)
            B = sum(P)
            seq = P + [P[0]]
            A = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(np.uint8) for i in range(8))
            p2, p3, p4, p5, p6, p7, p8, p9 = P
            if step == 0:
                c1, c2 = p2 * p4 * p6, p4 * p6 * p8
            else:
                c1, c2 = p2 * p4 * p8, p2 * p6 * p8
            kill = (img == 1) & (B >= 2) & (B <= 6) & (A == 1) & (c1 == 0) & (c2 == 0)
            if kill.any():
                img[kill] = 0
                changed = True
    return img.astype(bool)


def _runs(mask):
    out = np.zeros(mask.shape, np.int32)
    for i, row in enumerate(mask):
        d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
        for s, e in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
            out[i, s:e] = e - s
    return out


def segments(skel):
    nb = sum(n.astype(np.uint8) for n in _neighbours(skel)) * skel
    junction = _junctions(skel)
    body = skel & ~_dilate(junction, 1)   # cut the ring too: at a "+" the arm tips touch diagonally
    pts = set(zip(*np.nonzero(body)))
    segs = []
    while pts:
        start = next(iter(pts))
        # walk out to an end of this component, then order the path from there
        comp, q = {start}, deque([start])
        while q:
            y, x = q.popleft()
            for dy, dx in N8:
                n = (y + dy, x + dx)
                if n in pts and n not in comp:
                    comp.add(n); q.append(n)
        pts -= comp
        ends = [p for p in comp if sum((p[0] + dy, p[1] + dx) in comp for dy, dx in N8) <= 1]
        first = ends[0] if ends else start
        order, seen, cur = [first], {first}, first
        while True:
            nxt = [(cur[0] + dy, cur[1] + dx) for dy, dx in N8 if (cur[0] + dy, cur[1] + dx) in comp and (cur[0] + dy, cur[1] + dx) not in seen]
            if not nxt:
                break
            cur = nxt[0]; order.append(cur); seen.add(cur)
        segs.append(order)
    return segs, int(junction.sum()), int((skel & (nb == 1)).sum())


def _degree(skel):
    return sum(n.astype(np.uint8) for n in _neighbours(skel)) * skel


def _junctions(skel):
    """True forks: crossing number (0->1 transitions around the 8-neighbourhood)
    of 3+. Counting raw neighbours instead flags every staircase step on a
    diagonal line as a fake junction."""
    P = [n.astype(np.uint8) for n in _neighbours(skel)]
    seq = P + [P[0]]
    A = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(np.uint8) for i in range(8))
    return skel & (A >= 3)


def _dilate(mask, r):
    out = mask.copy()
    for _ in range(r):
        out = out | np.any(np.stack(_neighbours(out)), axis=0)
    return out


def prune_spurs(skel, k, rounds=2):
    """Thick strokes thin into a main line plus short side-spurs at their
    ends and bends. A spur = a short segment that runs from a loose end into a
    junction. Remove those (isolated short marks are kept: they're real)."""
    skel = skel.copy()
    for _ in range(rounds):
        nb = _degree(skel)
        ends, junction = skel & (nb == 1), _junctions(skel)
        near_j = _dilate(junction, 1)
        segs, _, _ = segments(skel)
        removed = False
        for s in segs:
            if len(s) >= k:
                continue
            a, b = s[0], s[-1]
            if (ends[a] or ends[b]) and (near_j[a] or near_j[b]) and not (ends[a] and ends[b]):
                for y, x in s:
                    skel[y, x] = False
                removed = True
        if not removed:
            break
    return skel


def analyse(im):
    ink = ink_mask(im)
    if ink.mean() < 0.002:
        return None
    width = np.minimum(_runs(ink), _runs(ink.T).T).astype(float)
    skel0 = zhang_suen(ink)
    typical_w = float(np.median(width[skel0])) if skel0.any() else 2.0
    skel = prune_spurs(skel0, k=max(10, int(2.5 * typical_w)))
    segs, n_junctions, n_ends = segments(skel)
    # at crossings both ink runs span whole lines, so "width" explodes there:
    # never sample width within reach of a junction
    near_j = _dilate(_junctions(skel), max(3, int(typical_w)))
    rows = []
    for s in segs:
        if len(s) < 6:
            continue
        a = np.array(s, float)
        steps = np.hypot(*np.diff(a, axis=0).T)
        path = float(steps.sum()) or 1.0
        chord = float(np.hypot(*(a[-1] - a[0])))
        w = np.array([width[y, x] for y, x in s if not near_j[y, x]], float)
        if len(w) < 6:
            w = np.array([width[y, x] for y, x in s], float)
        med = np.median(w)
        w = np.clip(w, 0, 3 * med)                       # robust to stray long runs
        k = max(2, len(w) // 6)
        mid = np.median(w[k:-k]) if len(w) > 2 * k else med
        taper = (np.median(w[:k]) + np.median(w[-k:])) / 2 / max(mid, 1e-6)
        c = a - a.mean(0)
        _, vec = np.linalg.eigh(c.T @ c)
        ang = (np.degrees(np.arctan2(-vec[0, -1], vec[1, -1])) % 180)
        rows.append((path, min(chord / path, 1.0), ang, taper, w.std() / max(w.mean(), 1e-6)))
    if not rows:
        return None
    L, straight, ang, taper, swing = (np.array(c) for c in zip(*rows))
    hist, _ = np.histogram(ang, bins=12, range=(0, 180), weights=L)
    p = hist / max(hist.sum(), 1)
    concentration = float(1 - (-(p[p > 0] * np.log(p[p > 0])).sum() / np.log(12)))
    skel_px = max(int(skel.sum()), 1)
    return {
        "segments": len(rows),
        "median_segment_px": int(np.median(L)),
        "segment_length_cv": round(float(L.std() / L.mean()), 2),
        "straightness": round(float(np.average(straight, weights=L)), 3),   # 1 = ruler-straight
        "taper": round(float(np.median(taper)), 3),                         # <1 = thinner at the ends
        "pressure_swing": round(float(np.median(swing)), 3),                # width CV along each stroke
        "direction_concentration": round(concentration, 3),
        "dominant_direction_deg": int(np.argmax(hist) * 15 + 7),
        "endpoints_per_1k_px": round(n_ends * 1000 / skel_px, 1),          # high = sketchy, broken line
        "junctions_per_1k_px": round(n_junctions * 1000 / skel_px, 1),
    }


def reading(r):
    out = []
    out.append("sketchy, searching line (many short strokes, lots of loose ends)" if r["endpoints_per_1k_px"] > 25 else
               "confident, continuous line" if r["endpoints_per_1k_px"] < 8 else "mixed: some long strokes, some searching marks")
    out.append("tapered strokes: pressure-sensitive pen or brush" if r["taper"] < 0.85 else
               "blunt, even strokes: technical pen or vector" if r["taper"] > 1.05 and r["pressure_swing"] < 0.25 else
               "slight taper")
    out.append("curvy, organic line" if r["straightness"] < 0.75 else "straight, ruled line" if r["straightness"] > 0.93 else "mix of curves and straights")
    if r["direction_concentration"] > 0.2:
        out.append(f"strokes lean one way (around {r['dominant_direction_deg']}°): a hatching or gesture habit")
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
        res[os.path.basename(f)] = {"strokes": r, "reading": reading(r) if r else ["no line work found"]}
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for k, v in res.items():
            print(f"\n{k}\n  {v['strokes']}")
            for line in v["reading"]:
                print("  -", line)
