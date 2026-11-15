#!/usr/bin/env python3
"""
nazar-voiceprint/engine/visual.py: the measurable layer of a design language.

Run it on a folder of someone's own past work (logos, layouts, illustrations,
posts). It extracts what the research says IS computable:
  - the recurring palette: k-means in OKLab (a perceptual space, so distance
    tracks perceived difference), k-means++ init, several seeds, best kept
  - palette proportions: how much ground vs. accent the person habitually uses
  - composition statistics: visual-weight centre, rule-of-thirds pull,
    left-right symmetry, negative-space share, edge density (busy vs. calm)

It does NOT extract intent, motifs, or the idea behind a piece. Gatys et al.
(2015) define style as feature correlations with spatial layout discarded, and
concede content and style can't be fully disentangled; the design literature on
tacit knowledge says the judgment behind choices doesn't transfer through
features. That layer comes from the confirm loop with the person, not from here.
See ../references/visual_design.md.

    python visual.py path/to/folder [--k 6] [--json]
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def srgb_to_oklab(rgb):
    """rgb: (N,3) floats 0..1 -> (N,3) OKLab (Ottosson 2020)."""
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    m1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                   [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]])
    lms = np.cbrt(c @ m1.T)
    m2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                   [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]])
    return lms @ m2.T


def oklab_to_srgb(lab):
    m2i = np.array([[1.0, 0.3963377774, 0.2158037573],
                    [1.0, -0.1055613458, -0.0638541728],
                    [1.0, -0.0894841775, -1.2914855480]])
    lms = (lab @ m2i.T) ** 3
    m1i = np.array([[4.0767416621, -3.3077115913, 0.2309699292],
                    [-1.2684380046, 2.6097574011, -0.3413193965],
                    [-0.0041960863, -0.7034186147, 1.7076147010]])
    c = np.clip(lms @ m1i.T, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def kmeans_pp(x, k, seed, iters=25):
    rng = np.random.default_rng(seed)
    centres = [x[rng.integers(len(x))]]
    for _ in range(1, k):
        d2 = np.min(((x[:, None, :] - np.array(centres)[None]) ** 2).sum(-1), axis=1)
        centres.append(x[rng.choice(len(x), p=d2 / d2.sum())])
    c = np.array(centres)
    for _ in range(iters):
        labels = np.argmin(((x[:, None, :] - c[None]) ** 2).sum(-1), axis=1)
        new = np.array([x[labels == i].mean(0) if np.any(labels == i) else c[i] for i in range(k)])
        if np.allclose(new, c, atol=1e-5):
            break
        c = new
    err = ((x - c[labels]) ** 2).sum()
    return c, labels, err


def load_images(folder, side=256):
    paths = sorted(os.path.join(folder, f) for f in os.listdir(folder)
                   if os.path.splitext(f)[1].lower() in EXTS)
    out = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        im.thumbnail((side, side))
        out.append((os.path.basename(p), im))
    return out


def palette(images, k=6, seeds=4, per_image=4000):
    rng = np.random.default_rng(0)
    samples = []
    for _, im in images:
        a = np.asarray(im, np.float32).reshape(-1, 3) / 255
        idx = rng.choice(len(a), min(per_image, len(a)), replace=False)
        samples.append(a[idx])
    lab = srgb_to_oklab(np.concatenate(samples))
    best = min((kmeans_pp(lab, k, s) for s in range(seeds)), key=lambda r: r[2])
    centres, labels, _ = best
    shares = np.bincount(labels, minlength=k) / len(labels)
    order = np.argsort(-shares)
    rows = []
    for i in order:
        L, a_, b_ = centres[i]
        rgb = oklab_to_srgb(centres[i][None])[0]
        chroma = float(np.hypot(a_, b_))
        rows.append({
            "hex": "#%02X%02X%02X" % tuple(int(round(v * 255)) for v in rgb),
            "share": round(float(shares[i]), 3),
            "lightness": round(float(L), 3),
            "chroma": round(chroma, 3),
            "role": "ground" if shares[i] > 0.35 else ("accent" if chroma > 0.12 and shares[i] < 0.12 else "support"),
        })
    return rows


def composition(im):
    g = np.asarray(im.convert("L"), np.float32) / 255
    h, w = g.shape
    edges = np.asarray(im.convert("L").filter(ImageFilter.FIND_EDGES), np.float32) / 255
    bg = np.median(np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]]))
    ink = np.abs(g - bg)                       # departure from the background = visual weight
    weight = ink + 0.5 * edges
    total = weight.sum() + 1e-9
    ys, xs = np.mgrid[0:h, 0:w]
    cx, cy = (weight * xs).sum() / total / w, (weight * ys).sum() / total / h
    band = 0.06
    thirds = np.zeros_like(g, bool)
    for t in (1 / 3, 2 / 3):
        thirds |= np.abs(xs / w - t) < band
        thirds |= np.abs(ys / h - t) < band
    thirds_pull = (weight[thirds].sum() / total) / thirds.mean()
    mirror = weight[:, ::-1]
    sym = 1 - np.abs(weight - mirror).sum() / (2 * total)
    return {
        "weight_centre": [round(float(cx), 3), round(float(cy), 3)],
        "thirds_pull": round(float(thirds_pull), 2),       # >1 means weight gathers on the thirds lines
        "lr_symmetry": round(float(sym), 3),                # 1 = mirror-symmetric
        "negative_space": round(float((ink < 0.08).mean()), 3),
        "edge_density": round(float((edges > 0.15).mean()), 3),
    }


def _sobel(g):
    p = np.pad(g, 1, mode="edge")
    gx = (p[:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[1:-1, :-2] + p[2:, :-2])
    gy = (p[2:, :-2] + 2 * p[2:, 1:-1] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[:-2, 1:-1] + p[:-2, 2:])
    return gx, gy


def _otsu(g):
    hist = np.bincount((g * 255).astype(np.uint8).ravel(), minlength=256).astype(float)
    w = np.cumsum(hist); mu = np.cumsum(hist * np.arange(256))
    with np.errstate(divide="ignore", invalid="ignore"):
        between = (mu[-1] * w - mu * w[-1]) ** 2 / (w * (w[-1] - w))
    return np.nanargmax(between[:-1]) / 255


def _runs(mask):
    """Length of the ink run each ink pixel sits in, along rows."""
    out = np.zeros(mask.shape, np.int32)
    for i, row in enumerate(mask):
        d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
        starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
        for s, e in zip(starts, ends):
            out[i, s:e] = e - s
    return out


def line_quality(im):
    """Illustrator layer (numpy approximations of the research methods):
    - stroke width ~ min(horizontal, vertical) ink run per pixel, a cheap
      stand-in for the Stroke Width Transform (Epshtein et al., CVPR 2010);
      CV of width = line-weight variation (expressive vs. mechanical line)
    - hatching/stroke direction: histogram of gradient angles on ink edges
      (dominant angle + how concentrated it is)
    - line vs. fill: edge pixels / ink pixels (line art vs. flat shapes)
    - angularity: share of edge pixels whose direction turns sharply versus
      their neighbours (angular vs. rounded shape language)"""
    g = np.asarray(im.convert("L"), np.float32) / 255
    bg = np.median(np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]]))
    dark_on_light = bg > 0.5
    gi, ti = np.rint(g * 255), round(_otsu(g) * 255)   # compare whole levels: float32 vs float64 at k/255 misfires
    ink = (gi <= ti) if dark_on_light else (gi > ti)
    if ink.mean() < 0.002:
        return None
    widths = np.minimum(_runs(ink), _runs(ink.T).T)[ink].astype(float)
    widths = widths[widths <= np.percentile(widths, 95)]   # drop solid fills from the line-weight stat
    gx, gy = _sobel(g)
    mag = np.hypot(gx, gy)
    edge = mag > max(0.25, np.percentile(mag, 90))
    ang = (np.degrees(np.arctan2(gy, gx)) % 180)[edge]
    hist, _ = np.histogram(ang, bins=12, range=(0, 180))
    p = hist / max(hist.sum(), 1)
    concentration = float(1 - (-(p[p > 0] * np.log(p[p > 0])).sum() / np.log(12)))
    theta = np.arctan2(gy, gx)
    turn = np.zeros_like(theta)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        sh = np.roll(np.roll(theta, dy, 0), dx, 1)
        turn = np.maximum(turn, np.abs(np.angle(np.exp(1j * (theta - sh)))))
    angular = float((turn[edge] > np.radians(50)).mean()) if edge.any() else 0.0
    return {
        "stroke_width_px": round(float(np.median(widths)), 2),
        "line_weight_variation": round(float(widths.std() / max(widths.mean(), 1e-6)), 3),
        "dominant_stroke_angle": int(np.argmax(hist) * 15 + 7),
        "direction_concentration": round(concentration, 3),   # 0 = all directions, 1 = one direction (hatching)
        "line_vs_fill": round(float(edge.sum() / max(ink.sum(), 1)), 3),
        "angularity": round(angular, 3),
    }


def tone(im):
    """Photographers and colourists: tone curve and colour lean."""
    a = np.asarray(im, np.float32).reshape(-1, 3) / 255
    lab = srgb_to_oklab(a)
    L = lab[:, 0]
    p5, p50, p95 = np.percentile(L, [5, 50, 95])
    return {
        "shadows_L": round(float(p5), 3), "midtone_L": round(float(p50), 3), "highlights_L": round(float(p95), 3),
        "contrast": round(float(p95 - p5), 3),
        "warm_cool_lean": round(float(lab[:, 2].mean()), 4),      # OKLab b: + warm/yellow, - cool/blue
        "green_magenta_lean": round(float(lab[:, 1].mean()), 4),  # OKLab a: + magenta, - green
        "mean_chroma": round(float(np.hypot(lab[:, 1], lab[:, 2]).mean()), 4),
    }


def summarise(comps):
    keys = ["thirds_pull", "lr_symmetry", "negative_space", "edge_density"]
    out = {}
    for k in keys:
        v = np.array([c[k] for c in comps])
        out[k] = {"mean": round(float(v.mean()), 3), "spread": round(float(v.std()), 3)}
    cx = np.array([c["weight_centre"][0] for c in comps])
    cy = np.array([c["weight_centre"][1] for c in comps])
    out["weight_centre_mean"] = [round(float(cx.mean()), 3), round(float(cy.mean()), 3)]
    for group in ("line", "tone"):
        rows = [c[group] for c in comps if c.get(group)]
        if rows:
            out[group] = {k: {"mean": round(float(np.mean([r[k] for r in rows])), 3),
                              "spread": round(float(np.std([r[k] for r in rows])), 3)}
                          for k in rows[0] if k != "dominant_stroke_angle"}
    return out


def read_plain(s, pal):
    """Plain-language reading. A starting point for the confirm loop, not a verdict."""
    lines = []
    neg = s["negative_space"]["mean"]
    lines.append("lots of air: most of the frame is left empty" if neg > 0.6 else
                 "dense: little empty space" if neg < 0.3 else "balanced fill vs. air")
    sym = s["lr_symmetry"]["mean"]
    lines.append("leans symmetric and centred" if sym > 0.85 else "asymmetric by habit" if sym < 0.7 else "mild asymmetry")
    tp = s["thirds_pull"]["mean"]
    if tp > 1.15:
        lines.append("weight gathers on the thirds lines")
    cx, cy = s["weight_centre_mean"]
    lean = []
    if cx < 0.45: lean.append("left")
    if cx > 0.55: lean.append("right")
    if cy < 0.45: lean.append("high")
    if cy > 0.55: lean.append("low")
    if lean:
        lines.append("visual weight sits " + "-".join(lean) + " in the frame")
    accents = [p for p in pal if p["role"] == "accent"]
    ground = [p for p in pal if p["role"] == "ground"]
    if ground and accents:
        lines.append(f"a {ground[0]['hex']} ground carrying {len(accents)} small accent(s) "
                     f"({', '.join(p['hex'] for p in accents)}), used sparingly")
    ln = s.get("line")
    if ln:
        v = ln["line_weight_variation"]["mean"]
        lines.append("expressive line: weight swells and thins" if v > 0.6 else
                     "even, mechanical line weight" if v < 0.3 else "moderate line-weight variation")
        lines.append("line-led drawing (outlines, hatching)" if ln["line_vs_fill"]["mean"] > 0.35 else
                     "shape-led: flat fills more than lines")
        lines.append("angular shape language" if ln["angularity"]["mean"] > 0.35 else
                     "rounded, flowing shape language" if ln["angularity"]["mean"] < 0.2 else "mix of curves and corners")
        if ln["direction_concentration"]["mean"] > 0.25:
            lines.append("strokes favour one direction (hatching habit)")
    tn = s.get("tone")
    if tn:
        w = tn["warm_cool_lean"]["mean"]
        lines.append("warm lean" if w > 0.01 else "cool lean" if w < -0.01 else "neutral colour lean")
        lines.append("low-contrast, soft tones" if tn["contrast"]["mean"] < 0.4 else
                     "high-contrast" if tn["contrast"]["mean"] > 0.75 else "medium contrast")
        lines.append("muted colour overall" if tn["mean_chroma"]["mean"] < 0.04 else "saturated colour overall")
    for k, label in (("negative_space", "air"), ("lr_symmetry", "symmetry")):
        if s[k]["spread"] > 0.15:
            lines.append(f"{label} varies a lot between pieces; may be project-driven, not a habit")
    return lines


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--k", type=int, default=6, help="palette size")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    imgs = load_images(a.folder)
    if not imgs:
        sys.exit(f"no images in {a.folder}")
    pal = palette(imgs, a.k)
    comps = [dict(file=n, **composition(im), line=line_quality(im), tone=tone(im)) for n, im in imgs]
    summ = summarise(comps)
    result = {"n_pieces": len(imgs), "palette": pal, "composition_summary": summ,
              "per_piece": comps, "plain_reading": read_plain(summ, pal)}
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{len(imgs)} pieces\n\npalette (by share):")
        for p in pal:
            print(f"  {p['hex']}  {p['share']*100:5.1f}%  L={p['lightness']:.2f} C={p['chroma']:.2f}  {p['role']}")
        print("\ncomposition (mean ± spread across pieces):")
        for k, v in summ.items():
            print(f"  {k:20} {v}")
        print("\nplain reading (confirm with the person):")
        for line in result["plain_reading"]:
            print("  -", line)
