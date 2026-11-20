"""Frosted / tinted translucent film pouch renderer (2D, physically motivated, no AI imagery).

How matte frosted film reads in a photo, and how each cue is coded here (full guide:
references/frosted_film_render.md):
1. Contact clarity: sharp where the product presses on the film, milky where there is air
   (headspace, edges, gusset). -> blur radius blended by a product-contact map.
2. Milky veil: the matte surface scatters light and lifts the blacks. -> white veil, stronger with no contact.
3. Tint: the film colour filters what's behind it. -> multiply + a little scattered tint.
4. Double film reads denser: header band above the zip, side seals, bottom gusset. -> denser tint.
5. Opaque white ink sits on top, crisp and matte. -> composited after the frost.
6. Coloured hard shadow: sun through tinted film throws coloured light into the shadow wherever no
   ink or product blocks it. -> shadow transmission map.
7. Matte sheen: broad soft highlights, never glossy streaks; crimp ribs on seals; the zip is two tracks.

API (plain inputs):
    pim, trans, tint = render_pouch("#c9a8d8", white_svg, dark_svg, GEO, fill="mango", photo=None)
    composite("#e9e1d4" or "plate.png", [(pim, trans, tint, cx, cy, angle, scale), ...], (W, H))
    scene_photo("plate.png", [(pim, trans, tint, cx_frac, base_frac, height_frac), ...])
SVGs are drawn in the front-panel frame: viewBox "0 0 W HP" in mm, HP = H - G/2.

Demo (neutral grey stand-in ink, synthetic plates):
    python engine/film.py --demo --out <folder>
Needs numpy, Pillow, CairoSVG (Windows: libcairo-2.dll on PATH, see LESSONS.md).
"""
import math, random, io, os, sys, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import cairosvg

GEO = {"W": 120, "H": 180, "G": 60, "side_seal": 6, "top_seal": 8, "zip_from_top": 26, "zip_band": 6}


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255.0


def blur(a, r):
    """Gaussian blur of a float array (H, W) or (H, W, 3) in 0..1 via PIL."""
    if r <= 0: return a
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), float) / 255.0


def svg_alpha(svg, w, h):
    """Alpha of an SVG string rendered at w x h. Empty string -> zeros."""
    if not svg: return np.zeros((h, w))
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=w, output_height=h)
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"), float)[..., 3] / 255.0


def _paste(canvas, im, x, y):
    """alpha_composite with clipping at the canvas edges."""
    cx0, cy0 = max(0, -x), max(0, -y)
    cx1, cy1 = min(im.width, canvas.width - x), min(im.height, canvas.height - y)
    if cx1 <= cx0 or cy1 <= cy0: return
    canvas.alpha_composite(im.crop((cx0, cy0, cx1, cy1)), (x + cx0, y + cy0))


def _place(dst, src, X, Y, mode="set"):
    """Write a 2D/3D array into dst at (X, Y), clipped. mode 'max' keeps the larger value."""
    H, W = dst.shape[:2]
    ys0, xs0 = max(0, -Y), max(0, -X); yd0, xd0 = max(0, Y), max(0, X)
    hh = min(src.shape[0] - ys0, H - yd0); ww = min(src.shape[1] - xs0, W - xd0)
    if hh <= 0 or ww <= 0: return
    s = src[ys0:ys0 + hh, xs0:xs0 + ww]
    if mode == "max": dst[yd0:yd0 + hh, xd0:xd0 + ww] = np.maximum(dst[yd0:yd0 + hh, xd0:xd0 + ww], s)
    else: dst[yd0:yd0 + hh, xd0:xd0 + ww] = s


def _over(canvas, rgb, a, X, Y):
    """Alpha-over an RGB array with alpha a onto canvas at (X, Y), clipped."""
    H, W = canvas.shape[:2]
    ys0, xs0 = max(0, -Y), max(0, -X); yd0, xd0 = max(0, Y), max(0, X)
    hh = min(rgb.shape[0] - ys0, H - yd0); ww = min(rgb.shape[1] - xs0, W - xd0)
    if hh <= 0 or ww <= 0: return
    aa = a[ys0:ys0 + hh, xs0:xs0 + ww, None]
    reg = canvas[yd0:yd0 + hh, xd0:xd0 + ww]
    canvas[yd0:yd0 + hh, xd0:xd0 + ww] = reg * (1 - aa) + rgb[ys0:ys0 + hh, xs0:xs0 + ww] * aa


