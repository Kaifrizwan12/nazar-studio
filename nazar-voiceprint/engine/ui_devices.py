#!/usr/bin/env python3
"""
nazar-voiceprint/engine/ui_devices.py: find UI-style devices on a finished piece: chat bubbles, buttons and pills, cards,
progress bars, notification badges and toggles. devices.py drops these (a pill reads as a text line, a card swallows its
contents), so they get their own pass.

    python ui_devices.py piece.png [more.png ...]     # prints what each piece carries, with boxes

How (the "old-fashioned" non-text pass from GUI element detection, kept simple; see references/research_ui_detection.md):
UI devices are FLAT FILLS with a regular outline, so the piece is downscaled to 320 px wide and split into flat colour
layers (a 3x3 mode filter folds anti-aliased edges back in; every pixel snaps to the nearest heavy colour, so JPEG noise
on a bin edge does not split a fill). Each layer is cut into connected regions, and each
region gets a shape reading: how much of its box it fills once holes (the label or text inside) are closed, whether its
corners are rounded (the top row's inset, beyond the ~2 px any filter chips off), how tall its end columns run (a pill's ends are half circles), whether a narrow tail hangs off
its bottom or top, and whether a round knob of another colour sits at one end (a toggle).
  badge        small filled circle (about 2 to 9% of the width)
  toggle       pill with a round knob of another colour at one end
  button/pill  wide short block (aspect 2 to 9, 2.5 to 12% of the height) with rounded or half-circle ends
  chat bubble  rounded block with a narrow tail at a bottom or top corner
  card         larger flat block (3 to 55% of the page), square or rounded corners
  progress bar two thin long blocks of different colours meeting end to end on one line (track + fill)
Tested on synthetic slides (test_ui_devices.py, PNG and JPEG q80); not yet on a real archive.
Limits: photo and gradient grounds have no flat layers, so nothing there is found; a bubble without a tail reads as a card;
a fill that sits exactly on a quantisation boundary can split. Candidates, not a verdict: look at the piece. Numpy + Pillow.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from devices import label  # noqa: E402

W = 320
KINDS = ("chat bubble", "button/pill", "card", "progress bar", "badge", "toggle")


def _layers(im):
    sc = W / im.width
    small = im.convert("RGB").resize((W, max(1, round(im.height * sc))), Image.BILINEAR)
    small = small.filter(ImageFilter.ModeFilter(3))          # anti-aliased edges fall back into their fill
    a = np.asarray(small, np.int32)
    q = (a // 16)                                              # 16 levels: a white card on an off-white ground stays apart
    key = q[..., 0] * 256 + q[..., 1] * 16 + q[..., 2]
    # a fill whose colour sits on a bin edge splits under JPEG noise: snap every pixel to the nearest heavy colour instead
    vals, cnt = np.unique(key, return_counts=True)
    flat = a.reshape(-1, 3); kf = key.ravel()
    cents = []
    for v in vals[cnt >= 0.0008 * key.size][np.argsort(-cnt[cnt >= 0.0008 * key.size])]:
        c = flat[kf == v].mean(0)
        if all(np.abs(c - d).max() > 14 for d in cents):
            cents.append(c)
    cents = np.array(cents)
    dist = np.abs(flat[:, None, :] - cents[None]).max(-1)
    lab = dist.argmin(1)
    lab[dist.min(1) > 22] = -1
    return a, lab.reshape(key.shape)


def _ground(key):
    border = np.concatenate([key[0], key[-1], key[:, 0], key[:, -1]])
    vals, cnt = np.unique(border, return_counts=True)
    return set(vals[cnt > 0.12 * border.size].tolist()) or {int(vals[cnt.argmax()])}


def _fill_holes(m):
    """Rows and columns closed between their first and last pixel: the region with its inner text filled in."""
    rows = np.zeros_like(m); cols = np.zeros_like(m)
    for y in range(m.shape[0]):
        xs = np.where(m[y])[0]
        if xs.size:
            rows[y, xs[0]:xs[-1] + 1] = True
    for x in range(m.shape[1]):
        ys = np.where(m[:, x])[0]
        if ys.size:
            cols[ys[0]:ys[-1] + 1, x] = True
    return rows & cols


def _shape(m):
    h, w = m.shape
    f = _fill_holes(m)
    fill = f.sum() / (w * h)
    k = max(1, min(h, w) // 8)
    corners = [f[:k, :k].mean(), f[:k, -k:].mean(), f[-k:, :k].mean(), f[-k:, -k:].mean()]
    cut = sum(c < 0.5 for c in corners)
    xs = np.where(f[0])[0]                                     # corner radius, read off the top row's inset: the mode filter
    r_top = ((xs[0] + (w - 1 - xs[-1])) / 2) if xs.size else 0  # chips ~2 px off any square corner, a real radius is larger
    ends = (f[:, 0].mean() + f[:, -1].mean()) / 2               # how tall the end columns run (pill ~ low)
    widths = f.sum(1) / w
    holes = f & ~m
    return dict(fill=fill, cut=cut, r=r_top, ends=ends, widths=widths, holes=holes, hole_share=holes.sum() / max(f.sum(), 1))


def _tail(widths):
    """A narrow tail at the bottom or top: 2+ rows under 40% of the width after (or before) rows over 70%."""
    n = len(widths)
    if n < 10:
        return False
    for seq in (widths, widths[::-1]):
        body = np.where(seq > 0.7)[0]
        if not body.size:
            continue
        rest = seq[body[-1] + 1:]
        if 2 <= np.sum((rest > 0) & (rest < 0.4)) <= 0.45 * n:
            return True
    return False


def _inside(b, outer):
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    return outer[0] <= cx <= outer[2] and outer[1] <= cy <= outer[3]


def _circles(key, ground, page, H, Wd):
    """Filled circles of any non-ground layer, as boxes in page fractions (toggle knobs, badges)."""
    out = []
    for v in np.unique(key):
        if int(v) in ground or v < 0:
            continue
        lab, n = label(key == v)
        for i in range(1, n + 1):
            ys, xs = np.where(lab == i)
            if ys.size < 20:
                continue
            bh, bw = ys.max() - ys.min() + 1, xs.max() - xs.min() + 1
            if 0.8 < bw / bh < 1.25 and 0.68 < ys.size / (bw * bh) < 0.9:
                out.append((xs.min() / Wd, ys.min() / H, (xs.max() + 1) / Wd, (ys.max() + 1) / H))
    return out


def _knob_at(c, box, h_frac):
    """A round knob inside a pill, at one end, about as tall as the pill."""
    if not _inside(c, box):
        return False
    d = c[3] - c[1]
    cx = ((c[0] + c[2]) / 2 - box[0]) / max(box[2] - box[0], 1e-6)
    return 0.5 * h_frac <= d <= 1.02 * h_frac and (cx < 0.4 or cx > 0.6)


def find(im):
    """List of dicts {kind, box (x0, y0, x1, y1) as fractions of the piece}."""
    a, key = _layers(im)
    H, Wd = key.shape
    page = H * Wd
    ground = _ground(key)
    found, bars = [], []
    circles = _circles(key, ground, page, H, Wd)
    for v in np.unique(key):
        if int(v) in ground or v < 0:
            continue
        mask = key == v
        if mask.sum() < 0.0008 * page:
            continue
        lab, n = label(mask)
        for i in range(1, n + 1):
            ys, xs = np.where(lab == i)
            if ys.size < 0.0008 * page:
                continue
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            bh, bw = y1 - y0, x1 - x0
            if bw * bh > 0.55 * page or min(bh, bw) < 3:
                continue
            m = lab[y0:y1, x0:x1] == i
            s = _shape(m)
            asp = bw / bh
            box = (x0 / Wd, y0 / H, x1 / Wd, y1 / H)
            solid = m.sum() / (bw * bh)
            if asp > 4 and bh <= 0.035 * H and s["fill"] > 0.8:
                bars.append((box, int(v), bh, (y0 + y1) / 2, x0, x1))
                continue
            if s["fill"] < 0.6:
                continue                                   # a letter, a doodle or a photo patch, not a UI block
            kind = None
            if 0.8 < asp < 1.25 and 0.68 < s["fill"] < 0.88 and 0.02 * Wd <= bw <= 0.09 * Wd and s["r"] >= max(2.5, 0.2 * bh) and solid > 0.65:   # solid: a letter o closed up is not a badge
                kind = "badge"
            elif 1.5 < asp < 2.9 and s["r"] >= max(2.5, 0.25 * bh) and s["ends"] < 0.75 and any(_knob_at(c, box, bh / H) for c in circles):
                kind = "toggle"
            elif 2 <= asp <= 9 and 0.025 * H <= bh <= 0.12 * H and s["r"] >= max(2.5, 0.25 * bh) and s["fill"] > 0.82 and s["hole_share"] < 0.6 and s["ends"] < 0.9:
                kind = "button/pill"
            elif s["r"] >= max(2.5, 0.08 * bh) and s["fill"] > 0.72 and bw * bh >= 0.012 * page and _tail(s["widths"]):
                kind = "chat bubble"
            elif 0.03 * page <= bw * bh and bw >= 0.2 * Wd and s["fill"] > 0.9 and solid > 0.5 and 0.25 < asp < 5:
                kind = "card"
            if kind:
                found.append(dict(kind=kind, box=tuple(round(float(c), 3) for c in box)))
    toggles = [f["box"] for f in found if f["kind"] == "toggle"]       # a toggle's knob is not a badge
    found = [f for f in found if not (f["kind"] == "badge" and any(_inside(f["box"], t) for t in toggles))]
    used = set()
    for i, (b1, v1, h1, yc1, xa1, xb1) in enumerate(bars):        # a track and its fill meet end to end on one line
        for j, (b2, v2, h2, yc2, xa2, xb2) in enumerate(bars):
            if j <= i or v1 == v2 or i in used or j in used:
                continue
            if abs(yc1 - yc2) <= max(h1, h2) * 0.6 and 0.5 < h1 / h2 < 2 and (abs(xb1 - xa2) <= 3 or abs(xb2 - xa1) <= 3):
                box = (min(b1[0], b2[0]), min(b1[1], b2[1]), max(b1[2], b2[2]), max(b1[3], b2[3]))
                found.append(dict(kind="progress bar", box=tuple(round(float(c), 3) for c in box)))
                used |= {i, j}
    return found


def summary(found):
    out = {}
    for f in found:
        out[f["kind"]] = out.get(f["kind"], 0) + 1
    return out


def shares(images):
    """Share of pieces that carry each UI device kind: the archive's habit, for score_pattern's habit score."""
    n = max(len(images), 1)
    seen = {k: 0 for k in KINDS}
    for im in images:
        for k in summary(find(im)):
            seen[k] += 1
    return {k: round(v / n, 2) for k, v in seen.items()}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        f = find(Image.open(p))
        print(f"{os.path.basename(p)}: " + (", ".join(f"{k} x{n}" for k, n in summary(f).items()) or "no UI-style devices"))
        for d in f:
            print(f"   {d['kind']:<13} at {d['box']}")
