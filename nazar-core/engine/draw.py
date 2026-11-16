#!/usr/bin/env python3
"""
nazar-core/engine/draw.py: the Pillow helpers every brand-slide job re-writes, tested once (see test_draw.py).

  from draw import Canvas, font, ink_text, wrap, card, bubble, ticket, star, wobble_line, ring, arrow, strike, pill, dashed, cutout,
                  alert_dialog, line_chart, tilt_paste
  cv = Canvas(1080, 1350, "#F4EFE6")                 # drawn at 2x, saved at 1x: smooth edges
  f = font("Anton-Regular.ttf", 96)                  # pass a size in 1x pixels
  ink_text(cv, 80, 120, "Headline", f, "#111")       # the INK's left edge sits at x=80, not the glyph box
  cv.save("slide.png")

All coordinates are in 1x pixels. Colours are anything PIL accepts. Every helper draws onto the Canvas and returns the 1x
box (x0, y0, x1, y1) it filled, so the next element can be placed from it. Generic: no brand names, you pass the brand's
fonts and colours. For the client's own logo or mascot use cutout(), which calls place_asset.py (never redraw them).
"""
import math, os, random, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")


class Canvas:
    """A 2x-supersampled canvas: draw in 1x coordinates through the helpers, save() downsamples to 1x."""
    def __init__(self, w, h, bg="white"):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w * S, h * S), bg)
        self.d = ImageDraw.Draw(self.img)

    def refresh(self):
        self.d = ImageDraw.Draw(self.img)

    def save(self, path, **kw):
        self.img.resize((self.w, self.h), Image.LANCZOS).save(path, **kw)

    def result(self):
        return self.img.resize((self.w, self.h), Image.LANCZOS)


def _b(box):
    return [round(v * S) for v in box]


def _o(box):
    return tuple(round(v / S) for v in box)


def font(path, size):
    """Load a font at a 1x pixel size (a bare file name is looked up in engine/fonts)."""
    if not os.path.exists(path):
        path = os.path.join(FONTS, path)
    return ImageFont.truetype(path, round(size * S))


def ink_box(text, f):
    """Ink bounding box of text in 1x px relative to the draw origin (left edge is the ink, not the glyph box)."""
    return tuple(v / S for v in f.getbbox(text, anchor="ls"))


def ink_text(cv, x, y, text, f, fill="black", anchor="top"):
    """Draw text so its ink left edge is exactly x; y is the top of the ink (anchor='top') or the baseline ('base')."""
    l, t, r, b = f.getbbox(text, anchor="ls")
    ox = x * S - l
    oy = (y * S - t) if anchor == "top" else y * S
    cv.d.text((ox, oy), text, font=f, fill=fill, anchor="ls")
    return _o((l + ox, t + oy, r + ox, b + oy))


def wrap(text, f, width):
    """Split text into lines that each fit width (1x px), breaking at spaces; returns a list of strings."""
    lines, cur = [], ""
    for wd in text.split():
        t = (cur + " " + wd).strip()
        if cur and f.getlength(t) / S > width:
            lines.append(cur); cur = wd
        else:
            cur = t
    return lines + ([cur] if cur else [])


def ink_para(cv, x, y, text, f, fill, width, leading=1.2):
    """Wrapped paragraph with ink-aligned left edges; returns the box it covers."""
    size = f.size / S
    top, boxes = y, []
    for i, ln in enumerate(wrap(text, f, width)):
        boxes.append(ink_text(cv, x, y + i * size * leading, ln, f, fill))
    return (min(b[0] for b in boxes), boxes[0][1], max(b[2] for b in boxes), boxes[-1][3]) if boxes else (x, y, x, y)


def _shadow(cv, box, r, blur, dy, alpha, color=(0, 0, 0)):
    x0, y0, x1, y1 = _b(box)
    pad = blur * S * 3
    lay = Image.new("L", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), 0)
    ImageDraw.Draw(lay).rounded_rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0), r * S, fill=int(255 * alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(blur * S))
    cv.img.paste(Image.new("RGB", lay.size, color), (x0 - pad, y0 - pad + dy * S), lay)
    cv.refresh()


