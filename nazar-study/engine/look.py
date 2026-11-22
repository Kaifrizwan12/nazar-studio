#!/usr/bin/env python3
"""look.py - back-engineer the look of a reference image, a set, or our own output (numpy + Pillow only).

Studying a master's frame by eye gives adjectives ("moody", "clean"). This gives numbers you can brief, prompt and
check against: where the blacks sit, how much clips, how saturated, which way the light falls off, what colour the
shadows and highlights lean, how much grain, how sharp, how much vignette, where the visual weight sits, how much
empty space, and the palette. Run it on 6-20 references and the set's median is the target look; run `compare` on
our render and it lists the gaps in order of size with the fix for each.

  python look.py card ref.jpg [-o out]            # one look card: JSON + Markdown + annotated sheet
  python look.py set refs/ -o out                 # every image + the set's median look + a contact sheet
  python look.py compare ours.jpg out/set.json    # our image against the target look: gaps and fixes
  python look.py --selftest

What it measures is in each field's name. What it cannot measure: light hardness from shadow edges (read it by eye,
references/reading_light.md), the number of lights, lens focal length, intent. Numbers describe a look; they do not
make one good. Their image is data for study, never pasted into our work.
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

EXTS = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")


def _load(path, long=1000):
    im = Image.open(path).convert("RGB")
    s = long / max(im.size)
    if s < 1:
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    return im


def _lum(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def _box(a, k, axis):
    if k < 1:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (k + 1, k)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * k + 1, 2 * k + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return (hi - lo) / (2 * k + 1)


def _blur(a, r):
    """Gaussian-like blur (three box passes per axis) on float arrays; Pillow cannot blur float images."""
    a = a.astype(np.float32)
    k = max(0, int(round(r * 0.85)))
    if k == 0:
        return a
    for ax in (0, 1):
        for _ in range(3):
            a = _box(a, k, ax)
    return a


def _kmeans(px, k=5, it=12, seed=0):
    rng = np.random.default_rng(seed)
    c = px[rng.choice(len(px), k, replace=False)].astype(np.float32)
    for _ in range(it):
        d = ((px[:, None, :] - c[None]) ** 2).sum(-1)
        lab = d.argmin(1)
        for j in range(k):
            if (lab == j).any():
                c[j] = px[lab == j].mean(0)
    share = np.bincount(lab, minlength=k) / len(lab)
    o = np.argsort(-share)
    return c[o], share[o]


def measure(im):
    a = np.asarray(im).astype(np.float32)
    H, W = a.shape[:2]
    L = _lum(a)
    p = {f"P{q}": round(float(np.percentile(L, q)), 1) for q in (1, 5, 50, 95, 99)}
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 1, (mx - mn) / np.maximum(mx, 1), 0)
    # colour lean of shadows and highlights: + warm (R over B), + magenta (R+B over 2G)
    lo, hi = L < np.percentile(L, 20), L > np.percentile(L, 80)
    mid = (~lo) & (~hi)

    def lean(m):
        if not m.any():
            return (0.0, 0.0)
        r, g, b = a[m].mean(0)
        return (round(float(r - b), 1), round(float((r + b) / 2 - g), 1))
    # light falloff, read on a heavily blurred image so detail does not vote
    small = np.asarray(im.resize((48, max(2, round(48 * H / W))), Image.BILINEAR)).astype(np.float32)
    Ls = _lum(small)
    t = Ls.shape[1] // 3
    lr = (Ls[:, :t].mean() - Ls[:, -t:].mean()) / max(Ls.mean(), 1)
    tb = (Ls[: Ls.shape[0] // 3].mean() - Ls[-Ls.shape[0] // 3:].mean()) / max(Ls.mean(), 1)
    cy0, cx0 = H // 2, W // 2
    cw, ch = W // 6, H // 6
    centre = L[cy0 - ch:cy0 + ch, cx0 - cw:cx0 + cw].mean()
    cs = max(4, min(H, W) // 10)
    corners = np.mean([L[:cs, :cs].mean(), L[:cs, -cs:].mean(), L[-cs:, :cs].mean(), L[-cs:, -cs:].mean()])
    # grain: robust sigma of the high-pass in the flattest blocks (where there is no detail to confuse it)
    hp = L - _blur(L, 1.2)
    bs = 16
    blocks = []
    for y in range(0, H - bs, bs):
        for x in range(0, W - bs, bs):
            blk = L[y:y + bs, x:x + bs]
            blocks.append((float(_blur(blk, 3).std()), y, x))
    blocks.sort()
    flat = [hp[y:y + bs, x:x + bs] for _, y, x in blocks[: max(8, len(blocks) // 10)]]
    fl = np.concatenate([f.ravel() for f in flat]) if flat else hp.ravel()
    grain = float(1.4826 * np.median(np.abs(fl - np.median(fl))))
    # sharpness: variance of the Laplacian on a 1000 px long side
    lap = (np.roll(L, 1, 0) + np.roll(L, -1, 0) + np.roll(L, 1, 1) + np.roll(L, -1, 1) - 4 * L)[2:-2, 2:-2]
    sharp = float(lap.var())
    # visual weight: local contrast + saturation; centroid and its nearest thirds point
    wgt = np.abs(L - _blur(L, max(H, W) / 40)) + 60 * sat
    wgt = _blur(wgt, max(H, W) / 60)
    yy, xx = np.mgrid[0:H, 0:W]
    cxw, cyw = float((wgt * xx).sum() / wgt.sum() / W), float((wgt * yy).sum() / wgt.sum() / H)
    thirds = [(x, y) for x in (1 / 3, 2 / 3) for y in (1 / 3, 2 / 3)]
    near = min(thirds + [(0.5, 0.5)], key=lambda q: (q[0] - cxw) ** 2 + (q[1] - cyw) ** 2)
    empty = float(np.mean([s < 4.0 for s, _, _ in blocks])) if blocks else 0.0
    # depth hint: detail in the weighted centre vs the frame edge
    mcx, mcy = int(cxw * W), int(cyw * H)
    r = max(8, min(H, W) // 8)
    core = lap[max(0, mcy - r):mcy + r, max(0, mcx - r):mcx + r]
    edge = np.concatenate([lap[:r].ravel(), lap[-r:].ravel()])
    depth = float(core.var() / max(edge.var(), 1e-3)) if core.size else 1.0
    px = np.asarray(im.resize((80, max(2, round(80 * H / W))), Image.BILINEAR)).reshape(-1, 3).astype(np.float32)
    pal, share = _kmeans(px, 5)
    m = dict(
        size=[W, H], aspect=round(W / H, 3), **p,
        black_point=p["P1"], white_point=p["P99"], contrast_p95_p5=round(p["P95"] - p["P5"], 1),
        clip_highlights_pct=round(float((mn >= 250).mean() * 100), 2), channel_clip_pct=round(float((mx >= 254).mean() * 100), 2),
        crush_shadows_pct=round(float((mx <= 6).mean() * 100), 2),
        saturation_mean=round(float(sat.mean()), 3), saturation_p90=round(float(np.percentile(sat, 90)), 3),
        shadow_lean_warm_magenta=lean(lo), mid_lean_warm_magenta=lean(mid), highlight_lean_warm_magenta=lean(hi),
        light_bias_left_minus_right=round(float(lr), 3), light_bias_top_minus_bottom=round(float(tb), 3),
        vignette_corner_over_centre=round(float(corners / max(centre, 1)), 3),
        grain_sigma=round(grain, 2), sharpness_lapvar=round(sharp, 1),
        weight_centroid=[round(cxw, 3), round(cyw, 3)], nearest_anchor=[round(near[0], 3), round(near[1], 3)],
        empty_space_share=round(empty, 3), subject_vs_edge_detail=round(depth, 2),
        palette=[("#%02x%02x%02x" % tuple(int(v) for v in c), round(float(s), 3)) for c, s in zip(pal, share)])
    m["words"] = words(m)
    return m


def words(m):
    """Plain prompt and brief words derived from the numbers (never adjectives without a number behind them)."""
    w = []
    med = m["P50"]
    w.append("low-key" if med < 70 else "high-key" if med > 170 else "mid-key")
    w.append("deep, true blacks" if m["black_point"] < 8 else "lifted, milky blacks" if m["black_point"] > 28 else "soft blacks")
    if m["clip_highlights_pct"] > 2:
        w.append("highlights allowed to clip")
    elif m["white_point"] < 225:
        w.append("no pure whites, highlights held down")
    c = m["contrast_p95_p5"]
    w.append("hard contrast" if c > 200 else "gentle contrast" if c < 120 else "moderate contrast")
    s = m["saturation_mean"]
    w.append("muted colour" if s < 0.18 else "rich colour" if s > 0.42 else "natural colour")
    sh, hl = m["shadow_lean_warm_magenta"][0], m["highlight_lean_warm_magenta"][0]
    if hl - sh > 14:
        w.append("warm highlights, cooler shadows")
    elif sh - hl > 14:
        w.append("cool highlights, warmer shadows")
    elif m["mid_lean_warm_magenta"][0] > 18:
        w.append("warm overall")
    elif m["mid_lean_warm_magenta"][0] < -12:
        w.append("cool overall")
    lr, tb = m["light_bias_left_minus_right"], m["light_bias_top_minus_bottom"]
    if abs(lr) > 0.08:
        w.append(f"light falls off from {'left to right' if lr > 0 else 'right to left'}")
    if tb > 0.1:
        w.append("light from above")
    elif tb < -0.1:
        w.append("brighter low in the frame")
    v = m["vignette_corner_over_centre"]
    if v < 0.75:
        w.append("strong vignette")
    elif v < 0.92:
        w.append("gentle vignette")
    g = m["grain_sigma"]
    w.append("visible grain" if g > 3.5 else "fine grain" if g > 1.5 else "clean, almost no grain")
    w.append("shallow focus, subject sharp against soft edges" if m["subject_vs_edge_detail"] > 4 else "deep focus")
    w.append(f"{m['empty_space_share']:.0%} of the frame is empty space")
    cx, cy = m["weight_centroid"]
    w.append("weight off-centre" if abs(cx - 0.5) > 0.08 or abs(cy - 0.5) > 0.08 else "weight centred")
    return w


# ---------------------------------------------------------------------------------------------- set and compare
NUMERIC = ["P50", "black_point", "white_point", "contrast_p95_p5", "clip_highlights_pct", "saturation_mean", "light_bias_left_minus_right",
           "light_bias_top_minus_bottom", "vignette_corner_over_centre", "grain_sigma", "sharpness_lapvar", "empty_space_share", "subject_vs_edge_detail"]

FIX = {
    "black_point": ("blacks", "lift or crush the blacks in the grade (composite.py lift; a levels black point)"),
    "white_point": ("whites", "pull or extend the highlights (a curve's top point; less exposure on the plate)"),
    "P50": ("overall key", "expose up or down; the plate and product together"),
    "contrast_p95_p5": ("contrast", "an S-curve, or flatten it; once, on the whole frame"),
    "clip_highlights_pct": ("clipped highlights", "recover highlights; check nothing clips on the printed whites"),
    "saturation_mean": ("saturation", "saturation on the whole frame (composite.py sat for the product)"),
    "light_bias_left_minus_right": ("left-right light falloff", "brief the key from the other side, or grade a soft side falloff"),
    "light_bias_top_minus_bottom": ("top-bottom falloff", "raise or lower the key; a graduated darkening"),
    "vignette_corner_over_centre": ("vignette", "composite.py vignette"),
    "grain_sigma": ("grain", "composite.py grain (the product) and a frame-wide grain pass"),
    "sharpness_lapvar": ("sharpness", "soften or sharpen the whole frame once; never only the product"),
    "empty_space_share": ("empty space", "recompose: more or less air around the product"),
    "subject_vs_edge_detail": ("depth of field", "open or stop down the plate's aperture in the brief (shotplan.py f_number)"),
}


def summarise(cards):
    s = {}
    for k in NUMERIC:
        v = np.array([c[k] for c in cards], float)
        s[k] = dict(median=round(float(np.median(v)), 3), lo=round(float(np.percentile(v, 15)), 3), hi=round(float(np.percentile(v, 85)), 3))
    allw = [w for c in cards for w in c["words"] if not w.endswith("empty space")]
    common = sorted({w for w in allw if allw.count(w) >= max(2, len(cards) * 0.5)}, key=lambda w: -allw.count(w))
    return dict(n=len(cards), stats=s, shared_words=common)


def compare(card, target):
    gaps = []
    for k in NUMERIC:
        st = target["stats"][k]
        v = card[k]
        spread = max(st["hi"] - st["lo"], abs(st["median"]) * 0.1, 1e-3)
        if v < st["lo"] or v > st["hi"]:
            z = (v - st["median"]) / spread
            gaps.append(dict(field=k, ours=v, target=st["median"], range=[st["lo"], st["hi"]], size=round(abs(z), 2),
                             what=FIX[k][0], fix=FIX[k][1], direction="higher" if v > st["median"] else "lower"))
    gaps.sort(key=lambda g: -g["size"])
    return gaps


# ---------------------------------------------------------------------------------------------- sheets
def _font(sz):
    for f in ("DejaVuSans.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def sheet(im, m, path):
    """The image with a thirds grid and the weight centroid, the luminance histogram, the palette and the words."""
    W = 1400
    s = 900 / im.height
    th = im.resize((max(1, round(im.width * s)), 900))
    if th.width > 860:
        th = th.resize((860, round(900 * 860 / th.width)))
    out = Image.new("RGB", (W, 960), (246, 243, 236))
    out.paste(th, (30, 30))
    d = ImageDraw.Draw(out)
    tw, thh = th.size
    for f in (1 / 3, 2 / 3):
        d.line([30 + tw * f, 30, 30 + tw * f, 30 + thh], fill=(255, 255, 255), width=1)
        d.line([30, 30 + thh * f, 30 + tw, 30 + thh * f], fill=(255, 255, 255), width=1)
    cx, cy = m["weight_centroid"]
    d.ellipse([30 + tw * cx - 9, 30 + thh * cy - 9, 30 + tw * cx + 9, 30 + thh * cy + 9], outline=(220, 40, 30), width=3)
    x0 = 30 + tw + 30
    L = _lum(np.asarray(im).astype(np.float32))
    hist, _ = np.histogram(L, 64, (0, 255))
    hist = hist / hist.max()
    for i, h in enumerate(hist):
        d.rectangle([x0 + i * 7, 230 - h * 180, x0 + i * 7 + 5, 230], fill=(40, 34, 30))
    d.text((x0, 238), f"black {m['black_point']}  mid {m['P50']}  white {m['white_point']}  clip {m['clip_highlights_pct']}%", fill=(40, 34, 30), font=_font(15))
    for i, (hx, sh) in enumerate(m["palette"]):
        d.rectangle([x0 + i * 92, 280, x0 + i * 92 + 84, 340], fill=hx)
        d.text((x0 + i * 92, 346), f"{hx} {sh:.0%}", fill=(40, 34, 30), font=_font(13))
    y = 390
    for w in m["words"]:
        d.text((x0, y), "· " + w, fill=(40, 34, 30), font=_font(17))
        y += 26
    out.save(path, quality=90)
    return path


def card_md(m, name):
    L = [f"# Look card: {name}", "", "**Words (from the numbers):** " + "; ".join(m["words"]), "", "| field | value |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in m.items() if k not in ("words", "palette")]
    L += [f"| palette | {', '.join(f'{h} ({s:.0%})' for h, s in m['palette'])} |"]
    return "\n".join(L) + "\n"


def run_set(folder, out):
    os.makedirs(out, exist_ok=True)
    files = sorted(f for f in glob.glob(os.path.join(folder, "*")) if f.lower().endswith(EXTS))
    cards = []
    for f in files:
        im = _load(f)
        m = measure(im)
        m["file"] = os.path.basename(f)
        cards.append(m)
        sheet(im, m, os.path.join(out, os.path.splitext(os.path.basename(f))[0] + "_look.jpg"))
    summ = summarise(cards)
    summ["cards"] = cards
    json.dump(summ, open(os.path.join(out, "set.json"), "w", encoding="utf-8"), indent=1)
    lines = [f"# Set look ({summ['n']} images)", "", "**Shared words:** " + "; ".join(summ["shared_words"]), "", "| field | median | 15-85% range |", "|---|---|---|"]
    lines += [f"| {k} | {v['median']} | {v['lo']} - {v['hi']} |" for k, v in summ["stats"].items()]
    open(os.path.join(out, "set.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    # contact sheet of thumbnails
    th = [_load(f, 300) for f in files]
    if th:
        cols = min(5, len(th)); rows = (len(th) + cols - 1) // cols
        cs = Image.new("RGB", (cols * 310 + 10, rows * 310 + 10), (246, 243, 236))
        for i, t in enumerate(th):
            cs.paste(t, (10 + (i % cols) * 310, 10 + (i // cols) * 310))
        cs.save(os.path.join(out, "set_contact.jpg"), quality=88)
    return summ


# ---------------------------------------------------------------------------------------------- self-test
def selftest():
    ok = True

    def check(name, cond, info=""):
        nonlocal ok
        ok &= bool(cond)
        print(("PASS " if cond else "FAIL ") + name + (f"  ({info})" if info else ""))

    W, H = 900, 700
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(0)
    left = np.stack([200 - 140 * x / W] * 3, -1)
    m = measure(Image.fromarray(np.clip(left + rng.normal(0, 0.5, (H, W, 1)), 0, 255).astype(np.uint8)))
    check("Light falling off left to right is read as such", m["light_bias_left_minus_right"] > 0.3 and "left to right" in " ".join(m["words"]), str(m["light_bias_left_minus_right"]))
    warm = np.stack([np.full((H, W), 190.), np.full((H, W), 150.), np.full((H, W), 105.)], -1)
    mw = measure(Image.fromarray(warm.astype(np.uint8)))
    check("A warm frame reads warm", "warm overall" in mw["words"], str(mw["mid_lean_warm_magenta"]))
    flat = np.full((H, W, 3), 128.0) + rng.normal(0, 4.0, (H, W, 1))
    mg = measure(Image.fromarray(np.clip(flat, 0, 255).astype(np.uint8)))
    check("Grain sigma 4 measured within 25% (high-pass of the flattest blocks)", 2.6 < mg["grain_sigma"] < 5.0, str(mg["grain_sigma"]))
    clip = np.full((H, W, 3), 120.0); clip[:, : W // 4] = 255
    mc = measure(Image.fromarray(clip.astype(np.uint8)))
    check("Blown whites counted (25% of the frame)", 23 < mc["clip_highlights_pct"] < 27, str(mc["clip_highlights_pct"]))
    flat = np.zeros((H, W, 3)); flat[...] = (255, 196, 40)       # a saturated brand yellow is a colour, not a blown highlight
    my = measure(Image.fromarray(flat.astype(np.uint8)))
    check("A flat saturated yellow is channel-saturated, not blown", my["clip_highlights_pct"] == 0 and my["channel_clip_pct"] > 99, f"{my['clip_highlights_pct']} / {my['channel_clip_pct']}")
    blob = np.full((H, W, 3), 60.0)
    yy, xx = np.ogrid[0:H, 0:W]
    blob[((xx - W * 2 / 3) ** 2 + (yy - H / 3) ** 2) < 60 ** 2] = (230, 120, 40)
    mb = measure(Image.fromarray(blob.astype(np.uint8)))
    check("Visual weight found near the upper-right thirds point", abs(mb["weight_centroid"][0] - 2 / 3) < 0.08 and abs(mb["weight_centroid"][1] - 1 / 3) < 0.1 and mb["nearest_anchor"] == [0.667, 0.333], str(mb["weight_centroid"]))
    check("Mostly empty frame reads as empty space", mb["empty_space_share"] > 0.7, str(mb["empty_space_share"]))
    target = summarise([measure(Image.fromarray(np.clip(np.stack([30 + 160 * x / W] * 3, -1) + rng.normal(0, 3, (H, W, 1)), 0, 255).astype(np.uint8))) for _ in range(4)])
    ours = measure(Image.fromarray(np.clip(np.stack([30 + 160 * x / W] * 3, -1) * 0 + 140 + rng.normal(0, 0.3, (H, W, 1)), 0, 255).astype(np.uint8)))
    gaps = compare(ours, target)
    names = [g["field"] for g in gaps]
    check("Compare flags lifted blacks and missing grain against the target set", "black_point" in names and "grain_sigma" in names, ", ".join(names[:5]))
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", choices=["card", "set", "compare"])
    ap.add_argument("a", nargs="?"); ap.add_argument("b", nargs="?")
    ap.add_argument("-o", "--out", default="look_out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    if a.cmd == "card" and a.a:
        os.makedirs(a.out, exist_ok=True)
        im = _load(a.a); m = measure(im)
        base = os.path.join(a.out, os.path.splitext(os.path.basename(a.a))[0])
        json.dump(m, open(base + "_look.json", "w"), indent=1)
        open(base + "_look.md", "w", encoding="utf-8").write(card_md(m, os.path.basename(a.a)))
        sheet(im, m, base + "_look.jpg")
        print(card_md(m, os.path.basename(a.a)))
        return 0
    if a.cmd == "set" and a.a:
        s = run_set(a.a, a.out)
        print(open(os.path.join(a.out, "set.md"), encoding="utf-8").read())
        return 0
    if a.cmd == "compare" and a.a and a.b:
        m = measure(_load(a.a))
        gaps = compare(m, json.load(open(a.b)))
        if not gaps:
            print("Inside the target look on every measured field.")
        for g in gaps:
            print(f"- {g['what']}: ours {g['ours']} vs target {g['target']} (range {g['range'][0]}-{g['range'][1]}), {g['direction']} by {g['size']} spreads -> {g['fix']}")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
