#!/usr/bin/env python3
"""
nazar-core/engine/usage.py: the brand's USAGE rules, learned from its own pieces, and the check of new slides against them.
A palette says which colours exist; usage says which colour goes on which element, on which kind of page, and where the marks sit.

  learn   marks        text that repeats at a stable place across pieces (the logo wordmark, the handle): where, how big, how often
          colour roles which colour each text role uses (headline, body, small) on each ground (light, dark), with shares
          ground words which words each ground tends to carry (what content goes on light, what on dark)
  check   a slide's text colours per role against the archive's for that role and ground (drift), its marks against their usual
          place, and whether its ground comes from the supplied backdrop files

    python usage.py learn train_folder usage.json
    python usage.py check slides_folder usage.json [backdrop files...]

Marks need macOS Vision (read_text.py) for the boxes. Roles come from type size: the tallest lines are the headline, the smallest the
small print. It measures; the person decides.
"""
import difflib
import json
import os
import re
import sys
from collections import Counter

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "nazar-voiceprint", "engine"))
import layout  # noqa: E402
import read_text  # noqa: E402
from score_pattern import is_photo, srgb_to_oklab  # noqa: E402
import visual  # noqa: E402

EXTS = (".png", ".jpg", ".jpeg", ".webp")
DRIFT = 0.07          # OKLab distance from every archive colour for that role and ground
STOP = set("the and for you your are with that this from what they will not but all can our was has its who how why".split())


def files_in(folder):
    return [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.lower().endswith(EXTS)]


def hexof(lab):
    rgb = np.clip(visual.oklab_to_srgb(np.asarray(lab, float)[None]), 0, 1)[0] * 255
    return "#%02X%02X%02X" % tuple(int(v) for v in rgb)


def ground_of(im):
    a = np.asarray(im.resize((64, 64)), float)
    band = np.concatenate([a[:4].reshape(-1, 3), a[-4:].reshape(-1, 3), a[:, :4].reshape(-1, 3), a[:, -4:].reshape(-1, 3)])
    return "light" if float(np.median(band, 0) @ [0.2126, 0.7152, 0.0722]) >= 110 else "dark"


