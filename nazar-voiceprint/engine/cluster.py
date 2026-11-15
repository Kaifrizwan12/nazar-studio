#!/usr/bin/env python3
"""
nazar-voiceprint/engine/cluster.py: sort a portfolio into its style "modes"
and find elements that recur across pieces (numpy + Pillow only).

Modes: every piece becomes a feature vector (grading look stats, colourfulness,
contrast, air, symmetry, edge density, line weight variation, angularity,
line-vs-fill), standardised, then k-means for k = 1..4 with k chosen by
silhouette score. Each mode is described by the features that set it apart.
Why it matters: most creatives have 2-3 modes (client work vs personal work,
day vs night shoots). A pattern built on the average of two modes describes
neither, so the person picks which mode the pattern is for.

Recurring elements: difference-hash (dHash) of a grid of tiles in every piece;
tiles whose hashes match across different pieces are reused elements (a mark,
an icon, a texture). This finds near-literal reuse, not semantic motifs ("the
eye shows up as a hidden detail"): those need embeddings (optional, with
open_clip installed) or, better, the maker telling you.

Embeddings group style well (CLIP+MLP ~73% artist accuracy over 372 artists)
but make errors experts reject (KU Leuven, arXiv 2409.03521): use them to
group, never to judge identity.

    python cluster.py folder [--json]
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade  # noqa: E402
import visual  # noqa: E402

EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
FEATURES = ["L_mean", "L_std", "a_mean", "b_mean", "colourfulness", "contrast", "air", "symmetry",
            "edge_density", "line_weight_variation", "angularity", "line_vs_fill"]


def features(im):
    g = grade.analyse(im)
    c = visual.composition(im.convert("RGB"))
    ln = visual.line_quality(im.convert("RGB")) or {"line_weight_variation": 0, "angularity": 0, "line_vs_fill": 0}
    ls = g["look_stats"]
    return [ls["L_mean"], ls["L_std"], ls["a_mean"], ls["b_mean"], g["colourfulness"], g["contrast_total"],
            c["negative_space"], c["lr_symmetry"], c["edge_density"],
            ln["line_weight_variation"], ln["angularity"], ln["line_vs_fill"]]


def kmeans(X, k, seeds=8, iters=50):
    best = None
    for s in range(seeds):
        rng = np.random.default_rng(s)
        C = X[rng.choice(len(X), k, replace=False)]
        for _ in range(iters):
            lab = np.argmin(((X[:, None] - C[None]) ** 2).sum(-1), 1)
            newC = np.array([X[lab == i].mean(0) if np.any(lab == i) else C[i] for i in range(k)])
            if np.allclose(newC, C):
                break
            C = newC
        err = ((X - C[lab]) ** 2).sum()
        if best is None or err < best[2]:
            best = (lab, C, err)
    return best


def silhouette(X, lab):
    k = lab.max() + 1
    if k < 2:
        return -1
    D = np.sqrt(((X[:, None] - X[None]) ** 2).sum(-1))
    s = []
    for i in range(len(X)):
        same = lab == lab[i]
        if same.sum() <= 1:
            s.append(0); continue
        a = D[i, same].sum() / (same.sum() - 1)
        b = min(D[i, lab == j].mean() for j in range(k) if j != lab[i] and np.any(lab == j))
        s.append((b - a) / max(a, b))
    return float(np.mean(s))


def modes(names, F):
    X = np.array(F, float)
    mu, sd = X.mean(0), X.std(0)
    sd[sd < 1e-9] = 1
    Z = (X - mu) / sd
    best_k, best = 1, (np.zeros(len(X), int), Z.mean(0, keepdims=True), 0)
    best_s = 0.25                     # a second mode must clearly earn its place
    for k in range(2, min(4, len(X) - 1) + 1):
        lab, C, err = kmeans(Z, k)
        s = silhouette(Z, lab)
        if s > best_s:
            best_k, best, best_s = k, (lab, C, err), s
    lab, C, _ = best
    out = []
    for i in range(best_k):
        members = [n for n, l in zip(names, lab) if l == i]
        if best_k > 1:
            top = np.argsort(-np.abs(C[i]))[:3]
            traits = [f"{'high' if C[i][j] > 0 else 'low'} {FEATURES[j].replace('_', ' ')}" for j in top]
        else:
            traits = ["one consistent mode"]
        out.append({"mode": i + 1, "pieces": members, "sets_it_apart": traits})
    return {"n_modes": best_k, "silhouette": round(best_s, 3) if best_k > 1 else None, "modes": out}


def dhash(tile, size=16):
    """256-bit difference hash: 64 bits can't tell sparse pages apart."""
    g = np.asarray(tile.convert("L").resize((size + 1, size), Image.BILINEAR), np.float32)
    return (g[:, 1:] > g[:, :-1]).flatten()


