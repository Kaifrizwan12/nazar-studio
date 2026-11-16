#!/usr/bin/env python3
"""
nazar-voiceprint/engine/score_pattern.py: does a folder of pieces follow a visual pattern?

Takes a small pattern file (what the visual layers measured) and scores each piece on five
checks that can be measured from pixels:
  format    the canvas has the pattern's shape (ratio within 1%: 4:5 stays 4:5 at any pixel size)
  ground    the outer band of the canvas is one of the pattern's grounds (OKLab distance < 0.10)
  palette   80%+ of pixels sit within 0.07 (OKLab) of a pattern swatch
  accent    the accent colour covers at most 20% of the piece, and 0.3%+ if the archive usually carries one
  device    no filled accent button or pill unless the archive itself uses them (10%+ of pieces)
Photo-led posts (a photo fills the frame) are scored on canvas size only, and reported apart, because the pattern describes flat-ground slides.
It scores conformance to the habits, so it says nothing about whether a piece is good or
whether the habits are the right ones. Two uses:
  held-out real pieces   a pattern built from some of a person's work, scored on the rest:
                         if the real ones pass, the habits generalise
  generated pieces       the same score on what an AI made with and without the PATTERN:
                         if the gap is large, the PATTERN changed the output
    python score_pattern.py --build train_folder pattern.json [asset files...]   # measure the pattern from the training set;
                                                                                 # asset files (exact backdrops) add their colours
    python score_pattern.py --prompt pattern.json                 # the pattern as a paste-ready prompt block
    python score_pattern.py pattern.json folder [--json]

pattern.json: {"format": [1080, 1350], "grounds": ["#DFE3DE", ...], "swatches": ["#FFFFFF", ...], "accent": "#338AE9"}
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from visual import srgb_to_oklab  # noqa: E402

EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def lab_of_hex(hexes):
    rgb = np.array([[int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)] for h in hexes], float)
    return srgb_to_oklab(rgb / 255.0)


def near(pix_lab, ref_lab):
    return np.min(np.linalg.norm(pix_lab[:, None, :] - ref_lab[None], axis=2), axis=1)


def is_photo(im):
    """Photo-led posts have far more colours than flat slides: entropy of a 3-bit-per-channel colour
    histogram of 4.3+ bits. Measured on a real archive: 6 of 7 photo posts (a dark night photo scored
    3.7 and is missed) and no flat slide reached it."""
    t = im.copy(); t.thumbnail((200, 200))
    q = (np.asarray(t) // 32).reshape(-1, 3)
    h = np.bincount(q[:, 0] * 64 + q[:, 1] * 8 + q[:, 2], minlength=512) / len(q)
    h = h[h > 0]
    return float(-(h * np.log2(h)).sum()) >= 4.3


def has_pill(im, accent_lab):
    """A filled accent-colour button or pill: a solid, wide, short block of the accent colour.
    Type and mascots in the accent colour are not solid blocks, so they don't count."""
    import layout
    t = im.copy(); t.thumbnail((400, 400))
    lab = srgb_to_oklab(np.asarray(t, float).reshape(-1, 3) / 255.0)
    m = (np.linalg.norm(lab - accent_lab[0], axis=1) < 0.08).reshape(t.height, t.width)
    for x0, y0, x1, y1, area in layout.components(m):
        w, h = x1 - x0, y1 - y0
        if 0.03 * t.height <= h <= 0.10 * t.height and 2 <= w / max(h, 1) <= 8 and area / (w * h) >= 0.75:
            return True
    return False


def score(path, pat, refs):
    im = Image.open(path).convert("RGB")
    photo = is_photo(im)
    size = list(im.size)
    sm = np.asarray(im.resize((96, 96)), float)
    band = np.concatenate([sm[:5].reshape(-1, 3), sm[-5:].reshape(-1, 3), sm[:, :5].reshape(-1, 3), sm[:, -5:].reshape(-1, 3)])
    ground_d = float(near(srgb_to_oklab(np.median(band, 0)[None] / 255.0), refs["grounds"])[0])
    lab = srgb_to_oklab(sm.reshape(-1, 3) / 255.0)
    pal_share = float((near(lab, refs["swatches"]) < 0.07).mean())
    acc_share = float((near(lab, refs["accent"]) < 0.08).mean())
    ratio_ok = abs(size[0] / size[1] - pat["format"][0] / pat["format"][1]) < 0.01     # 4:5 is the habit; pixel size varies by platform
    checks = {"format": ratio_ok, "ground": ground_d < 0.10,
              "palette": pal_share >= 0.80,
              "accent": acc_share <= 0.20 and (acc_share >= 0.003 or pat.get("accent_presence", 1.0) < 0.80),   # absence is fine if the archive often goes without
              "device": not (has_pill(im, refs["accent"]) and pat.get("devices", {}).get("accent_pill", 0) < 0.10)}
    if photo:   # a photo post can't sit on a flat ground: scored on canvas size only
        checks = {"format": checks["format"]}
    return {"file": os.path.basename(path), "mode": "photo" if photo else "flat", "checks": checks, "score": sum(checks.values()) / len(checks),
            "ground_dist": round(ground_d, 3), "palette_share": round(pal_share, 2), "accent_share": round(acc_share, 3)}