def mesh_warp(im, amp, seed, grid=(8, 12)):
    """Bend an image like film over a lumpy fill: smooth low-frequency displacement, edges included."""
    w, h = im.size; gx, gy = grid
    r = random.Random(seed); ph = [r.uniform(0, 6.28) for _ in range(4)]
    def d(x, y):
        u, v = x / w, y / h
        dx = amp * (math.sin(2.1 * v * 6.28 + ph[0]) * 0.6 + math.sin(1.3 * u * 6.28 + ph[1]) * 0.4) * (0.4 + 0.6 * abs(u - 0.5) * 2)
        dy = amp * 0.6 * (math.sin(1.7 * u * 6.28 + ph[2]) * 0.6 + math.sin(2.3 * v * 6.28 + ph[3]) * 0.4)
        return x + dx, y + dy
    data = []
    for i in range(gx):
        for j in range(gy):
            x0, x1, y0, y1 = w * i / gx, w * (i + 1) / gx, h * j / gy, h * (j + 1) / gy
            data.append(((int(x0), int(y0), int(x1), int(y1)), (*d(x0, y0), *d(x0, y1), *d(x1, y1), *d(x1, y0))))
    return im.transform(im.size, Image.MESH, data, Image.BICUBIC)


def crease_map(w, h, s, seed, contact):
    """Soft film creases: thin random curves turned into light/dark pairs (a ridge catching the sun)."""
    r = random.Random(seed)
    im = Image.new("L", (w, h), 0); dr = ImageDraw.Draw(im)
    for _ in range(14):
        y0 = r.uniform(0.05, 0.98) * h; amp = r.uniform(2, 9) * s; fr = r.uniform(0.5, 1.6); ph = r.uniform(0, 6.28)
        x0, x1 = r.uniform(-0.1, 0.5) * w, r.uniform(0.5, 1.1) * w; tilt = r.uniform(-0.25, 0.25)
        pts = [(x, y0 + tilt * (x - x0) + amp * math.sin(fr * x / w * 6.28 + ph)) for x in np.linspace(x0, x1, 40)]
        dr.line(pts, fill=r.randint(120, 255), width=max(1, int(0.5 * s)))
    a = np.asarray(im, float) / 255.0
    b = blur(a, 1.4 * s); sh = max(1, int(0.9 * s))
    sig = np.roll(b, -sh, axis=0) - np.roll(b, sh, axis=0)
    return sig * (1 - 0.65 * contact) + blur(a, 3 * s) * 0.15

# ------------------------------------------------------------------ the fill (what's inside)

def _blob(rnd, cx, cy, rx, ry, rot, n=40, wob=0.12):
    pts, ph = [], [rnd.uniform(0, 6.28) for _ in range(3)]
    for i in range(n):
        t = 6.2832 * i / n
        k = 1 + wob * (math.sin(2 * t + ph[0]) * 0.6 + math.sin(3 * t + ph[1]) * 0.3 + math.sin(5 * t + ph[2]) * 0.2)
        x, y = rx * k * math.cos(t), ry * k * math.sin(t)
        pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
    return pts

# edge -> centre tones, muted (photographed produce reads less saturated than you think)
PALETTE = {
    "mango": [(196, 108, 14), (226, 142, 26), (242, 170, 48), (248, 194, 92)],
    "strawberry": [(150, 28, 42), (196, 62, 76), (226, 120, 124), (242, 186, 176)],
    "kiwi": [(108, 94, 58), (112, 134, 58), (138, 160, 82), (188, 196, 134)],
    "apricot": [(186, 92, 22), (218, 120, 34), (236, 148, 52), (244, 172, 84)],
    "berry": [(40, 12, 34), (62, 20, 50), (86, 32, 70), (112, 52, 92)],
    "nut": [(120, 78, 40), (156, 106, 60), (186, 138, 88), (210, 172, 124)],
    "grey": [(110, 110, 110), (140, 140, 140), (165, 165, 165), (190, 190, 190)],
}
SIZE = {"mango": 30 * 15, "strawberry": 22 * 22, "kiwi": 25 * 23, "apricot": 26 * 21, "berry": 18 * 9, "nut": 20 * 14, "grey": 24 * 18}


