#!/usr/bin/env python3
"""Sketch → vector. Kaif draws by hand; this turns the scan or phone photo into clean, editable SVG curves.

    python engine/trace.py sketch.jpg                       # three variants + compare sheet + report
    python engine/trace.py sketch.jpg --out exports/trace --name mark_v1 --crop 120,80,1400,1200
    python engine/trace.py sketch.jpg --variants balanced --fill "#1B1A17" --width-mm 60

Pipeline (numpy + Pillow only, MIT; no potrace/GPL code):
  1. Clean the photo: greyscale, flatten uneven light (divide by a heavy blur), Otsu threshold, despeckle.
  2. Trace pixel boundaries into closed loops (ink on the right), drop specks and tiny holes by area.
  3. Find corners (sharp turns) and extremes (where the curve turns horizontal or vertical); those become nodes,
     which is where a professional vector artist would put them.
  4. Fit cubic Béziers between nodes with Schneider's least-squares method (Graphics Gems, 1990), recursively
     splitting until the curve is within tolerance of the drawing. Smooth nodes share a tangent; corners don't.
  5. Write an SVG (one evenodd path, so counters and holes work), a compare sheet (sketch under trace, nodes
     shown) and a report with node counts per variant.

The trace is a starting point. The mark is then refined by eye and tested (nazar-logo references/craft.md and
references/testing.md); package art goes onto the dieline (nazar-dieline design mode).
"""
import argparse, math, os, sys
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageDraw

VARIANTS = {   # tolerance is in px at a 1000 px working size; corner angle in degrees
    "tight":    {"tol": 1.0, "corner": 55, "extrema": True, "passes": 2,  "calm": 6},
    "balanced": {"tol": 2.2, "corner": 62, "extrema": True, "passes": 5,  "calm": 14},
    "smooth":   {"tol": 4.5, "corner": 70, "extrema": True, "passes": 10, "calm": 28},
}


# ----------------------------------------------------------------------------- 1. clean the photo

def load(path, max_px=2000, crop=None):
    im = ImageOps.exif_transpose(Image.open(path)).convert("L")
    if crop: im = im.crop(crop)
    s = min(1.0, max_px / max(im.size))
    if s < 1: im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    return im

def flatten(im):
    """Even out shadows and paper tone: divide by a heavy blur of itself."""
    a = np.asarray(im, dtype=np.float32) + 1
    bg = np.asarray(im.filter(ImageFilter.GaussianBlur(max(im.size) / 22)), dtype=np.float32) + 1
    out = np.clip(a / bg * 235, 0, 255)
    return out.astype(np.uint8)

def otsu(a):
    hist = np.bincount(a.ravel(), minlength=256).astype(np.float64)
    p = hist / hist.sum(); w = np.cumsum(p); mu = np.cumsum(p * np.arange(256)); mt = mu[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        sb = (mt * w - mu) ** 2 / (w * (1 - w))
    return int(np.nanargmax(sb))

def binarise(im, threshold=None, invert=False, smooth=1):
    a = flatten(im)
    t = threshold if threshold is not None else otsu(a)
    ink = (a > t) if invert else (a < t)
    if smooth:   # close pinholes in marker fills, then open away fuzz
        m = Image.fromarray((ink * 255).astype(np.uint8))
        for _ in range(smooth):
            m = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))   # close
            m = m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))   # open
        ink = np.asarray(m) > 127
    return ink, t


# ----------------------------------------------------------------------------- 2. boundary loops

