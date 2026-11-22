"""Hybrid-scene compositor: seat a real product render (RGBA) into an empty background plate.

Rule: AI (or a licensed photo) makes ONLY the empty plate. The product is always our own artwork render,
so its type and print stay sharp and true. Every output carries a disclosure stamp.

The seating pass, in order (each step is what a camera and a room do to a real object):
  1. perspective   keystone to the plate's camera height, scale to a measured height, lean (--angle)
  2. bend          a filled pack pinches in at the sides and rolls off the light
  3. shadows       projected cast shadow on the surface (away from the key) + tight contact shadow at the base
  4. tone match    the plate's low-frequency light (falloff) and colour cast, room saturation, black lift
  5. sheen         one broad soft highlight on the side facing the key, never glossy streaks
  6. edge occlusion and light wrap: the outer edge darkens where it turns away, the room bleeds over it
  7. re-lay        plate bands that sit IN FRONT of the product (shelf lip, table edge) are pasted back on top
  8. camera pass   micro-softness, halation, lens CA + falloff, grain matched to the plate's own noise
  9. stamp         "AI-generated background plate ..." bottom-left, small

CLI
  python composite.py --plate p.jpg --product a.png --at x,y --height px [--angle deg] --out o.jpg
      --at        where the product's base centre touches the surface, in plate pixels (or 0-1 fractions)
      --light     shadow direction dx,dy as a fraction of product height, or "auto" (default: read from the plate)
      --persp     keystone 0..0.2 (top narrower; camera looking down a little). Default 0.03
      --mode      stand (projected ground shadow, default) | lie (top-down: offset drop shadow)
      --relay     y0,y1[;y0,y1] plate bands (pixels or fractions) re-laid over the product, e.g. a shelf lip
      --bend      side pinch 0..0.06 (default 0.02)   --sheen 0..0.2 (0.08)   --wrap 0..0.6 (0.35)
      --ca        lateral chromatic aberration, % of centre-to-corner distance: 0 off (default), 0.05 subtle,
                  capped at 0.12 (lens tests: > 0.15 reads as a strong, visible fault). Synthetic/clean plates only
      --stamp     disclosure text ("" only when the plate is a licensed real photo)
  python composite.py --selftest [--out demo.jpg]    builds a synthetic plate + product and writes a demo

Library
  from composite import Scene
  s = Scene("plate.jpg"); s.seat("pack.png", at=(900, 1400), height=820, angle=-2); s.relay([(1390, 1440)])
  s.finish("out.jpg")
"""
import argparse
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

STAMP = "AI-generated background plate · product is the real artwork render · concept"


# ------------------------------------------------------------------ helpers

def _f(a):
    return np.asarray(a, np.float32)


def _u8(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def _box(a, k, axis):
    """Running-mean box filter of width 2k+1 along one axis, edges clamped (float, vectorised)."""
    if k < 1:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (k + 1, k)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * k + 1, 2 * k + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * k + 1)).astype(np.float32)


def gblur(a, r):
    """Gaussian blur (three box passes) of a float array (H, W) or (H, W, C); any value range, kept as float."""
    if r <= 0:
        return a
    a = np.asarray(a, np.float32)
    k = int(round((math.sqrt(4 * r * r + 1) - 1) / 2))        # three passes of width 2k+1 give variance k(k+1) ~ r^2
    if k < 1:                                                  # sub-pixel radius: blend toward the k=1 blur (variance 2)
        b = a
        for _ in range(3):
            b = _box(_box(b, 1, 0), 1, 1)
        t = min(1.0, r * r / 2)
        return a * (1 - t) + b * t
    for _ in range(3):
        a = _box(_box(a, k, 0), k, 1)
    return a


def _paste_region(W, H, x0, y0, w, h):
    """Clip a w*h box at (x0, y0) to the canvas: returns dest slice coords and source offsets."""
    xs, ys = max(0, x0), max(0, y0)
    xe, ye = min(W, x0 + w), min(H, y0 + h)
    return xs, ys, xe, ye, xs - x0, ys - y0