def piece_img(kind, rnd, s):
    """One drawn piece as a small RGBA image, soft (no outlines), tonal rings drifting to a top-left light."""
    pal = [tuple(max(0, min(255, v + rnd.randint(-12, 12))) for v in c) for c in PALETTE[kind]]
    if kind == "mango": rx, ry, wob = rnd.uniform(13, 22) * s, rnd.uniform(9, 14) * s, 0.3
    elif kind == "strawberry": rx = ry = rnd.uniform(9, 13) * s; wob = 0.08
    elif kind == "kiwi": rx = rnd.uniform(11, 14) * s; ry = rx * rnd.uniform(0.85, 0.95); wob = 0.04
    elif kind in ("apricot", "grey"): rx = rnd.uniform(11, 15) * s; ry = rx * rnd.uniform(0.75, 0.9); wob = 0.12
    elif kind == "nut": rx = rnd.uniform(8, 11) * s; ry = rx * rnd.uniform(0.6, 0.75); wob = 0.1
    else: rx, ry, wob = rnd.uniform(7, 11) * s, rnd.uniform(3.5, 5) * s, 0.1
    pad = int(4 * s); S2 = int(2 * max(rx, ry) + 2 * pad)
    im = Image.new("RGBA", (S2, S2), (0, 0, 0, 0)); dr = ImageDraw.Draw(im, "RGBA")
    c = S2 / 2; rot = rnd.uniform(0, 3.1416); lx, ly = -0.9 * s, -1.1 * s
    if kind == "berry":                                         # drupelets along a short body
        n = int(rx / s * 1.3)
        for i in range(n):
            t = (i / max(n - 1, 1) - 0.5) * 2 * rx
            for side in (-1, 0, 1):
                o = side * 1.9 * s + rnd.uniform(-0.5, 0.5) * s
                x, y = c + t * math.cos(rot) - o * math.sin(rot), c + t * math.sin(rot) + o * math.cos(rot)
                r = rnd.uniform(1.5, 2.1) * s * (1 - abs(t) / (2 * rx) * 0.7)
                dr.ellipse([x - r, y - r, x + r, y + r], fill=pal[rnd.randint(0, 2)] + (255,))
                dr.ellipse([x - r * 0.5, y - r * 0.6, x, y - r * 0.15], fill=pal[3] + (120,))
        return im.filter(ImageFilter.GaussianBlur(0.25 * s))
    if kind == "strawberry":
        def shape(k, ox=0, oy=0):
            pts = []
            for i in range(48):
                t = 6.2832 * i / 48
                x = rx * k * 0.95 * math.sin(t); y = -ry * k * (0.85 * math.cos(t) - 0.25 * math.cos(2 * t) - 0.1)
                pts.append((c + ox + x * math.cos(rot) - y * math.sin(rot), c + oy + x * math.sin(rot) + y * math.cos(rot)))
            return pts
    else:
        seed = rnd.random()
        def shape(k, ox=0, oy=0):
            return _blob(random.Random(seed), c + ox, c + oy, rx * k, ry * k, rot, wob=wob)
    for j, k in enumerate((1.0, 0.86, 0.66, 0.42)):
        f = j / 3
        dr.polygon(shape(k, lx * f, ly * f), fill=pal[j] + (255,))
    if kind == "kiwi":                                          # faint seed ring + pale core
        for i in range(26):
            t = 6.2832 * i / 26; rr = rx * rnd.uniform(0.36, 0.46)
            x, y = c + rr * math.cos(t), c + rr * 0.9 * math.sin(t)
            dr.ellipse([x - 0.45 * s, y - 0.3 * s, x + 0.45 * s, y + 0.3 * s], fill=(52, 54, 26, 110))
        dr.polygon(_blob(rnd, c, c, rx * 0.22, ry * 0.12, rot, wob=0.1), fill=(222, 220, 170, 200))
    if kind == "strawberry":
        pts = shape(0.88)
        for i in range(12):
            x, y = pts[(i * 4) % 48]
            dr.ellipse([x - 0.35 * s, y - 0.25 * s, x + 0.35 * s, y + 0.25 * s], fill=(236, 200, 120, 90))
    if kind in ("mango", "apricot", "nut"):                      # fibres / wrinkles, barely there
        for _ in range(7):
            a = rnd.uniform(-0.6, 0.6) * rx; o = rnd.uniform(-0.5, 0.5) * ry
            x0, y0 = c + a * math.cos(rot) - o * math.sin(rot), c + a * math.sin(rot) + o * math.cos(rot)
            l = rnd.uniform(0.2, 0.5) * rx
            dr.line([(x0, y0), (x0 + l * math.cos(rot), y0 + l * math.sin(rot))], fill=pal[0] + (40,), width=max(1, int(0.35 * s)))
    return im.filter(ImageFilter.GaussianBlur(0.45 * s))