def text_roles(im):
    """[(role, oklab colour, box)] for the text lines of a piece; role by type size."""
    t = im.copy(); t.thumbnail((900, 1200))
    m = layout.ink(t); h, w = m.shape
    a = np.asarray(t.resize((w, h)), float) / 255.0
    lines = []
    for b in layout.components(layout.dilate_x(m, max(6, w // 28))):
        sub = m[b[1]:b[3], b[0]:b[2]]; ys, xs = np.where(sub)
        if not len(ys):
            continue
        x0, y0, x1, y1 = b[0] + xs.min(), b[1] + ys.min(), b[0] + xs.max() + 1, b[1] + ys.max() + 1
        bw, bh = x1 - x0, y1 - y0
        if bw > 0.06 * w and 0.006 * h < bh < 0.2 * h and bw > 1.6 * bh:
            lines.append((x0, y0, x1, y1))
    if not lines:
        return []
    hmax = max(y1 - y0 for _, y0, _, y1 in lines)
    out = []
    for x0, y0, x1, y1 in lines:
        box = a[y0:y1, x0:x1].reshape(-1, 3); ring = np.concatenate([a[y0, x0:x1], a[y1 - 1, x0:x1], a[y0:y1, x0], a[y0:y1, x1 - 1]])
        lab, bg = srgb_to_oklab(box), srgb_to_oklab(np.median(ring, 0)[None])[0]
        ink = lab[np.linalg.norm(lab - bg, axis=1) > 0.15]
        if len(ink) < 15:
            continue
        hh = y1 - y0
        role = "headline" if hh >= 0.6 * hmax else "small" if hh < 0.35 * hmax else "body"
        out.append((role, np.median(ink, 0), (x0 / w, y0 / h, (x1 - x0) / w, hh / h)))
    return out


def norm(s):
    return re.sub(r"[^a-z0-9@.]", "", s.lower())


def learn(train):
    paths = [p for p in files_in(train) if not is_photo(Image.open(p).convert("RGB"))]
    n = len(paths)
    cols, gw, grounds = {}, {"light": Counter(), "dark": Counter()}, Counter()
    for p in paths:
        im = Image.open(p).convert("RGB"); g = ground_of(im); grounds[g] += 1
        for role, lab, _ in text_roles(im):
            cols.setdefault(f"{g}/{role}", []).append(lab)
    roles = {}
    for k, v in cols.items():
        X = np.array(v)
        kk = min(3, len(np.unique(np.round(X, 3), axis=0)))
        try:
            if kk <= 1:
                raise ValueError
            c, lbl, _ = visual.kmeans_pp(X, kk, 0)
        except Exception:                                  # one colour only (or identical points): a single role colour
            c, lbl = np.median(X, 0)[None], np.zeros(len(X), int)
        sh = np.bincount(lbl, minlength=len(c)) / len(X)
        roles[k] = sorted([[hexof(ci), round(float(s), 2), [round(float(x), 4) for x in ci]] for ci, s in zip(c, sh)], key=lambda r: -r[1])
    # calibration: how far the archive's OWN lines sit from their role's colours; flag only what is more unusual than 95% of them
    tol = {}
    for k, v in cols.items():
        C = np.array([r[2] for r in roles[k]])
        d = [float(np.min(np.linalg.norm(C - x, axis=1))) for x in v]
        tol[k] = round(max(DRIFT, float(np.percentile(d, 95)) * 1.25), 3)
    # marks: OCR text that repeats across pieces at a stable place
    boxes = read_text.read_boxes(paths)
    clusters = []                                          # [rep, set(pieces), [boxes]]
    for p in paths:
        g = ground_of(Image.open(p).convert("RGB"))
        for c_, text, b in boxes.get(p, []):
            k = norm(text)
            if len(k) < 5 or b is None:
                continue
            for cl in clusters:
                if difflib.SequenceMatcher(None, cl[0], k).ratio() >= 0.72:
                    cl[1].add(p); cl[2].append(b); break
            else:
                clusters.append([k, {p}, [b]])
            for wd in re.findall(r"[a-z]{4,}", text.lower()):
                if wd not in STOP:
                    gw[g][wd] += 1
    marks = []
    for rep, ps, bs in clusters:
        if len(ps) / max(n, 1) >= 0.25:
            Bs = np.array(bs); B = np.median(Bs, 0)
            cen = np.stack([Bs[:, 0] + Bs[:, 2] / 2, Bs[:, 1] + Bs[:, 3] / 2], 1); c0 = np.array([B[0] + B[2] / 2, B[1] + B[3] / 2])
            spread = float(np.percentile(np.abs(cen - c0).max(1), 90))      # how far the mark wanders in the archive's own pieces
            marks.append({"text": rep, "pieces": len(ps), "share": round(len(ps) / n, 2), "kind": "handle" if rep.startswith("@") else "mark",
                          "box": [round(float(x), 3) for x in B], "tol": round(max(0.06, spread * 1.25), 3)})
    return {"pieces": n, "grounds": dict(grounds), "colour_roles": roles, "role_tol": tol, "marks": marks,
            "ground_words": {g: [w for w, _ in c.most_common(10)] for g, c in gw.items()}}


def fit_backdrop(path, size):
    """The supplied backdrop fitted to the slide's size the way place_asset does it: crop if taller, else uniform upscale and side crop."""
    im = Image.open(path).convert("RGB"); w, h = im.size; W, H = size
    if h / w >= H / W:
        sc = W / w; im = im.resize((W, round(h * sc)), Image.BILINEAR); return im.crop((0, 0, W, H))
    sc = H / h; im = im.resize((round(w * sc), H), Image.BILINEAR); return im.crop((im.width - W, 0, im.width, H))


def backdrop_distance(im, backdrops):
    """Mean OKLab distance between the slide's outer band and each backdrop's, after fitting; returns (best distance, file)."""
    small = (90, round(90 * im.height / im.width))
    def band(x):
        a = np.asarray(x.resize(small, Image.BILINEAR), float) / 255.0
        k = max(2, small[0] // 20)
        return srgb_to_oklab(np.concatenate([a[:, :k].reshape(-1, 3), a[:, -k:].reshape(-1, 3), a[-k:].reshape(-1, 3)]))
    s = band(im)
    best = (9.0, None)
    for b in backdrops:
        d = float(np.median(np.linalg.norm(s - band(fit_backdrop(b, im.size)), axis=1)))
        best = min(best, (d, os.path.basename(b)))
    return best


def check(slides, usage, backdrops=()):
    roles = usage["colour_roles"]
    marks = [m for m in usage["marks"] if m["share"] >= 0.4]
    out = ["USAGE (each element's colour against what the archive uses for that element on that ground; marks against their usual place)"]
    paths = files_in(slides)
    boxes = read_text.read_boxes(paths) if marks else {}
    for p in paths:
        im = Image.open(p).convert("RGB"); g = ground_of(im); flags = []
        seen = set()
        for role, lab, _ in text_roles(im):
            arch = roles.get(f"{g}/{role}")
            if not arch or role in seen:
                continue
            d = min(float(np.linalg.norm(lab - np.array(c[2]))) for c in arch)
            if d > usage.get("role_tol", {}).get(f"{g}/{role}", DRIFT):
                seen.add(role)
                flags.append(f"{role} on {g} is {hexof(lab)}; the archive sets it in " + ", ".join(f"{c[0]} ({c[1]:.0%})" for c in arch))
        for mk in marks:
            hit = [b for _, t, b in boxes.get(p, []) if b and difflib.SequenceMatcher(None, mk["text"], norm(t)).ratio() >= 0.72]
            if hit:
                b, a = hit[0], mk["box"]
                tolm = mk.get("tol", 0.12)
                if abs((b[0] + b[2] / 2) - (a[0] + a[2] / 2)) > tolm or abs((b[1] + b[3] / 2) - (a[1] + a[3] / 2)) > tolm:
                    flags.append(f"the {mk['kind']} '{mk['text']}' sits at x {b[0]:.0%}, y {b[1]:.0%}; the archive puts it at x {a[0]:.0%}, y {a[1]:.0%}")
        if backdrops:
            d, f = backdrop_distance(im, backdrops)
            if d > 0.06:
                flags.append(f"its ground does not match any supplied backdrop (closest {f}, distance {d:.2f})")
        out.append(f"  {os.path.basename(p)} [{g}]: " + ("ok" if not flags else "; ".join(flags)))
    return "\n".join(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "learn":
        u = learn(a[1]); json.dump(u, open(a[2], "w"), indent=1)
        print(f"{a[2]}: {u['pieces']} pieces; grounds {u['grounds']}; marks " + ", ".join(f"{m['kind']} '{m['text']}' in {m['share']:.0%} at x {m['box'][0]:.0%} y {m['box'][1]:.0%}" for m in u["marks"]))
        for k, v in u["colour_roles"].items():
            print(f"  {k}: " + ", ".join(f"{c[0]} {c[1]:.0%}" for c in v))
        for g, ws in u["ground_words"].items():
            print(f"  words on {g}: {', '.join(ws)}")
    elif len(a) >= 3 and a[0] == "check":
        print(check(a[1], json.load(open(a[2])), a[3:]))
    else:
        sys.exit(__doc__)
