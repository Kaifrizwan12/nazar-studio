#!/usr/bin/env python3
"""composers.py: product groups for case-study pages, each composed as ONE transparent RGBA picture.

The deck engine (nazar-pitch/engine/deck.py) fails the build when two placed images overlap or an image runs off
the page. So any group where products touch, tuck behind each other or bleed off an edge is composed here first,
then placed with a single d.img(). Works with any product cut-out: pouches, bottles, cans, cartons, tubes, jars,
books, devices. Plain Pillow + numpy.

    import sys; sys.path.insert(0, ".claude/skills/nazar-story/engine")
    from composers import Item, Light, fan, couple, row, cascade, stack, bleed_hero, grid, scatter, extend_canvas
    c = row([Item("small.png", height_mm=120), Item("big.png", height_mm=200)], true_scale=True, overlap=0.15)
    d.img(c.save(os.path.join(d.cache, "lineup.png")), 80, 300, 900, 600)
    d.page(b, device=c.device)                      # every composite names its layout device

Every composer returns a Composite: .image (RGBA cropped tight to its pixels; bleed_hero is the exact box),
.device (the layout device name, for nazar-story's no-repeat rule), .items (name, box, scale, angle, mask per
product), .scale (px per mm when true_scale, else None), .shadow (the shadow alpha, for checks) and .meta.

Shadows: one Light object is shared by every composer, so all shadows on a page fall the same way (default: light
from above and a little to the left, the direction the eye assumes). Each product gets a soft shadow plus a
tight contact shadow drawn from its exact silhouette, so seal teeth, tear notches and caps stay readable at the
ground line; 'cast' adds a ground-plane shadow trailing away from the light.

Scale truth: row/grid(true_scale=True) size products by their real height (or width) in mm, so a 30 g pack
never looks as big as a 250 g one (misleading size is a consumer-law issue in the EU, UK, US, India and
Pakistan; see nazar-story/references/research_composers.md).

CLI:
    python composers.py --selftest                       # synthetic products, asserts every guarantee
    python composers.py sheet [out.jpg]                  # contact sheet of every composer (synthetic products)
    python composers.py demo <folder of pack PNGs> [out.jpg]   # optional demo on real cut-outs
    python composers.py compose row a.png b.png -o out.png [--mm 120,200] [--overlap 0.2] [--seed 7]
    python composers.py extend photo.jpg -o out.jpg --left 300 [--feather 60]
"""
import os, sys, math, argparse, copy
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.normpath(os.path.join(HERE, "..", "..", "nazar-core", "engine", "fonts"))
ALPHA_MIN = 8            # alpha at or below this is treated as empty when cropping products and composites


# ---------------------------------------------------------------- light: one direction for the whole deck
@dataclass
class Light:
    """One light for every composer, so shadows on a page (and across a deck) agree.

    azimuth: degrees from straight up, where the light comes FROM; negative = from the left. Default -30
             (above and a little left: the perceptual prior measured at about -22 deg, rounded for a clear read).
    elevation: degrees above the ground; lower light = longer shadows.
    soft / contact / cast: opacities. *_lift: how far each shadow is thrown, as a fraction of the product height.
    *_blur: blur radius as a fraction of the product height (contact stays tiny so silhouette details survive).
    """
    azimuth: float = -30.0
    elevation: float = 52.0
    colour: tuple = (18, 14, 10)
    soft: float = 0.30
    soft_lift: float = 0.035
    soft_blur: float = 0.028
    contact: float = 0.55
    contact_lift: float = 0.006
    contact_blur: float = 0.0022
    cast: float = 0.26
    cast_squash: float = 0.30
    cast_blur: float = 0.012

    def direction(self):
        """Unit vector (image coords, y down) the shadow falls toward: away from the light."""
        a = math.radians(self.azimuth)
        return -math.sin(a), math.cos(a)

    def offset(self, h, lift):
        """Shadow offset (dx, dy) in px for a product h px tall thrown by `lift`."""
        t = h * lift / math.tan(math.radians(max(5.0, min(85.0, self.elevation))))
        ux, uy = self.direction()
        return ux * t, uy * t

    def scaled(self, k):
        """Same direction, shadows thrown k times as far (k < 1 for flat-lays: products lie on the surface)."""
        c = copy.copy(self); c.soft_lift *= k; c.contact_lift *= k; return c


LIGHT = Light()


# ---------------------------------------------------------------- products
class Item:
    """One product cut-out (path or PIL image), cropped to its own pixels so sizes mean the product, not padding.
    height_mm / width_mm: the real size, needed for true_scale (scale truth)."""

    def __init__(self, src, name=None, height_mm=None, width_mm=None):
        im = src if isinstance(src, Image.Image) else Image.open(src)
        im = im.convert("RGBA")
        bb = im.getchannel("A").point(lambda v: 255 if v > ALPHA_MIN else 0).getbbox()
        if bb is None: raise ValueError(f"empty product image: {name or src}")
        self.im = im.crop(bb)
        self.name = name or (os.path.splitext(os.path.basename(src))[0] if isinstance(src, str) else "item")
        self.height_mm, self.width_mm = height_mm, width_mm

    def px_per_mm(self):
        if self.height_mm: return self.im.height / self.height_mm
        if self.width_mm: return self.im.width / self.width_mm
        return None


def _items(xs):
    out = []
    for i, x in enumerate(xs):
        it = x if isinstance(x, Item) else Item(x)
        if it.name == "item": it.name = f"item{i + 1}"
        out.append(it)
    return out


def _prep(item, scale, angle=0.0):
    """Resize and turn a product in premultiplied alpha (no dark fringes), then crop to its pixels."""
    im = item.im.convert("RGBa")
    if abs(scale - 1) > 1e-6:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    if abs(angle) > 1e-6:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    im = im.convert("RGBA")
    bb = im.getchannel("A").point(lambda v: 255 if v > ALPHA_MIN else 0).getbbox()
    return im.crop(bb) if bb else im


def _true_scales(items, size, axis="height"):
    """Per-item resize factors so every product shares one px-per-mm; the tallest real product gets `size` px."""
    missing = [it.name for it in items if not (it.height_mm or it.width_mm)]
    if missing: raise ValueError("true_scale needs height_mm or width_mm on every item: " + ", ".join(missing))
    ref = max((it.height_mm or it.width_mm * it.im.height / it.im.width) for it in items)
    k = size / ref                                                          # px per mm
    return [k / it.px_per_mm() for it in items], k


# ---------------------------------------------------------------- shadows
def _blur(a, r):
    """Gaussian blur of a float alpha array (0..1)."""
    if r <= 0.05: return a
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im, np.float32) / 255


def shadow_layer(alpha, light, h, kind="soft"):
    """A shadow for one product. alpha: float array (0..1) of the product's silhouette; h: its height in px.
    Returns (alpha array, ox, oy): where to put the array's top-left relative to the product's top-left.
    kind 'contact' keeps the exact silhouette (tiny blur, tiny offset): notches and seal teeth stay visible."""
    if kind in ("soft", "contact"):
        k = light.soft if kind == "soft" else light.contact
        lift = light.soft_lift if kind == "soft" else light.contact_lift
        r = h * light.soft_blur if kind == "soft" else max(0.8, h * light.contact_blur)
        pad = int(math.ceil(r * 3)) + 2
        a = np.pad(alpha * k, pad)
        dx, dy = light.offset(h, lift)
        return _blur(a, r), dx - pad, dy - pad
    if kind == "cast":                                                      # ground plane, trailing away from the light
        hh, w = alpha.shape
        hs = max(2, int(hh * light.cast_squash))
        small = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).resize((w, hs), Image.BILINEAR), np.float32) / 255
        ux, _ = light.direction()
        sh = ux * hs / math.tan(math.radians(max(5.0, light.elevation))) * 1.6
        W_ = w + int(abs(sh)) + 2; out = np.zeros((hs, W_), np.float32); x0 = int(abs(sh)) if sh < 0 else 0
        for y in range(hs):
            t = (hs - 1 - y) / max(1, hs - 1)                               # 0 at the base, 1 at the far end
            s = x0 + int(round(sh * t)); out[y, s:s + w] = np.maximum(out[y, s:s + w], small[y] * (1 - 0.8 * t))
        r = max(1.0, h * light.cast_blur); pad = int(math.ceil(r * 3)) + 2
        a = _blur(np.pad(out * light.cast, pad), r)
        return a, -x0 - pad, hh - hs - pad
    raise ValueError(f"unknown shadow kind: {kind}")


