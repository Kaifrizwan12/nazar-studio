#!/usr/bin/env python3
"""
nazar-voiceprint/engine/devices.py: find a brand's recurring visual DEVICES (mascot, stickers, ID cards, chat bubbles,
stars, badges) in a folder of finished pieces, so a job can reuse them. cluster.py's recurring() tiles a fixed grid and
cannot find an object that moves between pieces; this segments objects instead.

  python devices.py <folder of finished pieces> <out folder> [--min-pieces 2]
  -> <out>/devices_sheet.jpg  best crop of each device, labelled "in N of M pieces" (and how many were an exact match)
     <out>/devices.txt        the same as a short list (size, colours, where it sits, which pieces)

How: per piece (downscaled to 320 px wide) the page ground is the colour(s) dominating the border; everything unlike it is
"ink"; ink is closed by a small dilation so one object becomes one region; regions are cut out as connected components.
Text lines are dropped (thin, one colour, or made of many small letter parts). Each crop gets a thumbnail, a colour
histogram, a size and an aspect. Two crops from DIFFERENT pieces link if the thumbnails match (same sticker) or the
colour family, size and aspect agree (same character in another pose). Groups count distinct pieces.
Limits: photo or gradient grounds have no single ground colour, so objects there are missed; an object touching the page
edge is cut; a card with text inside is one device (that is intended). Pure numpy + Pillow.
"""
import argparse, os, sys, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W = 320


def load(folder):
    out = []
    for p in sorted(glob.glob(os.path.join(folder, "*"))):
        if p.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            try:
                out.append((os.path.basename(p), Image.open(p).convert("RGB")))
            except Exception:
                pass
    return out


def label(mask):
    """4-connected components of a boolean mask (numpy, run-based union-find). Returns (labels, n)."""
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    parent = [0]

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    nxt = 1
    prev = []  # runs of previous row: (start, end, id)
    for y in range(h):
        row = mask[y]
        d = np.diff(np.concatenate(([0], row.astype(np.int8), [0])))
        starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
        cur = []
        for s, e in zip(starts, ends):
            ids = [r[2] for r in prev if r[0] < e and r[1] > s]
            if ids:
                i = find(ids[0])
                for j in ids[1:]:
                    parent[find(j)] = i
            else:
                i = nxt; parent.append(i); nxt += 1
            lab[y, s:e] = i
            cur.append((s, e, i))
        prev = cur
    roots = np.array([find(i) for i in range(nxt)])
    _, inv = np.unique(roots, return_inverse=True)
    return inv[lab] * (lab > 0) if nxt > 1 else lab, int(inv.max()) if nxt > 1 else 0


def dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + 1:
                out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def quant(a):
    q = (a // 64).astype(np.int32)           # 4 levels per channel
    return q[..., 0] * 16 + q[..., 1] * 4 + q[..., 2]


def objects(im):
    """Cut candidate non-text objects out of one piece. Returns a list of dicts."""
    sc = W / im.width
    small = im.resize((W, max(1, round(im.height * sc))), Image.BILINEAR)
    a = np.asarray(small, np.uint8)
    h, w = a.shape[:2]
    q = quant(a)
    border = np.concatenate([q[0], q[-1], q[:, 0], q[:, -1]])
    cnt = np.bincount(border, minlength=64) / border.size
    ground = set(np.where(cnt > 0.12)[0].tolist()) or {int(cnt.argmax())}
    # near-ground colours (neighbouring bins) count as ground too, so soft edges do not become objects
    gcol = np.array([[(g // 16) * 64 + 32, ((g // 4) % 4) * 64 + 32, (g % 4) * 64 + 32] for g in ground], np.float32)
    d = np.abs(a[:, :, None, :].astype(np.float32) - gcol[None, None]).max(-1).min(-1)
    ink = d > 48
    ink[:2] = ink[-2:] = False
    ink[:, :2] = ink[:, -2:] = False
    closed = dilate(ink, 3)
    lab, n = label(closed)
    out = []
    page = h * w
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if ys.size < 0.004 * page:
            continue
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        bw, bh = x1 - x0, y1 - y0
        if bw * bh > 0.55 * page or bw > 0.9 * w or bh > 0.9 * h:
            continue
        if min(bw, bh) < 14:
            continue
        m = ink[y0:y1, x0:x1] & (lab[y0:y1, x0:x1] == i)
        if m.mean() < 0.12:
            continue
        pix = a[y0:y1, x0:x1][m]
        hist = np.bincount(quant(pix), minlength=64) / len(pix)
        top2 = np.sort(hist)[-2:].sum()
        parts = label(m)[1]
        asp = bw / bh
        if (top2 > 0.9 and (asp > 2.6 or asp < 0.38)) or (top2 > 0.9 and parts > 12) or parts > 40:
            continue                               # a text line or block
        # the crop keeps the original pixels, cut at the full-resolution box
        box = tuple(int(round(v / sc)) for v in (x0 - 3, y0 - 3, x1 + 3, y1 + 3))
        crop = im.crop((max(0, box[0]), max(0, box[1]), min(im.width, box[2]), min(im.height, box[3])))
        sub = a[y0:y1, x0:x1].astype(np.float32).copy()
        sub[~m] = 128                              # ground is not part of the object: compare ink only
        th = np.asarray(Image.fromarray(sub.astype(np.uint8)).resize((24, 24), Image.BILINEAR), np.float32)
        out.append(dict(crop=crop, thumb=th, hist=hist, size=bw * bh / page, asp=asp,
                        pos=((x0 + x1) / 2 / w, (y0 + y1) / 2 / h), colours=np.argsort(hist)[-3:][::-1].tolist(),
                        parts=parts))
    return out


def link(a, b):
    """'same' (thumbnails match), 'family' (colour, size and shape agree) or None."""
    r = a["asp"] / b["asp"]
    if not 0.8 < r < 1.25:
        return None
    s = a["size"] / b["size"]
    if np.abs(a["thumb"] - b["thumb"]).mean() < 26 and 0.7 < s < 1.45:
        return "same"
    if np.minimum(a["hist"], b["hist"]).sum() > 0.72 and 0.6 < s < 1.65 and 0.85 < r < 1.18:
        return "family"
    return None


def find_devices(folder, min_pieces=2):
    pieces = load(folder)
    items = []
    for pi, (name, im) in enumerate(pieces):
        for o in objects(im):
            o["piece"] = pi; o["name"] = name
            items.append(o)
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    exact = {}
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i]["piece"] == items[j]["piece"]:
                continue
            k = link(items[i], items[j])
            if k:
                parent[find(i)] = find(j)
                if k == "same":
                    exact.setdefault(i, set()).add(j); exact.setdefault(j, set()).add(i)
    groups = {}
    for i in range(len(items)):
        groups.setdefault(find(i), []).append(i)
    res = []
    for g in groups.values():
        ps = {items[i]["piece"] for i in g}
        if len(ps) < min_pieces:
            continue
        ex = {items[i]["piece"] for i in g if i in exact}
        # best crop: the member with the most colour variety and the most links of its own
        best = max(g, key=lambda i: (len(exact.get(i, ())), items[i]["crop"].width * items[i]["crop"].height))
        res.append(dict(pieces=sorted(items[i]["name"] for i in g if True), n=len(ps), n_exact=len(ex), best=items[best],
                        members=g))
    res.sort(key=lambda r: (r["n"], r["n_exact"]), reverse=True)
    return res, len(pieces), items


def sheet(res, total, out, cell=240, cols=4, limit=16):
    res = res[:limit]
    if not res:
        Image.new("RGB", (cell, 60), "white").save(out); return
    rows = (len(res) + cols - 1) // cols
    sh = Image.new("RGB", (cols * cell, rows * (cell + 34)), (245, 245, 245))
    dr = ImageDraw.Draw(sh)
    try:
        f = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "..", "..", "nazar-core", "engine", "fonts",
                                            "SpaceGrotesk-Medium.ttf"), 15)
    except Exception:
        f = ImageFont.load_default()
    for k, r in enumerate(res):
        cr = r["best"]["crop"].copy(); cr.thumbnail((cell - 16, cell - 16))
        x, y = (k % cols) * cell, (k // cols) * (cell + 34)
        sh.paste(cr, (x + (cell - cr.width) // 2, y + 8 + (cell - 16 - cr.height) // 2))
        dr.text((x + 8, y + cell + 6), f"{r['n']} of {total} pieces ({r['n_exact']} exact)", fill=(20, 20, 20), font=f)
    sh.save(out, quality=90)


def write(folder, out, min_pieces=2):
    os.makedirs(out, exist_ok=True)
    res, total, _ = find_devices(folder, min_pieces)
    sheet(res, total, os.path.join(out, "devices_sheet.jpg"))
    lines = [f"{len(res)} recurring object group(s) across {total} pieces (look at devices_sheet.jpg and name each one):"]
    for k, r in enumerate(res[:16], 1):
        b = r["best"]
        lines.append(f"{k}. in {r['n']} of {total} pieces ({r['n_exact']} near-identical); size {b['size']*100:.0f}% of page, "
                     f"aspect {b['asp']:.2f}, usually at ({b['pos'][0]:.2f},{b['pos'][1]:.2f}); e.g. {', '.join(r['pieces'][:3])}")
    open(os.path.join(out, "devices.txt"), "w").write("\n".join(lines) + "\n")
    return res, total, lines


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder"); ap.add_argument("out"); ap.add_argument("--min-pieces", type=int, default=2)
    a = ap.parse_args()
    print("\n".join(write(a.folder, a.out, a.min_pieces)[2]))