def card(cv, box, r=28, fill="white", outline=None, width=0, shadow=True, blur=14, dy=10, alpha=0.18):
    """Rounded card with an optional soft shadow."""
    if shadow:
        _shadow(cv, box, r, blur, dy, alpha)
    cv.d.rounded_rectangle(_b(box), r * S, fill=fill, outline=outline, width=round(width * S))
    return tuple(box)


def bubble(cv, box, tail="bl", r=34, fill="white", outline=None, width=0, shadow=True, tail_size=36):
    """Chat bubble: rounded box with a tail at its bottom-left ('bl') or bottom-right ('br')."""
    if shadow:
        _shadow(cv, box, r, 10, 8, 0.15)
    x0, y0, x1, y1 = box
    cv.d.rounded_rectangle(_b(box), r * S, fill=fill, outline=outline, width=round(width * S))
    tx = x0 + r if tail == "bl" else x1 - r
    sg = 1 if tail == "bl" else -1
    pts = [(tx, y1 - 4), (tx + sg * tail_size, y1 - 4), (tx, y1 + tail_size * 0.8)]
    cv.d.polygon([(px * S, py * S) for px, py in pts], fill=fill)
    return (x0, y0, x1, y1 + tail_size * 0.8)


def dashed(cv, p0, p1, color="black", width=3, dash=14, gap=10):
    """Dashed straight rule from p0 to p1."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / L, (y1 - y0) / L
    t = 0
    while t < L:
        e = min(t + dash, L)
        cv.d.line([((x0 + ux * t) * S, (y0 + uy * t) * S), ((x0 + ux * e) * S, (y0 + uy * e) * S)], fill=color,
                  width=round(width * S))
        t += dash + gap
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def ticket(cv, box, notch=22, fill="white", outline=None, width=3, perf=True, shadow=True, perf_color="#888", ground=None):
    """Ticket: rectangle with a half-circle notch cut in both sides and a dashed perforation 28% from the left."""
    x0, y0, x1, y1 = box
    if ground is None:                                    # the ground colour, sampled above the box before any shadow
        ground = cv.img.getpixel((round(x0 * S), max(0, round((y0 - 6) * S))))
    if shadow:
        _shadow(cv, box, 10, 12, 8, 0.16)
    cv.d.rounded_rectangle(_b(box), 10 * S, fill=fill, outline=outline, width=round(width * S))
    ym = (y0 + y1) / 2
    for cx, a0, a1 in ((x0, -90, 90), (x1, 90, 270)):     # notches show the ground behind, edged by one clean arc
        cv.d.ellipse(_b((cx - notch - width, ym - notch - width, cx + notch + width, ym + notch + width)), fill=ground)
        if outline:
            cv.d.arc(_b((cx - notch, ym - notch, cx + notch, ym + notch)), a0, a1, fill=outline, width=round(width * S))
    if perf:
        px = x0 + (x1 - x0) * 0.28
        dashed(cv, (px, y0 + 12), (px, y1 - 12), perf_color, 3, 10, 8)
    return tuple(box)


def star(cv, cx, cy, r, color="black", width=6, fill=None, rot=0, points=5, inner=0.45):
    """Star outline (or filled when fill is given), rot in degrees."""
    pts = []
    for i in range(points * 2):
        rad = r if i % 2 == 0 else r * inner
        a = math.radians(rot) + i * math.pi / points
        pts.append((cx + rad * math.sin(a), cy - rad * math.cos(a)))
    P = [(x * S, y * S) for x, y in pts]
    if fill:
        cv.d.polygon(P, fill=fill)
    if width:
        cv.d.line(P + [P[0], P[1]], fill=color, width=round(width * S), joint="curve")
        for x, y in P:
            rr = width * S / 2
            cv.d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=color)
    return (cx - r, cy - r, cx + r, cy + r)


def _stroke(cv, pts, color, width):
    P = [(x * S, y * S) for x, y in pts]
    cv.d.line(P, fill=color, width=round(width * S), joint="curve")
    rr = width * S / 2
    for x, y in (P[0], P[-1]):
        cv.d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=color)


def wobble_line(cv, p0, p1, color="black", width=5, amp=3.0, seed=1):
    """Hand-drawn line: a straight line with a slow, small wobble across it (amp in px)."""
    rnd = random.Random(seed)
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0); n = max(6, int(L / 12))
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    ph, f2 = rnd.uniform(0, 6.28), rnd.uniform(1.2, 2.2)
    pts = []
    for i in range(n + 1):
        t = i / n; o = amp * math.sin(t * math.pi * f2 + ph) * math.sin(t * math.pi) + rnd.uniform(-amp, amp) * 0.15
        pts.append((x0 + (x1 - x0) * t + nx * o, y0 + (y1 - y0) * t + ny * o))
    _stroke(cv, pts, color, width)
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def ring(cv, box, color="black", width=5, pad=14, seed=2):
    """Hand-drawn loop around a word (box = the word's ink box); it overshoots and does not close."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 * 1.08, (y1 - y0) / 2 * 1.15
    a0 = rnd.uniform(-2.2, -1.6); pts = []
    for i in range(0, 118):
        a = a0 + i / 100 * 2 * math.pi
        k = 1 + 0.035 * math.sin(3 * a + seed) + (i / 118) * 0.05
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    _stroke(cv, pts, color, width)
    return (x0 - 4, y0 - 4, x1 + 4, y1 + 4)


def arrow(cv, p0, p1, color="black", width=5, bend=0.25, head=22):
    """Curved hand-drawn arrow from p0 to p1; bend is how far the middle bows (fraction of length)."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    cxp, cyp = (x0 + x1) / 2 - (y1 - y0) * bend, (y0 + y1) / 2 + (x1 - x0) * bend
    pts = [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cxp + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cyp + t * t * y1)
           for t in [i / 24 for i in range(25)]]
    _stroke(cv, pts, color, width)
    a = math.atan2(y1 - pts[-3][1], x1 - pts[-3][0])
    for s in (-1, 1):
        _stroke(cv, [(x1, y1), (x1 - head * math.cos(a + s * 0.5), y1 - head * math.sin(a + s * 0.5))], color, width)
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def strike(cv, box, color="black", width=6, overshoot=10):
    """Level strike-through across the MIDDLE of the text's ink box (box from ink_text), a pixel of wobble at most."""
    x0, y0, x1, y1 = box
    ym = (y0 + y1) / 2
    wobble_line(cv, (x0 - overshoot, ym), (x1 + overshoot, ym), color, width, amp=1.0, seed=5)
    return (x0 - overshoot, ym - width, x1 + overshoot, ym + width)


def pill(cv, xy, text, f, fill="black", fg="white", arrow_glyph=True, padx=34, pady=18, anchor="left"):
    """Rounded tag with text and an optional arrow; xy is the top-left (anchor='left') or top-right ('right')."""
    tw = f.getlength(text) / S
    aw = f.size / S * 1.3 if arrow_glyph else 0
    asc, desc = f.getmetrics(); th = (asc + desc) / S
    w, h = tw + aw + 2 * padx, th + 2 * pady
    x, y = (xy[0], xy[1]) if anchor == "left" else (xy[0] - w, xy[1])
    cv.d.rounded_rectangle(_b((x, y, x + w, y + h)), h / 2 * S, fill=fill)
    l, t, r, b = f.getbbox(text, anchor="ls")
    base = (y + h / 2) * S + (-(t + b) / 2)
    cv.d.text((x * S + padx * S - l, base), text, font=f, fill=fg, anchor="ls")
    if arrow_glyph:
        ax, ay, ln = x + padx + tw + aw * 0.15, y + h / 2, aw * 0.7
        _stroke(cv, [(ax, ay), (ax + ln, ay)], fg, max(3, f.size / S / 12))
        _stroke(cv, [(ax + ln - 10, ay - 9), (ax + ln, ay), (ax + ln - 10, ay + 9)], fg, max(3, f.size / S / 12))
    return (x, y, x + w, y + h)


def alert_dialog(cv, box, title, body, f_title, f_body, buttons=("OK",), accent="#1F6FEB", fill="white", ink="#111"):
    """An OS-style alert window: title bar with three tiny controls, a warning triangle, body text and outlined buttons."""
    x0, y0, x1, y1 = box
    card(cv, box, r=10, fill=fill, outline=ink, width=3)
    bar = (x0, y0, x1, y0 + 46)
    cv.d.rounded_rectangle(_b(bar), 10 * S, fill=accent)
    ink_text(cv, x0 + 16, y0 + 8, title, f_title, "white")
    for i in range(3):
        bx = x1 - 22 - i * 24
        cv.d.rectangle(_b((bx - 8, y0 + 15, bx + 8, y0 + 31)), fill="white")
    tx, ty = x0 + 30, y0 + 78
    cv.d.polygon([(tx * S, (ty + 44) * S), ((tx + 24) * S, ty * S), ((tx + 48) * S, (ty + 44) * S)], fill="#F5C518", outline=ink)
    ink_text(cv, tx + 20, ty + 14, "!", f_title, ink)
    yb = ink_para(cv, x0 + 100, y0 + 70, body, f_body, ink, x1 - x0 - 130)
    bx = x1 - 30
    for label in reversed(buttons):
        w = ink_box(label, f_body)[2] + 44
        card(cv, (bx - w, y1 - 70, bx, y1 - 24), r=6, fill=fill, outline=ink, width=3, shadow=False)
        ink_text(cv, bx - w + 22, y1 - 62, label, f_body, ink)
        bx -= w + 16
    return tuple(box)


def line_chart(cv, box, pts, color="black", width=5, axes=True, amp=2.0, seed=3):
    """A hand-drawn line chart: L-shaped axes and a wobbly line through pts, a list of (x, y) in 0..1 (y up)."""
    x0, y0, x1, y1 = box
    if axes:
        wobble_line(cv, (x0, y0), (x0, y1), color, max(2, width - 2), amp=1.5, seed=seed)
        wobble_line(cv, (x0, y1), (x1, y1), color, max(2, width - 2), amp=1.5, seed=seed + 1)
    P = [(x0 + px * (x1 - x0), y1 - py * (y1 - y0)) for px, py in pts]
    for i, (a, b) in enumerate(zip(P, P[1:])):
        wobble_line(cv, a, b, color, width, amp=amp, seed=seed + 5 + i)
    return tuple(box)


def tilt_paste(cv, layer, x, y, angle, key=(255, 0, 255), shadow=True):
    """Paste a layer rotated by `angle` degrees, centred at (x, y). Draw the layer as a Canvas whose bg is the key colour
    (default magenta) with shadow=False on its elements; the shadow is added here, under the rotated shape."""
    from PIL import ImageChops
    im = layer.img.convert("RGB")
    mask = ImageChops.difference(im, Image.new("RGB", im.size, key)).convert("L").point(lambda v: 255 if v > 24 else 0)
    rgba = im.convert("RGBA"); rgba.putalpha(mask)
    rot = rgba.rotate(angle, expand=True, resample=Image.BICUBIC)
    px, py = round(x * S - rot.width / 2), round(y * S - rot.height / 2)
    if shadow:
        sh = Image.new("RGBA", rot.size, (0, 0, 0, 0))
        sh.putalpha(rot.getchannel("A").filter(ImageFilter.GaussianBlur(12 * S)).point(lambda v: int(v * 0.28)))
        cv.img.paste(sh, (px, py + 10 * S), sh)
    cv.img.paste(rot, (px, py), rot)
    cv.refresh()
    return (px / S, py / S, (px + rot.width) / S, (py + rot.height) / S)


def cutout(cv, kind, art_path, x, y, height):
    """Paste the client's exact mascot (flood-fill paper removal) or logo (multiply, light grounds) via place_asset.py."""
    sys.path.insert(0, HERE)
    import place_asset, io, contextlib
    fd, tmp = tempfile.mkstemp(suffix=".png"); os.close(fd)
    try:
        cv.img.save(tmp)
        with contextlib.redirect_stdout(io.StringIO()):
            getattr(place_asset, kind)(tmp, art_path, round(x * S), round(y * S), round(height * S))
        cv.img = Image.open(tmp).convert("RGB"); cv.img.load()
    finally:
        os.remove(tmp)
    cv.refresh()
    return (x, y, x, y + height)


if __name__ == "__main__":
    cv = Canvas(900, 600, "#F4EFE6")
    ink_text(cv, 60, 60, "Draw kit", font("Anton-Regular.ttf", 110), "#111")
    cv.save(os.path.join(tempfile.gettempdir(), "draw_demo.png")); print("demo written")