# ---------------------------------------------------------------- the composite
@dataclass
class Composite:
    image: Image.Image
    device: str
    items: list = field(default_factory=list)         # dicts: name, box (x0,y0,x1,y1), scale, angle, mask (bool, box-sized)
    scale: float = None                                # px per mm when true_scale
    shadow: np.ndarray = None                          # union of shadow alphas before products cover them
    meta: dict = field(default_factory=dict)

    @property
    def size(self): return self.image.size

    def save(self, path):
        """Write the RGBA (PNG) or a flattened copy (JPEG on meta['paper'] or white). Returns the path."""
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        if path.lower().endswith((".jpg", ".jpeg")):
            bg = Image.new("RGBA", self.image.size, self.meta.get("paper", "#FFFFFF")); bg.alpha_composite(self.image.convert("RGBA"))
            bg.convert("RGB").save(path, quality=92)
        else:
            self.image.save(path)
        return path


def _assemble(placed, light, shadows, device, crop="tight", meta=None, scale=None):
    """placed: back-to-front dicts {im, x, y, name, scale, angle, h}. Each product's shadows are laid first, so a
    front product's shadow falls on whatever sits behind it; then the product. Returns a Composite."""
    light = light or LIGHT
    reach = 0
    for p in placed:
        dx, dy = light.offset(p["h"], light.soft_lift)
        reach = max(reach, int(abs(dx) + abs(dy) + p["h"] * light.soft_blur * 3 + p["h"] * 0.6 * ("cast" in shadows) + 8))
    x0 = min(p["x"] for p in placed) - reach; y0 = min(p["y"] for p in placed) - reach
    x1 = max(p["x"] + p["im"].width for p in placed) + reach; y1 = max(p["y"] + p["im"].height for p in placed) + reach
    W_, H_ = int(math.ceil(x1 - x0)), int(math.ceil(y1 - y0))
    cv = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); sh_acc = np.zeros((H_, W_), np.float32); col = tuple(light.colour)
    recs = []
    for p in placed:
        ix, iy = int(round(p["x"] - x0)), int(round(p["y"] - y0))
        al = np.asarray(p["im"].getchannel("A"), np.float32) / 255
        for kind in shadows:
            a, ox, oy = shadow_layer(al, light, p["h"], kind)
            sx, sy = int(round(ix + ox)), int(round(iy + oy))
            lay = Image.new("RGBA", (a.shape[1], a.shape[0]), col + (0,)); lay.putalpha(Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)))
            cx0, cy0 = max(0, sx), max(0, sy)
            if cx0 > sx or cy0 > sy: lay = lay.crop((cx0 - sx, cy0 - sy, lay.width, lay.height)); a = a[cy0 - sy:, cx0 - sx:]
            cv.alpha_composite(lay, (cx0, cy0))
            reg = sh_acc[cy0:cy0 + a.shape[0], cx0:cx0 + a.shape[1]]
            sh_acc[cy0:cy0 + reg.shape[0], cx0:cx0 + reg.shape[1]] = np.maximum(reg, a[:reg.shape[0], :reg.shape[1]])
        cv.alpha_composite(p["im"], (ix, iy))
        recs.append({"name": p["name"], "box": (ix, iy, ix + p["im"].width, iy + p["im"].height), "scale": p["scale"],
                     "angle": p.get("angle", 0.0), "mask": al > ALPHA_MIN / 255})
    if crop == "tight":
        bb = cv.getchannel("A").point(lambda v: 255 if v > 2 else 0).getbbox()
    else:                                                                    # an exact box in placement coords
        bx0, by0, bx1, by1 = crop; bb = (int(round(bx0 - x0)), int(round(by0 - y0)), int(round(bx1 - x0)), int(round(by1 - y0)))
    out = cv.crop(bb); sh = np.zeros((bb[3] - bb[1], bb[2] - bb[0]), np.float32)
    sx0, sy0 = max(0, bb[0]), max(0, bb[1]); sx1, sy1 = min(W_, bb[2]), min(H_, bb[3])
    sh[sy0 - bb[1]:sy1 - bb[1], sx0 - bb[0]:sx1 - bb[0]] = sh_acc[sy0:sy1, sx0:sx1]
    for r in recs:
        a, b, c, d = r["box"]; r["box"] = (a - bb[0], b - bb[1], c - bb[0], d - bb[1])
    m = dict(meta or {}); m["light"] = light; m["shadow_offsets"] = [light.offset(p["h"], light.soft_lift) for p in placed]
    m["notes"] = m.get("notes", [])
    return Composite(out, device, recs, scale, sh, m)


def _odd_note(n, meta):
    if n in (2, 4, 6) and n > 2: meta.setdefault("notes", []).append(f"{n} items: groups of 3 or 5 usually read calmer (advisory)")
    return meta


# ---------------------------------------------------------------- composers
def fan(items, height=600, step=0.62, angle=6.0, arc=0.035, light=None, shadows=("soft", "contact")):
    """A hand of cards: products overlap left to right, the outer ones turned out and dropped on an arc.
    step: horizontal step as a fraction of the product width; angle: turn per step out from the middle (deg);
    arc: drop of the outermost card per step squared, as a fraction of the height."""
    items = _items(items); n = len(items); mid = (n - 1) / 2; placed = []
    wref = height * np.mean([it.im.width / it.im.height for it in items])
    for i, it in enumerate(items):
        s = height / it.im.height; ang = (mid - i) * angle; im = _prep(it, s, ang)
        cx, cy = i * step * wref, (abs(mid - i) ** 2) * arc * height
        placed.append({"im": im, "x": cx - im.width / 2, "y": cy - im.height / 2, "name": it.name, "scale": s, "angle": ang, "h": height})
    return _assemble(placed, light, shadows, "hand of cards", meta=_odd_note(n, {"step": step, "angle": angle}))


def couple(front, back, height=600, overlap=0.60, rise=0.08, tilt=4.0, side="right", back_scale=1.0, light=None,
           shadows=("soft", "contact")):
    """Front leading, the second item (its back, or a partner) tucked behind, raised and turned a touch.
    overlap: fraction of the narrower item's width that the two share horizontally (0.6 = 60%).
    rise: how much higher the back item's base sits, as a fraction of the height. side: where the back peeks out."""
    f, b = _items([front, back]); sf = height / f.im.height; sb = height * back_scale / b.im.height
    fi = _prep(f, sf, 0.0); bi = _prep(b, sb, -tilt if side == "right" else tilt)
    mw = min(fi.width, bi.width); base = float(height)
    if side == "right": fx, bx = 0.0, fi.width - overlap * mw
    else: fx, bx = 0.0, -(bi.width - overlap * mw)
    placed = [{"im": bi, "x": bx, "y": base - rise * height - bi.height, "name": b.name, "scale": sb, "angle": -tilt, "h": height * back_scale},
              {"im": fi, "x": fx, "y": base - fi.height, "name": f.name, "scale": sf, "angle": 0.0, "h": height}]
    return _assemble(placed, light, shadows, "front-back pair", meta={"overlap": overlap, "rise": rise, "tilt": tilt})


