#!/usr/bin/env python3
"""Parametric concept dielines: SVG + PDF + PNG + DXF + a spec sheet, from inside dimensions.

    python engine/dieline.py templates/dieline.json            # every job in the file
    python engine/dieline.py templates/dieline.json --only rte_carton
    python engine/dieline.py --style rte --L 60 --W 30 --D 120 --caliper 0.45

Styles (see references/styles.md for when to use each):
  rte, ste, sleeve                tube cartons (ECMA A20 family)
  tray                            four-wall tray with glued corner flaps (ECMA A60-type)
  rsc, hsc                        corrugated slotted containers (FEFCO 0201 / 0200)
  mailer                          roll-end tuck-front mailer (FEFCO 0427-type)
  pillow                          pillow pack with curved ends
  rigid                           set-up box: greyboard tray blank + wrap paper with turn-ins
  cone_label, wrap_label          tapered (frustum) and cylindrical labels
  pouch                           stand-up pouch print layout: seals, gusset, zipper, notch, eye mark
  flowwrap                        chips / snack pillow bag: fin seal, crimped end seals, split back, gussets
  sleeve_grid                     shrink-sleeve shrink map from a container profile

Every output is a CONCEPT dieline. The converter's dieline, from their CAD and their board, is the one that
goes to production. Allowances here are documented starting rules (references/engineering.md), not a standard.
Inside dimensions are L x W x D in mm (ECMA convention: L and W are the opening, L the longer; D the depth).
Coordinates: mm, origin top-left, y down. No dependencies except CairoSVG (PDF/PNG) and Pillow (contact sheet).
"""
import argparse, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Layer colours. Spot names match references/layers.md. Only CUT/CREASE/PERF/GLUE go to the converter.
COL = {"CUT": "#E6007E", "CREASE": "#0091D5", "PERF": "#F07D00", "GLUE": "#7F7F7F", "BLEED": "#E6007E",
       "SAFE": "#2E9E4F", "ZONE": "#7F7F7F", "GUIDE": "#6A4FD8", "DIM": "#4D4D4D", "INK": "#1A1A1A"}
FONT = "Space Mono, DejaVu Sans Mono, Menlo, monospace"

def clamp(v, lo, hi): return max(lo, min(hi, v))
def rad(a): return math.radians(a)

def arc(cx, cy, r, a0, a1, n=24):
    """Points on an arc in the uv plane, angles in degrees (0 = +u, 90 = +v)."""
    return [(cx + r * math.cos(rad(a0 + (a1 - a0) * i / n)), cy + r * math.sin(rad(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]

def sag_arc(a, b, s, n=32):
    """Circular arc from (a,0) to (b,0) bulging to v = s at the middle (s < 0 bulges inward)."""
    c = (b - a) / 2
    if abs(s) < 1e-6: return [(a, 0), (b, 0)]
    r = (c * c + s * s) / (2 * abs(s))
    sign = 1 if s > 0 else -1
    cy = sign * (abs(s) - r)               # centre on the far side of the chord
    mid = a + c
    a0 = math.degrees(math.atan2(0 - cy, a - mid))
    a1 = math.degrees(math.atan2(0 - cy, b - mid))
    if sign > 0 and a1 > a0: a1 -= 360
    if sign < 0 and a1 < a0: a1 += 360
    pts = arc(mid, cy, r, a0, a1, n)
    pts[0], pts[-1] = (a, 0.0), (b, 0.0)
    return pts

def area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2

def length(pl, closed=False):
    pts = pl + ([pl[0]] if closed else [])
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))

def dedupe(pts, eps=1e-6):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) > eps: out.append(p)
    if len(out) > 1 and math.dist(out[0], out[-1]) < eps: out.pop()
    return out


class Drawing:
    def __init__(self, name, style, p):
        self.name, self.style, self.p = name, style, p
        self.outlines = []                    # closed cut contours (one per piece)
        self.holes = []                       # closed interior cuts (windows, slots, hang holes)
        self.lines = {"CUT": [], "CREASE": [], "PERF": [], "GUIDE": [], "ZONE": []}   # open polylines
        self.glue, self.zones = [], []        # hatched areas: glue (no ink/varnish), seals and other zones
        self.panels = []                      # (name, poly, safe_inset or None)
        self.labels = []                      # (x, y, text, size, colour, anchor, rotate)
        self.arrows = []                      # (x, y, angle_deg, text) grain / flute / unwind arrows
        self.notes, self.warn = [], []
        self.facts = {}                       # extra rows for the spec sheet
        self.nobleed = set()                  # outline indexes that are unprinted (e.g. greyboard)

    def line(self, kind, *pts): self.lines[kind].append(list(pts))

    def all_points(self):
        pts = [q for o in self.outlines for q in o] + [q for h in self.holes for q in h]
        for k in self.lines: pts += [q for l in self.lines[k] for q in l]
        pts += [q for z in self.zones for q in z]
        return pts

    def bbox(self):
        pts = [q for o in self.outlines for q in o] or self.all_points()
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        return min(xs), min(ys), max(xs), max(ys)


class Frame:
    """Local frame on a rectangle edge: u runs along the edge (clockwise), v points outward."""
    def __init__(self, o, u, v, n): self.o, self.u, self.v, self.len = o, u, v, n
    def P(self, q):
        return (self.o[0] + q[0] * self.u[0] + q[1] * self.v[0], self.o[1] + q[0] * self.u[1] + q[1] * self.v[1])


class Prof:
    """A flap (or chain of flaps) attached to an edge segment [a, b]."""
    def __init__(self, a, b):
        self.a, self.b = a, b
        self.pts, self.lines, self.glue, self.zones, self.holes, self.panels, self.labels = [], [], [], [], [], [], []
    def crease(self, *pts): self.lines.append(("CREASE", list(pts)))
    def cut(self, *pts): self.lines.append(("CUT", list(pts)))
    def panel(self, name, poly, safe=None, up=(0, 1)): self.panels.append((name, poly, safe, up))   # up: art-up direction in uv


class Piece:
    EDGES = ("top", "right", "bottom", "left")
    def __init__(self, d, x0, y0, x1, y1):
        self.d, self.r = d, (x0, y0, x1, y1)
        self.att = {e: [] for e in self.EDGES}
    def frame(self, e):
        x0, y0, x1, y1 = self.r
        return {"top": Frame((x0, y0), (1, 0), (0, -1), x1 - x0),
                "right": Frame((x1, y0), (0, 1), (1, 0), y1 - y0),
                "bottom": Frame((x1, y1), (-1, 0), (0, 1), x1 - x0),
                "left": Frame((x0, y1), (0, -1), (-1, 0), y1 - y0)}[e]
    def attach(self, e, prof): self.att[e].append(prof); return prof
    def close(self):
        d, pts = self.d, []
        for e in self.EDGES:
            f = self.frame(e)
            pts.append(f.P((0, 0)))
            for pr in sorted(self.att[e], key=lambda q: q.a):
                pts += [f.P(q) for q in pr.pts]
                for kind, pl in pr.lines: d.lines[kind].append([f.P(q) for q in pl])
                d.glue += [[f.P(q) for q in g] for g in pr.glue]
                d.zones += [[f.P(q) for q in z] for z in pr.zones]
                d.holes += [[f.P(q) for q in h] for h in pr.holes]
                d.panels += [(n, [f.P(q) for q in poly], s, (up[0] * f.u[0] + up[1] * f.v[0], up[0] * f.u[1] + up[1] * f.v[1]))
                             for n, poly, s, up in pr.panels]
                d.labels += [(*f.P((u, v)), t, sz, c, a, 0) for (u, v, t, sz, c, a) in pr.labels]
        d.outlines.append(dedupe(pts))