def photo_fill(path, w, h, s, seed=1, y_top=0.28):
    """A real product photo (top-down pile filling the frame) as the fill: cover-cropped, with a lumpy
    settled top edge that slumps to the sides, darker deep in the pile. Returns RGB (h, w, 3), coverage (h, w)."""
    im = Image.open(path).convert("RGB")
    sc = max(w / im.width, h * (1 - y_top + 0.05) / im.height)
    im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
    ph = np.asarray(im, float) / 255.0
    ox = max(0, (ph.shape[1] - w) // 2)
    rgb = np.zeros((h, w, 3))
    y0 = int(h * (y_top - 0.04))
    hh = min(h - y0, ph.shape[0]); rgb[y0:y0 + hh] = ph[:hh, ox:ox + w]
    rnd = np.random.default_rng(seed)
    xs = np.arange(w); edge = np.zeros(w)
    for k in range(1, 6):
        edge += np.sin(xs / w * np.pi * (k + rnd.uniform(0, 1)) + rnd.uniform(0, 6.28)) * (5.5 / k) * s
    edge += h * y_top + (np.abs(xs - w / 2) / (w / 2)) ** 2 * 6 * s
    yy = np.arange(h)[:, None]
    al = np.clip((yy - edge[None, :]) / (1.2 * s), 0, 1)
    depth = np.clip((yy - edge[None, :]) / (25 * s), 0, 1)
    return rgb * (0.82 + 0.18 * depth[..., None]), al


def drawn_fill(kind, w, h, s, seed=1, y_top=0.28):
    """Fallback fill: a packed pile of drawn pieces. Returns RGB (h, w, 3), coverage (h, w)."""
    kind = kind if kind in PALETTE else "grey"
    rnd = random.Random(seed)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    n = int(w * h * (1 - y_top) / (SIZE[kind] * s * s) * 2.4)
    for _ in range(n):
        y = h * (y_top + (1 - y_top) * (rnd.random() ** 0.75)) + rnd.uniform(-5, 5) * s
        x = rnd.uniform(-0.05, 1.05) * w
        pc = piece_img(kind, rnd, s)
        sh = Image.new("RGBA", pc.size, (20, 10, 0, 0))
        sh.putalpha(pc.split()[3].point(lambda v: int(v * 0.5)).filter(ImageFilter.GaussianBlur(1.4 * s)))
        x0, y0 = int(x - pc.width / 2), int(y - pc.height / 2)
        _paste(canvas, sh, x0 + int(1.2 * s), y0 + int(1.6 * s)); _paste(canvas, pc, x0, y0)
    a = np.asarray(canvas, float) / 255.0
    depth = blur(np.asarray(Image.effect_noise((w, h), 60).convert("L"), float) / 255.0, 6 * s)
    return a[..., :3] * (0.78 + 0.32 * depth[..., None]), a[..., 3]

# ------------------------------------------------------------------ the pouch

def render_pouch(tint, white_svg="", dark_svg="", geo=None, fill="grey", photo=None, s=6, seed=1,
                 date=None, font=None, dark_ink="#26211f"):
    """Stand-up pouch lying flat, front view.
    tint: film colour hex. white_svg / dark_svg: ink layers as SVG strings, viewBox 0 0 W HP (mm).
    geo: W, H, G (gusset depth), side_seal, top_seal, zip_from_top, zip_band (mm); defaults to GEO.
    fill: drawn-piece kind (PALETTE key) used when photo is None or missing. photo: path to a top-down
    product photo. date: optional inkjet date string on the top seal; font: optional .ttf path for it.
    Returns (RGBA image, shadow-transmission map (h, w) 0..1, tint as RGB 0..1)."""
    g = dict(GEO, **(geo or {}))
    W, H, G = g["W"], g["H"], g["G"]
    HP = H - G / 2
    ss, ts, zt, zb = g["side_seal"], g["top_seal"], g["zip_from_top"], g["zip_band"]
    w, h, hp = int(W * s), int(H * s), int(HP * s)
    tint = hexrgb(tint)
    lum = float(tint @ np.array([0.2126, 0.7152, 0.0722]))
    yy, xx = np.mgrid[0:h, 0:w]
    u, v = xx / w, yy / h

    # inside: back film (tinted, diffuse) behind the pile
    back = np.ones((h, w, 3)) * (tint * 0.6 + 0.1)
    y_top = (zt + zb + 22) / H
    if photo and os.path.exists(photo): fr, fa = photo_fill(photo, w, h, s, seed, y_top)
    else: fr, fa = drawn_fill(fill, w, h, s, seed, y_top)
    scene = back * (1 - fa[..., None]) + fr * fa[..., None]

    # 1. contact clarity: dense product presses the film -> sharp; air -> milky
    contact = np.clip((blur(fa, 7 * s) - 0.18) * 2.6, 0, 1)
    contact *= np.clip((v - (zt + zb + 18) / H) * 8, 0, 1)            # headspace never touches
    contact *= np.clip((np.minimum(u, 1 - u) - ss / W) * 18, 0, 1)    # edges curve away
    contact *= np.clip((HP / H + 0.02 - v) * 14, 0, 1)               # gusset lifts off
    c3 = contact[..., None]
    img = blur(scene, 1.3 * s / 6) * c3 + blur(scene, 4.0 * s) * (1 - c3)

    # 2-3. milky veil + tint filtering
    veil = (0.06 + 0.32 * (1 - contact))[..., None]
    img = img * (1 - veil) + np.array([0.95, 0.95, 0.93]) * veil
    img = img * (tint * 0.45 + 0.55)
    img = img * 0.84 + tint * 0.16

    # 4. double film: header band, side seals, gusset arc
    dense = (v < (zt + zb) / H).astype(float)
    dense = np.maximum(dense, ((u < ss / W) | (u > 1 - ss / W)).astype(float) * 0.8)
    arc = HP / H + (G / 2 / H) * 0.55 * (1 - ((u - 0.5) * 2) ** 2) ** 0.5
    dense = blur(np.maximum(dense, (v > arc).astype(float) * 0.55), 0.6 * s)
    dfilm = tint * 0.9 + 0.06 + (0.04 if lum > 0.5 else 0.0)
    img = img * (1 - 0.78 * dense[..., None]) + dfilm * 0.78 * dense[..., None]

    # 5. inks on top (front panel 0..HP; the gusset strip below is unprinted film)
    def lay(svg):
        a = np.zeros((h, w)); a[:hp] = svg_alpha(svg, w, hp); return a
    white, darkink = lay(white_svg), lay(dark_svg)
    img = img * (1 - 0.97 * white[..., None]) + np.array([0.965, 0.955, 0.93]) * 0.97 * white[..., None]
    img = img * (1 - darkink[..., None]) + hexrgb(dark_ink) * darkink[..., None]

    # 7. surface: flat pillow shading, matte sheen, creases, crimp ribs, zip tracks
    edge = np.minimum(u, 1 - u) * 2
    shade = (0.84 + 0.16 * np.clip(edge * 2.2, 0, 1) ** 0.6) * (1 - 0.06 * np.clip((v - 0.85) * 6, 0, 1))
    rnd = random.Random(seed + 7); sheen = np.zeros((h, w))
    for _ in range(3):
        cx, wd = rnd.uniform(0.15, 0.85), rnd.uniform(0.06, 0.14)
        sheen += np.exp(-((u - cx - 0.08 * (v - 0.5)) / wd) ** 2) * rnd.uniform(0.04, 0.08)
    sheen += np.exp(-((v - 0.02) / 0.02) ** 2) * 0.05
    img = img * shade[..., None] + sheen[..., None]
    img = img + crease_map(w, h, s, seed + 3, contact)[..., None] * 0.55
    rib = np.sin(xx / (0.9 * s) * 6.2832) * 0.5 + 0.5
    m = yy < ts * s
    img[m] *= (0.94 + 0.06 * rib[m])[..., None]
    for y0 in (zt, zt + zb - 2.5):
        m = (yy >= y0 * s) & (yy < (y0 + 1.2) * s); img[m] = img[m] * 0.82
        m2 = (yy >= (y0 + 1.2) * s) & (yy < (y0 + 1.8) * s); img[m2] = img[m2] * 0.9 + 0.1
    img = np.clip(img, 0, 1)
    pim = Image.fromarray((img * 255).astype(np.uint8)).convert("RGBA")

    if date:                                                     # optional inkjet date on the top seal
        try: f = ImageFont.truetype(font, int(3.4 * s)) if font else ImageFont.load_default(size=int(3.4 * s))
        except Exception: f = ImageFont.load_default()
        dl = Image.new("L", (w, h), 0)
        ImageDraw.Draw(dl).text(((W - ss - 4) * s, (ts + 9) * s), date, font=f, fill=150, anchor="rs")
        pim.paste(Image.new("RGBA", (w, h), tuple(int(c * 255 * 0.72) for c in dfilm) + (255,)), (0, 0), dl)

    # outline: small corner radius + two tear notches, lit cut edge
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask); md.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(2.5 * s), fill=255)
    ny = int((ts + zt) / 2 * s)
    for x0, sgn in ((0, 1), (w - 1, -1)):
        md.polygon([(x0, ny - 2.5 * s), (x0 + sgn * 3.5 * s, ny), (x0, ny + 2.5 * s)], fill=0)
    mask = mask.filter(ImageFilter.GaussianBlur(0.6)); pim.putalpha(mask)
    mk = np.asarray(mask, float) / 255.0
    rim = np.clip(mk - blur(mk, 0.5 * s), 0, 1) * 3.0
    arr = np.asarray(pim, float).copy()
    arr[..., :3] = np.clip(arr[..., :3] + rim[..., None] * 60, 0, 255)
    pim = mesh_warp(Image.fromarray(arr.astype(np.uint8)), 1.1 * s, seed + 5)

    # 6. light transmission for the coloured shadow: ink and dense product block light
    trans = np.clip(1 - white * 0.95 - darkink - fa * 0.55 * (1 - dense), 0.05, 1)
    trans = np.asarray(mesh_warp(Image.fromarray((trans * 255).astype(np.uint8)), 1.1 * s, seed + 5), float) / 255.0
    return pim, trans, tint