def row(items, height=500, overlap=0.0, true_scale=False, on_top="auto", light=None, shadows=("soft", "contact")):
    """A lineup on one baseline. overlap > 0 tucks each item under the next by that fraction of the narrower width;
    overlap < 0 leaves a gap of that fraction. true_scale: size by real height_mm/width_mm (tallest = height px).
    on_top: 'auto' (the item nearer the light sits on top, so its shadow lands on its neighbour and the tuck
    reads as depth), 'right' (each item over its left neighbour) or 'left'."""
    items = _items(items); n = len(items)
    if true_scale: scales, k = _true_scales(items, height)
    else: scales, k = [height / it.im.height for it in items], None
    ims = [_prep(it, s) for it, s in zip(items, scales)]
    xs, x = [], 0.0
    for i, im in enumerate(ims):
        if i: x += ims[i - 1].width - overlap * min(ims[i - 1].width, im.width)
        xs.append(x)
    base = float(max(im.height for im in ims))
    placed = [{"im": im, "x": xs[i], "y": base - im.height, "name": items[i].name, "scale": scales[i], "angle": 0.0, "h": im.height}
              for i, im in enumerate(ims)]
    if on_top == "auto": on_top = "left" if (light or LIGHT).direction()[0] > 0 else "right"
    if on_top == "left": placed = placed[::-1]
    dev = "scale lineup" if true_scale else ("overlap row" if overlap > 0 else "standing row")
    return _assemble(placed, light, shadows, dev, meta=_odd_note(n, {"overlap": overlap, "true_scale": true_scale}), scale=k)


def cascade(items, height=600, step=(0.34, -0.10), shrink=0.07, tilt=0.0, light=None, shadows=("soft", "contact")):
    """The first item in front and largest; each next one steps back (right and up by `step` of the front's width
    and height) and shrinks by `shrink`, like products walking into depth."""
    items = _items(items); placed = []; w0 = height * items[0].im.width / items[0].im.height
    for i, it in enumerate(items):
        hh = height * (1 - shrink) ** i; s = hh / it.im.height; im = _prep(it, s, tilt * (i % 2 * 2 - 1) if tilt else 0.0)
        base = height + step[1] * height * i
        placed.append({"im": im, "x": step[0] * w0 * i, "y": base - im.height, "name": it.name, "scale": s, "angle": 0.0, "h": hh})
    return _assemble(placed[::-1], light, shadows, "cascade", meta={"step": step, "shrink": shrink})


def stack(items, width=520, seed=3, jitter=0.04, max_turn=2.5, true_scale=False, light=None, shadows=("soft", "contact")):
    """A pile: items lying on top of each other (boxes, books, bars, folded garments), bottom item first,
    with a small seeded shift and turn so it reads as stacked by hand. true_scale uses width_mm/height_mm."""
    items = _items(items); rng = np.random.default_rng(seed)
    if true_scale:
        scales, k = _true_scales(items, 1.0)
        mx = max(it.im.width * s for it, s in zip(items, scales)); scales = [s * width / mx for s in scales]; k *= width / mx
    else: scales, k = [width / it.im.width for it in items], None
    placed, surf = [], {}                                                   # surf: column -> top of the pile (y, px)
    for it, s in zip(items, scales):
        ang = float(rng.uniform(-max_turn, max_turn)); im = _prep(it, s, ang)
        x = int(round(-im.width / 2 + float(rng.uniform(-jitter, jitter)) * width))
        m = np.asarray(im.getchannel("A")) > 128; bottom = m.shape[0] - 1 - np.argmax(m[::-1], 0)   # lowest pixel per column
        if not surf: y = -im.height
        else:                                                               # drop it until its silhouette touches the pile
            gaps = [surf[x + c] - bottom[c] for c in range(m.shape[1]) if m[:, c].any() and (x + c) in surf]
            y = int(min(gaps)) - 1 + max(1, int(0.004 * im.height)) if gaps else -im.height
        top_ = np.argmax(m, 0)
        for c in range(m.shape[1]):
            if m[:, c].any(): surf[x + c] = min(surf.get(x + c, 10 ** 9), y + top_[c])
        placed.append({"im": im, "x": float(x), "y": float(y), "name": it.name, "scale": s, "angle": ang, "h": im.height})
    return _assemble(placed, light, shadows, "stack", meta={"seed": seed}, scale=k)


def bleed_hero(item, box=(1000, 1080), edge="right", off=0.30, tilt=-9.0, height=None, along=0.5, light=None,
               shadows=("soft", "contact")):
    """One product, turned and large, cut by one edge of an exact box so it bleeds off the page. Place the result
    flush with that page edge (e.g. d.img(path, page_w - box_w, 0, box_w, box_h)) and the off-page guard passes.
    off: fraction of the turned product's extent (across the edge) that falls outside. along: 0..1 position on
    the edge. meta['clipped'] is the measured fraction; meta['other_edges_clipped'] lists any unintended cuts."""
    it = _items([item])[0]; bw, bh = box; height = height or 0.82 * bh
    s = height / it.im.height; im = _prep(it, s, tilt); pw, ph = im.size
    if edge == "right": x, y = bw - (1 - off) * pw, along * bh - ph / 2
    elif edge == "left": x, y = -off * pw, along * bh - ph / 2
    elif edge == "top": x, y = along * bw - pw / 2, -off * ph
    elif edge == "bottom": x, y = along * bw - pw / 2, bh - (1 - off) * ph
    else: raise ValueError("edge must be right, left, top or bottom")
    placed = [{"im": im, "x": x, "y": y, "name": it.name, "scale": s, "angle": tilt, "h": height}]
    c = _assemble(placed, light, shadows, "hero bleed", crop=(0, 0, bw, bh), meta={"edge": edge, "off": off})
    x0, y0, x1, y1 = c.items[0]["box"]                                       # product box in box coords
    ext = {"right": (x1 - bw) / pw, "left": -x0 / pw, "top": -y0 / ph, "bottom": (y1 - bh) / ph}
    c.meta["clipped"] = max(0.0, ext[edge])
    c.meta["other_edges_clipped"] = [e for e, v in ext.items() if e != edge and v > 0.002]
    return c


def grid(items, cols=None, height=300, gap=0.18, true_scale=False, light=None, shadows=("soft", "contact")):
    """A specimen grid: equal cells, each product on its row's baseline and centred in its cell, nothing touching.
    height: the cell's product height (tallest real product when true_scale); gap: fraction of the height."""
    items = _items(items); n = len(items); cols = cols or int(math.ceil(math.sqrt(n * 1.6)))
    if true_scale: scales, k = _true_scales(items, height)
    else: scales, k = [min(height / it.im.height, height * 0.8 / it.im.width) for it in items], None
    ims = [_prep(it, s) for it, s in zip(items, scales)]
    cw = max(im.width for im in ims) + gap * height; ch = height + gap * height
    placed = []
    for i, im in enumerate(ims):
        r, c = divmod(i, cols); base = r * ch + height
        placed.append({"im": im, "x": c * cw + (cw - im.width) / 2, "y": base - im.height, "name": items[i].name,
                       "scale": scales[i], "angle": 0.0, "h": im.height})
    return _assemble(placed, light, shadows, "specimen grid", meta={"cols": cols}, scale=k)