def rect_poly(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

# ----------------------------------------------------------------- flap profiles (uv, v outward)

def p_flap(a, b, h, inset=0.0, chamfer=0.0, name=None, safe=None, crease=True):
    pr = Prof(a, b)
    a2, b2, ch = a + inset, b - inset, min(chamfer, h * 0.9, (b - a) / 2 - inset - 0.1)
    pr.pts = dedupe([(a2, 0), (a2, h - ch), (a2 + ch, h), (b2 - ch, h), (b2, h - ch), (b2, 0)])
    if crease: pr.crease((a2, 0), (b2, 0))
    if name: pr.panel(name, [(a2, 0), (b2, 0), (b2, h), (a2, h)], safe)
    return pr

def p_dust(a, b, h, c, bevel=15.0, name="Dust flap"):
    """Dust flap with corner relief c at the crease and a bevelled shoulder so it clears the closure."""
    pr = Prof(a, b)
    i = min(h * math.tan(rad(bevel)), (b - a) / 2 - c - 1)
    pr.pts = [(a + c, 0), (a + c, h * 0.25), (a + c + i, h), (b - c - i, h), (b - c, h * 0.25), (b - c, 0)]
    pr.crease((a + c, 0), (b - c, 0))
    pr.labels.append(((a + b) / 2, h * 0.55, name, 2.2, COL["DIM"], "middle"))
    return pr

def p_tuck(a, b, hc, T, c, name="Closure", safe=None, lock=True):
    """Closure panel (hc) and tuck tongue (T). The step of c at the tuck crease is a friction shoulder."""
    pr = Prof(a, b)
    r = min(T * 0.7, (b - a) / 4)
    corners = arc(a + c + r, hc + T - r, r, 180, 90, 10) + arc(b - c - r, hc + T - r, r, 90, 0, 10)
    pr.pts = dedupe([(a, 0), (a, hc), (a + c, hc)] + corners + [(b - c, hc), (b, hc), (b, 0)])
    pr.crease((a, 0), (b, 0))
    pr.crease((a + c, hc), (b - c, hc))
    pr.panel(name, [(a, 0), (b, 0), (b, hc), (a, hc)], safe, up=(0, -1))   # art reads toward the hinge
    pr.labels.append(((a + b) / 2, hc + T * 0.45, "Tuck", 2.2, COL["DIM"], "middle"))
    return pr

def p_glue(a, b, g, taper=15.0, c=1.0, name="Glue flap"):
    pr = Prof(a, b)
    e = g * math.tan(rad(taper))
    pr.pts = [(a + c, 0), (a + c + e, g), (b - c - e, g), (b - c, 0)]
    pr.crease((a + c, 0), (b - c, 0))
    k = 1.0
    pr.glue.append([(a + c + k, k), (a + c + e + k * 0.5, g - k), (b - c - e - k * 0.5, g - k), (b - c - k, k)])
    pr.labels.append(((a + b) / 2, g * 0.5, "GLUE · no ink, no varnish", 2.0, COL["DIM"], "middle"))
    return pr


# ----------------------------------------------------------------- shared parameters

FLUTE = {"F": 0.8, "E": 1.6, "B": 3.2, "C": 4.0, "A": 4.8, "EB": 4.8, "BC": 7.2}   # approx. caliper, mm

def dims(p):
    L, W, D = float(p["L"]), float(p["W"]), float(p.get("D", 0))
    if W > L and p.get("style") in ("rte", "ste", "sleeve", "tray", "rsc", "hsc", "mailer"):
        L, W = W, L
    t = float(p.get("caliper") or FLUTE.get(str(p.get("flute", "")).upper(), 0.45))
    return L, W, D, t

def safe_of(p): return float(p.get("safe", 3.0))


# ----------------------------------------------------------------- styles

def s_tube(d, p, mode):
    L, W, D, t = dims(p)
    Lp, Wp = L + t, W + t                              # crease-to-crease panel widths: inside + 1 caliper
    Dp = D + (0 if mode == "sleeve" else 2 * t)        # + 1 caliper per closure
    g = float(p.get("glue_flap", clamp(0.9 * Wp, 8, 18)))
    sf = safe_of(p)
    xs = [0, Wp, Wp + Lp, 2 * Wp + Lp, 2 * Wp + 2 * Lp]
    pc = Piece(d, 0, 0, xs[4], Dp)
    for x in xs[1:4]: d.line("CREASE", (x, 0), (x, Dp))
    for n, (x0, x1) in zip(["Side A", "Front", "Side B", "Back"], zip(xs, xs[1:])):
        d.panels.append((n, rect_poly(x0, 0, x1, Dp), sf))
    pc.attach("left", p_glue(0, Dp, g, float(p.get("glue_taper", 15))))
    c = max(t, 0.8)
    if mode == "sleeve":
        nr = float(p.get("thumb_notch", 0))
        if nr:
            for e in ("top", "bottom"):
                u0 = (xs[1] + xs[2]) / 2 if e == "top" else xs[4] - (xs[1] + xs[2]) / 2
                pr = Prof(u0 - nr, u0 + nr); pr.pts = sag_arc(u0 - nr, u0 + nr, -nr); pc.attach(e, pr)
        d.notes.append("Sleeve: open both ends. Check the product's slide-in direction against the grain and any thumb notch.")
    else:
        hc = Wp
        T = float(p.get("tuck", clamp(0.45 * Wp, 8, 20)))
        Hd = float(p.get("dust", min(0.45 * Lp, 0.8 * Wp)))
        if Hd > 0.5 * Lp - c: d.warn.append("Dust flaps longer than half the length; they will collide. Shorten 'dust'.")
        top_close = (xs[3], xs[4])                       # back panel (both styles)
        pc.attach("top", p_dust(xs[0], xs[1], Hd, c)); pc.attach("top", p_dust(xs[2], xs[3], Hd, c))
        pc.attach("top", p_tuck(*top_close, hc, T, c, "Top closure", sf))
        # bottom edge runs right to left: u = xs[4] - x
        U = lambda x0, x1: (xs[4] - x1, xs[4] - x0)
        pc.attach("bottom", p_dust(*U(xs[0], xs[1]), Hd, c)); pc.attach("bottom", p_dust(*U(xs[2], xs[3]), Hd, c))
        bot = U(xs[1], xs[2]) if mode == "rte" else U(xs[3], xs[4])
        pc.attach("bottom", p_tuck(*bot, hc, T, c, "Bottom closure", sf))
        d.notes.append("Reverse tuck end: top tuck hinged on the back, bottom tuck on the front. Ask the converter which way the tucks run on their line."
                       if mode == "rte" else "Straight tuck end: both tucks hinged on the back panel, so the front face prints with no closure crease.")
    pc.close()
    d.arrows.append((xs[2] + Lp / 2, Dp / 2, 0, "GRAIN (default: around the tube; confirm)"))
    d.facts.update({"Panels (crease to crease)": f"side {Wp:.1f} · front/back {Lp:.1f} · depth {Dp:.1f}",
                    "Glue flap": f"{g:.1f} mm, {p.get('glue_taper', 15)}° taper"})


def s_tray(d, p):
    L, W, D, t = dims(p)
    Lp, Wp, Dw = L + t, W + t, D + t
    c = max(t, 0.8)
    gf = float(p.get("corner_flap", clamp(0.45 * Wp, 8, 25)))
    sf = safe_of(p)
    pc = Piece(d, 0, 0, Lp, Wp)
    d.panels.append(("Base", rect_poly(0, 0, Lp, Wp), sf))

    def long_wall(name):
        pr = Prof(0, Lp)
        e = min(gf * math.tan(rad(15)), (Dw - 2 * c) / 3)
        left = [(0, 0), (0, c), (-gf, c + e), (-gf, Dw - c - e), (0, Dw - c), (0, Dw)]
        right = [(Lp - u, v) for u, v in reversed(left)]
        pr.pts = left + right
        pr.crease((0, 0), (Lp, 0))
        pr.crease((0, c), (0, Dw - c)); pr.crease((Lp, c), (Lp, Dw - c))
        for s in (1, -1):
            x0 = 0 if s == 1 else Lp
            pr.glue.append([(x0 - s * 1, c + 1), (x0 - s * (gf - 1), c + e + 1), (x0 - s * (gf - 1), Dw - c - e - 1), (x0 - s * 1, Dw - c - 1)])
        pr.panel(name, [(0, 0), (Lp, 0), (Lp, Dw), (0, Dw)], sf)
        return pr
    pc.attach("top", long_wall("Back wall"))
    pc.attach("bottom", long_wall("Front wall"))
    for e, n in (("left", "End wall"), ("right", "End wall")):
        pc.attach(e, p_flap(0, Wp, D, name=n, safe=sf))
    pc.close()
    d.notes.append("Corner flaps glue to the inside of the end walls. For a display tray, raise the back wall into a header (add 'header').")
    d.arrows.append((Lp / 2, Wp / 2, 0, "GRAIN (default: along L; confirm)"))
    d.facts["Walls"] = f"long {Dw:.1f} · end {D:.1f} · corner flaps {gf:.1f}"


def s_rsc(d, p, half=False):
    L, W, D, t = dims(p)
    Lp, Wp, Dp = L + t, W + t, D + 2 * t
    s = float(p.get("slot", max(3.0, 2 * t)))
    j = float(p.get("joint", 35.0))
    Fh = float(p.get("flap", (W + t) / 2))
    sf = safe_of(p)
    xs = [0, Lp, Lp + Wp, 2 * Lp + Wp, 2 * Lp + 2 * Wp]
    pc = Piece(d, 0, 0, xs[4], Dp)
    for x in xs[1:4]: d.line("CREASE", (x, 0), (x, Dp))
    for n, (x0, x1) in zip(["Front (L)", "Side (W)", "Back (L)", "Side (W)"], zip(xs, xs[1:])):
        d.panels.append((n, rect_poly(x0, 0, x1, Dp), sf))
    pc.attach("left", p_glue(0, Dp, j, 15, c=max(2, t), name="Manufacturer's joint"))
    for e in ("bottom",) + (() if half else ("top",)):
        for x0, x1 in zip(xs, xs[1:]):
            a, b = (x0, x1) if e == "top" else (xs[4] - x1, xs[4] - x0)
            pc.attach(e, p_flap(a, b, Fh, inset=s / 2))
    pc.close()
    d.arrows.append((xs[0] + Lp / 2, Dp / 2, 90, "FLUTES vertical (stacking strength)"))
    perim_in = 2 * (L + W) / 25.4
    ect = float(p.get("ect", 0))
    if ect:
        bct_lbf = 5.87 * ect * math.sqrt((t / 25.4) * perim_in)
        d.facts["McKee estimate"] = (f"BCT ≈ {bct_lbf:.0f} lbf ≈ {bct_lbf * 0.4536:.0f} kgf for ECT {ect:g} lb/in, caliper {t} mm, "
                                     "perimeter {:.0f} mm. Empty box, lab conditions: apply the stacking safety factor (references/display_shipping.md).".format(2 * (L + W)))
    d.facts.update({"Panels": f"L {Lp:.1f} · W {Wp:.1f} · depth {Dp:.1f} · flaps {Fh:.1f}", "Slot / joint": f"{s:.1f} / {j:.1f} mm",
                    "Board": f"{p.get('flute', '?')} flute ≈ {t} mm"})
    d.notes.append("FEFCO layouts are drawn from the inside of the case; this one is drawn from the print side. Check which side your converter expects.")


def s_mailer(d, p):
    L, W, D, t = dims(p)
    Lp, Wp, Dw = L + t, W + 2 * t, D + t
    c = max(t, 1.0)
    sf = safe_of(p)
    ear = clamp(0.9 * Dw, 10, 0.45 * Wp)
    pc = Piece(d, 0, 0, Lp, Wp)
    d.panels.append(("Base", rect_poly(0, 0, Lp, Wp), sf))
    tw, th = float(p.get("tab_w", clamp(0.18 * Lp, 12, 30))), 1.5 * t + 1.5

    def ear_pts(v0, h):           # ear on the u<0 side of a wall, hinged on u=0 from v0+c to v0+h-c
        ch = min(ear * 0.35, h * 0.3)
        return [(0, v0 + c), (-ear, v0 + c + ch), (-ear, v0 + h - c), (0, v0 + h - c)]

    def tabs_on(length, v_edge, pts_dir=1):
        """Tab points (u, v) along a far edge at v_edge, two tabs at 1/4 and 3/4."""
        out = []
        for uc in (length * 0.25, length * 0.75):
            out.append([(uc - tw / 2, v_edge), (uc - tw / 2 + 1, v_edge + th), (uc + tw / 2 - 1, v_edge + th), (uc + tw / 2, v_edge)])
        return out

    # back wall -> lid -> lid front -> tuck, mirrored about the middle
    pr = Prof(0, Lp)
    Tk = Dw - 2 * t - 1
    hd = Dw - 2 * t
    r = min(Tk * 0.5, 12)
    left = [(0, 0)] + ear_pts(0, Dw) + [(0, Dw)]
    left += [(0, Dw + c), (-hd, Dw + c + hd * 0.3), (-hd, Dw + Wp - c - 2), (0, Dw + Wp - c), (0, Dw + Wp), (0, 2 * Dw + Wp), (c, 2 * Dw + Wp)]
    tip = 2 * Dw + Wp + Tk
    left += [(c + r - r * math.cos(rad(a)), tip - r + r * math.sin(rad(a))) for a in range(0, 91, 10)] + [(Lp / 2, tip)]
    pr.pts = dedupe(left + [(Lp - u, v) for u, v in reversed(left[:-1])])
    for v in (0, Dw, Dw + Wp): pr.crease((0, v), (Lp, v))
    pr.crease((c, 2 * Dw + Wp), (Lp - c, 2 * Dw + Wp))
    for u in (0, Lp):
        pr.crease((u, c), (u, Dw - c)); pr.crease((u, Dw + c), (u, Dw + Wp - c))
    pr.panel("Back wall", [(0, 0), (Lp, 0), (Lp, Dw), (0, Dw)], sf)
    pr.panel("Lid (outside)", [(0, Dw), (Lp, Dw), (Lp, Dw + Wp), (0, Dw + Wp)], sf, up=(0, -1))
    pr.panel("Lid front", [(0, Dw + Wp), (Lp, Dw + Wp), (Lp, 2 * Dw + Wp), (0, 2 * Dw + Wp)], sf, up=(0, -1))
    pr.labels.append((Lp / 2, 2 * Dw + Wp + Tk * 0.5, "Tuck", 2.2, COL["DIM"], "middle"))
    pc.attach("top", pr)

    # front wall (double) with ears; inner wall tabs lock into base slots
    def double_wall(length, ears, name):
        q = Prof(0, length)
        h2 = Dw - t
        left = [(0, 0)] + (ear_pts(0, Dw) if ears else [(0, c)] if False else []) + [(0, Dw), (0, Dw + h2)]
        if not ears: left = [(c, 0), (c, Dw), (c, Dw + h2)]
        far = Dw + h2
        tabs = tabs_on(length, far)
        top = []
        for tb in tabs: top += tb
        rightside = [(length - u, v) for u, v in reversed(left)]
        q.pts = dedupe(left + top + rightside)
        a0 = 0 if ears else c
        q.crease((a0, 0), (length - a0, 0)); q.crease((a0, Dw), (length - a0, Dw))
        if ears:
            for u in (0, length): q.crease((u, c), (u, Dw - c))
        for tb in tabs:      # matching slots in the base, just inside the crease
            u0, u1 = tb[0][0] - 0.5, tb[-1][0] + 0.5
            q.holes.append([(u0, -0.5 * t), (u1, -0.5 * t), (u1, -(1.5 * t + 1)), (u0, -(1.5 * t + 1))])
        q.panel(name, [(a0, 0), (length - a0, 0), (length - a0, Dw), (a0, Dw)], sf)
        q.labels.append((length / 2, Dw + h2 * 0.5, "Inner wall", 2.2, COL["DIM"], "middle"))
        return q
    pc.attach("bottom", double_wall(Lp, True, "Front wall"))
    pc.attach("left", double_wall(Wp, False, "Side wall"))
    pc.attach("right", double_wall(Wp, False, "Side wall"))
    pc.close()
    d.arrows.append((Lp / 2, Wp / 2, 0, "FLUTES across L (confirm with converter)"))
    d.notes.append("FEFCO 0427-type concept: double side walls lock with tabs into base slots; the ears fold in between the double walls. "
                   "The lid's inside and the base are the unboxing canvas: print inside only if the converter can (two-sided print costs more).")


def s_pillow(d, p):
    L, W, D, t = dims(p)
    Pw = L + t
    s = float(p.get("sag", min(W / 2, 0.3 * Pw)))
    g = float(p.get("glue_flap", clamp(0.5 * W, 8, 15)))
    sf = safe_of(p)
    pc = Piece(d, 0, 0, 2 * Pw, D)
    d.line("CREASE", (Pw, 0), (Pw, D))
    for n, x0 in (("Front", 0), ("Back", Pw)): d.panels.append((n, rect_poly(x0, s, x0 + Pw, D - s), sf))
    pc.attach("left", p_glue(0, D, g))
    for e in ("top", "bottom"):
        for a in (0, Pw):
            pr = Prof(a, a + Pw); pr.pts = sag_arc(a, a + Pw, s)
            pr.crease(*sag_arc(a, a + Pw, -s))
            pc.attach(e, pr)
    pc.close()
    d.notes.append("Pillow ends close by pushing the curved creases in. A tighter sag makes a flatter pack. Use a light board (≈0.35–0.45 mm) that won't crack on the curve; test fold.")
    d.facts["Curve"] = f"sagitta {s:.1f} mm on a {Pw:.1f} mm panel"


def s_rigid(d, p):
    L, W, D, t = dims(p)
    b = float(p.get("board", 2.0))                     # greyboard thickness
    T = float(p.get("turn_in", 15.0))
    ct = float(p.get("corner_tab", 12.0))
    c = 0.8
    sf = safe_of(p)
    # piece 1: greyboard tray blank (V-groove scored walls, square corners taped)
    gx, gy = 0, 0
    pc = Piece(d, gx, gy, gx + L + b, gy + W + b)
    d.panels.append(("Greyboard base", rect_poly(gx, gy, gx + L + b, gy + W + b), None))
    for e, n in (("top", L + b), ("bottom", L + b), ("left", W + b), ("right", W + b)):
        pc.attach(e, p_flap(0, n, D, name="Wall"))
    pc.close()
    d.nobleed.add(len(d.outlines) - 1)
    d.labels.append((gx + (L + b) / 2, gy - D - 6, f"GREYBOARD {b} mm · creases = V-grooves · corners taped (stay tape)", 2.4, COL["INK"], "middle", 0))
    # piece 2: wrap paper
    Lo, Wo, H1 = L + 2 * b, W + 2 * b, D + b
    ox = gx + L + b + D + 2 * (H1 + b + T) + 30
    oy = gy + (W + b) / 2 - Wo / 2
    wp = Piece(d, ox, oy, ox + Lo, oy + Wo)
    d.panels.append(("Wrap · underside", rect_poly(ox, oy, ox + Lo, oy + Wo), sf))
    m = T * 0.3

    def long_wall():
        q = Prof(0, Lo)
        left = [(0, 0), (0, c), (-ct, c + ct), (-ct, H1), (0, H1), (0, H1 + b), (m, H1 + b + T)]
        q.pts = left + [(Lo - u, v) for u, v in reversed(left)]
        for v in (0, H1, H1 + b): q.crease((0, v), (Lo, v))
        for u in (0, Lo): q.crease((u, c), (u, H1))
        q.panel("Wall wrap", [(0, 0), (Lo, 0), (Lo, H1), (0, H1)], sf)
        q.labels.append((Lo / 2, H1 + b + T * 0.55, "turn-in (shows inside)", 2.0, COL["DIM"], "middle"))
        return q

    def short_wall():
        q = Prof(0, Wo)
        q.pts = [(0, 0), (0, H1 + b), (m, H1 + b + T), (Wo - m, H1 + b + T), (Wo, H1 + b), (Wo, 0)]
        for v in (0, H1, H1 + b): q.crease((0, v), (Wo, v))
        q.panel("End wrap", [(0, 0), (Wo, 0), (Wo, H1), (0, H1)], sf)
        return q
    wp.attach("top", long_wall()); wp.attach("bottom", long_wall())
    wp.attach("left", short_wall()); wp.attach("right", short_wall())
    wp.close()
    d.labels.append((ox + Lo / 2, oy - H1 - b - T - 6, "WRAP PAPER (fully glued) · art runs past every fold", 2.4, COL["INK"], "middle", 0))
    d.notes.append("Turn-ins show inside the box: carry the colour or pattern over the top edge, never stop art at the fold. "
                   "Corner tabs wrap the corners; the end wrap covers them. Magnet cavities, ribbon pulls and inserts are separate drawings.")
    d.facts["Rigid"] = f"greyboard {b} mm · wrap turn-in {T} mm · corner tabs {ct} mm · outside {Lo:.1f} × {Wo:.1f} × {H1:.1f}"


def s_cone_label(d, p):
    dt, db, h = float(p["d_top"]), float(p["d_bottom"]), float(p["h"])
    cover, ov = float(p.get("cover", 1.0)), float(p.get("overlap", 6.0 if float(p.get("cover", 1.0)) >= 1 else 0))
    sf = safe_of(p)
    if abs(dt - db) < 0.01:
        return s_wrap_label(d, dict(p, d=dt))
    Dg, dg = max(dt, db), min(dt, db)
    s = math.sqrt(h ** 2 + ((Dg - dg) / 2) ** 2)
    R1 = s * Dg / (Dg - dg); R2 = R1 - s
    theta = math.degrees((math.pi * Dg * cover + ov) / R1)
    if theta >= 359: d.warn.append("The label wraps almost the whole sector; split it or reduce cover.")
    wide_bottom = db > dt
    a0, a1 = 90 - theta / 2, 90 + theta / 2           # centred on +y (screen down)
    outer = arc(0, 0, R1, a0, a1, 96); inner = arc(0, 0, R2, a1, a0, 96)
    poly = outer + inner
    if not wide_bottom: poly = [(x, -y) for x, y in poly]
    d.outlines.append(poly)
    for k in range(1, 12):                            # radial guides = verticals on the container
        a = a0 + theta * k / 12
        q1, q2 = (R2 * math.cos(rad(a)), R2 * math.sin(rad(a))), (R1 * math.cos(rad(a)), R1 * math.sin(rad(a)))
        if not wide_bottom: q1, q2 = (q1[0], -q1[1]), (q2[0], -q2[1])
        d.line("GUIDE", q1, q2)
    for f in (0.25, 0.5, 0.75):
        rr = R2 + s * f
        pts = arc(0, 0, rr, a0, a1, 64)
        d.line("GUIDE", *[(x, y if wide_bottom else -y) for x, y in pts])
    if ov:
        ao = a1 - math.degrees(ov / R1)
        q1, q2 = (R2 * math.cos(rad(ao)), R2 * math.sin(rad(ao))), (R1 * math.cos(rad(ao)), R1 * math.sin(rad(ao)))
        if not wide_bottom: q1, q2 = (q1[0], -q1[1]), (q2[0], -q2[1])
        d.line("ZONE", q1, q2)
        d.notes.append(f"Overlap {ov} mm at the right end: keep it free of barcodes and small type, and print it so the seam reads cleanly.")
    d.notes.append("Radial guides are the container's verticals; arcs are its horizontals. Set type on the arcs; never on straight lines.")
    d.facts.update({"Frustum": f"slant {s:.2f} · outer radius {R1:.2f} · inner radius {R2:.2f} · sector {theta:.2f}°",
                    "Container": f"Ø top {dt} · Ø bottom {db} · label height {h} · cover {cover:.0%}"})
    d.notes.append("Measure the container where the label sits (on a sample from the line, not a drawing). Irregular tapers and necks need a test print.")


def s_wrap_label(d, p):
    dd, h = float(p["d"]), float(p["h"])
    cover = float(p.get("cover", 1.0)); ov = float(p.get("overlap", 6.0 if cover >= 1 else 0))
    w = math.pi * dd * cover + ov
    d.outlines.append(rect_poly(0, 0, w, h))
    d.panels.append(("Label", rect_poly(0, 0, w - ov, h), safe_of(p)))
    for k in range(1, 4):
        d.line("GUIDE", (w * k / 4 - ov * k / 4, 0), (w * k / 4 - ov * k / 4, h))
    if ov:
        d.zones.append(rect_poly(w - ov, 0, w, h))
        d.labels.append((w - ov / 2, h / 2, "overlap", 2.0, COL["DIM"], "middle", -90))
    d.notes.append("Quarter lines show front / side / back / side. Put the front face at the first quarter and keep the barcode horizontal (picket fence) if the curve is tight.")
    d.facts["Wrap"] = f"Ø {dd} · circumference {math.pi * dd:.2f} · width {w:.2f} incl. {ov} mm overlap"


def s_pouch(d, p):
    W, H, G = float(p["W"]), float(p["H"]), float(p.get("G", 0.35 * float(p["W"])))
    ss, ts = float(p.get("side_seal", 8)), float(p.get("top_seal", 10))
    zip_off, zip_w = float(p.get("zip_from_top", 25)), float(p.get("zip_band", 10))
    Hp = H - G / 2
    tot = 2 * Hp + G
    d.outlines.append(rect_poly(0, 0, W, tot))
    # front panel (top of the web) reads upright; back panel reads upside down below the gusset
    d.panels.append(("FRONT (art reads up)", rect_poly(ss, ts, W - ss, Hp), safe_of(p)))
    d.panels.append(("BACK (art rotated 180°)", rect_poly(ss, Hp + G, W - ss, tot - ts), safe_of(p), (0, 1)))
    d.zones += [rect_poly(0, 0, W, ts), rect_poly(0, tot - ts, W, tot)]
    d.zones += [rect_poly(0, 0, ss, Hp), rect_poly(W - ss, 0, W, Hp), rect_poly(0, Hp + G, ss, tot), rect_poly(W - ss, Hp + G, W, tot)]
    d.line("CREASE", (0, Hp + G / 2), (W, Hp + G / 2))              # gusset fold
    d.line("GUIDE", (0, Hp), (W, Hp)); d.line("GUIDE", (0, Hp + G), (W, Hp + G))
    d.labels.append((W / 2, Hp + G / 2 - 1.5, "bottom gusset fold", 2.0, COL["DIM"], "middle", 0))
    rb = min(G * 0.9, W * 0.18)                                      # rounded-bottom corner seals
    for (cx, cy, a0, a1) in ((ss, Hp, 270, 360), (W - ss, Hp, 180, 270), (ss, Hp + G, 0, 90), (W - ss, Hp + G, 90, 180)):
        pts = arc(cx, cy, rb, a0, a1, 16)
        d.zones.append([(cx, cy)] + [(x, y) for x, y in pts])
    for y0 in (zip_off, tot - zip_off - zip_w):
        d.zones.append(rect_poly(0, y0, W, y0 + zip_w))
        d.labels.append((W / 2, y0 + zip_w / 2 + 0.8, "zipper band · no barcode, no fine type", 2.0, COL["DIM"], "middle", 0))
    nt = (ts + zip_off) / 2
    for y in (nt, tot - nt):
        d.holes.append([(0, y - 2.5), (3.5, y), (0, y + 2.5)])
        d.labels.append((ss + 1, y + 0.7, "tear notch", 1.8, COL["DIM"], "start", 0))
    if p.get("hang_hole", True):
        for yc in (ts / 2 + 3, tot - ts / 2 - 3):
            w2 = 12
            d.holes.append(arc(W / 2 - w2 / 2, yc, 2.5, 90, 270, 8) + arc(W / 2 + w2 / 2, yc, 2.5, -90, 90, 8))
    em = (6, 12)
    d.zones.append(rect_poly(W - ss - em[0] - 1, Hp + G / 2 - em[1] / 2, W - ss - 1, Hp + G / 2 + em[1] / 2))
    d.labels.append((W - ss - em[0] - 2, Hp + G / 2 + 0.7, "eye mark", 1.8, COL["DIM"], "end", 0))
    d.arrows.append((W + 8, tot / 2, 90, "UNWIND / WEB DIRECTION: ask the converter"))
    d.notes.append("Seal widths, zipper position, notch and eye-mark spec come from the converter and their filling line. These are placeholders.")
    d.notes.append("Seals print but distort: keep logos, type and barcodes out of hatched zones; let colour run through them.")
    d.facts["Pouch"] = f"W {W} × H {H} × gusset {G} · panels {W - 2 * ss:.0f} × {Hp - ts:.0f} printable · side seal {ss} · top seal {ts}"


def s_sleeve_grid(d, p):
    prof = sorted([(float(h), float(dd)) for h, dd in p["profile"]])
    Hs = prof[-1][0] - prof[0][0]
    dmax = max(dd for _, dd in prof)
    ease = float(p.get("ease", 0.03)); md = float(p.get("md_shrink", 0.03))
    C0 = math.pi * dmax * (1 + ease)
    Hf = Hs * (1 + md)
    d.outlines.append(rect_poly(0, 0, C0, Hf))
    d.line("CREASE", (C0 / 2, 0), (C0 / 2, Hf))
    d.labels.append((C0 / 4, -2, "FRONT (lay-flat face)", 2.2, COL["INK"], "middle", 0))
    d.labels.append((3 * C0 / 4, -2, "BACK", 2.2, COL["INK"], "middle", 0))

    def dia(h):
        for (h0, d0), (h1, d1) in zip(prof, prof[1:]):
            if h0 <= h <= h1: return d0 + (d1 - d0) * (h - h0) / max(h1 - h0, 1e-9)
        return prof[-1][1]
    steps = max(8, int(Hs / 4))
    for i in range(steps):
        hA = prof[0][0] + Hs * i / steps; hB = prof[0][0] + Hs * (i + 1) / steps
        k = math.pi * dia((hA + hB) / 2) / C0
        shrink = 1 - k
        y1 = Hf - (hA - prof[0][0]) * (1 + md); y0 = Hf - (hB - prof[0][0]) * (1 + md)
        band = rect_poly(0, y0, C0, y1)
        d.zones.append(band) if shrink > 0.3 else None
        col = "#2E9E4F" if shrink < 0.1 else "#F07D00" if shrink < 0.3 else "#C8102E"
        d.labels.append((C0 + 2, (y0 + y1) / 2 + 0.8, f"{shrink * 100:4.0f}%  ×{1 / k:.2f}", 2.0, col, "start", 0))
        if i % max(1, steps // 6) == 0:
            for xc in (C0 / 4, 3 * C0 / 4):
                rx, ry = 4 / k, 4
                d.line("GUIDE", *[(xc + rx * math.cos(rad(a)), (y0 + y1) / 2 + ry * math.sin(rad(a))) for a in range(0, 361, 15)])
    d.notes.append("Right-hand column: horizontal shrink at that height and the pre-stretch factor. Red bands (>30%): no type, no barcodes, no faces.")
    d.notes.append("Ellipses show how a 8 mm circle must be pre-stretched to land round. First pass only: confirm with the film's TD/MD shrink curve and a printed grid shrunk on the real container.")
    d.facts["Sleeve"] = f"lay-flat circumference {C0:.1f} (Ø max {dmax} + {ease:.0%} ease) · height {Hf:.1f} incl. {md:.0%} MD shrink"


def s_flowwrap(d, p):
    """Flow-wrap / VFFS pillow bag (chips, snacks, bars): fin seal on the back, crimped end seals, optional side gussets.
    The web runs: fin | back left half | gusset | FRONT | gusset | back right half | fin. The back's art is split across both edges."""
    W, H = float(p["W"]), float(p["H"])
    f, e, G = float(p.get("fin", 10)), float(p.get("end_seal", 12)), float(p.get("gusset", 0))
    z, amp = float(p.get("serration", 3)), 1.2
    xs = [0, f, f + W / 2, f + W / 2 + G, f + W / 2 + G + W, f + W / 2 + 2 * G + W, f + 1.5 * W + 2 * G, 2 * f + 2 * W + 2 * G]
    tot = xs[-1]
    n = max(2, int(tot / z))
    top = [(tot * i / n, amp if i % 2 else 0) for i in range(n + 1)]
    bot = [(tot * i / n, H - (amp if i % 2 else 0)) for i in range(n, -1, -1)]
    d.outlines.append(dedupe(top + bot))
    folds = sorted(set(round(x, 3) for x in (xs[1], xs[2], xs[3], xs[4], xs[5], xs[6])))
    for x in folds: d.line("CREASE", (x, e), (x, H - e))
    if G:
        for gc in (xs[2] + G / 2, xs[4] + G / 2):
            d.line("PERF", (gc, e), (gc, H - e))
            d.labels.append((gc + 1, H / 2, "gusset fold (in)", 1.8, COL["DIM"], "start", -90))
            d.panels.append(("Gusset", rect_poly(gc - G / 2, e, gc + G / 2, H - e), None, (0, -1)))
    d.zones += [rect_poly(0, 0, f, H), rect_poly(tot - f, 0, tot, H), rect_poly(0, 0, tot, e), rect_poly(0, H - e, tot, H)]
    d.panels.append(("FRONT", rect_poly(xs[3], e, xs[4], H - e), safe_of(p), (0, -1)))
    d.panels.append(("Back-half L", rect_poly(xs[1], e, xs[2], H - e), None, (0, -1)))
    d.panels.append(("Back-half R", rect_poly(xs[5], e, xs[6], H - e), None, (0, -1)))
    d.split_back = {"BL": xs[1], "BR": xs[5], "W": W, "y0": e, "h": H - 2 * e, "fin": f}
    d.labels.append(((xs[1] + xs[2]) / 2, e + 6, "back: RIGHT half of the back art", 1.9, COL["DIM"], "middle", 0))
    d.labels.append(((xs[5] + xs[6]) / 2, e + 6, "back: LEFT half of the back art", 1.9, COL["DIM"], "middle", 0))
    d.labels.append((f / 2, H / 2, "fin seal", 1.8, COL["DIM"], "middle", -90))
    d.labels.append((tot - f / 2, H / 2, "fin seal", 1.8, COL["DIM"], "middle", -90))
    d.labels.append((tot / 2, e / 2 + 0.7, "crimped end seal · serrated cut-off", 1.9, COL["DIM"], "middle", 0))
    em = min(6, e - 2)
    d.zones.append(rect_poly(xs[6] - 14, (e - em) / 2, xs[6] - 2, (e + em) / 2))
    d.labels.append((xs[6] - 15, e / 2 + 0.7, "eye mark", 1.8, COL["DIM"], "end", 0))
    d.arrows.append((tot / 2, H + 4, 0, "WEB / UNWIND DIRECTION + CUT-OFF: from the converter and the wrapper"))
    d.notes.append("Back art is split: its LEFT half prints at the web's right edge and its RIGHT half at the left edge; they meet at the fin seal down the back's centre.")
    d.notes.append(f"The fin folds flat over the back, covering about {f:g} mm beside the centre line: keep type and barcodes off it.")
    d.notes.append("Print can drift up to ~4 mm against folds and seals on form-fill-seal lines: no thin borders at panel edges; let colour run through seals.")
    d.notes.append("Snacks with fats (chips, nuts) need a light and oxygen barrier: metallised film plus nitrogen flush is the usual answer. A clear window trades shelf life for show-through, so ask the food technologist.")
    d.facts["Flow wrap"] = f"web width {tot:.1f} · cut-off (repeat) {H:.1f} · front {W:g} × {H - 2 * e:.0f} printable · fin {f:g} · end seals {e:g}" + (f" · gussets {G:g}" if G else "")


STYLES = {"rte": lambda d, p: s_tube(d, p, "rte"), "ste": lambda d, p: s_tube(d, p, "ste"),
          "sleeve": lambda d, p: s_tube(d, p, "sleeve"), "tray": s_tray, "rsc": s_rsc,
          "hsc": lambda d, p: s_rsc(d, p, half=True), "mailer": s_mailer, "pillow": s_pillow, "rigid": s_rigid,
          "cone_label": s_cone_label, "wrap_label": s_wrap_label, "pouch": s_pouch, "sleeve_grid": s_sleeve_grid,
          "flowwrap": s_flowwrap}
TITLES = {"rte": "Reverse tuck end (ECMA A20.20-type)", "ste": "Straight tuck end (ECMA A20.20-type)",
          "sleeve": "Sleeve / tube", "tray": "Glued-corner tray", "rsc": "Regular slotted container (FEFCO 0201)",
          "hsc": "Half slotted container (FEFCO 0200)", "mailer": "Tuck-front mailer (FEFCO 0427-type)",
          "pillow": "Pillow pack", "rigid": "Rigid set-up box: blank + wrap", "cone_label": "Tapered (cone) label",
          "wrap_label": "Wrap-around label", "pouch": "Stand-up pouch print layout", "sleeve_grid": "Shrink-sleeve shrink map",
          "flowwrap": "Flow-wrap pillow bag (chips / snack packet)"}


# ----------------------------------------------------------------- output

def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def path_d(pts, closed=True):
    return "M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in pts) + (" Z" if closed else "")

def inset_rect(poly, k):
    xs, ys = [q[0] for q in poly], [q[1] for q in poly]
    x0, y0, x1, y1 = min(xs) + k, min(ys) + k, max(xs) - k, max(ys) - k
    return None if x1 <= x0 or y1 <= y0 else rect_poly(x0, y0, x1, y1)

def render(d, out):
    p = d.p
    bleed = float(p.get("bleed", 3.0))
    x0, y0, x1, y1 = bbox = d.bbox()
    pts = d.all_points()
    ex0 = min(q[0] for q in pts); ey0 = min(q[1] for q in pts); ex1 = max(q[0] for q in pts); ey1 = max(q[1] for q in pts)
    lab_extra = 55 if d.style == "sleeve_grid" else 0
    m = 18 + bleed
    ox, oy = m - min(ex0, x0) , m + 6 - min(ey0, y0)
    W = (max(ex1, x1) - min(ex0, x0)) + 2 * m + lab_extra + (40 if d.style == "pouch" else 0)
    tb = 34
    H = (max(ey1, y1) - min(ey0, y0)) + 2 * m + 12 + tb
    W = max(W, 200)
    T = lambda pl: [(x + ox, y + oy) for x, y in pl]
    sw = 0.3
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
         f'width="{W:.2f}mm" height="{H:.2f}mm" viewBox="0 0 {W:.3f} {H:.3f}" font-family="{FONT}">',
         '<defs><pattern id="hatch" patternUnits="userSpaceOnUse" width="1.6" height="1.6" patternTransform="rotate(45)">'
         f'<line x1="0" y1="0" x2="0" y2="1.6" stroke="{COL["ZONE"]}" stroke-width="0.25"/></pattern>'
         '<pattern id="hatchg" patternUnits="userSpaceOnUse" width="1.2" height="1.2" patternTransform="rotate(-45)">'
         f'<line x1="0" y1="0" x2="0" y2="1.2" stroke="{COL["GLUE"]}" stroke-width="0.3"/></pattern>'
         f'<marker id="ar" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{COL["GUIDE"]}"/></marker>'
         '</defs>', f'<rect width="{W:.3f}" height="{H:.3f}" fill="#ffffff"/>']
    def layer(name, body): o.append(f'<g id="{name}" inkscape:label="{name}" inkscape:groupmode="layer">{body}</g>')
    # bleed: a band 2×bleed wide on the cut contour, then paper over the inside, so only the outer half shows
    if bleed > 0 and d.style not in ("sleeve_grid",):
        layer("BLEED", "".join(f'<path d="{path_d(T(ol))}" fill="none" stroke="{COL["BLEED"]}" stroke-opacity="0.13" stroke-width="{2 * bleed:.3f}" stroke-linejoin="miter" stroke-miterlimit="3"/>' for i, ol in enumerate(d.outlines) if i not in d.nobleed)
              + "".join(f'<path d="{path_d(T(ol))}" fill="#ffffff"/>' for ol in d.outlines))
    layer("ZONES", "".join(f'<path d="{path_d(T(z))}" fill="url(#hatch)" stroke="{COL["ZONE"]}" stroke-width="0.15"/>' for z in d.zones))
    layer("GLUE", "".join(f'<path d="{path_d(T(g))}" fill="url(#hatchg)" stroke="{COL["GLUE"]}" stroke-width="0.2"/>' for g in d.glue))
    sf = []
    for n, poly, s, *_ in d.panels:
        if s:
            r = inset_rect(poly, s)
            if r: sf.append(f'<path d="{path_d(T(r))}" fill="none" stroke="{COL["SAFE"]}" stroke-width="0.2" stroke-dasharray="0.8 0.8"/>')
    layer("SAFE", "".join(sf))
    lab = []
    for n, poly, s, *_ in d.panels:
        xs, ys = [q[0] for q in T(poly)], [q[1] for q in T(poly)]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        size = clamp(min(max(xs) - min(xs), max(ys) - min(ys)) * 0.09, 2.0, 4.2)
        lab.append(f'<text x="{cx:.2f}" y="{cy:.2f}" font-size="{size:.2f}" text-anchor="middle" fill="{COL["INK"]}" fill-opacity="0.55">{esc(n)}</text>')
        lab.append(f'<text x="{cx:.2f}" y="{cy + size * 1.3:.2f}" font-size="{size * 0.6:.2f}" text-anchor="middle" fill="{COL["DIM"]}" fill-opacity="0.7">'
                   f'{max(xs) - min(xs):.1f} × {max(ys) - min(ys):.1f}</text>')
    for x, y, t, sz, c, a, rt in d.labels:
        x, y = x + ox, y + oy
        tr = f' transform="rotate({rt} {x:.2f} {y:.2f})"' if rt else ""
        lab.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{sz}" text-anchor="{a}" fill="{c}"{tr}>{esc(t)}</text>')
    for x, y, ang, t in d.arrows:
        x, y = x + ox, y + oy
        dx, dy = 9 * math.cos(rad(ang)), 9 * math.sin(rad(ang))
        lab.append(f'<line x1="{x - dx:.2f}" y1="{y - dy + 9:.2f}" x2="{x + dx:.2f}" y2="{y + dy + 9:.2f}" stroke="{COL["GUIDE"]}" stroke-width="0.35" marker-end="url(#ar)"/>')
        lab.append(f'<text x="{x:.2f}" y="{y + 9 + (12 if ang == 90 else 3.5):.2f}" font-size="1.9" text-anchor="middle" fill="{COL["GUIDE"]}">{esc(t)}</text>')
    layer("LABELS", "".join(lab))
    layer("GUIDE", "".join(f'<path d="{path_d(T(l), False)}" fill="none" stroke="{COL["GUIDE"]}" stroke-width="0.18" stroke-opacity="0.8"/>' for l in d.lines["GUIDE"])
          + "".join(f'<path d="{path_d(T(l), False)}" fill="none" stroke="{COL["ZONE"]}" stroke-width="0.25" stroke-dasharray="1 0.6"/>' for l in d.lines["ZONE"]))
    layer("CREASE", "".join(f'<path d="{path_d(T(l), False)}" fill="none" stroke="{COL["CREASE"]}" stroke-width="{sw}" stroke-dasharray="3 1.5"/>' for l in d.lines["CREASE"]))
    layer("PERF", "".join(f'<path d="{path_d(T(l), False)}" fill="none" stroke="{COL["PERF"]}" stroke-width="{sw}" stroke-dasharray="1 1"/>' for l in d.lines["PERF"]))
    layer("CUT", "".join(f'<path d="{path_d(T(ol))}" fill="none" stroke="{COL["CUT"]}" stroke-width="{sw}" stroke-linejoin="round"/>' for ol in d.outlines)
          + "".join(f'<path d="{path_d(T(h))}" fill="none" stroke="{COL["CUT"]}" stroke-width="{sw}"/>' for h in d.holes)
          + "".join(f'<path d="{path_d(T(l), False)}" fill="none" stroke="{COL["CUT"]}" stroke-width="{sw}"/>' for l in d.lines["CUT"]))
    # dimensions: overall flat size
    X0, Y0, X1, Y1 = x0 + ox, y0 + oy, x1 + ox, y1 + oy
    dm = (f'<line x1="{X0:.2f}" y1="{Y1 + bleed + 6:.2f}" x2="{X1:.2f}" y2="{Y1 + bleed + 6:.2f}" stroke="{COL["DIM"]}" stroke-width="0.2"/>'
          f'<line x1="{X0:.2f}" y1="{Y1 + bleed + 4:.2f}" x2="{X0:.2f}" y2="{Y1 + bleed + 8:.2f}" stroke="{COL["DIM"]}" stroke-width="0.2"/>'
          f'<line x1="{X1:.2f}" y1="{Y1 + bleed + 4:.2f}" x2="{X1:.2f}" y2="{Y1 + bleed + 8:.2f}" stroke="{COL["DIM"]}" stroke-width="0.2"/>'
          f'<text x="{(X0 + X1) / 2:.2f}" y="{Y1 + bleed + 10.5:.2f}" font-size="2.6" text-anchor="middle" fill="{COL["DIM"]}">{x1 - x0:.1f} mm flat</text>'
          f'<line x1="{X0 - bleed - 6:.2f}" y1="{Y0:.2f}" x2="{X0 - bleed - 6:.2f}" y2="{Y1:.2f}" stroke="{COL["DIM"]}" stroke-width="0.2"/>'
          f'<text x="{X0 - bleed - 8:.2f}" y="{(Y0 + Y1) / 2:.2f}" font-size="2.6" text-anchor="middle" fill="{COL["DIM"]}" transform="rotate(-90 {X0 - bleed - 8:.2f} {(Y0 + Y1) / 2:.2f})">{y1 - y0:.1f} mm</text>')
    layer("DIM", dm)
    # title block
    ty = H - tb + 4
    L_, W_, D_ = p.get("L", ""), p.get("W", ""), p.get("D", "")
    size = f"{L_} × {W_} × {D_} mm inside" if L_ != "" else ""
    board = (f"{p.get('flute')} flute" if p.get("flute") else f"caliper {p.get('caliper', '')} mm" if p.get("caliper") else "")
    keys = [("CUT", "solid"), ("CREASE", "3 1.5"), ("PERF", "1 1"), ("SAFE", "0.8 0.8"), ("GUIDE", "")]
    kx = 12
    kb = ""
    for k, da in keys:
        dash = f' stroke-dasharray="{da}"' if da and da != "solid" else ""
        kb += f'<line x1="{kx}" y1="{ty + 15}" x2="{kx + 8}" y2="{ty + 15}" stroke="{COL[k]}" stroke-width="0.4"{dash}/><text x="{kx + 10}" y="{ty + 15.8}" font-size="2.2" fill="{COL["INK"]}">{k}</text>'
        kx += 26
    kb += (f'<rect x="{kx}" y="{ty + 13}" width="8" height="4" fill="url(#hatchg)" stroke="{COL["GLUE"]}" stroke-width="0.2"/><text x="{kx + 10}" y="{ty + 15.8}" font-size="2.2" fill="{COL["INK"]}">GLUE / ZONE</text>'
           f'<rect x="{kx + 40}" y="{ty + 13}" width="8" height="4" fill="{COL["BLEED"]}" fill-opacity="0.13"/><text x="{kx + 50}" y="{ty + 15.8}" font-size="2.2" fill="{COL["INK"]}">BLEED {bleed:g} mm</text>')
    o.append(f'<g id="TITLE"><line x1="10" y1="{ty - 2}" x2="{W - 10:.2f}" y2="{ty - 2}" stroke="{COL["INK"]}" stroke-width="0.3"/>'
             f'<text x="12" y="{ty + 5}" font-size="4" fill="{COL["INK"]}">{esc(d.name)}</text>'
             f'<text x="12" y="{ty + 10}" font-size="2.4" fill="{COL["DIM"]}">{esc(TITLES[d.style])} · {esc(size)} {esc(board)} · flat {x1 - x0:.1f} × {y1 - y0:.1f} mm</text>'
             f'{kb}<text x="12" y="{ty + 23}" font-size="2.1" fill="#C8102E">CONCEPT DIELINE · not for tooling · the converter\'s CAD dieline supersedes this drawing</text></g>')
    o.append("</svg>")
    svg = "".join(o)
    os.makedirs(out, exist_ok=True)
    base = os.path.join(out, d.name)
    open(base + ".svg", "w").write(svg)
    try:
        import cairosvg
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=base + ".pdf")
        cairosvg.svg2png(bytestring=svg.encode(), write_to=base + ".png", output_width=int(min(3000, W * 8)))
    except Exception as e:                            # SVG + DXF still ship
        d.warn.append(f"PDF/PNG skipped ({e.__class__.__name__}): pip install CairoSVG")
    write_dxf(d, base + ".dxf")
    write_spec(d, base + "_spec.md", bbox)
    return base


