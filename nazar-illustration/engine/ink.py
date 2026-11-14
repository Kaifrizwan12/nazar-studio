"""ink: draw like a hand, in code. Pressure strokes, construction curves, hatching, stipple, offset flats, riso layers.

Use it from a scene script (see examples/), not as a filter:

    from ink import Sheet, ellipse_pts, arc_pts
    s = Sheet(200, 150, paper="#F4EFE6", seed=7)                  # mm
    s.flat(shape, "#D97757", offset=(0.8, -0.6))                    # a fill, misregistered like print
    s.stroke([(20, 40), (60, 22), (110, 30)], width=1.2, taper=0.3) # a pen line through hand-placed points
    s.hatch(shape, angle=35, gap=1.4, width=0.25, tone=2)           # nested hatching (tone 1-4)
    s.stipple(shape, n=900, r=0.25)                                 # Poisson-disk stipple
    s.save("out/scene")                                             # .svg (vector) + .png (+ riso grain if layers used)

Rules baked in (from the research in references/method.md):
  - Strokes are filled outlines (width × pressure curve, tapered ends), never a uniform stroke-width.
  - Paths go through centripetal Catmull–Rom splines (alpha 0.5: no cusps or loops) with LOW-frequency wobble only.
  - Ends overshoot or stop short a little; shapes don't close perfectly unless asked.
  - Tone comes from marks (hatch layers nest; darker tones add a crossing layer), not from opacity blur.
  - Flats are offset from the line like misregistered print. One accent colour is the default budget.
Dependencies: numpy, Pillow, CairoSVG (all in nazar-core/engine/requirements.txt).
"""
import math, os, random
import numpy as np

# ------------------------------------------------------------------ geometry helpers

def catmull_rom(pts, n=16, alpha=0.5, closed=False):
    """Centripetal Catmull–Rom through pts. Returns a dense polyline."""
    P = [np.array(p, float) for p in pts]
    if len(P) < 2: return np.array(P)
    if closed: P = [P[-1]] + P + [P[0], P[1]]
    else: P = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t0 = 0.0
        t1 = t0 + max(np.linalg.norm(p1 - p0), 1e-6) ** alpha
        t2 = t1 + max(np.linalg.norm(p2 - p1), 1e-6) ** alpha
        t3 = t2 + max(np.linalg.norm(p3 - p2), 1e-6) ** alpha
        for t in np.linspace(t1, t2, n, endpoint=False):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    out.append(P[-2])
    return np.array(out)

def ellipse_pts(cx, cy, rx, ry, rot=0.0, n=12, start=0.0, sweep=360.0, closed=True):
    """Key points on an ellipse (feed to stroke/flat). Slight asymmetry is added by the Sheet's hand, not here."""
    a0, r = math.radians(start), math.radians(rot)
    k = n if closed else n + 1
    pts = []
    for i in range(k):
        a = a0 + math.radians(sweep) * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)))
    return pts

def arc_pts(cx, cy, r, a0, a1, n=8):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

def _arclen(p):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    return d

def _normals(p):
    t = np.gradient(p, axis=0)
    t /= (np.linalg.norm(t, axis=1, keepdims=True) + 1e-9)
    return np.c_[-t[:, 1], t[:, 0]]

def smooth_noise(n, seed, octaves=2, freq=1.5):
    """Low-frequency 1D noise in [-1, 1] over n samples (sum of a few random sines: no high-frequency jitter)."""
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 1, n)
    v = np.zeros(n)
    for o in range(octaves):
        f = freq * (2 ** o) * rng.uniform(0.7, 1.3)
        v += np.sin(2 * math.pi * f * x + rng.uniform(0, 6.283)) / (2 ** o)
    return v / max(1e-9, np.abs(v).max())

def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi): inside = not inside
        j = i
    return inside

def _clip_line(poly, p0, d, L):
    """Intersections of the line p0 + t·d (t in [-L, L]) with poly; returns inside segments (even-odd)."""
    ts = []
    n = len(poly)
    for i in range(n):
        a, b = np.array(poly[i]), np.array(poly[(i + 1) % n])
        e = b - a
        den = d[0] * e[1] - d[1] * e[0]
        if abs(den) < 1e-12: continue
        w = a - p0
        t = (w[0] * e[1] - w[1] * e[0]) / den
        u = (w[0] * d[1] - w[1] * d[0]) / den
        if 0 <= u < 1: ts.append(t)
    ts.sort()
    return [(ts[i], ts[i + 1]) for i in range(0, len(ts) - 1, 2)]