def _persp_coeffs(dst, src):
    """Coefficients for Image.PERSPECTIVE mapping output points (dst) to input points (src)."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


# ------------------------------------------------------------------ reading the plate

def light_map(plate, k=0.06):
    """Low-frequency light of the plate: gain (H, W) normalised so the open lit area ~ 1, and the colour cast (H, W, 3)."""
    small = plate.resize((max(8, int(plate.width * k)), max(8, int(plate.height * k))), Image.BILINEAR)
    L = _f(small.filter(ImageFilter.GaussianBlur(4)).resize(plate.size, Image.BILINEAR))
    lum = L.mean(-1)
    gain = (lum / max(np.percentile(lum, 92), 1)).clip(0.25, 1.15)
    cast = L / np.maximum(L.mean(-1, keepdims=True), 1)
    return gain, cast


def noise_sigma(plate):
    """Photo grain estimate: robust std of the high-pass in the flattest third of the frame."""
    g = _f(plate.convert("L"))
    hp = g - _f(plate.convert("L").filter(ImageFilter.GaussianBlur(1.5)))
    loc = _f(_u8(np.abs(hp)).filter(ImageFilter.BoxBlur(12)))
    flat = hp[loc <= np.percentile(loc, 33)]
    return float(1.4826 * np.median(np.abs(flat - np.median(flat)))) if flat.size else 2.5


def estimate_light(gain, length=0.35, back=0.12):
    """Where the key light comes from, read from the plate's left-right light falloff. Returns the shadow offset
    (dx, dy) as a fraction of product height: the shadow falls away from the brighter side and a little back.
    Advisory only: brief the plate's light direction and pass --light when you know it."""
    W = gain.shape[1]
    left, right = float(gain[:, : W // 3].mean()), float(gain[:, -W // 3:].mean())
    ratio = (left - right) / max((left + right) / 2, 1e-6)        # + = brighter on the left
    dx = float(np.clip(ratio * 4, -1, 1)) * length
    return (dx, back)


# ------------------------------------------------------------------ shaping the product

def keystone(p, persp):
    """Top edge narrower by `persp` of the width; a negative value narrows the base instead.
    Physics (shotplan.py computes the signed value): an upright product seen from above has its top nearer the lens, so
    the top is slightly WIDER (negative); a low camera or a pack leaning back narrows the top (positive)."""
    if abs(persp) < 1e-6:
        return p
    w, h = p.size
    inset = abs(persp) * w / 2
    dst = [(inset, 0), (w - inset, 0), (w, h), (0, h)] if persp > 0 else [(0, 0), (w, 0), (w - inset, h), (inset, h)]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    return p.transform((w, h), Image.PERSPECTIVE, _persp_coeffs(dst, src), Image.BICUBIC)


def pinch(p, amount, top=0.15, bottom=0.92):
    """A filled pack is a pillow, not a card: body rows narrow by up to `amount` of the width; header and base stay."""
    if amount <= 0:
        return p
    w, h = p.size
    n = 32
    mesh = []

    def d(y):
        t = min(1.0, max(0.0, (y / h - top) / (bottom - top)))
        return amount * w * math.sin(math.pi * t) ** 0.8

    for i in range(n):
        ya, yb = int(h * i / n), int(h * (i + 1) / n)
        da, db = d(ya), d(yb)
        mesh.append(((0, ya, w, yb), (-da, ya, -db, yb, w + db, yb, w + da, ya)))
    return p.transform((w, h), Image.MESH, mesh, Image.BICUBIC)


def prepare(src, height, angle=0.0, persp=0.03, bend=0.02, soft=0.5):
    """Load, scale to `height` px, pinch, keystone, slight lens softness, lean. Returns RGBA."""
    p = src if isinstance(src, Image.Image) else Image.open(src)
    p = p.convert("RGBA")
    p = p.resize((max(2, int(p.width * height / p.height)), int(height)), Image.LANCZOS)
    p = pinch(p, bend)
    p = keystone(p, persp)
    if soft:
        p = p.filter(ImageFilter.GaussianBlur(soft))
    if angle:
        p = p.rotate(angle, Image.BICUBIC, expand=True)
    return p


CA_MAX = 0.12   # % of the centre-to-corner distance. lens-test practice grades lateral CA in % of distance from the centre:
                # < 0.04 insignificant, 0.04-0.08 low, 0.08-0.15 moderate, > 0.15 strong. Cap below "strong".
CA_DEFAULT = 0.05


def lateral_ca(c, pct=CA_DEFAULT):
    """Lateral chromatic aberration, optional and subtle (off by default in camera_pass). A lens magnifies red
    slightly more and blue slightly less than green, so R and B are displaced against G radially, growing with
    distance from the centre: zero in the middle, `pct` % of the centre-to-corner distance at the corner (capped
    at CA_MAX). It shows only on strong tangential edges, as in a real photo; flat areas are unchanged.
    c: H x W x 3 float. Use it only on a clean or synthetic plate; a real photo plate already has its own lens."""
    H, W = c.shape[:2]
    cy, cx = (H - 1) / 2, (W - 1) / 2
    rmax = math.hypot(cx, cy)
    px = float(np.clip(pct, 0, CA_MAX)) / 100 * rmax          # displacement at the corner, in px
    if px <= 0:
        return c
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    out = c.copy()
    for ch, sign in ((0, 1.0), (2, -1.0)):
        k = 1 + sign * px / rmax                          # red magnified, blue shrunk, by px at the corner
        sx = np.clip(cx + (xx - cx) / k, 0, W - 1)
        sy = np.clip(cy + (yy - cy) / k, 0, H - 1)
        x0 = np.floor(sx).astype(np.int32); y0 = np.floor(sy).astype(np.int32)
        x1 = np.minimum(x0 + 1, W - 1); y1 = np.minimum(y0 + 1, H - 1)
        fx, fy = sx - x0, sy - y0
        a = c[..., ch]
        out[..., ch] = (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x1] * fx * (1 - fy)
                        + a[y1, x0] * (1 - fx) * fy + a[y1, x1] * fx * fy)
    return out


def measure_ca(img, band=0.15):
    """R-vs-G horizontal displacement (px) at strong edges in the right-hand band of the frame, by
    cross-correlation of row gradients. Used by the self-test; positive = red pushed outward."""
    a = np.asarray(img, np.float32)
    H, W = a.shape[:2]
    x0 = int(W * (1 - band))
    gr = np.diff(a[:, x0:, 0], axis=1); gg = np.diff(a[:, x0:, 1], axis=1)
    best, arg = -1e18, 0.0
    for s10 in range(-40, 41):
        s = s10 / 10
        i = int(math.floor(s)); f = s - i
        sh = np.roll(gg, i, axis=1) * (1 - f) + np.roll(gg, i + 1, axis=1) * f
        v = float((gr[:, 5:-5] * sh[:, 5:-5]).sum())
        if v > best:
            best, arg = v, s
    return arg


# ------------------------------------------------------------------ the scene

class Scene:
    def __init__(self, plate, long=None):
        im = plate if isinstance(plate, Image.Image) else Image.open(plate)
        im = im.convert("RGB")
        if long and max(im.size) < long * 0.95:
            k = long / max(im.size)
            im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
        self.plate = im
        self.W, self.H = im.size
        self.can = _f(im).copy()
        self.gain, self.cast = light_map(im)
        self.mask = np.zeros((self.H, self.W), np.float32)
        self.sigma = noise_sigma(im)

    # -------------------------------------------------------------- shadows
    def _darken(self, m, x0, y0, dark):
        xs, ys, xe, ye, ox, oy = _paste_region(self.W, self.H, x0, y0, m.shape[1], m.shape[0])
        if xe > xs and ye > ys:
            mm = m[oy:oy + ye - ys, ox:ox + xe - xs]
            self.can[ys:ye, xs:xe] *= (1 - dark * mm)[..., None]

    def _ground_shadow(self, A, x0, y0, light, dark, blur, squash):
        """Standing product: its silhouette laid down on the surface, sheared away from the key, penumbra growing
        with distance from the base (a projected shadow, not a drop shadow)."""
        hp, wp = A.shape
        dx, dy = light
        rows = max(4, int(squash * hp * (0.6 + 2.0 * max(dy, 0.02))))
        span = int(dx / max(abs(dy) + 0.15, 0.15) * hp * 0.9)
        gw = wp + abs(span)
        G = np.zeros((rows, gw), np.float32)
        for r in range(rows):
            t = 1 - r / (rows - 1)                       # 1 = far tip of the shadow, 0 = at the base
            src_r = min(hp - 1, int((1 - t) * (hp - 1)))
            o = int(t * span) if span >= 0 else abs(span) + int(t * span)
            G[r, o:o + wp] = np.maximum(G[r, o:o + wp], A[src_r] * (1 - 0.75 * t))
        # penumbra grows with distance from the base: sharp and dark at contact, wide and faint at the tip
        pad = int(blur * 6)
        bot = max(2, int(blur * 2))                         # room below the base row so the near edge blurs, not clips
        G = np.pad(G, ((pad, bot), (pad, pad)))
        far = np.concatenate([np.ones(pad), np.linspace(1, 0, rows), np.zeros(bot)])[:, None]
        G = gblur(G, max(2, blur)) * (1 - far) + gblur(G, max(4, blur * 5)) * far
        gw += 2 * pad
        gx0 = (x0 if span >= 0 else x0 - abs(span)) - pad
        self._darken(G, gx0, y0 + hp - rows - pad + int(hp * 0.004), dark)

    def _drop_shadow(self, A, x0, y0, off, dark, blur):
        pad = int(blur * 3)
        m = np.zeros((A.shape[0] + 2 * pad, A.shape[1] + 2 * pad), np.float32)
        m[pad:pad + A.shape[0], pad:pad + A.shape[1]] = A
        self._darken(gblur(m, blur), x0 + off[0] - pad, y0 + off[1] - pad, dark)

    def _contact(self, x0, base_y, wp, hp, dark):
        """Tight occlusion where the product meets the surface: the darkest few millimetres in any real photo."""
        w, h = int(wp * 1.1), max(6, int(hp * 0.06))
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).ellipse([wp * 0.07, h * 0.30, w - wp * 0.07, h * 0.70], fill=255)
        m = _f(m.filter(ImageFilter.GaussianBlur(max(2, hp * 0.010)))) / 255
        self._darken(m, int(x0 - wp * 0.05), int(base_y - h / 2), dark)

    # -------------------------------------------------------------- seat one product
    def seat(self, src, at, height, angle=0.0, light=None, persp=0.03, mode="stand", bend=0.02,
             sheen=0.08, wrap=0.35, sat=0.88, cast_k=0.45, light_k=1.0, lift=0.4, shadow_dark=0.5,
             contact_dark=0.55, soft=0.5, dim=1.0):
        """Place `src` (path or RGBA) so its base centre sits on `at` (x, y px). Height in plate px."""
        p = prepare(src, height, angle, persp, bend, soft)
        hp, wp = p.height, p.width
        x0, y0 = int(at[0] - wp / 2), int(at[1] - hp)
        if light is None or light == "auto":
            light = estimate_light(self.gain)
        A = _f(p.split()[3]) / 255
        if mode == "lie":
            self._drop_shadow(A, x0, y0, (int(light[0] * hp), int(light[1] * hp)), shadow_dark, max(3, hp * 0.03))
            self._drop_shadow(A, x0, y0, (int(light[0] * hp * 0.2), int(light[1] * hp * 0.2)), 0.45, max(2, hp * 0.006))
        else:
            self._ground_shadow(A, x0, y0, light, shadow_dark, max(2, hp * 0.02), 0.22)
            self._contact(x0, at[1], wp, hp, contact_dark)

        xs, ys, xe, ye, ox, oy = _paste_region(self.W, self.H, x0, y0, wp, hp)
        if xe <= xs or ye <= ys:
            return self
        P = _f(p)[oy:oy + ye - ys, ox:ox + xe - xs]
        a2 = A[oy:oy + ye - ys, ox:ox + xe - xs]
        rgb = P[..., :3]
        hh, ww = a2.shape
        # tone match: room saturation, the plate's light falloff and colour cast at this spot
        lum = rgb.mean(-1, keepdims=True)
        rgb = lum + (rgb - lum) * sat
        g = self.gain[ys:ye, xs:xe][..., None]
        c = self.cast[ys:ye, xs:xe]
        yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
        u = xx / max(ww - 1, 1) * 2 - 1
        v = yy / max(hh - 1, 1) * 2 - 1
        lx, ly = -light[0], -light[1]
        nrm = max(math.hypot(lx, ly), 1e-6)
        toward = (u * lx + v * ly) / nrm                      # +1 = side facing the key light
        roll = 1 - 0.10 * (np.abs(u) ** 2.2) * (bend > 0)     # filled pack rolls off at the sides
        shade = (1 + 0.10 * toward) * roll
        rgb = rgb * (1 - light_k + light_k * g) * (1 - cast_k + cast_k * c) * shade[..., None]
        # sheen: broad, soft, along the light axis
        if sheen:
            sh = np.exp(-((toward - 0.55) ** 2) / 0.08) * sheen * (1 - np.abs(u) ** 3)
            rgb = rgb + (255 - rgb) * sh[..., None] * np.clip(g, 0, 1)
        # edge occlusion: the outer edge turns away from the light and darkens
        er = gblur(a2, max(2, ww / 90))
        rgb = rgb * (0.80 + 0.20 * np.clip(er, 0, 1)[..., None] ** 0.6)
        # black lift to the plate's own black level (pure render darks read pasted)
        blk = np.percentile(self.can[ys:ye, xs:xe].reshape(-1, 3), 2, axis=0)
        rgb = blk * lift + rgb * (1 - blk * lift / 255)
        # light wrap: the room's colour spills a little over the outer edge
        if wrap:
            env = gblur(self.can[ys:ye, xs:xe], max(3, ww / 60))
            inner = _f(_u8(a2 * 255).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(max(2, ww / 120)))) / 255
            band = np.clip(a2 - inner, 0, 1)[..., None]
            rgb = rgb * (1 - wrap * band) + env * wrap * band
        rgb = rgb * dim
        a = a2[..., None]
        self.can[ys:ye, xs:xe] = self.can[ys:ye, xs:xe] * (1 - a) + rgb * a
        self.mask[ys:ye, xs:xe] = np.maximum(self.mask[ys:ye, xs:xe], a2)
        return self

    # -------------------------------------------------------------- bands in front of the product
    def relay(self, bands):
        """Paste plate bands (y0, y1 px) back on top: a shelf lip or a table edge that sits in front of the base."""
        P = _f(self.plate)
        for y0, y1 in bands:
            y0, y1 = int(max(0, y0)), int(min(self.H, y1))
            self.can[y0:y1] = P[y0:y1]
            self.mask[y0:y1] = 0
        return self

    # -------------------------------------------------------------- the camera
    def camera_pass(self, halation=0.08, ca=0.0, vignette=0.14, grain=None, soften=0.5, seed=3):
        """What a lens and sensor add to CG: micro-softness on the product, warm halation on highlights,
        optional lateral chromatic aberration (ca = % of centre-to-corner, 0 = off), light falloff, and grain matched to the plate's own noise
        (on the product only; the plate keeps its grain)."""
        c = self.can / 255
        H, W = self.H, self.W
        a3 = self.mask[..., None]
        if soften:
            c = c * (1 - soften * a3) + gblur(c, 0.7) * soften * a3
        if halation:
            hi = np.clip(c @ np.array([0.3, 0.59, 0.11], np.float32) - 0.82, 0, 1) * 4
            c = c + gblur(hi, max(4, W / 200))[..., None] * np.array([1.0, 0.85, 0.65], np.float32) * halation
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        rr = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
        if ca:
            c = lateral_ca(c, ca)
        if vignette:
            c = c * (1 - vignette * np.clip(rr - 0.45, 0, 1) ** 1.6)[..., None]
        sig = (self.sigma if grain is None else grain) / 255
        rnd = np.random.default_rng(seed)
        n = gblur(rnd.normal(0, 1, (H, W)).astype(np.float32), 0.6)
        n = n / max(n.std(), 1e-6)
        c = c + (n * sig)[..., None] * a3
        self.can = np.clip(c, 0, 1) * 255
        return self

    def stamp(self, text=STAMP):
        if not text:
            return self
        im = _u8(self.can)
        d = ImageDraw.Draw(im)
        fs = max(12, im.width // 110)
        font = None
        for name in ("arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc"):
            try:
                font = ImageFont.truetype(name, fs)
                break
            except Exception:
                pass
        if font is None:
            try:
                font = ImageFont.load_default(size=fs)
            except Exception:
                font = ImageFont.load_default()
        d.text((int(fs * 1.4), im.height - int(fs * 2.2)), text, fill=(255, 255, 255), font=font,
               stroke_width=1, stroke_fill=(0, 0, 0))
        self.can = _f(im)
        return self

    def image(self):
        return _u8(self.can)

    def finish(self, out, stamp=STAMP, quality=92, **camera):
        self.camera_pass(**camera)
        self.stamp(stamp)
        im = self.image()
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        im.save(out, quality=quality)
        return out


# ------------------------------------------------------------------ self-test

def synthetic_plate(W=1600, H=1200, table_y=0.62, seed=1):
    """A plain room: warm wall lit from the upper left, a wooden table with grain, a front edge band, plate noise."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ty = int(H * table_y)
    wall = np.array([214, 204, 188], np.float32) * (1.06 - 0.22 * (xx / W) - 0.10 * (yy / H))[..., None]
    wood = np.array([142, 98, 64], np.float32)
    streak = np.sin(xx / W * 60 + np.sin(yy / H * 9) * 3) * 0.05 + gblur(rng.normal(0, 1, (H, W)).astype(np.float32), 3) * 0.04
    table = wood * (1.10 - 0.25 * (xx / W) + (yy - ty) / H * 0.25 + streak)[..., None]
    img = np.where((yy < ty)[..., None], wall, table)
    img[ty:ty + 3] *= 0.75                                         # back edge where table meets wall
    edge0 = int(H * 0.90)                                          # raised front rail (a shelf lip) in front of the surface
    img[edge0:] = (wood * 0.62)[None, None, :] * (1.0 - 0.2 * (xx[edge0:] / W))[..., None]
    img[edge0:edge0 + 3] = img[edge0:edge0 + 3] * 0.4 + 255 * 0.25                    # lit lip highlight
    img = img + rng.normal(0, 3.0, (H, W, 1)).astype(np.float32)
    return _u8(img), ty, edge0


def synthetic_product(w=520, h=760, tint=(224, 132, 40), header=(176, 92, 22), name="SAMPLE"):
    """A stand-in pouch: tinted film, darker header band with crimp ribs, a white label panel with real type."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], int(w * 0.05), fill=tint + (255,))
    d.rectangle([0, 0, w, int(h * 0.12)], fill=header + (255,))
    rib = tuple(int(v * 0.85) for v in header)
    for i in range(0, w, 6):                                          # crimp ribs on the top seal
        d.line([i, 4, i, int(h * 0.05)], fill=rib + (255,), width=2)
    d.rectangle([int(w * 0.12), int(h * 0.38), int(w * 0.88), int(h * 0.78)], fill=(250, 247, 240, 255))
    try:
        f1 = ImageFont.truetype("arial.ttf", int(h * 0.075)); f2 = ImageFont.truetype("arial.ttf", int(h * 0.03))
    except Exception:
        f1 = f2 = ImageFont.load_default()
    d.text((w / 2, h * 0.52), name, fill=(30, 26, 23), font=f1, anchor="mm")
    d.text((w / 2, h * 0.64), "PRODUCT · 100 g", fill=(30, 26, 23), font=f2, anchor="mm")
    d.rectangle([0, int(h * 0.95), w, h], fill=header + (255,))
    return im


def _lum(a):
    return a[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)


def _hp_sigma(a):
    """Noise sigma of a flat patch: robust std of the high-pass."""
    g = _lum(a)
    hp = g - gblur(g, 1.5)
    return float(1.4826 * np.median(np.abs(hp - np.median(hp))))


def ca_selftest():
    """Lateral CA on a synthetic grid of vertical bars: off = no shift; on = red pushed outward at the edge,
    none at the centre, and never beyond the cap."""
    W, H = 2000, 1000
    xx = np.arange(W)
    bars = ((xx // 24) % 2).astype(np.float32)
    g = np.repeat(bars[None, :], H, 0)
    img = np.stack([g, g, g], -1) * 0.8 + 0.1
    off = measure_ca(img * 255)
    on = lateral_ca(img, CA_MAX)
    edge = measure_ca(on * 255)
    mid = lateral_ca(img, CA_MAX)[:, W // 2 - 150:W // 2 + 150]
    centre = measure_ca(mid * 255, band=1.0)
    rmax = math.hypot((W - 1) / 2, (H - 1) / 2)
    cap_px = CA_MAX / 100 * rmax
    return [("CA off by default leaves no R/G shift", abs(off) < 0.15),
            ("CA on: red displaced outward at the frame edge", edge > 0.3),
            ("CA on: no shift at the centre", abs(centre) < 0.3),
            (f"CA never beyond the cap ({CA_MAX}% = {cap_px:.2f} px at the corner)", edge <= cap_px + 0.15)]


def selftest(out):
    """Builds a synthetic plate + two products and checks the result against the QA list in
    references/camera_pass.md (each check is a known tell of a fake composite)."""
    plate, ty, edge0 = synthetic_plate()
    s = Scene(plate)
    W, H = s.W, s.H
    light = estimate_light(s.gain)
    # back pack: fully visible base, used for the grounding checks
    bx, by, ph = int(W * 0.64), int(H * 0.80), int(H * 0.40)
    s.seat(synthetic_product(tint=(118, 150, 70), header=(84, 110, 46), name="KIWI"), at=(bx, by), height=ph, angle=1.0, dim=0.97)
    # front pack: its base stands just behind the rail, so the rail must be re-laid over it
    fx0, fy0 = int(W * 0.30), int(H * 0.915)
    s.seat(synthetic_product(), at=(fx0, fy0), height=int(H * 0.52), angle=-1.5)
    mask = s.mask.copy()
    s.relay([(edge0, H)])
    pre_cam = s.can.copy()
    s.finish(out)
    R = _f(Image.open(out).convert("RGB"))
    P = _f(plate)
    LR, LP = _lum(R), _lum(P)
    pw = int(ph * 520 / 760)
    LP = LP * 1.0
    checks = [("size matches plate", R.shape[:2] == P.shape[:2])]
    # 1. grounding: tight contact shadow at the base
    under = LR[by - 3:by + 4, bx - pw // 4:bx + pw // 4].mean()
    open_t = LP[by - 3:by + 4, bx - pw // 4:bx + pw // 4].mean()
    checks.append(("contact shadow: base at least 25% darker than the bare table", under < open_t * 0.75))
    # 2. cast shadow falls away from the key (light from the left here -> shadow on the right of the base)
    yb = by - int(ph * 0.03)
    right = (LR[yb - 6:yb, bx + pw // 2 + 4:bx + pw // 2 + 40] / np.maximum(LP[yb - 6:yb, bx + pw // 2 + 4:bx + pw // 2 + 40], 1)).mean()
    left = (LR[yb - 6:yb, bx - pw // 2 - 40:bx - pw // 2 - 4] / np.maximum(LP[yb - 6:yb, bx - pw // 2 - 40:bx - pw // 2 - 4], 1)).mean()
    checks.append((f"cast shadow falls away from the key light (light dx {light[0]:+.2f})", (right < left - 0.03) if light[0] > 0 else (left < right - 0.03)))
    # 3. shadow is darkest near the base and fades with distance
    near = (LR[yb - 8:yb - 2, bx + pw // 2 + 4:bx + pw // 2 + 30] / np.maximum(LP[yb - 8:yb - 2, bx + pw // 2 + 4:bx + pw // 2 + 30], 1)).mean()
    fx = bx + pw // 2 + int(light[0] * ph * 0.9) - 10
    far = (LR[yb - 8:yb - 2, fx:fx + 26] / np.maximum(LP[yb - 8:yb - 2, fx:fx + 26], 1)).mean()
    checks.append(("cast shadow darkest at the base, lighter further out", near < far))
    # 4. black level: the product's darkest tones are not below the plate's (pure render blacks read pasted)
    m = mask > 0.99
    checks.append(("black level: product P1 >= 90% of plate P1", np.percentile(LR[m], 1) >= np.percentile(LP, 1) * 0.9))
    # 5. no dark halo: the ring just outside the side edges is not darker than the room beyond it
    r0, r1 = int(by - ph * 0.85), int(by - ph * 0.45)
    row = mask[(r0 + r1) // 2].copy(); row[: bx - pw] = 0
    xl = int(np.argmax(row > 0.02))                                   # outermost trace of the silhouette
    ring = LR[r0:r1, xl - 6:xl - 2].mean(); beyond = LR[r0:r1, xl - 20:xl - 10].mean()
    checks.append(("edges: no dark fringe outside the silhouette", ring > beyond * 0.95))
    # 6. light wrap: the outermost product pixels move toward the room colour
    inner = pre_cam[r0:r1, xl + 14:xl + 20].mean(); outer = pre_cam[r0:r1, xl + 3:xl + 5].mean()
    room = pre_cam[r0:r1, xl - 20:xl - 10].mean()
    checks.append(("light wrap: edge pixels lean toward the room", abs(outer - room) < abs(inner - room)))
    # 7. grain: the product carries the plate's grain (within 0.6-1.6x)
    ly0, ly1 = int(by - ph * 0.30), int(by - ph * 0.26)                  # flat label area under the type
    pg = _hp_sigma(R[ly0:ly1, bx - pw // 6:bx + pw // 6]); plg = _hp_sigma(P[int(H * 0.1):int(H * 0.3), int(W * 0.05):int(W * 0.25)])
    checks.append((f"grain matched to the plate ({pg:.2f} vs {plg:.2f})", 0.6 * plg <= pg <= 1.6 * plg))
    # 8. the print stays readable: label type keeps real edge contrast after the camera pass
    t0, t1 = int(by - ph * 0.53), int(by - ph * 0.43)
    text = LR[t0:t1, bx - pw // 4:bx + pw // 4]
    checks.append(("print stays sharp (type contrast > 120 levels)", np.percentile(text, 98) - np.percentile(text, 2) > 120))
    # 9. re-lay: the front lip sits over the product
    checks.append(("front lip re-laid over the product", mask[edge0:].max() > 0 and np.abs(pre_cam[edge0:] - P[edge0:]).max() == 0))
    # 10. disclosure stamp
    st = R[H - 30:H - 8, 10:400]
    checks.append(("disclosure stamp present", (st.min(-1) > 235).sum() > 30))
    checks += ca_selftest()
    for k, v in checks:
        print(("PASS " if v else "FAIL ") + k)
    print(out, f"{W}x{H}", "plate grain sigma", round(s.sigma, 2), "light", tuple(round(v, 2) for v in light))
    return all(v for _, v in checks)


# ------------------------------------------------------------------ CLI

def _pair(s, ref=None):
    a, b = (float(v) for v in s.split(","))
    if ref and abs(a) <= 1 and abs(b) <= 1 and ("." in s):
        a, b = a * ref[0], b * ref[1]
    return a, b


def main(argv=None):
    ap = argparse.ArgumentParser(description="Seat a real product render into an empty plate.")
    ap.add_argument("--plate"); ap.add_argument("--product"); ap.add_argument("--at"); ap.add_argument("--height", type=float)
    ap.add_argument("--angle", type=float, default=0.0); ap.add_argument("--out", default="composite_out.jpg")
    ap.add_argument("--light", default="auto"); ap.add_argument("--persp", type=float, default=0.03)
    ap.add_argument("--mode", choices=["stand", "lie"], default="stand")
    ap.add_argument("--relay", default=""); ap.add_argument("--bend", type=float, default=0.02)
    ap.add_argument("--sheen", type=float, default=0.08); ap.add_argument("--wrap", type=float, default=0.35)
    ap.add_argument("--grain", type=float, default=None); ap.add_argument("--long", type=int, default=None)
    ap.add_argument("--ca", type=float, default=0.0, help="lateral CA, %% of centre-to-corner (0 off, 0.05 subtle, cap 0.12)")
    ap.add_argument("--stamp", default=STAMP); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        out = a.out if a.out != "composite_out.jpg" else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples", "composite_demo.jpg")
        return 0 if selftest(os.path.normpath(out)) else 1
    if not (a.plate and a.product and a.at and a.height):
        ap.error("--plate, --product, --at and --height are required (or --selftest)")
    s = Scene(a.plate, long=a.long)
    at = _pair(a.at, (s.W, s.H))
    h = a.height * s.H if a.height <= 1 else a.height
    light = "auto" if a.light == "auto" else _pair(a.light)
    s.seat(a.product, at=at, height=h, angle=a.angle, light=light, persp=a.persp, mode=a.mode,
           bend=a.bend, sheen=a.sheen, wrap=a.wrap)
    if a.relay:
        s.relay([_pair(b, (s.H, s.H)) for b in a.relay.split(";") if b.strip()])
    print(s.finish(a.out, stamp=a.stamp, grain=a.grain, ca=a.ca))
    return 0


if __name__ == "__main__":
    sys.exit(main())