def write_dxf(d, path):
    """AutoCAD R12 ASCII: LINE entities on CUT / CREASE / PERF / GLUE layers, mm, y flipped (DXF is y-up)."""
    ent = []
    def seg(layer, a, b): ent.append(f"0\nLINE\n8\n{layer}\n10\n{a[0]:.4f}\n20\n{-a[1]:.4f}\n30\n0.0\n11\n{b[0]:.4f}\n21\n{-b[1]:.4f}\n31\n0.0")
    def poly(layer, pts, closed):
        q = pts + ([pts[0]] if closed else [])
        for a, b in zip(q, q[1:]): seg(layer, a, b)
    for ol in d.outlines: poly("CUT", ol, True)
    for h in d.holes: poly("CUT", h, True)
    for l in d.lines["CUT"]: poly("CUT", l, False)
    for l in d.lines["CREASE"]: poly("CREASE", l, False)
    for l in d.lines["PERF"]: poly("PERF", l, False)
    for g in d.glue: poly("GLUE", g, True)
    layers = {"CUT": 1, "CREASE": 5, "PERF": 30, "GLUE": 8}
    tbl = "".join(f"0\nLAYER\n2\n{n}\n70\n0\n62\n{c}\n6\nCONTINUOUS\n" for n, c in layers.items())
    open(path, "w").write("0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n0\nENDSEC\n"
                          f"0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n{len(layers)}\n{tbl}0\nENDTAB\n0\nENDSEC\n"
                          "0\nSECTION\n2\nENTITIES\n" + "\n".join(ent) + "\n0\nENDSEC\n0\nEOF\n")