def add_volume(p, light=(-0.55, -0.25, 0.80), bulge=0.9, pinch=0.03, top=0.17, bottom=0.92):
    """A filled pouch is a pillow, not a card: the sides pull in where the product swells the film,
    a side light rolls off across the curve, a broad matte highlight sits on the lit shoulder and the far
    edge falls into shadow. top/bottom = fraction of height where the filled body starts/ends."""
    w, h = p.size
    def d(y):
        t = np.clip((y / h - top) / (bottom - top), 0, 1)
        return pinch * w * np.sin(np.pi * t) ** 0.8
    n = 24; mesh = []
    for i in range(n):
        ya, yb = int(h * i / n), int(h * (i + 1) / n)
        da, db = d(ya), d(yb)
        mesh.append(((0, ya, w, yb), (-da, ya, -db, yb, w + db, yb, w + da, ya)))
    p = p.transform((w, h), Image.MESH, mesh, resample=Image.BICUBIC)
    a = np.asarray(p, float); rgb, al = a[..., :3] / 255.0, a[..., 3:] / 255.0
    yy, xx = np.mgrid[0:h, 0:w]; u, v = xx / w, yy / h
    body = np.clip((v - top) / 0.06, 0, 1) * np.clip((bottom + 0.06 - v) / 0.08, 0, 1)
    amp = bulge * body * (0.55 + 0.45 * np.sin(np.pi * np.clip((v - top) / (bottom - top), 0, 1)))
    nx = (u - 0.5) * 2 * 0.92 * amp
    ny = (v - (top + bottom) / 2) * 0.35 * amp
    nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0.05, 1))
    L = np.array(light) / np.linalg.norm(light)
    lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    hi = np.exp(-((u - 0.28) / 0.13) ** 2) * body * 0.07
    edge_dark = np.clip((u - 0.80) / 0.20, 0, 1) ** 1.6 * 0.20 * (0.4 + 0.6 * body)
    rgb = rgb * (0.80 + 0.30 * lam - edge_dark)[..., None] + hi[..., None]
    return Image.fromarray(np.concatenate([np.clip(rgb, 0, 1) * 255, al * 255], axis=2).astype(np.uint8))