# ------------------------------------------------------------------ the sheet

class Sheet:
    def __init__(self, w, h, paper="#F4EFE6", ink="#1A1917", seed=1, hand=1.0):
        self.w, self.h, self.paper, self.ink = w, h, paper, ink
        self.rng = random.Random(seed); self.seed = seed
        self.hand = hand                      # 0 = mechanical, 1 = natural, 2 = loose
        self.layers = {}                      # colour → list of svg elements (for riso separation)
        self.order = []                       # paint order of (colour, element)
        self.stats = {"strokes": 0, "flats": 0, "hatch_lines": 0, "dots": 0}

    def _add(self, colour, el):
        self.layers.setdefault(colour, []).append(el)
        self.order.append((colour, el))

    def _key(self, pts, closed=False):
        """Hand-placed points get a small, low-frequency human offset (never per-sample jitter)."""
        if self.hand <= 0: return [tuple(p) for p in pts]
        span = max(1e-6, max(math.dist(pts[0], p) for p in pts))
        a = 0.006 * span * self.hand
        return [(x + self.rng.gauss(0, a), y + self.rng.gauss(0, a)) for x, y in pts]

    # ---- line
    def stroke(self, pts, width=1.0, taper=0.25, taper_end=None, pressure="swell", colour=None, closed=False,
               overshoot=None, wobble=None, n=18, corners=False):
        """A pen/brush line through key points. pressure: 'swell' (thick middle), 'even', 'start' (heavy start),
        'end', or a list of 0-1 values per key point."""
        colour = colour or self.ink
        kp = self._key(pts, closed)
        if closed and overshoot is None: overshoot = 0.04 * self.hand   # a real hand rarely lands exactly on its start
        if corners:                       # straight runs between key points (boxes, folds, tools): no spline rounding
            seq = kp + (kp[:1] if closed else [])
            p = np.vstack([np.linspace(seq[i], seq[i + 1], max(3, n // 2), endpoint=False) for i in range(len(seq) - 1)] + [np.array(seq[-1])[None]])
            if closed and overshoot:
                e = np.array(seq[1]) - np.array(seq[0]); p = np.vstack([p, np.array(seq[0]) + e * overshoot * 1.5])
        elif closed:                      # loop continues smoothly past its start, so the seam has no kink
            loop = catmull_rom(kp, n=n, closed=True)
            extra = int(len(loop) * (overshoot or 0))
            p = np.vstack([loop, loop[:max(extra, 1)]])
        else:
            p = catmull_rom(kp, n=n, closed=False)
        if len(p) < 2: return
        s = _arclen(p); L = s[-1] or 1; u = s / L
        wob = (wobble if wobble is not None else 0.004 * self.hand) * L
        if wob: p = p + _normals(p) * (smooth_noise(len(p), self.rng.randint(0, 1 << 30)) * wob)[:, None]
        if isinstance(pressure, (list, tuple)):
            kpos = np.linspace(0, 1, len(pressure)); pr = np.interp(u, kpos, pressure)
        elif pressure == "even": pr = np.ones_like(u)
        elif pressure == "start": pr = 1 - 0.55 * u
        elif pressure == "end": pr = 0.45 + 0.55 * u
        else: pr = 0.62 + 0.38 * np.sin(math.pi * u)
        pr = pr * (1 + 0.08 * self.hand * smooth_noise(len(u), self.rng.randint(0, 1 << 30), 1, 2.5))
        te = taper if taper_end is None else taper_end
        tap = np.ones_like(u)
        if taper > 0: tap = np.minimum(tap, np.clip(u / taper, 0, 1) ** 0.6)
        if te > 0: tap = np.minimum(tap, np.clip((1 - u) / te, 0, 1) ** 0.6)
        r = np.maximum(width * 0.5 * pr * np.maximum(tap, 0.08), 0.02)
        nm = _normals(p)
        left, right = p + nm * r[:, None], p - nm * r[:, None]
        cap_s = [p[0] - (p[1] - p[0]) / (np.linalg.norm(p[1] - p[0]) + 1e-9) * r[0] * 0.8]
        cap_e = [p[-1] + (p[-1] - p[-2]) / (np.linalg.norm(p[-1] - p[-2]) + 1e-9) * r[-1] * 0.8]
        outline = np.vstack([left, cap_e, right[::-1], cap_s])
        d = "M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in outline) + " Z"
        self._add(colour, f'<path d="{d}" fill="{colour}"/>')
        self.stats["strokes"] += 1
        return p

    # ---- fills
    def flat(self, pts, colour, offset=(0.0, 0.0), smooth=True, n=10, opacity=1.0):
        """A flat colour area through key points, offset like misregistered print (offset in mm)."""
        kp = self._key(pts, True)
        p = catmull_rom(kp, n=n, closed=True) if smooth else np.array(kp)
        p = p + np.array(offset)
        d = "M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in p) + " Z"
        self._add(colour, f'<path d="{d}" fill="{colour}" fill-opacity="{opacity}"/>')
        self.stats["flats"] += 1
        return [tuple(q) for q in p]

    def shape(self, pts, smooth=True, n=10):
        """The polygon a set of key points describes (for hatch/stipple clipping), without drawing."""
        return [tuple(q) for q in (catmull_rom(pts, n=n, closed=True) if smooth else np.array(pts))]

    # ---- tone
    def hatch(self, poly, angle=35.0, gap=1.2, width=0.22, tone=1, colour=None, cross=None, margin=0.0):
        """Nested hatching inside poly. tone 1-4: each step adds a layer; tone ≥3 adds a crossing angle."""
        colour = colour or self.ink
        P = np.array(poly)
        c = P.mean(axis=0); R = np.max(np.linalg.norm(P - c, axis=1)) + 2
        angles = [angle]
        if tone >= 2: angles.append(angle)              # second pass offset by half a gap: denser, same direction
        if tone >= 3: angles.append(cross if cross is not None else angle + 75)
        if tone >= 4: angles.append((cross if cross is not None else angle + 75) + 30)
        for li, a in enumerate(angles):
            th = math.radians(a)
            dvec = np.array([math.cos(th), math.sin(th)]); nvec = np.array([-dvec[1], dvec[0]])
            off = (gap / 2) if (li == 1 and tone >= 2) else 0
            k = -R
            while k < R:
                p0 = c + nvec * (k + off + self.rng.uniform(-0.15, 0.15) * gap)
                for t0, t1 in _clip_line(poly, p0, dvec, R):
                    t0 += self.rng.uniform(-0.6, 0.9) * gap * 0.5 + margin   # hatch stops short / overshoots a touch
                    t1 -= self.rng.uniform(-0.6, 0.9) * gap * 0.5 + margin
                    if t1 - t0 < gap * 0.6: continue
                    a_, b_ = p0 + dvec * t0, p0 + dvec * t1
                    mid = (a_ + b_) / 2 + nvec * self.rng.uniform(-0.12, 0.12) * gap
                    self.stroke([tuple(a_), tuple(mid), tuple(b_)], width=width, taper=0.18, pressure="start", colour=colour, wobble=0.0015, n=6)
                    self.stats["hatch_lines"] += 1
                k += gap * (1.0 if tone < 2 or li != 1 else 1.0)

    def stipple(self, poly, n=600, r=0.25, colour=None, density=None):
        """Poisson-disk-ish stipple inside poly (dart throwing with a minimum distance). density(x, y) → 0..1 optional."""
        colour = colour or self.ink
        P = np.array(poly); x0, y0 = P.min(axis=0); x1, y1 = P.max(axis=0)
        area = 0.5 * abs(np.dot(P[:, 0], np.roll(P[:, 1], 1)) - np.dot(P[:, 1], np.roll(P[:, 0], 1)))
        dmin = math.sqrt(area / max(n, 1)) * 0.75
        pts, tries = [], 0
        cell = {}
        while len(pts) < n and tries < n * 40:
            tries += 1
            x, y = self.rng.uniform(x0, x1), self.rng.uniform(y0, y1)
            if not point_in_poly(x, y, poly): continue
            if density and self.rng.random() > density(x, y): continue
            gx, gy = int(x / dmin), int(y / dmin)
            if any(math.dist((x, y), q) < dmin for i in (-1, 0, 1) for j in (-1, 0, 1) for q in cell.get((gx + i, gy + j), [])): continue
            cell.setdefault((gx, gy), []).append((x, y)); pts.append((x, y))
        for x, y in pts:
            rr = r * self.rng.uniform(0.75, 1.25)
            self._add(colour, f'<ellipse cx="{x:.3f}" cy="{y:.3f}" rx="{rr:.3f}" ry="{rr * self.rng.uniform(0.8, 1):.3f}" fill="{colour}"/>')
        self.stats["dots"] += len(pts)

    def text_note(self, x, y, s, size=3, colour=None):
        """Small hand-set annotation in a system font (use the core engine for real brand type)."""
        colour = colour or self.ink
        self._add(colour, f'<text x="{x}" y="{y}" font-family="Space Mono, monospace" font-size="{size}" fill="{colour}">{s}</text>')

    # ---- output
    def svg(self, grain=False):
        body = "".join(el for _, el in self.order)
        g = ""
        if grain:
            g = ('<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="1.6" numOctaves="2" seed="3"/>'
                 '<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.10 0"/></filter>'
                 f'<rect width="{self.w}" height="{self.h}" filter="url(#grain)"/>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" viewBox="0 0 {self.w} {self.h}">'
                f'<rect width="{self.w}" height="{self.h}" fill="{self.paper}"/>{body}{g}</svg>')

    def save(self, base, px=2400, riso=False, misregister=0.5, overprint=False):
        """Write base.svg (vector) and base.png.
        riso=True: print look with correct occlusion: uneven ink density, paper grain, a hair of misregistration
                   between the flats and the line work.
        overprint=True: true riso overprint: each colour is its own ink, multiplied, NO occlusion (inks mix where
                   they overlap). Only for art designed for overprint (2-3 inks, planned overlaps)."""
        os.makedirs(os.path.dirname(base) or ".", exist_ok=True)
        open(base + ".svg", "w").write(self.svg())
        import cairosvg, io
        from PIL import Image, ImageChops, ImageFilter
        if not riso:
            cairosvg.svg2png(bytestring=self.svg().encode(), write_to=base + ".png", output_width=px)
            return base
        H = int(px * self.h / self.w)
        rng0 = np.random.default_rng(self.seed + 1)
        if not overprint:
            flats = [el for c, el in self.order if 'fill-opacity' in el or el.startswith('<path d=') and 'Z"' in el and c != self.ink]
            img = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=self.svg().encode(), output_width=px, output_height=H))).convert("RGB")
            # (misregistration lives in the flats' own offsets, so occlusion stays correct)
            a_ = np.asarray(img, dtype=np.float32)
            g = rng0.random((H, px)).astype(np.float32)
            g = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), dtype=np.float32) / 255
            dark = 1 - a_.mean(axis=2, keepdims=True) / 255                       # ink coverage
            a_ = a_ + (g[..., None] - 0.5) * 38 * (0.35 + dark)                   # uneven density, stronger in ink
            fib = np.asarray(Image.fromarray((rng0.random((H // 3, px // 3)) * 255).astype(np.uint8)).resize((px, H)).filter(ImageFilter.GaussianBlur(2)), dtype=np.float32) / 255
            a_ = a_ * (0.965 + 0.035 * fib[..., None])                            # paper fibre
            Image.fromarray(np.clip(a_, 0, 255).astype(np.uint8)).save(base + ".png")
            return base
        out = Image.new("RGB", (px, H), self.paper)
        rng = np.random.default_rng(self.seed)
        for colour, els in self.layers.items():
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}"><rect width="{self.w}" height="{self.h}" fill="#ffffff"/>'
                   + "".join(els) + "</svg>")
            lay = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=px, output_height=H))).convert("RGB")
            dx, dy = (rng.normal(0, misregister * px / self.w, 2)).astype(int)
            lay = ImageChops.offset(lay, int(dx), int(dy))
            noise = Image.fromarray((rng.random((H, px)) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
            mask = ImageChops.invert(lay.convert("L"))                       # ink coverage
            mask = ImageChops.multiply(mask, noise.point(lambda v: 205 + v // 5))  # uneven ink density
            inked = Image.composite(lay, Image.new("RGB", (px, H), "#ffffff"), mask)
            out = ImageChops.multiply(out, inked)
        out.save(base + ".png")
        return base