def nest(fw, fh, sheet, gutter, grip):
    sw, sh = sheet
    best = None
    for w, h, rot in ((fw, fh, False), (fh, fw, True)):
        nx = int((sw + gutter) // (w + gutter)); ny = int((sh - grip + gutter) // (h + gutter))
        if best is None or nx * ny > best[0]: best = (nx * ny, nx, ny, rot)
    return best


def write_spec(d, path, bbox):
    p = d.p
    x0, y0, x1, y1 = bbox
    fw, fh = x1 - x0, y1 - y0
    board = sum(area(o) for o in d.outlines) - sum(area(h) for h in d.holes)
    cut = sum(length(o, True) for o in d.outlines) + sum(length(h, True) for h in d.holes) + sum(length(l) for l in d.lines["CUT"])
    crease = sum(length(l) for l in d.lines["CREASE"])
    sheet = p.get("sheet", [720, 1020] if d.style in ("rte", "ste", "sleeve", "tray", "pillow") else [1600, 2400] if d.style in ("rsc", "hsc", "mailer") else None)
    rows = [("Style", TITLES[d.style]), ("Inputs", ", ".join(f"{k}={v}" for k, v in p.items() if k not in ("name", "style", "notes", "art", "_base_dir", "_figma")))]
    rows += [("Flat size", f"{fw:.1f} × {fh:.1f} mm"), ("Board area (one-up)", f"{board / 1e6:.4f} m²  ({board / 100:.0f} cm²)"),
             ("Cut rule", f"{cut:.0f} mm"), ("Crease rule", f"{crease:.0f} mm"), ("Bleed / safe", f"{p.get('bleed', 3)} / {p.get('safe', 3)} mm")]
    if sheet and d.style not in ("cone_label", "wrap_label", "pouch", "sleeve_grid", "flowwrap"):
        n = nest(fw, fh, sheet, float(p.get("gutter", 6)), float(p.get("gripper", 12)))
        rows.append(("Rough nesting", f"{n[0]}-up on {sheet[0]}×{sheet[1]} ({n[1]}×{n[2]}{', rotated' if n[3] else ''}). "
                     "Simple grid only: interlocked or tumbled nests often fit more. The converter's step-and-repeat decides."))
    rows += list(d.facts.items())
    md = [f"# {d.name}: concept dieline spec", "", "| | |", "|---|---|"] + [f"| {k} | {esc(v)} |" for k, v in rows]
    if d.warn: md += ["", "## Warnings"] + [f"- {w}" for w in d.warn]
    md += ["", "## Notes"] + [f"- {n}" for n in d.notes + [str(x) for x in p.get("notes", [])]]
    md += ["", "## Before this goes anywhere",
           "- [ ] Converter's own dieline requested (CAD: CF2 / DXF / ARD / PDF) for the actual board and machine",
           "- [ ] White sample (unprinted, cut and creased on the real board) built and filled with the real product",
           "- [ ] Grain / flute direction agreed with the converter", "- [ ] Artwork placed on the converter's dieline, never on this one",
           "", "Files: `.svg` (layers), `.pdf` (preview), `.png`, `.dxf` (CUT/CREASE/PERF/GLUE for CAD), this spec."]
    open(path, "w").write("\n".join(md) + "\n")


def build(job, out):
    st = job["style"]
    if st not in STYLES: sys.exit(f"Unknown style '{st}'. Styles: {', '.join(STYLES)}")
    d = Drawing(job.get("name", st), st, job)
    STYLES[st](d, job)
    if job.get("art"):
        import art as _art
        _art.collect_windows(d)        # board windows become real cuts before the dieline is drawn
    base = render(d, out)
    if job.get("art"):
        import art as _art
        _art.render_art(d, out)
    if job.get("_figma"):
        import figma as _fig
        fp, n = _fig.plan(d, out)
        print(f"  → Figma plan: {os.path.relpath(fp)} ({n} talk-to-figma steps)")
    for w in d.warn: print(f"  ! {d.name}: {w}")
    return base


def contact_sheet(pngs, path, cols=3, cell=900):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return
    ims = [Image.open(p).convert("RGB") for p in pngs if os.path.exists(p)]
    if not ims: return
    rows = math.ceil(len(ims) / cols)
    sheet = Image.new("RGB", (cols * cell, rows * cell), "white")
    for i, im in enumerate(ims):
        im.thumbnail((cell - 30, cell - 30))
        x, y = (i % cols) * cell + (cell - im.width) // 2, (i // cols) * cell + (cell - im.height) // 2
        sheet.paste(im, (x, y))
        ImageDraw.Draw(sheet).rectangle([(i % cols) * cell + 4, (i // cols) * cell + 4, (i % cols + 1) * cell - 4, (i // cols + 1) * cell - 4], outline=(220, 220, 220))
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", nargs="?")
    ap.add_argument("--only"); ap.add_argument("--out")
    ap.add_argument("--style"); ap.add_argument("--name")
    for k in ("L", "W", "D", "caliper", "bleed", "safe"): ap.add_argument(f"--{k}", type=float)
    ap.add_argument("--flute")
    ap.add_argument("--figma", action="store_true", help="also write <name>_figma.json for claude-talk-to-figma-mcp")
    a = ap.parse_args()
    if a.config:
        cfg = json.load(open(a.config))
        jobs = cfg.get("jobs", [cfg])
        defaults = {k: v for k, v in cfg.items() if k not in ("jobs", "out")}
        out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.config)), cfg.get("out", "../exports/dielines"))
    elif a.style:
        jobs = [{k: v for k, v in vars(a).items() if v is not None and k not in ("config", "only", "out")}]
        defaults, out = {}, a.out or "exports/dielines"
    else:
        ap.print_help(); return
    built = []
    for j in jobs:
        job = {**defaults, **j}
        if a.figma: job["_figma"] = True
        job.setdefault("_base_dir", os.path.dirname(os.path.abspath(a.config)) if a.config else os.getcwd())
        if a.only and job.get("name") != a.only: continue
        base = build(job, out)
        built.append(base + ".png")
        if job.get("art"): built.append(base + "_art.png")
        print(f"✓ {os.path.relpath(base)}  (.svg .pdf .png .dxf _spec.md)")
    if len(built) > 1 and not a.only: contact_sheet(built, os.path.join(out, "sheet.png")); print(f"✓ {os.path.relpath(os.path.join(out, 'sheet.png'))}")

if __name__ == "__main__":
    main()