def recurring(images, grid=4, max_frac=0.08):
    """Tiles that recur across different pieces = reused elements.
    A tile only counts if it has real content (contrast and edges), and two
    tiles only match if both their structure (dHash) and their colour agree."""
    tiles = []
    for name, im in images:
        im = im.convert("RGB")
        w, h = im.size
        for gy in range(grid):
            for gx in range(grid):
                t = im.crop((gx * w // grid, gy * h // grid, (gx + 1) * w // grid, (gy + 1) * h // grid))
                a = np.asarray(t.convert("L"), np.float32)
                edges = (np.abs(np.diff(a, axis=0)) > 30).mean() + (np.abs(np.diff(a, axis=1)) > 30).mean()
                if a.std() < 20 or edges < 0.02:
                    continue
                tiles.append((name, dhash(t), np.asarray(t, np.float32).reshape(-1, 3).mean(0)))
    parent = list(range(len(tiles)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    lim = int(max_frac * tiles[0][1].size) if tiles else 0
    for i in range(len(tiles)):
        for j in range(i + 1, len(tiles)):
            if tiles[i][0] == tiles[j][0]:
                continue
            if int((tiles[i][1] != tiles[j][1]).sum()) <= lim and np.abs(tiles[i][2] - tiles[j][2]).max() < 25:
                parent[find(i)] = find(j)
    groups = {}
    for i, t in enumerate(tiles):
        groups.setdefault(find(i), set()).add(t[0])
    out = sorted((sorted(g) for g in groups.values() if len(g) >= 2), key=len, reverse=True)
    return [{"appears_in": g, "count": len(g)} for g in out[:8]]


def near_duplicates(images, max_frac=0.06):
    hs = [(n, dhash(im)) for n, im in images]
    lim = int(max_frac * hs[0][1].size) if hs else 0
    pairs = []
    for i in range(len(hs)):
        for j in range(i + 1, len(hs)):
            d = int((hs[i][1] != hs[j][1]).sum())
            if d <= lim:
                pairs.append({"pieces": [hs[i][0], hs[j][0]], "distance": d})
    return pairs


def run(folder):
    files = sorted(os.path.join(folder, f) for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in EXTS)
    images = []
    for f in files:
        im = Image.open(f).convert("RGB")
        im.thumbnail((512, 512))
        images.append((os.path.basename(f), im))
    names = [n for n, _ in images]
    F = [features(im) for _, im in images]
    dups = near_duplicates(images)
    dup_sets = [set(p["pieces"]) for p in dups]
    # a "recurring element" that only lives inside one re-saved version isn't a habit
    rec = [r for r in recurring(images) if not any(set(r["appears_in"]) <= d for d in dup_sets)]
    seen, uniq = set(), []
    for r in rec:
        key = tuple(r["appears_in"])
        if key not in seen:
            seen.add(key); uniq.append(r)
    return {"n_pieces": len(images), "style_modes": modes(names, F) if len(images) >= 3 else None,
            "recurring_elements": uniq, "near_duplicates": dups}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = run(a.folder)
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        m = r["style_modes"]
        print(f"{r['n_pieces']} pieces -> {m['n_modes']} style mode(s)" + (f" (silhouette {m['silhouette']})" if m["silhouette"] else ""))
        for md in m["modes"]:
            print(f"  mode {md['mode']}: {', '.join(md['sets_it_apart'])}\n    {md['pieces']}")
        if r["recurring_elements"]:
            print("recurring elements across pieces:")
            for e in r["recurring_elements"]:
                print(f"  in {e['count']} pieces: {e['appears_in']}")
        if r["near_duplicates"]:
            print("near-duplicates / versions:", [p["pieces"] for p in r["near_duplicates"]])