def loops_from(ink):
    """Closed loops along pixel boundaries, ink on the right (y down). Saddles resolve by turning right."""
    b = np.pad(ink, 1, constant_values=False)
    H, W = b.shape
    out = {}
    ys, xs = np.nonzero(b[1:, :] != b[:-1, :])            # horizontal edges at y = ys+1, x .. x+1
    for y, x in zip(ys + 1, xs):
        if b[y, x]: out.setdefault((x, y), []).append((x + 1, y))       # ink below: walk east
        else:       out.setdefault((x + 1, y), []).append((x, y))       # ink above: walk west
    ys, xs = np.nonzero(b[:, 1:] != b[:, :-1])            # vertical edges at x = xs+1, y .. y+1
    for y, x in zip(ys, xs + 1):
        if b[y, x - 1]: out.setdefault((x, y), []).append((x, y + 1))   # ink to the west: walk south
        else:           out.setdefault((x, y + 1), []).append((x, y))   # ink to the east: walk north
    loops = []
    while out:
        start = next(iter(out))
        pts, cur, prev_d = [start], start, None
        while True:
            nxts = out.get(cur)
            if not nxts: break
            if len(nxts) > 1 and prev_d is not None:      # saddle: prefer a right turn (y-down)
                rd = (-prev_d[1], prev_d[0])
                nxts.sort(key=lambda n: 0 if (n[0] - cur[0], n[1] - cur[1]) == rd else 1)
            nxt = nxts.pop(0)
            if not nxts: del out[cur]
            prev_d = (nxt[0] - cur[0], nxt[1] - cur[1])
            cur = nxt
            if cur == start: break
            pts.append(cur)
        if len(pts) >= 8: loops.append(np.array(pts, dtype=np.float64) - 1)   # undo the padding
    return loops

def signed_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * (np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


# ----------------------------------------------------------------------------- 3. corners and extremes

def soften(p, passes=2):
    """Edge midpoints remove the pixel staircase; a light circular average removes jitter."""
    q = (p + np.roll(p, -1, axis=0)) / 2
    for _ in range(passes):
        q = (np.roll(q, 1, axis=0) + 2 * q + np.roll(q, -1, axis=0)) / 4
    return q

def turning(p, k):
    a = p - np.roll(p, k, axis=0); b = np.roll(p, -k, axis=0) - p
    ang = np.arctan2(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0], (a * b).sum(1))
    return np.degrees(np.abs(ang))