# ------------------------------------------------------------------ scenes

def _grain(canvas, grain, seed):
    canvas = canvas + np.random.default_rng(seed).normal(0, grain, canvas.shape[:2])[..., None]
    return Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8))


def composite(bg, items, size, light=(0.9, 1.1), shadow_len=22, grain=0.025, seed=3):
    """Top-down flat lay. bg: flat colour hex OR path to a top-down photo plate.
    items: list of (pouch RGBA, transmission, tint, cx, cy, angle_deg, scale), drawn in order (later = on top).
    Sun from the top-left: hard, dense shadow (a full pack blocks most light) with a faint tinted glow."""
    Wc, Hc = size
    if isinstance(bg, str) and os.path.exists(bg):
        canvas = np.asarray(Image.open(bg).convert("RGB").resize((Wc, Hc), Image.LANCZOS), float) / 255.0
    else:
        canvas = np.ones((Hc, Wc, 3)) * hexrgb(bg)
        yy, xx = np.mgrid[0:Hc, 0:Wc]                     # slight falloff across the table, no radial glow
        canvas *= (0.97 + 0.05 * (1 - xx / Wc) * (1 - yy / Hc))[..., None]
    dx, dy = light[0] * shadow_len, light[1] * shadow_len
    for pim, trans, tint, cx, cy, ang, sc in items:
        p = add_volume(pim.resize((int(pim.width * sc), int(pim.height * sc)), Image.LANCZOS), bulge=0.7, pinch=0.022)
        t = Image.fromarray((trans * 255).astype(np.uint8)).resize(p.size, Image.LANCZOS)
        p = p.rotate(ang, resample=Image.BICUBIC, expand=True)
        t = t.rotate(ang, resample=Image.BICUBIC, expand=True)
        x0, y0 = int(cx - p.width / 2), int(cy - p.height / 2)
        a = np.asarray(p, float)[..., 3] / 255.0
        tr = np.asarray(t, float) / 255.0
        sh = np.zeros((Hc, Wc)); trm = np.zeros((Hc, Wc))
        _place(sh, a, x0 + int(dx), y0 + int(dy)); _place(trm, tr * a, x0 + int(dx), y0 + int(dy))
        sh = blur(sh, 3.0) * 0.92; trm = blur(trm, 14)
        shadow_col = canvas * (0.56 + 0.08 * trm[..., None] * (tint * 0.85 + 0.15))
        canvas = canvas * (1 - sh[..., None]) + np.clip(shadow_col, 0, 1) * sh[..., None]
        ao = np.zeros((Hc, Wc)); _place(ao, a, x0 + 3, y0 + 4)      # tight contact shadow
        canvas *= (1 - 0.18 * blur(ao, 7))[..., None]
        _over(canvas, np.asarray(p, float)[..., :3] / 255.0, a, x0, y0)
    return _grain(canvas, grain, seed)