def asset_swatches(paths, k=6):
    """The colours of the brand's exact asset files (backdrops, logo): they ARE the palette, glows included."""
    import visual
    out = []
    for p in paths:
        im = Image.open(p).convert("RGB"); im.thumbnail((200, 200))
        x = srgb_to_oklab(np.asarray(im, float).reshape(-1, 3) / 255.0)
        idx = np.random.default_rng(0).choice(len(x), min(6000, len(x)), replace=False)
        cent = visual.kmeans_pp(x[idx], k, 0)[0]
        rgb = (np.clip(visual.oklab_to_srgb(cent), 0, 1) * 255).astype(int)
        out += ["#%02X%02X%02X" % tuple(c) for c in rgb]
    return out


def build(folder, assets=()):
    """Measure a pattern file from a folder of pieces (the training set): the most common canvas size,
    the palette of the light-ground pieces and of the dark-ground pieces (their two biggest colours
    are the grounds), and the one accent colour."""
    import portfolio, visual
    files = sorted(os.path.join(folder, f) for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in EXTS)
    small, sizes = [], []
    for f in files:
        im = Image.open(f).convert("RGB"); sizes.append(im.size); im.thumbnail((256, 256)); small.append((os.path.basename(f), im))
    lum = []
    for _, im in small:
        a = np.asarray(im.resize((64, 64)), float)
        band = np.concatenate([a[:4].reshape(-1, 3), a[-4:].reshape(-1, 3), a[:, :4].reshape(-1, 3), a[:, -4:].reshape(-1, 3)])
        lum.append(np.median(band, 0) @ [0.2126, 0.7152, 0.0722])
    grounds, swatches, accent = [], [], None
    for dark in (False, True):
        grp = [x for x, l in zip(small, lum) if (l < 110) == dark]
        if len(grp) < 3:
            continue
        pal = visual.palette(grp)
        ordered = sorted(pal, key=lambda c: -c["share"])
        grounds += [c["hex"] for c in ordered if c["role"] in ("ground", "support")][:2]
        swatches += [c["hex"] for c in ordered if c["role"] == "support"][2:]
        accent = accent or next((c["hex"] for c in pal if c["role"] == "accent"), None)
    size = max(set(sizes), key=sizes.count)
    acc = lab_of_hex([accent])
    pills = float(np.mean([has_pill(Image.open(f).convert("RGB"), acc) for f in files]))
    pat = {"format": list(size), "grounds": grounds, "swatches": swatches + ["#FFFFFF", "#000000"], "accent": accent,
           "devices": {"accent_pill": round(pills, 2)}}
    pat["accent_presence"] = round(float(np.mean([0.003 <= float((near(srgb_to_oklab(np.asarray(Image.open(f).convert("RGB").resize((96, 96)), float).reshape(-1, 3) / 255.0), acc) < 0.08).mean()) <= 0.20 for f in files])), 2)
    if assets:
        pat["asset_swatches"] = asset_swatches(assets)
    return pat


def prompt_block(pat):
    """The pattern as the prompt an expert would write: measured facts first, then blanks only the person can fill
    (exact asset files, voice, reference pieces). Paste it into any AI before the brief."""
    w, h = pat["format"]
    from math import gcd
    g = gcd(w, h)
    lines = [f"Format is {w // g}:{h // g} ({w}x{h}).",
             f"Grounds: {', '.join(pat['grounds'])}. Light and dark slides share one layout; use the exact backdrop files, never redraw or recolour them.",
             f"One accent colour, {pat['accent']}, used sparingly (about 0.3% to 20% of a piece), never as a filled block.",
             "Palette beyond that: " + ", ".join(pat["swatches"][:6]) + ".",
             "Do not add buttons, pills or any device this brand's own work doesn't use" + (f" (a filled accent button appears in only {pat['devices']['accent_pill']:.0%} of its pieces)." if pat.get("devices") else "."),
             "Not measured, so the person writes it in: <exact asset files and where they sit> <headline style, from the VLM pass> <voice and language mix> <two or three reference pieces>."]
    return "\n".join(lines)


def run(pat, folder):
    refs = {"grounds": lab_of_hex(pat["grounds"]), "accent": lab_of_hex([pat["accent"]]),
            "swatches": lab_of_hex(pat["swatches"] + pat.get("asset_swatches", []) + pat["grounds"] + [pat["accent"]])}
    files = sorted(os.path.join(folder, f) for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in EXTS)
    rows = [score(f, pat, refs) for f in files]
    flat = [r for r in rows if r["mode"] == "flat"]; photo = [r for r in rows if r["mode"] == "photo"]
    per = {k: round(float(np.mean([r["checks"][k] for r in flat])), 2) for k in ("format", "ground", "palette", "accent", "device")} if flat else {}
    return {"n": len(rows), "flat_pieces": len(flat), "photo_posts": len(photo),
            "mean_score": round(float(np.mean([r["score"] for r in flat])), 2) if flat else None, "per_check": per,
            "photo_size_ok": round(float(np.mean([r["score"] for r in photo])), 2) if photo else None, "pieces": rows}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    if sys.argv[1] == "--prompt":
        print(prompt_block(json.load(open(sys.argv[2])))); sys.exit()
    if sys.argv[1] == "--build":
        pat = build(sys.argv[2], sys.argv[4:]); json.dump(pat, open(sys.argv[3], "w"), indent=1); print(json.dumps(pat)); sys.exit()
    r = run(json.load(open(sys.argv[1])), sys.argv[2])
    if "--json" in sys.argv:
        print(json.dumps(r, indent=1))
    else:
        print(f"{r['flat_pieces']} flat pieces, mean score {r['mean_score']}  per check {r['per_check']};  {r['photo_posts']} photo posts, right canvas size: {r['photo_size_ok']}")