def find_nodes(p, raw, corner_deg, extrema, scale, calm=10):
    n = len(p)
    k = max(3, int(round(6 * scale)))
    src = raw if len(raw) == n else p
    t = turning(src, k)
    t2 = turning(src, 2 * k)                      # a real corner holds its angle at two scales; staircase noise doesn't
    t = np.where(t2 >= 0.75 * corner_deg, t, 0)
    corners = []
    for i in np.argsort(-t):
        if t[i] < corner_deg: break
        if all(min(abs(i - c), n - abs(i - c)) > 2 * k for c in corners): corners.append(int(i))
    nodes = {c: "corner" for c in corners}
    if extrema:
        q = p.copy()                              # find extremes on a calmer copy, so noise can't fake them
        for _ in range(int(calm * max(1, scale))):
            q = (np.roll(q, 1, axis=0) + 2 * q + np.roll(q, -1, axis=0)) / 4
        d = np.roll(q, -2, axis=0) - np.roll(q, 2, axis=0)
        gap = max(6, int(14 * scale))
        span = max(np.ptp(p[:, 0]), np.ptp(p[:, 1]))
        gap = max(gap, int(len(p) * 0.04)) if span > 0 else gap
        dp = np.roll(p, -2, axis=0) - np.roll(p, 2, axis=0)
        norm = np.linalg.norm(dp, axis=1) + 1e-9
        for axis in (0, 1):                       # tangent horizontal (dy=0) or vertical (dx=0)
            s = np.sign(d[:, axis])
            flips = np.nonzero((s != np.roll(s, -1)) & (s != 0))[0]
            for i in flips:
                # snap to where the REAL curve is flattest nearby; only force h/v if it truly is (≤ ~8°)
                w = [(int(i) + o) % n for o in range(-gap // 2, gap // 2 + 1)]
                j = min(w, key=lambda m: abs(dp[m, axis]) / norm[m])
                if abs(dp[j, axis]) / norm[j] > 0.14: continue
                if all(min(abs(j - q_), n - abs(j - q_)) > gap for q_ in nodes): nodes[j] = "h" if axis == 1 else "v"
    if extrema and len(nodes) < 2:                # a featureless loop: split it in four
        for j in range(4): nodes.setdefault(int(j * n / 4), "smooth")
    return dict(sorted(nodes.items()))


# ----------------------------------------------------------------------------- 4. Schneider curve fitting

def _bez(c, t):
    mt = 1 - t
    return (mt ** 3)[:, None] * c[0] + (3 * mt * mt * t)[:, None] * c[1] + (3 * mt * t * t)[:, None] * c[2] + (t ** 3)[:, None] * c[3]

def _bez1(c, t):
    mt = 1 - t
    return (3 * mt * mt)[:, None] * (c[1] - c[0]) + (6 * mt * t)[:, None] * (c[2] - c[1]) + (3 * t * t)[:, None] * (c[3] - c[2])

def _bez2(c, t):
    return (6 * (1 - t))[:, None] * (c[2] - 2 * c[1] + c[0]) + (6 * t)[:, None] * (c[3] - 2 * c[2] + c[1])

def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v

def _chord(pts):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    return d / d[-1] if d[-1] > 0 else np.linspace(0, 1, len(pts))

def _gen(pts, u, t1, t2):
    p0, p3 = pts[0], pts[-1]
    A1 = (3 * (1 - u) ** 2 * u)[:, None] * t1
    A2 = (3 * (1 - u) * u ** 2)[:, None] * t2
    C = np.array([[np.sum(A1 * A1), np.sum(A1 * A2)], [np.sum(A1 * A2), np.sum(A2 * A2)]])
    tmp = pts - _bez(np.array([p0, p0, p3, p3]), u)
    X = np.array([np.sum(A1 * tmp), np.sum(A2 * tmp)])
    det = C[0, 0] * C[1, 1] - C[0, 1] * C[1, 0]
    seg = np.linalg.norm(p3 - p0)
    a1 = a2 = 0.0
    if abs(det) > 1e-12:
        a1 = (X[0] * C[1, 1] - X[1] * C[0, 1]) / det
        a2 = (C[0, 0] * X[1] - C[1, 0] * X[0]) / det
    eps = 1e-6 * seg
    if a1 < eps or a2 < eps or a1 > seg * 2 or a2 > seg * 2:   # degenerate: Wu/Barsky heuristic
        a1 = a2 = seg / 3
    return np.array([p0, p0 + t1 * a1, p3 + t2 * a2, p3])

def _err(pts, c, u):
    d = np.sum((_bez(c, u) - pts) ** 2, axis=1)
    i = int(np.argmax(d[1:-1])) + 1 if len(pts) > 2 else len(pts) // 2
    return d[i], i

def _reparam(pts, c, u):
    q, q1, q2 = _bez(c, u) - pts, _bez1(c, u), _bez2(c, u)
    num = np.sum(q * q1, axis=1); den = np.sum(q1 * q1, axis=1) + np.sum(q * q2, axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        nu = np.where(np.abs(den) > 1e-12, u - num / den, u)
    return np.clip(nu, 0, 1)

def fit_cubic(pts, t1, t2, tol, depth=0):
    if len(pts) == 2 or depth > 12:
        d = np.linalg.norm(pts[-1] - pts[0]) / 3
        return [np.array([pts[0], pts[0] + t1 * d, pts[-1] + t2 * d, pts[-1]])]
    u = _chord(pts)
    c = _gen(pts, u, t1, t2)
    e, si = _err(pts, c, u)
    if e < tol * tol: return [c]
    if e < (tol * 4) ** 2:
        for _ in range(12):
            u = _reparam(pts, c, u); c = _gen(pts, u, t1, t2); e, si = _err(pts, c, u)
            if e < tol * tol: return [c]
    si = max(1, min(len(pts) - 2, si))
    tc = _unit(pts[si - 1] - pts[si + 1])
    return fit_cubic(pts[:si + 1], t1, tc, tol, depth + 1) + fit_cubic(pts[si:], -tc, t2, tol, depth + 1)

def tangent_at(p, i, kind, k):
    n = len(p)
    if kind == "h": t = np.array([np.sign(p[(i + 1) % n, 0] - p[(i - 1) % n, 0]) or 1.0, 0.0])
    elif kind == "v": t = np.array([0.0, np.sign(p[(i + 1) % n, 1] - p[(i - 1) % n, 1]) or 1.0])
    else: t = _unit(p[(i + k) % n] - p[(i - k) % n])
    return t

def smooth_pinned(p, pins, passes):
    """Smooth a closed loop but keep corner points (and their immediate neighbours) where they are."""
    if not pins: return soften(p, passes) if passes else p
    q = p.copy(); n = len(q)
    fixed = np.zeros(n, bool)
    for c in pins:
        for d in (-1, 0, 1): fixed[(c + d) % n] = True
    for _ in range(passes):
        sm = (np.roll(q, 1, axis=0) + 2 * q + np.roll(q, -1, axis=0)) / 4
        q = np.where(fixed[:, None], q, sm)
    return q

def fit_loop(p, raw, cfg, scale):
    tol = cfg["tol"] * scale
    p1 = soften(raw, 1)                                   # light: corners still crisp
    corners = find_nodes(p1, p1, cfg["corner"], False, scale)
    corners = [i for i, k in corners.items() if k == "corner"]
    p = smooth_pinned(p1, corners, cfg.get("passes", 2))
    nodes = find_nodes(p, p1, cfg["corner"], cfg["extrema"], scale, cfg.get("calm", 10))
    for c in corners: nodes[c] = "corner"
    nodes = dict(sorted(nodes.items()))
    idx = list(nodes)
    n, k = len(p), max(2, int(2 * scale))
    curves = []
    for a, b in zip(idx, idx[1:] + [idx[0] + n]):
        seg = np.array([p[j % n] for j in range(a, b + 1)])
        if len(seg) < 2: continue
        ka, kb = nodes[a], nodes[b % n]
        t1 = _unit(seg[min(k, len(seg) - 1)] - seg[0]) if ka == "corner" else tangent_at(p, a, ka, k)
        t2 = _unit(seg[max(0, len(seg) - 1 - k)] - seg[-1]) if kb == "corner" else -tangent_at(p, b % n, kb, k)
        curves += fit_cubic(seg, t1, t2, tol)
    return curves, nodes


# ----------------------------------------------------------------------------- 5. output

def path_d(curves, s, ox=0, oy=0):
    f = lambda q: f"{q[0] * s + ox:.2f},{q[1] * s + oy:.2f}"
    d = "M" + f(curves[0][0])
    for c in curves: d += " C" + " ".join(f(q) for q in c[1:])
    return d + " Z"

def trace(path, out, name, variants, fill, width_mm, threshold, invert, crop, min_area, max_px):
    im = load(path, max_px, crop)
    ink, t = binarise(im, threshold, invert)
    scale = max(im.size) / 1000
    loops = [l for l in loops_from(ink) if abs(signed_area(l)) >= min_area * scale * scale]
    os.makedirs(out, exist_ok=True)
    W, H = im.size
    s = (width_mm / W) if width_mm else 1.0
    unit = "mm" if width_mm else "px"
    rows, results = [], {}
    for v in variants:
        cfg = VARIANTS[v]
        paths, total_nodes, total_curves = [], 0, 0
        for raw in loops:
            curves, nodes = fit_loop(None, raw, cfg, scale)
            if not curves: continue
            paths.append(path_d(curves, s)); total_nodes += len(curves); total_curves += 1
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * s:.2f}{unit}" height="{H * s:.2f}{unit}" viewBox="0 0 {W * s:.3f} {H * s:.3f}">'
               f'<path fill="{fill}" fill-rule="evenodd" d="{" ".join(paths)}"/></svg>')
        f = os.path.join(out, f"{name}_{v}.svg")
        open(f, "w").write(svg)
        results[v] = (svg, total_nodes, total_curves)
        rows.append((v, total_nodes, total_curves))
        print(f"✓ {os.path.relpath(f)}  ({total_curves} shapes, {total_nodes} nodes)")
    compare(im, ink, results, os.path.join(out, f"{name}_compare.png"), s)
    report(path, out, name, rows, t, scale, im.size, unit, s)
    return results

def trace_levels(path, out, name, levels, palette, width_mm, crop, min_area, max_px, variant="balanced"):
    """Multi-tone trace for hand-drawn package art: k tone bands, each traced and stacked lightest → darkest."""
    im = load(path, max_px, crop)
    a = flatten(im)
    ink_px = a[a < otsu(a)]
    qs = np.linspace(0, 1, levels + 1)[1:]                    # thresholds spread over the inked tones
    ts = sorted(set(int(np.quantile(np.r_[ink_px, otsu(a)], q)) for q in qs), reverse=True)
    scale = max(im.size) / 1000
    W, H = im.size
    s = (width_mm / W) if width_mm else 1.0
    unit = "mm" if width_mm else "px"
    cols = palette or [f"#{v:02x}{v:02x}{v:02x}" for v in np.linspace(190, 26, len(ts)).astype(int)]
    layers = []
    for i, t in enumerate(ts):                                 # lightest band first (largest area)
        m = Image.fromarray(((a < t) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
        ink = np.asarray(m) > 127
        paths = []
        for raw in loops_from(ink):
            if abs(signed_area(raw)) < min_area * scale * scale: continue
            curves, _ = fit_loop(None, raw, VARIANTS[variant], scale)
            if curves: paths.append(path_d(curves, s))
        layers.append(f'<path id="tone_{i + 1}" fill="{cols[i % len(cols)]}" fill-rule="evenodd" d="{" ".join(paths)}"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * s:.2f}{unit}" height="{H * s:.2f}{unit}" viewBox="0 0 {W * s:.3f} {H * s:.3f}">'
           + "".join(layers) + "</svg>")
    os.makedirs(out, exist_ok=True)
    f = os.path.join(out, f"{name}_levels{len(ts)}.svg"); open(f, "w").write(svg)
    print(f"✓ {os.path.relpath(f)}  ({len(ts)} tone layers, ids tone_1..tone_{len(ts)}: recolour them to brand tokens)")

def compare(im, ink, results, path, s):
    try:
        import cairosvg, io
    except ImportError:
        print("  (compare sheet skipped: pip install CairoSVG)"); return
    W, H = im.size
    cell = 700
    tiles = [("sketch", im.convert("RGB")), ("threshold", Image.fromarray(((~ink) * 255).astype(np.uint8)).convert("RGB"))]
    for v, (svg, nn, nc) in results.items():
        png = cairosvg.svg2png(bytestring=svg.replace(f'width="{W * s:.2f}', f'data-w="{W * s:.2f}').encode(), output_width=W, output_height=H)
        tr = Image.open(io.BytesIO(png)).convert("RGBA")
        base = Image.blend(im.convert("RGB"), Image.new("RGB", im.size, "white"), 0.7)
        over = base.copy(); over.paste(Image.new("RGB", im.size, (20, 20, 20)), (0, 0), tr.split()[3].point(lambda a: int(a * 0.85)))
        dr = ImageDraw.Draw(over)
        for m in __import__("re").finditer(r"([CM])([^CMZ]+)", svg.split('d="')[1]):
            pts = m.group(2).split()
            if pts:
                x, y = map(float, pts[-1].split(","))
                x, y = x / s, y / s
                dr.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(230, 0, 126), width=2)
        tiles.append((f"{v} · {nn} nodes", over))
    cols = len(tiles)
    sheet = Image.new("RGB", (cols * cell, cell + 40), "white")
    d = ImageDraw.Draw(sheet)
    for i, (label, t) in enumerate(tiles):
        t = t.copy(); t.thumbnail((cell - 20, cell - 20))
        sheet.paste(t, (i * cell + (cell - t.width) // 2, 10 + (cell - 20 - t.height) // 2))
        d.text((i * cell + 12, cell + 8), label, fill=(30, 30, 30))
    sheet.save(path)
    print(f"✓ {os.path.relpath(path)}")

def report(src, out, name, rows, t, scale, size, unit, s):
    md = [f"# Trace report: {name}", "", f"Source: `{src}` · working size {size[0]}×{size[1]} px · threshold {t} · output in {unit}", "",
          "| Variant | Shapes | Nodes | Use when |", "|---|---|---|---|"]
    use = {"tight": "the sketch's character IS the mark (brush, hand lettering): keeps wobble", "balanced": "default: clean curves that still feel drawn",
           "smooth": "geometric intent drawn by hand: fewest nodes, closest to a constructed mark"}
    md += [f"| {v} | {c} | {n} | {use[v]} |" for v, n, c in rows]
    md += ["", "## Next steps (nazar-logo craft)",
           "1. Pick a variant from the compare sheet; open its SVG in Figma (or via claude-talk-to-figma `set_svg`) or Illustrator.",
           "2. Refine by eye: nodes on extremes, tangents horizontal/vertical, no kinks; fix optical overshoot on rounds; even stroke contrast.",
           "3. Rebuild any geometry you meant to be geometric (circles, straights) instead of keeping traced wobble, unless the wobble is the idea.",
           "4. Run the stress tests: blur, 16 px, one colour, reversed, at distance (nazar-logo references/testing.md).",
           "5. For package art, place the cleaned SVG with a `logo` block in nazar-dieline design mode.",
           "", "Shooting tips for a better trace: black marker on white paper, flat daylight, phone parallel to the page, fill the frame, no shadows. Scans at 600 dpi beat photos."]
    open(os.path.join(out, f"{name}_report.md"), "w").write("\n".join(md) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--out", default="exports/trace"); ap.add_argument("--name")
    ap.add_argument("--variants", default="tight,balanced,smooth")
    ap.add_argument("--fill", default="#1A1A1A")
    ap.add_argument("--width-mm", type=float, help="scale output to this width in mm (default: px)")
    ap.add_argument("--threshold", type=int, help="0-255; default Otsu after light flattening")
    ap.add_argument("--invert", action="store_true", help="light drawing on dark ground")
    ap.add_argument("--crop", help="x0,y0,x1,y1 in source pixels")
    ap.add_argument("--min-area", type=float, default=30, help="drop specks/holes smaller than this (px² at 1000 px)")
    ap.add_argument("--max-px", type=int, default=2000)
    ap.add_argument("--levels", type=int, help="multi-tone trace with N tone layers (package art, shaded sketches)")
    ap.add_argument("--palette", help="comma-separated fills for --levels, lightest first (brand hexes)")
    a = ap.parse_args()
    crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
    name = a.name or os.path.splitext(os.path.basename(a.image))[0]
    vs = [v.strip() for v in a.variants.split(",") if v.strip() in VARIANTS]
    if a.levels:
        pal = [c.strip() for c in a.palette.split(",")] if a.palette else None
        trace_levels(a.image, a.out, name, a.levels, pal, a.width_mm, crop, a.min_area, a.max_px)
    else:
        trace(a.image, a.out, name, vs, a.fill, a.width_mm, a.threshold, a.invert, crop, a.min_area, a.max_px)

if __name__ == "__main__":
    main()