def scene_photo(bg_path, items, out_w=2048, light_x=1.0, grain=0.018, seed=5):
    """Standing pouches in an eye-level photo plate. items: list of
    (pouch RGBA, transmission, tint, cx_frac, base_frac, height_frac); base_frac = where the base meets
    the table. Sun from the upper left: a flipped, squashed, sheared ground shadow to the right/back,
    tinted where light passes the film, penumbra growing with distance, contact occlusion at the base."""
    bg = Image.open(bg_path).convert("RGB")
    Wc = out_w; Hc = int(bg.height * out_w / bg.width)
    canvas = np.asarray(bg.resize((Wc, Hc), Image.LANCZOS), float) / 255.0
    for pim, trans, tint, cxf, basef, hf in sorted(items, key=lambda it: it[4]):
        ph = int(Hc * hf); sc = ph / pim.height
        p = add_volume(pim.resize((int(pim.width * sc), ph), Image.LANCZOS))
        t = Image.fromarray((trans * 255).astype(np.uint8)).resize(p.size, Image.LANCZOS)
        pw = p.width
        x0, y0 = int(Wc * cxf - pw / 2), int(Hc * basef - ph)
        a = np.asarray(p, float)[..., 3] / 255.0
        sh_h = max(1, int(ph * 0.32)); off = int(0.75 * light_x * ph)
        shear = lambda im: im.transform((pw + off, sh_h), Image.AFFINE, (1, off / sh_h, -off, 0, 1, 0), resample=Image.BICUBIC)
        A = Image.fromarray((a * 255).astype(np.uint8)).resize((pw, sh_h), Image.LANCZOS)
        As = np.asarray(shear(A), float) / 255.0
        Ts = np.asarray(shear(t.resize((pw, sh_h), Image.LANCZOS)), float) / 255.0
        sx, sy = x0, y0 + ph - sh_h + int(0.01 * ph)
        shm = np.zeros((Hc, Wc)); trm = np.zeros((Hc, Wc))
        _place(shm, As, sx, sy, "max"); _place(trm, Ts * As, sx, sy, "max")
        far = np.clip((y0 + ph - np.arange(Hc)[:, None]) / sh_h, 0, 1)
        shm = blur(shm, 2.5) * (1 - 0.35 * far); trm = blur(trm, 10)
        shadow_col = canvas * (0.40 + 0.30 * trm[..., None] * (tint * 0.8 + 0.2))
        canvas = canvas * (1 - shm[..., None]) + shadow_col * shm[..., None]
        base = Image.new("L", (Wc, Hc), 0)
        ImageDraw.Draw(base).ellipse([x0 + pw * 0.04, y0 + ph - 0.018 * ph, x0 + pw * 0.98, y0 + ph + 0.022 * ph], fill=255)
        canvas *= (1 - 0.55 * blur(np.asarray(base, float) / 255.0, 0.012 * ph))[..., None]
        rgb = np.asarray(p, float)[..., :3] / 255.0
        rgb = rgb * (1.04 - 0.12 * np.linspace(0, 1, pw)[None, :, None])      # light falls off across it
        if x0 > 0:                                                              # warm key sampled from the plate
            key = np.clip(canvas[max(0, y0):y0 + ph, max(0, x0 - pw):x0].reshape(-1, 3).mean(0), 0.2, 1)
            rgb = rgb * (0.88 + 0.12 * key / key.max())
        _over(canvas, rgb, a, x0, y0)
    return _grain(canvas, grain, seed)


