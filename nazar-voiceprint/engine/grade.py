#!/usr/bin/env python3
"""
nazar-voiceprint/engine/grade.py: colour grading and effects as measurable
habits, for photographers, filmmakers, colourists and designers who grade.

A look is reduced to numbers, never to a film-stock name. Steve Yedlin's
Display Prep Demo (ASC) showed viewers couldn't tell film from digital once a
fixed transform was applied. So we describe the transform, not the stock.

  look stats      mean/std of L, a, b in OKLab (Reinhard et al. 2001 used lab
                  mean+std as the whole "look"; OKLab is a modern stand-in)
  colourfulness   Hasler & Suesstrunk 2003 (r > 0.9 with observers)
  split-toning    hue/chroma of the shadows (L < P20) vs highlights (L > P80)
  fade / crush    lifted black floor vs a wall of near-black pixels
  roll-off        clipped highlights vs a gentle top end
  S-curve         midtone spread vs total spread
  sat by band     chroma in five lightness bands (film drops it in highlights)
  palette breadth how many hue families carry the colour; mono / duotone
  vignette        centre vs edge lightness
  grain           Immerkaer 1996 noise estimate, measured on flat patches only
  softness        variance of the Laplacian (low = soft)
  bloom           warm, bright excess in a ring around clipped highlights

Look labels are rules over these numbers, each tagged [measured] (the rule
follows from the mechanism) or [folklore] (practitioner convention).

    python grade.py image_or_folder [--json]
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from visual import srgb_to_oklab  # noqa: E402

EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def _hue(a, b):
    return (math.degrees(math.atan2(b, a)) + 360) % 360


def _laplace(g):
    p = np.pad(g, 1, mode="edge")
    return p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] - 4 * g


def immerkaer(g):
    """Immerkaer (1996) noise sigma, restricted to the flattest third of 8x8
    blocks: grain is easiest to see, and least confused with texture, there."""
    M = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], float)
    h, w = g.shape
    p = np.pad(g, 1, mode="edge")
    conv = sum(M[i, j] * p[i:i + h, j:j + w] for i in range(3) for j in range(3))
    bs = 8
    hh, ww = h // bs * bs, w // bs * bs
    if hh == 0 or ww == 0:
        return 0.0
    grad = np.abs(np.diff(g, axis=0, append=g[-1:])) + np.abs(np.diff(g, axis=1, append=g[:, -1:]))
    gb = grad[:hh, :ww].reshape(hh // bs, bs, ww // bs, bs).mean((1, 3))
    cb = np.abs(conv[:hh, :ww]).reshape(hh // bs, bs, ww // bs, bs).mean((1, 3))
    flat = gb <= np.percentile(gb, 33)
    return float(math.sqrt(math.pi / 2) * cb[flat].mean() / 6)


def analyse(im, side=512):
    im = im.convert("RGB")
    im.thumbnail((side, side))
    rgb = np.asarray(im, np.float32) / 255
    h, w, _ = rgb.shape
    lab = srgb_to_oklab(rgb.reshape(-1, 3)).reshape(h, w, 3)
    L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.hypot(A, B)
    p = {k: float(np.percentile(L, k)) for k in (1, 5, 10, 20, 25, 50, 75, 80, 90, 95, 99)}

    # Hasler & Suesstrunk colourfulness (0-255 RGB)
    R8, G8, B8 = (rgb[..., i] * 255 for i in range(3))
    rg, yb = R8 - G8, 0.5 * (R8 + G8) - B8
    colourfulness = math.hypot(rg.std(), yb.std()) + 0.3 * math.hypot(rg.mean(), yb.mean())

    # by rank, not by threshold: a hard crush puts 20%+ of pixels at one value,
    # and "L < P20" would then select nothing
    order = np.argsort(L, axis=None)
    n20 = max(1, L.size // 5)
    sh = np.zeros(L.size, bool); sh[order[:n20]] = True; sh = sh.reshape(L.shape)
    hi = np.zeros(L.size, bool); hi[order[-n20:]] = True; hi = hi.reshape(L.shape)
    sha, shb = float(A[sh].mean()), float(B[sh].mean())
    hia, hib = float(A[hi].mean()), float(B[hi].mean())
    sh_c, hi_c = math.hypot(sha, shb), math.hypot(hia, hib)
    sh_h, hi_h = _hue(sha, shb), _hue(hia, hib)
    hue_gap = min(abs(sh_h - hi_h), 360 - abs(sh_h - hi_h))

    bands = np.linspace(0, 1, 6)
    sat_by_band = []
    for lo, up in zip(bands[:-1], bands[1:]):
        m = (L >= lo) & (L < up)
        sat_by_band.append(round(float(C[m].mean()), 4) if m.sum() > 50 else None)

    colourful = C > 0.03
    hues = (np.degrees(np.arctan2(B, A)) + 360) % 360
    hist, _ = np.histogram(hues[colourful], bins=12, range=(0, 360), weights=C[colourful])
    share = hist / max(hist.sum(), 1e-9)
    families = int((share > 0.05).sum())
    top2 = float(np.sort(share)[-2:].sum()) if hist.sum() > 0 else 0.0

    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / math.sqrt(2)
    centre = L[r < 0.3].mean()
    ring = r > 0.8
    quads = [ring & (yy < h / 2) & (xx < w / 2), ring & (yy < h / 2) & (xx >= w / 2),
             ring & (yy >= h / 2) & (xx < w / 2), ring & (yy >= h / 2) & (xx >= w / 2)]
    corner_ratios = [float(L[q].mean() / max(centre, 1e-6)) for q in quads if q.any()]
    # a real vignette darkens every corner; a dark floor or bright sky alone doesn't count
    vignette = max(corner_ratios) if corner_ratios else 1.0

    clipped = L > 0.97
    bloom = None
    if clipped.mean() > 0.001:
        from visual import _sobel  # noqa
        near = clipped.copy()
        far = clipped.copy()
        for _ in range(3):
            near = near | np.roll(near, 1, 0) | np.roll(near, -1, 0) | np.roll(near, 1, 1) | np.roll(near, -1, 1)
        for _ in range(12):
            far = far | np.roll(far, 1, 0) | np.roll(far, -1, 0) | np.roll(far, 1, 1) | np.roll(far, -1, 1)
        ring_in, ring_out = near & ~clipped, far & ~near
        if ring_in.any() and ring_out.any():
            warm = (rgb[..., 0] - rgb[..., 2])
            lum_x = float(L[ring_in].mean() - L[ring_out].mean())
            warm_x = float(warm[ring_in].mean() - warm[ring_out].mean())
            bloom = round(min(lum_x, 4 * warm_x), 3)   # needs both: brighter AND warmer near the highlight

    out = {
        "look_stats": {"L_mean": round(float(L.mean()), 3), "L_std": round(float(L.std()), 3),
                       "a_mean": round(float(A.mean()), 4), "a_std": round(float(A.std()), 4),
                       "b_mean": round(float(B.mean()), 4), "b_std": round(float(B.std()), 4)},
        "colourfulness": round(colourfulness, 1),
        "mean_chroma": round(float(C.mean()), 4),
        "split_tone": {"shadow_hue": round(sh_h), "shadow_chroma": round(sh_c, 4),
                       "highlight_hue": round(hi_h), "highlight_chroma": round(hi_c, 4),
                       "hue_gap": round(hue_gap)},
        "black_floor_P1": round(p[1], 3),
        "crushed_share": round(float((L < 0.06).mean()), 4),
        "clipped_share": round(float(clipped.mean()), 4),
        "top_end_slope": round(p[99] - p[90], 3),              # small = compressed, rolled-off top
        "contrast_total": round(p[95] - p[5], 3),
        "midtone_spread": round(p[75] - p[25], 3),
        "sat_by_band": sat_by_band,
        "hue_families": families,
        "top2_hue_share": round(top2, 3),
        "vignette_ratio": round(vignette, 3),                   # < 0.85 = darkened edges
        "grain_sigma": round(immerkaer(L), 4),
        "softness_laplace_var": round(float(_laplace(L).var()), 5),
        "bloom": bloom,
    }
    out["looks"] = looks(out)
    return out


def looks(m):
    """Labels as rules over the numbers. [measured] = follows from the
    mechanism; [folklore] = practitioner convention, treat as a hint."""
    L = []
    st = m["split_tone"]
    if m["mean_chroma"] < 0.012:
        L.append("monochrome [measured]")
    elif m["top2_hue_share"] > 0.95 and m["hue_families"] <= 2:
        L.append("duotone / limited palette [measured]")
    if st["shadow_chroma"] > 0.02 and st["highlight_chroma"] > 0.02 and st["hue_gap"] > 60:
        L.append(f"split-toned: shadows {st['shadow_hue']}°, highlights {st['highlight_hue']}° [measured]")
        # a blue image on warm aged paper is split too (a real test on Met cyanotypes),
        # but "teal & orange" names a colour grade: require a genuinely multi-hue image
        if 160 <= st["shadow_hue"] <= 250 and 30 <= st["highlight_hue"] <= 100 and m["hue_families"] >= 3:
            L.append("teal & orange [folklore label, measured split]")
    # OKLab L is perceptual: true black reads ~0.12 after noise, so "lifted" starts higher
    if m["black_floor_P1"] >= 0.22 and m["contrast_total"] < 0.6:
        L.append("faded / matte blacks [measured]")
    if m["crushed_share"] > 0.03:
        L.append("crushed blacks [measured]")
    if 0.012 <= m["mean_chroma"] < 0.05 and m["contrast_total"] > 0.7 and m["crushed_share"] > 0.01:
        L.append("bleach-bypass-like: desaturated, hard, dense shadows [measured mechanism]")
    # "highlights desaturate" is left to the portfolio summary: in one image it
    # can't be told apart from a white sky. Across 20 pieces it can.
    if m["vignette_ratio"] < 0.85:
        L.append("vignette [measured]")
    if m["grain_sigma"] > 0.01:
        L.append("visible grain / noise [measured]")
    if m["softness_laplace_var"] < 0.0004:
        L.append("soft focus / low micro-contrast [measured]")
    if m["bloom"] is not None and m["bloom"] > 0.05:
        L.append("halation / bloom around highlights [measured]")
    if m["colourfulness"] > 80 and m["contrast_total"] > 0.8 and m["clipped_share"] > 0.02:
        L.append("cross-processed-like: loud colour, hard contrast, blown highs [folklore]")
    return L


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    files = [a.path] if os.path.isfile(a.path) else sorted(
        os.path.join(a.path, f) for f in os.listdir(a.path) if os.path.splitext(f)[1].lower() in EXTS)
    res = {os.path.basename(f): analyse(Image.open(f)) for f in files}
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for k, v in res.items():
            print(f"\n{k}: colourfulness {v['colourfulness']}, contrast {v['contrast_total']}, black floor {v['black_floor_P1']}, "
                  f"vignette {v['vignette_ratio']}, grain {v['grain_sigma']}")
            for lab in v["looks"] or ["no strong look: close to neutral"]:
                print("  -", lab)