def scatter(items, seed=7, height=300, max_turn=18.0, overlap=0.0, area=None, gap=0.04, light=None,
            shadows=("soft", "contact"), tries=500):
    """A flat-lay: products thrown on a surface at seeded turns and spots. overlap: the largest share of the
    smaller product another may cover (0 = never touching, with a `gap` fraction of the height kept clear).
    The same seed always gives the same picture. Shadows are thrown half as far (products lie flat)."""
    items = _items(items); rng = np.random.default_rng(seed); light = (light or LIGHT).scaled(0.5)
    ims, scales, angs = [], [], []
    for it in items:
        s = height / max(it.im.height, it.im.width) * 1.0; a = float(rng.uniform(-max_turn, max_turn))
        ims.append(_prep(it, s, a)); scales.append(s); angs.append(a)
    if area is None:
        tot = sum(int((np.asarray(im.getchannel("A")) > ALPHA_MIN).sum()) for im in ims) * 2.6
        area = (int(math.sqrt(tot * 4 / 3)), int(math.sqrt(tot * 3 / 4)))
    AW, AH = area; g = max(1, int(gap * height)) if overlap <= 0 else 0
    masks = [np.asarray(im.getchannel("A")) > ALPHA_MIN for im in ims]
    dil = [np.asarray(im.getchannel("A").point(lambda v: 255 if v > ALPHA_MIN else 0).filter(ImageFilter.MaxFilter(2 * g + 1))) > 0
           if g else m for im, m in zip(ims, masks)]
    for _round in range(12):
        occ = np.full((AH, AW), -1, np.int32); pos = []; ok_all = True
        for i, (im, m, dm) in enumerate(zip(ims, masks, dil)):
            mh, mw = m.shape; ok = False
            for _ in range(tries):
                if AW - mw <= 0 or AH - mh <= 0: break
                x = int(rng.integers(0, AW - mw)); y = int(rng.integers(0, AH - mh))
                reg = occ[y:y + mh, x:x + mw]; hit = reg[dm]
                if overlap <= 0:
                    ok = not (hit >= 0).any()
                else:                                                         # exact pairwise share against every placed mask
                    ok = True
                    for j, (xj, yj) in enumerate(pos):
                        mj = masks[j]; ax0, ay0 = max(x, xj), max(y, yj)
                        ax1, ay1 = min(x + mw, xj + mj.shape[1]), min(y + mh, yj + mj.shape[0])
                        if ax1 <= ax0 or ay1 <= ay0: continue
                        inter = (m[ay0 - y:ay1 - y, ax0 - x:ax1 - x] & mj[ay0 - yj:ay1 - yj, ax0 - xj:ax1 - xj]).sum()
                        if inter / min(m.sum(), mj.sum()) > overlap: ok = False; break
                if ok: break
            if not ok: ok_all = False; break
            occ[y:y + mh, x:x + mw][m] = i; pos.append((x, y))
        if ok_all: break
        AW, AH = int(AW * 1.12), int(AH * 1.12)                                 # deterministic: grow and retry
    else:
        raise RuntimeError("scatter: could not place every product; raise overlap or area")
    placed = [{"im": im, "x": float(x), "y": float(y), "name": it.name, "scale": s, "angle": a, "h": height}
              for im, (x, y), it, s, a in zip(ims, pos, items, scales, angs)]
    return _assemble(placed, light, shadows, "scatter" if overlap <= 0 else "toss",
                     meta=_odd_note(len(items), {"seed": seed, "overlap": overlap, "area": (AW, AH)}))