def label(im, text="AI concept render · internal"):
    """Stamp the disclosure line bottom-right. Use it on anything with an AI plate or AI texture inside."""
    d = ImageDraw.Draw(im); w, h = im.size
    try: f = ImageFont.load_default(size=max(12, h // 70))
    except Exception: f = ImageFont.load_default()
    d.text((w - 20, h - 16), text, fill=(90, 80, 70), font=f, anchor="rs")
    return im

# ------------------------------------------------------------------ demo (neutral stand-in)

def _demo_layers(geo):
    """Grey placeholder ink: a white brand block with a product window left open, dark copy bars."""
    W, HP = geo["W"], geo["H"] - geo["G"] / 2
    vb = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {HP}">'
    white = (vb + f'<path fill-rule="evenodd" fill="#fff" d="M 14 {HP*0.30} h {W-28} v {HP*0.58} h {-(W-28)} Z '
             f'M 24 {HP*0.52} h {W-48} v {HP*0.26} h {-(W-48)} Z"/>'
             f'<rect x="{W*0.3}" y="{HP*0.06}" width="{W*0.4}" height="5" fill="#fff"/></svg>')
    dark = (vb + f'<rect x="22" y="{HP*0.34}" width="{W*0.5}" height="9" fill="#000"/>'
            f'<rect x="22" y="{HP*0.42}" width="{W*0.32}" height="3" fill="#000"/>'
            f'<rect x="22" y="{HP*0.81}" width="{W*0.22}" height="3" fill="#000"/></svg>')
    return white, dark


def _demo_plates(out):
    """Synthetic stand-ins so the demo runs without any AI plate: a sweep, and a 'photo' pile texture."""
    w, h = 1600, 1000
    yy, xx = np.mgrid[0:h, 0:w]
    sweep = np.clip(0.80 + 0.12 * (1 - yy / h) - 0.08 * xx / w, 0, 1)[..., None] * np.array([1.0, 0.97, 0.92])
    table = (yy > h * 0.72)[..., None]
    sweep = np.where(table, sweep * 0.93, sweep)
    Image.fromarray((sweep * 255).astype(np.uint8)).save(os.path.join(out, "plate_sweep.png"))
    rnd = random.Random(9); tex = Image.new("RGBA", (900, 900), (120, 100, 80, 255))
    for _ in range(260):
        pc = piece_img("nut", rnd, 4); _paste(tex, pc, rnd.randint(-40, 900), rnd.randint(-40, 900))
    tex.convert("RGB").save(os.path.join(out, "texture_pile.png"))
    return os.path.join(out, "plate_sweep.png"), os.path.join(out, "texture_pile.png")


def demo(out):
    os.makedirs(out, exist_ok=True)
    white, dark = _demo_layers(GEO)
    plate, tex = _demo_plates(out)
    tints = ["#b9a7cf", "#9cc3b4", "#e6b88f"]
    packs = [render_pouch(t, white, dark, GEO, fill=f, s=6, seed=i + 1, date="20.11.26")
             for i, (t, f) in enumerate(zip(tints, ["grey", "apricot", "berry"]))]
    packs.append(render_pouch("#c8c2b8", white, dark, GEO, photo=tex, s=6, seed=4))
    packs[0][0].save(os.path.join(out, "pouch_front.png"))
    packs[3][0].save(os.path.join(out, "pouch_photo_fill.png"))
    flat = composite("#e9e3d8", [(*packs[1], 380, 360, 17, 0.75), (*packs[2], 1420, 420, -11, 0.75),
                                 (*packs[3], 300, 1080, -24, 0.75), (*packs[0], 900, 760, -6, 0.85)],
                     (1600, 1200), shadow_len=40)
    label(flat, "concept render · demo stand-in").save(os.path.join(out, "flatlay.jpg"), quality=92)
    stand = scene_photo(plate, [(*p, x, 0.86, 0.58) for p, x in zip(packs[:3], (0.25, 0.5, 0.75))], out_w=1600)
    label(stand, "concept render · demo stand-in").save(os.path.join(out, "range_standing.jpg"), quality=92)
    for f in sorted(os.listdir(out)): print(" ", os.path.join(out, f))


if __name__ == "__main__":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    ap = argparse.ArgumentParser(description="Frosted tinted-film pouch renderer")
    ap.add_argument("--demo", action="store_true", help="render a neutral stand-in demo")
    ap.add_argument("--out", default=os.path.join(os.getcwd(), "film_demo"))
    a = ap.parse_args()
    if a.demo: demo(a.out)
    else: ap.print_help()