def extend_canvas(photo, left=0, right=0, top=0, bottom=0, feather=None, sample=24, blur=None, grain=True, seed=1, trend=True):
    """Extend a photo's surface past its edge (a plate too tight for the layout): each new band repeats the edge's
    own colour profile (sampled `sample` px deep, smoothed along the edge by `blur`), with matched grain so it
    doesn't read as a flat strip, and a feathered seam that blends `feather` px of the original into the fill.
    trend: carry the edge's own light falloff on for a while and ease it flat (a flat fill next to a gradient
    shows a dark or light Mach band at the seam). Only for even surfaces (a table, a wall, a sky); objects at
    the edge are not continued. Returns a Composite
    (device 'extended plate'); meta['seams'] holds where each original edge now sits."""
    im = photo if isinstance(photo, Image.Image) else Image.open(photo)
    mode = "RGBA" if im.mode in ("RGBA", "LA") else "RGB"; arr = np.asarray(im.convert(mode), np.float32)
    rng = np.random.default_rng(seed); seams = {}
    for side, n in (("left", left), ("right", right), ("top", top), ("bottom", bottom)):
        if n <= 0: continue
        a = arr if side in ("left", "right") else arr.transpose(1, 0, 2)    # work on columns; top/bottom transpose
        if side in ("right", "bottom"): a = a[:, ::-1]
        H_ = a.shape[0]; s = min(sample, a.shape[1]); strip = a[:, :s]
        prof = strip.mean(1)                                                 # (H, C) the edge's colour profile
        r = blur if blur is not None else max(4.0, H_ / 40)
        k = np.exp(-0.5 * (np.arange(-int(3 * r), int(3 * r) + 1) / r) ** 2); k /= k.sum()
        pp = np.pad(prof, ((len(k) // 2, len(k) // 2), (0, 0)), mode="edge")
        prof = np.stack([np.convolve(pp[:, c], k, mode="valid") for c in range(prof.shape[1])], 1)
        fill = np.repeat(prof[:, None, :], n, 1)
        if trend and s >= 8:                                                  # slope per px going outward, eased flat over L px
            half = s // 2; slope = (strip[:, :half].mean(1) - strip[:, half:].mean(1)) / half
            pp2 = np.pad(slope, ((len(k) // 2, len(k) // 2), (0, 0)), mode="edge")
            slope = np.stack([np.convolve(pp2[:, c], k, mode="valid") for c in range(slope.shape[1])], 1)
            L = 3.0 * s; d = np.arange(n, 0, -1, dtype=np.float32)            # distance from the original edge (fill is outside-first)
            fill = fill + slope[:, None, :] * (L * (1 - np.exp(-d / L)))[None, :, None]
            if fill.shape[2] == 4: fill[..., 3] = np.repeat(prof[:, None, 3], n, 1)
        if grain:
            sd = (strip - strip.mean(1, keepdims=True)).std((0, 1))           # the edge's own texture amplitude
            noise = rng.normal(0, 1, fill.shape[:2])[..., None] * sd[None, None, :] * 0.9
            if fill.shape[2] == 4: noise[..., 3] = 0
            fill = fill + noise
        fz = int(feather if feather is not None else max(24, 0.04 * a.shape[1]))
        fz = min(fz, a.shape[1]); t = np.linspace(0, 1, fz)[None, :, None]; t = t * t * (3 - 2 * t)   # smoothstep
        a = a.copy(); a[:, :fz] = prof[:, None, :] * (1 - t) + a[:, :fz] * t
        a = np.concatenate([fill, a], 1)
        if side in ("right", "bottom"): a = a[:, ::-1]
        arr = a if side in ("left", "right") else a.transpose(1, 0, 2)
        seams[side] = n
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    W_, H_ = out.size
    seams = {k_: (v if k_ in ("left", "top") else (W_ - v if k_ == "right" else H_ - v)) for k_, v in seams.items()}
    rec = [{"name": "photo", "box": (left, top, W_ - right, H_ - bottom), "scale": 1.0, "angle": 0.0, "mask": None}]
    return Composite(out, "extended plate", rec, None, None, {"seams": seams, "feather": feather})


# ---------------------------------------------------------------- devices: nazar-story's no-repeat rule
DEVICES = {
    "hand of cards": "fan(): every variant overlapping on an arc",
    "front-back pair": "couple(): front leading, its back (or a partner) tucked behind",
    "overlap row": "row(overlap>0): a till-side lineup, each tucked under the next",
    "standing row": "row(overlap<=0): products standing apart on one baseline",
    "scale lineup": "row(true_scale=True): real sizes side by side",
    "cascade": "cascade(): products stepping back into depth",
    "stack": "stack(): a hand-made pile",
    "hero bleed": "bleed_hero(): one product huge, cut by the page edge",
    "specimen grid": "grid(): equal cells, a catalogue of the range",
    "scatter": "scatter(overlap=0): a flat-lay, nothing touching",
    "toss": "scatter(overlap>0): thrown loosely, some overlap",
    "extended plate": "extend_canvas(): a photo surface extended under the layout",
}


def _dev_names(x):
    if x is None: return []
    if isinstance(x, Composite): return [x.device]
    if isinstance(x, str): return [x]
    out = []
    for y in x: out += _dev_names(y)
    return out


def check_devices(pages, warn=True):
    """pages: [(page_no, device or Composite or a list of them), ...]. Returns a warning for every device used on
    more than one page (several of one device on the SAME page, e.g. a row of couples, is one use)."""
    seen, rep = {}, []
    for n, things in pages:
        for d in dict.fromkeys(s.strip().lower() for s in _dev_names(things) if s):
            if d in seen and seen[d] != n: rep.append(f"device '{d}' repeats: p{seen[d]} and p{n}")
            seen.setdefault(d, n)
    if warn:
        for r in rep: print("WARN", r)
    return rep


class DeviceLog:
    """Collect devices while building: log.add(page_no, composite_or_name, ...); log.report() lists repeats.
    log.add_deck(deck) also reads every d.page(..., device=...) a nazar-pitch Deck has recorded."""

    def __init__(self): self.pages = []

    def add(self, page, *things): self.pages.append((page, list(things))); return things[0] if len(things) == 1 else things

    def add_deck(self, deck): self.pages += [(n, d) for n, d in getattr(deck, "devices", [])]

    def report(self, warn=True): return check_devices(self.pages, warn)


def check_scale(comp, items, tol=0.03):
    """Scale truth: in a composite made with true_scale, every product's pixel height over its real height must
    agree within tol. Returns warnings (empty = truthful)."""
    out, ref = [], None
    for rec, it in zip(sorted(comp.items, key=lambda r: [i.name for i in items].index(r["name"])), items):
        m = rec["mask"]; rows = np.where(m.any(1))[0]; cols = np.where(m.any(0))[0]
        px = (rows[-1] - rows[0] + 1) / it.height_mm if it.height_mm else (cols[-1] - cols[0] + 1) / it.width_mm
        ref = ref or px
        if abs(px / ref - 1) > tol: out.append(f"{it.name}: {px:.3f} px/mm vs {ref:.3f} (misleading size)")
    return out


# ---------------------------------------------------------------- synthetic products (tests and the sheet; no brands)
def _hex(c): c = c.lstrip("#"); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def synthetic(kind="pouch", h=600, colour="#C8553D", accent="#F2E6D0", seed=0):
    """Draw a plain stand-in product (no brand): pouch (seal teeth + tear notches), bottle, can, carton, tube,
    jar, book. Flat colour, a label band and one soft highlight, drawn 2x and downsampled."""
    S = 2; H_ = h * S; col = _hex(colour); acc = _hex(accent)
    ratio = {"pouch": 0.62, "bottle": 0.34, "can": 0.52, "carton": 0.58, "tube": 0.30, "jar": 0.78, "book": 0.68, "sachet": 0.70, "spine": 4.6}[kind]
    W_ = int(H_ * ratio); im = Image.new("RGBA", (W_, H_), col + (0,)); d = ImageDraw.Draw(im)
    a = Image.new("L", (W_, H_), 0); da = ImageDraw.Draw(a)
    shade = tuple(max(0, int(v * 0.82)) for v in col); light_ = tuple(min(255, int(v * 1.12 + 18)) for v in col)
    if kind in ("pouch", "sachet"):
        t = max(6, H_ // 60); n = max(8, W_ // (t * 2))
        da.rectangle((0, t, W_ - 1, H_ - (t if kind == "sachet" else 1)), fill=255)
        for i in range(n):                                                    # seal teeth along the top (and bottom for a sachet)
            x0 = i * W_ / n; da.polygon([(x0, t), (x0 + W_ / n / 2, 0), (x0 + W_ / n, t)], fill=255)
            if kind == "sachet": da.polygon([(x0, H_ - t), (x0 + W_ / n / 2, H_ - 1), (x0 + W_ / n, H_ - t)], fill=255)
        ny, nd = int(H_ * 0.09), int(W_ * 0.05)                                # tear notches, both sides
        da.polygon([(0, ny - nd), (nd, ny), (0, ny + nd)], fill=0); da.polygon([(W_ - 1, ny - nd), (W_ - 1 - nd, ny), (W_ - 1, ny + nd)], fill=0)
        d.rectangle((0, 0, W_, H_), fill=col); d.rectangle((0, int(H_ * 0.16), W_, int(H_ * 0.17)), fill=shade)
        d.rectangle((int(W_ * 0.1), int(H_ * 0.45), int(W_ * 0.9), int(H_ * 0.72)), fill=acc)
        d.rectangle((int(W_ * 0.16), int(H_ * 0.52), int(W_ * 0.7), int(H_ * 0.56)), fill=col)
        if kind == "pouch": d.rectangle((0, int(H_ * 0.9), W_, H_), fill=shade)   # the gusset fold
    elif kind == "bottle":
        nw = int(W_ * 0.34); cx = W_ // 2
        da.rounded_rectangle((cx - nw // 2, 0, cx + nw // 2, int(H_ * 0.11)), radius=nw // 6, fill=255)           # cap
        da.rectangle((cx - nw // 2 + 4, int(H_ * 0.1), cx + nw // 2 - 4, int(H_ * 0.22)), fill=255)                 # neck
        da.polygon([(cx - nw // 2 + 4, int(H_ * 0.22)), (cx + nw // 2 - 4, int(H_ * 0.22)), (W_ - 1, int(H_ * 0.36)), (0, int(H_ * 0.36))], fill=255)
        da.rounded_rectangle((0, int(H_ * 0.34), W_ - 1, H_ - 1), radius=W_ // 8, fill=255)
        d.rectangle((0, 0, W_, H_), fill=col); d.rectangle((0, 0, W_, int(H_ * 0.11)), fill=shade)
        d.rectangle((0, int(H_ * 0.5), W_, int(H_ * 0.78)), fill=acc)
        d.rectangle((int(W_ * 0.14), int(H_ * 0.36), int(W_ * 0.22), int(H_ * 0.95)), fill=light_)
    elif kind == "can":
        r = int(H_ * 0.03)
        da.rounded_rectangle((0, r, W_ - 1, H_ - r), radius=r * 2, fill=255); da.rectangle((int(W_ * 0.06), 0, int(W_ * 0.94), H_ - 1), fill=255)
        d.rectangle((0, 0, W_, H_), fill=col); d.rectangle((0, 0, W_, int(H_ * 0.06)), fill=(190, 190, 186)); d.rectangle((0, int(H_ * 0.95), W_, H_), fill=(170, 170, 166))
        d.rectangle((0, int(H_ * 0.3), W_, int(H_ * 0.62)), fill=acc); d.rectangle((int(W_ * 0.12), int(H_ * 0.06), int(W_ * 0.2), int(H_ * 0.95)), fill=light_)
    elif kind == "carton":
        da.rectangle((0, int(H_ * 0.08), W_ - 1, H_ - 1), fill=255); da.polygon([(0, int(H_ * 0.08)), (W_ * 0.5, 0), (W_ - 1, int(H_ * 0.08))], fill=255)
        d.rectangle((0, 0, W_, H_), fill=col); d.line((0, int(H_ * 0.08), W_, int(H_ * 0.08)), fill=shade, width=S * 3)
        d.rectangle((0, int(H_ * 0.58), W_, int(H_ * 0.84)), fill=acc)
    elif kind == "tube":
        t = max(5, H_ // 70); n = max(6, W_ // (t * 2))
        da.rectangle((0, t, W_ - 1, int(H_ * 0.86)), fill=255)
        for i in range(n): x0 = i * W_ / n; da.polygon([(x0, t), (x0 + W_ / n / 2, 0), (x0 + W_ / n, t)], fill=255)  # crimp
        cw = int(W_ * 0.5); da.rounded_rectangle(((W_ - cw) // 2, int(H_ * 0.85), (W_ + cw) // 2, H_ - 1), radius=cw // 8, fill=255)
        d.rectangle((0, 0, W_, H_), fill=col); d.rectangle((0, int(H_ * 0.85), W_, H_), fill=(236, 234, 228)); d.rectangle((0, int(H_ * 0.3), W_, int(H_ * 0.5)), fill=acc)
    elif kind == "jar":
        lid = int(H_ * 0.16)
        da.rounded_rectangle((int(W_ * 0.06), 0, int(W_ * 0.94), lid), radius=lid // 5, fill=255); da.rounded_rectangle((0, lid - 4, W_ - 1, H_ - 1), radius=W_ // 10, fill=255)
        d.rectangle((0, 0, W_, H_), fill=col); d.rectangle((0, 0, W_, lid), fill=shade); d.rectangle((0, int(H_ * 0.38), W_, int(H_ * 0.74)), fill=acc)
        d.rectangle((int(W_ * 0.1), lid + 10, int(W_ * 0.16), int(H_ * 0.92)), fill=light_)
    elif kind == "spine":                                                    # a book or box lying flat, seen edge-on
        da.rounded_rectangle((0, 0, W_ - 1, H_ - 1), radius=max(2, H_ // 14), fill=255)
        d.rectangle((0, 0, W_, H_), fill=col); d.rectangle((int(W_ * 0.06), 0, int(W_ * 0.1), H_), fill=acc); d.rectangle((int(W_ * 0.9), 0, int(W_ * 0.94), H_), fill=acc)
        d.rectangle((int(W_ * 0.2), int(H_ * 0.38), int(W_ * 0.62), int(H_ * 0.62)), fill=acc)
    elif kind == "book":
        da.rectangle((0, 0, W_ - 1, H_ - 1), fill=255)
        d.rectangle((0, 0, W_, H_), fill=col); d.rectangle((0, 0, int(W_ * 0.07), H_), fill=shade)
        d.rectangle((int(W_ * 0.18), int(H_ * 0.18), int(W_ * 0.86), int(H_ * 0.22)), fill=acc); d.rectangle((int(W_ * 0.18), int(H_ * 0.26), int(W_ * 0.6), int(H_ * 0.28)), fill=acc)
    im.putalpha(a)
    return im.resize((W_ // S, H_ // S), Image.LANCZOS)


PALETTE = ["#C8553D", "#2E6F6A", "#D9A441", "#3F4E8C", "#8C3F6E", "#6E8C3F", "#B5652B"]


# ---------------------------------------------------------------- contact sheet
def _font(sz):
    try: return ImageFont.truetype(os.path.join(FONTS, "SpaceMono-Regular.ttf"), sz)
    except OSError: return ImageFont.load_default()


def _fit_into(cell, im, pad, align="center"):
    w, h = cell.size; k = min((w - 2 * pad) / im.width, (h - 2 * pad - 40) / im.height, 1.0)
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    x = (w - im.width) // 2 if align == "center" else w - im.width
    cell.alpha_composite(im, (x, pad + (h - 2 * pad - 40 - im.height) // 2 if align == "center" else 0)); return cell


def sheet(path, comps, title="composers", cols=3, cw=620, ch=520, paper="#EEE8DD", ink=(30, 28, 25)):
    """Lay composites out on one sheet, each in its own cell with its device name. A 'hero bleed' cell is placed
    flush right (the box is the cell), the way it sits on a page."""
    rows = (len(comps) + cols - 1) // cols; f = _font(20); g = 14
    sh = Image.new("RGBA", (cols * (cw + g) + g, rows * (ch + g) + g + 60), (34, 32, 30, 255))
    ImageDraw.Draw(sh).text((g, 18), title, fill=(230, 226, 218), font=_font(24))
    for i, (label, c) in enumerate(comps):
        cell = Image.new("RGBA", (cw, ch), paper)
        if c.device == "hero bleed":
            im = c.image; k = min(ch / im.height, cw / im.width); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
            cell.alpha_composite(im, (cw - im.width, 0))
        else:
            _fit_into(cell, c.image if c.image.mode == "RGBA" else c.image.convert("RGBA"), 28)
            if c.device == "extended plate" and "left" in c.meta.get("seams", {}):     # mark where the original edge was
                k = min((cw - 56) / c.image.width, (ch - 96) / c.image.height, 1.0); x0 = (cw - c.image.width * k) / 2
                y0 = 28 + (ch - 96 - c.image.height * k) / 2; xs = x0 + c.meta["seams"]["left"] * k; dr = ImageDraw.Draw(cell)
                dr.polygon([(xs - 7, y0 - 14), (xs + 7, y0 - 14), (xs, y0 - 3)], fill=ink)
                dr.text((xs + 12, y0 - 24), "original edge", fill=ink, font=_font(15))
        ImageDraw.Draw(cell).text((18, ch - 34), label, fill=ink, font=f)
        sh.alpha_composite(cell, (g + (i % cols) * (cw + g), 60 + g + (i // cols) * (ch + g)))
    sh.convert("RGB").save(path, quality=90); return path


def demo_set():
    """Every composer on synthetic products; returns [(label, Composite)]."""
    P = lambda k, i, h=600: Item(synthetic(k, h, PALETTE[i % len(PALETTE)]), name=f"{k}{i}")
    pouches = [P("pouch", i) for i in range(5)]
    backs = [Item(synthetic("pouch", 600, "#EFE6D6", PALETTE[i]), name=f"back{i}") for i in range(5)]
    plate = Image.new("RGB", (640, 480), (214, 190, 150)); pa = np.asarray(plate, np.float32)
    pa += np.random.default_rng(2).normal(0, 6, pa.shape) + np.linspace(-12, 12, 640)[None, :, None]
    plate = Image.fromarray(np.clip(pa, 0, 255).astype(np.uint8)); ImageDraw.Draw(plate).ellipse((380, 140, 560, 320), fill=(240, 236, 228))
    sizes = [("sachet", 70, 0), ("pouch", 160, 1), ("pouch", 240, 2)]
    return [
        ("fan: hand of cards", fan(backs, 500)),
        ("couple: front-back pair", couple(pouches[0], backs[0], 520)),
        ("row: overlap row (till-side)", row([P("sachet", i, 300) for i in range(5)], 300, overlap=0.22)),
        ("row: scale lineup 70/160/240 mm", row([Item(synthetic(k, 600, PALETTE[c]), f"{k}{c}", height_mm=mm) for k, mm, c in sizes], 420,
                                               overlap=-0.12, true_scale=True)),
        ("row: standing row (mixed)", row([P("bottle", 1), P("can", 2), P("jar", 3), P("tube", 4), P("carton", 0)], 380, overlap=-0.16)),
        ("cascade", cascade([P("bottle", i) for i in range(3)], 520)),
        ("stack: a pile of five", stack([Item(synthetic("spine", h_, PALETTE[i]), f"spine{i}") for i, h_ in enumerate([90, 70, 110, 80, 60])], 440)),
        ("bleed_hero: right edge, 30% off", bleed_hero(pouches[3], (560, 600), "right", 0.30, -9, 560)),
        ("grid: specimen grid", grid([P("can", i, 300) for i in range(6)], cols=3, height=220)),
        ("scatter: flat-lay, seeded", scatter([P(k, i, 300) for i, k in enumerate(["pouch", "sachet", "tube", "jar", "book"])], seed=11, height=220)),
        ("couple + cast shadow", couple(P("bottle", 5), P("bottle", 6), 520, overlap=0.35, shadows=("cast", "soft", "contact"))),
        ("extend_canvas: +200 px left", extend_canvas(plate, left=200, feather=60)),
    ]


# ---------------------------------------------------------------- self-test
def _outside(comp):
    """Shadow alpha outside every product mask (what the eye sees as shadow)."""
    m = np.zeros(comp.shadow.shape, bool)
    for r in comp.items:
        x0, y0, x1, y1 = r["box"]; sx0, sy0 = max(0, x0), max(0, y0); sx1, sy1 = min(m.shape[1], x1), min(m.shape[0], y1)
        if sx1 > sx0 and sy1 > sy0: m[sy0:sy1, sx0:sx1] |= r["mask"][sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0]
    return np.where(m, 0, comp.shadow), m


def _col_overlap(a, b):
    """Shared horizontal extent of two placed masks / the narrower width (from the pixels)."""
    def ext(r):
        cols = np.where(r["mask"].any(0))[0]; return r["box"][0] + cols[0], r["box"][0] + cols[-1] + 1
    (a0, a1), (b0, b1) = ext(a), ext(b)
    return max(0, min(a1, b1) - max(a0, b0)) / min(a1 - a0, b1 - b0)


def selftest(verbose=True):
    fails = []

    def check(name, ok, info=""):
        if verbose: print(("PASS " if ok else "FAIL ") + name, info)
        if not ok: fails.append(name)

    P = lambda k, i, h=400: Item(synthetic(k, h, PALETTE[i % len(PALETTE)]), name=f"{k}{i}")
    comps = {
        "fan": fan([P("pouch", i) for i in range(5)], 300),
        "couple": couple(P("pouch", 0), P("pouch", 1), 300, overlap=0.55),
        "row": row([P("can", i) for i in range(4)], 260, overlap=0.25),
        "cascade": cascade([P("bottle", i) for i in range(3)], 300),
        "stack": stack([P("book", i) for i in range(3)], 260),
        "grid": grid([P("jar", i) for i in range(6)], cols=3, height=160),
        "scatter": scatter([P(k, i) for i, k in enumerate(["pouch", "tube", "jar", "book", "can"])], seed=5, height=160),
    }
    # 1 single RGBA, tight bbox
    for k, c in comps.items():
        a = np.asarray(c.image.getchannel("A")) > 2
        tight = a[0].any() and a[-1].any() and a[:, 0].any() and a[:, -1].any()
        check(f"{k}: one RGBA with a tight bbox", c.image.mode == "RGBA" and tight, c.image.size)
    # 2 nothing clipped (items wholly inside, full pixel count kept)
    for k, c in comps.items():
        W_, H_ = c.image.size
        inside = all(r["box"][0] >= 0 and r["box"][1] >= 0 and r["box"][2] <= W_ and r["box"][3] <= H_ for r in c.items)
        check(f"{k}: no product clipped", inside)
    # 3 overlap fractions
    cp = comps["couple"]; ov = _col_overlap(cp.items[0], cp.items[1])
    check("couple: overlap within 0.03 of 0.55", abs(ov - 0.55) <= 0.03, f"{ov:.3f}")
    rw = comps["row"]; ovs = [_col_overlap(rw.items[i], rw.items[i + 1]) for i in range(len(rw.items) - 1)]
    check("row: every overlap within 0.03 of 0.25", all(abs(o - 0.25) <= 0.03 for o in ovs), [f"{o:.3f}" for o in ovs])
    gp = row([P("can", i) for i in range(3)], 200, overlap=-0.2)
    check("row: a negative overlap leaves a gap", all(_col_overlap(gp.items[i], gp.items[i + 1]) == 0 for i in range(2)))
    # 4 true scale
    its = [Item(synthetic("sachet", 500, PALETTE[0]), "s30", height_mm=95), Item(synthetic("pouch", 300, PALETTE[1]), "p250", height_mm=260),
           Item(synthetic("pouch", 700, PALETTE[2]), "p100", height_mm=190)]
    ts = row(its, 400, overlap=-0.1, true_scale=True)
    hs = {r["name"]: np.ptp(np.where(r["mask"].any(1))[0]) + 1 for r in ts.items}
    r1, r2 = hs["s30"] / hs["p250"], hs["p100"] / hs["p250"]
    check("true scale: 95 mm / 260 mm ratio within 2%", abs(r1 / (95 / 260) - 1) < 0.02, f"{r1:.4f} vs {95 / 260:.4f}")
    check("true scale: 190 mm / 260 mm ratio within 2%", abs(r2 / (190 / 260) - 1) < 0.02, f"{r2:.4f} vs {190 / 260:.4f}")
    check("true scale: check_scale finds no misleading size", not check_scale(ts, its), check_scale(ts, its))
    check("true scale: the tallest real product is `height` px", abs(hs["p250"] - 400) <= 2, hs["p250"])
    try: row([P("can", 0), P("can", 1)], true_scale=True); check("true scale: missing mm raises", False)
    except ValueError: check("true scale: missing mm raises", True)
    check("true scale: device is 'scale lineup' and px/mm recorded", ts.device == "scale lineup" and abs(ts.scale - 400 / 260) < 1e-6)
    # 5 contact shadow below each product
    for k in ("row", "couple", "grid", "fan"):
        c = comps[k]; vis, m = _outside(c); ok = True
        for r in c.items:
            x0, y0, x1, y1 = r["box"]; rows = np.where(r["mask"].any(1))[0]; yb = y0 + rows[-1]
            band = vis[yb + 1:yb + 4, x0:x1]
            ok &= band.size > 0 and band.max() > 0.25
        check(f"{k}: a dark contact shadow sits under every product", ok)
    # 6 silhouette notches survive in the contact shadow (tested on the shadow layer itself)
    pouch = synthetic("pouch", 400); al = np.asarray(pouch.getchannel("A"), np.float32) / 255
    a, ox, oy = shadow_layer(al, LIGHT, 400, "contact"); H_, W_ = al.shape
    ny, nd = int(400 * 2 * 0.09) // 2, int(W_ * 2 * 0.05) // 2
    cdx, cdy = LIGHT.offset(400, LIGHT.contact_lift)                       # array index of the shadow of product point p = p + d - o
    yy = int(round(ny + cdy - oy)); xn = int(round(nd // 3 + cdx - ox)); xb = int(round(W_ // 2 + cdx - ox))
    check("contact shadow keeps the tear notch (notch < 45% of body)", a[yy, xn] < 0.45 * a[yy, xb], f"{a[yy, xn]:.3f} vs {a[yy, xb]:.3f}")
    ty = int(round(3 + cdy - oy)); prof = a[ty, int(round(cdx - ox)):int(round(W_ + cdx - ox))]
    check("contact shadow keeps the seal teeth (strong ripple along the top)", prof.std() > 0.08 * prof.max() and prof.min() < 0.6 * prof.max(),
          f"std {prof.std():.3f} max {prof.max():.3f}")
    s_soft, *_ = shadow_layer(al, LIGHT, 400, "soft")
    check("soft shadow is wider and softer than contact", s_soft.shape[0] > a.shape[0])
    # 7 one light direction: every shadow offset and every measured shadow centroid share a sign
    offs = [o for c in comps.values() for o in c.meta["shadow_offsets"]]
    check("light: every shadow offset shares one sign (x and y)", len({np.sign(o[0]) for o in offs}) == 1 and len({np.sign(o[1]) for o in offs}) == 1)
    signs = set()
    for k in ("couple", "grid", "scatter", "row"):
        vis, m = _outside(comps[k]); ys, xs = np.nonzero(vis > 0.05); my, mx = np.nonzero(m)
        signs.add((np.sign(xs.mean() - mx.mean()), np.sign(ys.mean() - my.mean())))
    check("light: measured shadow centroids fall the same way in every composer", len(signs) == 1, signs)
    left = Light(azimuth=40); cl = couple(P("pouch", 0), P("pouch", 1), 300, light=left)
    check("light: a light from the right throws shadows left", all(o[0] < 0 for o in cl.meta["shadow_offsets"]))
    # 8 bleed hero clips only the asked edge by the asked fraction
    for edge, off in (("right", 0.30), ("left", 0.2), ("bottom", 0.25)):
        b = bleed_hero(P("pouch", 2), (500, 560), edge, off, -8, 380)
        check(f"bleed_hero {edge}: clipped {off:.2f} +/- 0.02, other edges whole, exact box",
              abs(b.meta["clipped"] - off) <= 0.02 and not b.meta["other_edges_clipped"] and b.image.size == (500, 560),
              f"{b.meta['clipped']:.3f} {b.meta['other_edges_clipped']}")
    # 9 scatter: seeded and non-overlapping
    sa = scatter([P(k, i) for i, k in enumerate(["pouch", "tube", "jar", "book", "can"])], seed=5, height=160)
    check("scatter: same seed gives identical pixels", np.array_equal(np.asarray(sa.image), np.asarray(comps["scatter"].image)))
    sb = scatter([P(k, i) for i, k in enumerate(["pouch", "tube", "jar", "book", "can"])], seed=6, height=160)
    check("scatter: another seed gives another picture", sa.image.size != sb.image.size or not np.array_equal(np.asarray(sa.image), np.asarray(sb.image)))
    occ = np.zeros(sa.shadow.shape, np.int32)
    for r in sa.items:
        x0, y0, x1, y1 = r["box"]; occ[y0:y1, x0:x1] += r["mask"]
    check("scatter(overlap=0): no two products touch", occ.max() == 1)
    sc = scatter([P("book", i) for i in range(5)], seed=2, height=160, overlap=0.3, area=(380, 300))
    ok = True
    for i in range(5):
        for j in range(i + 1, 5):
            A, B = sc.items[i], sc.items[j]; m1 = np.zeros(sc.shadow.shape, bool); m2 = m1.copy()
            m1[A["box"][1]:A["box"][3], A["box"][0]:A["box"][2]] = A["mask"]; m2[B["box"][1]:B["box"][3], B["box"][0]:B["box"][2]] = B["mask"]
            ok &= (m1 & m2).sum() / min(m1.sum(), m2.sum()) <= 0.3 + 1e-6
    check("scatter(overlap=0.3): no pair shares more than 30%", ok and sc.device == "toss")
    # 10 extend_canvas: size, untouched interior, smooth seam
    ph = Image.new("RGB", (300, 200), (200, 170, 120)); pa = np.asarray(ph, np.float32) + np.linspace(-20, 20, 200)[:, None, None]
    ph = Image.fromarray(np.clip(pa + np.random.default_rng(0).normal(0, 4, pa.shape), 0, 255).astype(np.uint8))
    ex = extend_canvas(ph, left=120, right=40, feather=40, seed=3); e = np.asarray(ex.image, np.float32)
    check("extend_canvas: size grows by the asked amounts", ex.image.size == (460, 200))
    check("extend_canvas: the photo's interior is untouched", np.array_equal(e[:, 120 + 41:120 + 300 - 41], np.asarray(ph, np.float32)[:, 41:259]))
    cm = e.mean(0).mean(1); jump = np.abs(np.diff(cm[60:220])).max()
    check("extend_canvas: no visible step across the seam", jump < 3.0, f"max column jump {jump:.2f}")
    check("extend_canvas: fill keeps the edge's vertical gradient", abs((e[:20, :100].mean() - e[-20:, :100].mean()) - (pa[:20, :10].mean() - pa[-20:, :10].mean())) < 6)
    # 11 devices
    log = DeviceLog(); log.add(3, comps["fan"]); log.add(4, comps["couple"], comps["couple"]); log.add(5, "split line/image")
    check("devices: no warning without a repeat", not log.report(warn=False))
    log.add(7, fan([P("pouch", 0), P("pouch", 1), P("pouch", 2)], 200))
    rep = log.report(warn=False)
    check("devices: a reused device warns (p3 and p7)", len(rep) == 1 and "hand of cards" in rep[0] and "p3" in rep[0] and "p7" in rep[0], rep)
    check("devices: every composer tags a known device", all(c.device in DEVICES for c in list(comps.values()) + [ts, ex, b, sc]))
    if verbose: print(f"\n{'ALL PASS' if not fails else str(len(fails)) + ' FAIL'}")
    return fails


# ---------------------------------------------------------------- CLI
def _demo(folder, out):
    """Optional demo on real cut-outs: up to 5 '*front*.png' and their '*back*.png' twins from a folder."""
    fs = sorted(f for f in os.listdir(folder) if f.endswith(".png") and "front" in f)[:5]
    if not fs: print("no *front*.png in", folder, "- demo skipped"); return None
    fr = [Item(os.path.join(folder, f)) for f in fs]
    bk = [Item(os.path.join(folder, f.replace("front", "back"))) for f in fs if os.path.exists(os.path.join(folder, f.replace("front", "back")))]
    comps = [("DEMO fan of fronts", fan(fr, 520)), ("DEMO bleed hero", bleed_hero(fr[0], (560, 600), "right", 0.3, -9, 560)),
             ("DEMO grid", grid(fr, cols=len(fr), height=260)), ("DEMO scatter", scatter(fr, seed=4, height=240))]
    if bk: comps.insert(1, ("DEMO couple", couple(fr[0], bk[0], 520))); comps.insert(2, ("DEMO fan of backs", fan(bk, 520)))
    return sheet(out, comps, "composers DEMO on real pack renders (demo only, not a deliverable)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    sp = ap.add_subparsers(dest="cmd")
    s1 = sp.add_parser("sheet"); s1.add_argument("out", nargs="?", default=os.path.join(HERE, "..", "examples", "composers_sheet.jpg"))
    s2 = sp.add_parser("demo"); s2.add_argument("folder"); s2.add_argument("out", nargs="?", default="composers_demo.jpg")
    s3 = sp.add_parser("compose"); s3.add_argument("device", choices=["fan", "couple", "row", "cascade", "stack", "grid", "scatter", "bleed"])
    s3.add_argument("pngs", nargs="+"); s3.add_argument("-o", "--out", required=True); s3.add_argument("--height", type=int, default=600)
    s3.add_argument("--overlap", type=float, default=None); s3.add_argument("--mm", default=None, help="real heights in mm, comma separated (true scale)")
    s3.add_argument("--seed", type=int, default=7); s3.add_argument("--edge", default="right"); s3.add_argument("--off", type=float, default=0.3)
    s3.add_argument("--box", default="1000x1080")
    s4 = sp.add_parser("extend"); s4.add_argument("photo"); s4.add_argument("-o", "--out", required=True)
    for k in ("left", "right", "top", "bottom"): s4.add_argument("--" + k, type=int, default=0)
    s4.add_argument("--feather", type=int, default=None)
    a = ap.parse_args(argv)
    if a.selftest: sys.exit(1 if selftest() else 0)
    if a.cmd == "sheet":
        p = sheet(os.path.normpath(a.out), demo_set(), "nazar-story composers: every device on synthetic stand-in products (one light, top-left)")
        print(p); return
    if a.cmd == "demo":
        if not os.path.isdir(a.folder): print("demo folder not found - skipped:", a.folder); return
        print(_demo(a.folder, a.out)); return
    if a.cmd == "compose":
        mm = [float(v) for v in a.mm.split(",")] if a.mm else [None] * len(a.pngs)
        its = [Item(p, height_mm=m) for p, m in zip(a.pngs, mm)]; ts = a.mm is not None
        f = {"fan": lambda: fan(its, a.height), "couple": lambda: couple(its[0], its[1], a.height, **({"overlap": a.overlap} if a.overlap is not None else {})),
             "row": lambda: row(its, a.height, a.overlap or 0.0, true_scale=ts), "cascade": lambda: cascade(its, a.height),
             "stack": lambda: stack(its, a.height, seed=a.seed, true_scale=ts), "grid": lambda: grid(its, height=a.height, true_scale=ts),
             "scatter": lambda: scatter(its, a.seed, a.height, overlap=a.overlap or 0.0),
             "bleed": lambda: bleed_hero(its[0], tuple(int(v) for v in a.box.split("x")), a.edge, a.off, height=a.height)}[a.device]
        c = f(); print(c.save(a.out), c.device, c.image.size, *c.meta.get("notes", [])); return
    if a.cmd == "extend":
        c = extend_canvas(a.photo, a.left, a.right, a.top, a.bottom, a.feather); print(c.save(a.out), c.image.size); return
    ap.print_help()


if __name__ == "__main__":
    main()
