"""Draft artwork on a concept dieline: MVP pack designs placed panel by panel, the right way up on every flap.

Called by dieline.py when a job has an "art" block (see references/design_on_dieline.md and templates/dieline.json):

    "art": {
      "bg": "light", "ink": "base", "accent": "accent",          # brand tokens (nazar-core brand.json) or hex
      "pattern": {"type": "stripes", "angle": 45, "pitch": 9, "width": 3, "color": "accent"},   # optional, runs across folds
      "panels": {                                                  # keys match panel names; "Side" matches "Side A"/"Side B"
        "Front": {"bg": "base", "blocks": [
            {"type": "logo", "src": "assets/logo.svg", "x": 0.5, "y": 0.18, "w": 0.6},
            {"type": "text", "text": "Brand", "x": 0.5, "y": 0.42, "size": 11, "font": "display", "color": "light", "anchor": "middle"},
            {"type": "band", "y": 0.78, "h": 0.08, "fill": "accent", "full": true},
            {"type": "text", "text": "250 g", "x": 0.5, "y": 0.95, "size": 3, "role": "netqty", "anchor": "middle"}]},
        "Back": {"blocks": [{"type": "para", "text": "...", "x": 0, "y": 0.1, "w": 1, "size": 2.2},
                            {"type": "placeholder", "label": "Ingredients (client copy)", "x": 0, "y": 0.5, "w": 1, "h": 0.2},
                            {"type": "barcode", "x": 0.5, "y": 0.85, "mag": 1.0}]}}
    }

Coordinates are fractions of the panel's SAFE box in the panel's own upright frame (x right, y down, art reading up).
Text sizes are in mm (cap-to-descender font size); 1 mm ≈ 2.83 pt. Writes <name>_art.svg/.pdf/.png, <name>_box.svg/.png
(an oblique technical view of the folded pack, where the style allows) and <name>_art_qa.md with automatic draft checks.
"""
import base64, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "nazar-core", "engine")))
try:
    import lib                                    # outlined type + brand tokens from nazar-core
    HAVE_LIB = True
except Exception as e:                            # still draws, with system-font <text>
    lib, HAVE_LIB = None, False
    LIB_ERR = e

from dieline import COL, path_d, rect_poly, esc, clamp

# faces for the oblique view: (front, right side, top). None = no top face drawn.
BOXVIEW = {"rte": ("Front", "Side B", "Top closure"), "ste": ("Front", "Side B", "Top closure"), "sleeve": ("Front", "Side B", None),
           "rsc": ("Front (L)", "Side (W)", None), "hsc": ("Front (L)", "Side (W)", None),
           "mailer": ("Lid front", "Side wall", "Lid (outside)"), "tray": ("Front wall", "End wall", None)}
PRINCIPAL = ("Front", "Front (L)", "Lid (outside)", "Front wall", "Label", "FRONT")


def token(v, default="#1A1A1A"):
    if not v: return default
    if isinstance(v, str) and v.startswith("#"): return v
    if HAVE_LIB and v in lib.C: return lib.C[v]
    return {"base": "#1B1A17", "light": "#EFE9DF", "accent": "#E8572A", "secondary": "#A39C90"}.get(v, default)

def contrast(a, b):
    def lum(h):
        r, g, b_ = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b_)
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

FONTKEY = {"display": "display", "text": "text", "medium": "text-m", "light": "text-l", "label": "label", "mono": "label"}

def tw(chars, size, font, track=0):
    """Text width in mm: exact via harfbuzz when the core engine is present, estimated otherwise."""
    if HAVE_LIB:
        try: return lib.width(FONTKEY.get(font, font), chars, size, track)
        except Exception: pass
    return len(chars) * size * (0.42 if font == "display" else 0.55)

def text_svg(chars, x, y, size, font, fill, anchor="start", track=0, op=1):
    if HAVE_LIB:
        try: return lib.text(chars, x, y, size, FONTKEY.get(font, font), fill, op, track, anchor)
        except Exception: pass
    fam = "Anton, Impact, sans-serif" if font == "display" else "Space Grotesk, Helvetica, sans-serif"
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size:.2f}" font-family="{fam}" text-anchor="{anchor}" fill="{fill}" fill-opacity="{op}">{esc(chars)}</text>'

def wrap(chars, size, maxw, font, track=0):
    out = []
    for para in str(chars).split("\n"):
        cur = ""
        for word in para.split(" "):
            t = (cur + " " + word).strip()
            if cur and tw(t, size, font, track) > maxw: out.append(cur); cur = word
            else: cur = t
        out.append(cur)
    return out

def image_href(src, base_dir):
    path = src if os.path.isabs(src) else os.path.normpath(os.path.join(base_dir, src))
    data = open(path, "rb").read()
    if path.lower().endswith(".svg"):
        m = re.search(rb'viewBox="\s*([\d.\-]+)[ ,]+([\d.\-]+)[ ,]+([\d.]+)[ ,]+([\d.]+)', data)
        if m: ar = float(m.group(4)) / float(m.group(3))
        else:
            w = re.search(rb'\bwidth="([\d.]+)', data); h = re.search(rb'\bheight="([\d.]+)', data)
            ar = float(h.group(1)) / float(w.group(1)) if w and h else 1.0
        return "data:image/svg+xml;base64," + base64.b64encode(data).decode(), ar
    from PIL import Image
    im = Image.open(path)
    mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(data).decode(), im.height / im.width


def panel_frame(poly, up):
    """Local upright frame for an axis-aligned panel: returns (transform, pw, ph)."""
    ux, uy = up
    th = math.degrees(math.atan2(ux, -uy))
    lx = (math.cos(math.radians(th)), math.sin(math.radians(th)))
    ly = (-math.sin(math.radians(th)), math.cos(math.radians(th)))
    xs, ys = [q[0] for q in poly], [q[1] for q in poly]
    corners = [(x, y) for x in (min(xs), max(xs)) for y in (min(ys), max(ys))]
    o = min(corners, key=lambda c: (round(c[0] * lx[0] + c[1] * lx[1], 6) + round(c[0] * ly[0] + c[1] * ly[1], 6)))
    pw = abs((max(xs) - min(xs)) * lx[0]) + abs((max(ys) - min(ys)) * lx[1])
    ph = abs((max(xs) - min(xs)) * ly[0]) + abs((max(ys) - min(ys)) * ly[1])
    return f"translate({o[0]:.3f},{o[1]:.3f}) rotate({th:.1f})", pw, ph


def match_panel(name, panels_cfg):
    if name in panels_cfg: return panels_cfg[name]
    for k, v in panels_cfg.items():
        if name.startswith(k) or name.split(" ")[0] == k: return v
    return None


def frame_axes(poly, up):
    """(origin, local x axis, local y axis, pw, ph) for an axis-aligned panel in its art-up frame."""
    ux, uy = up
    th = math.atan2(ux, -uy)
    lx, ly = (math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))
    xs, ys = [q[0] for q in poly], [q[1] for q in poly]
    corners = [(x, y) for x in (min(xs), max(xs)) for y in (min(ys), max(ys))]
    o = min(corners, key=lambda c: round(c[0] * lx[0] + c[1] * lx[1], 6) + round(c[0] * ly[0] + c[1] * ly[1], 6))
    pw = abs((max(xs) - min(xs)) * lx[0]) + abs((max(ys) - min(ys)) * lx[1])
    ph = abs((max(xs) - min(xs)) * ly[0]) + abs((max(ys) - min(ys)) * ly[1])
    return o, lx, ly, pw, ph


def shape_poly(x, y, w, h, shape="rect", r=0.0, n=10):
    """Window outline in panel-local coordinates."""
    if shape == "circle":
        return [(x + w / 2 + w / 2 * math.cos(2 * math.pi * i / 72), y + h / 2 + h / 2 * math.sin(2 * math.pi * i / 72)) for i in range(72)]
    if shape == "pill": r = min(w, h) / 2
    r = min(r, w / 2, h / 2)
    if r <= 0: return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        pts += [(cx + r * math.cos(math.radians(a0 + 90 * i / n)), cy + r * math.sin(math.radians(a0 + 90 * i / n))) for i in range(n + 1)]
    return pts


SUBSTRATES = ("board", "clear", "metallised", "white", "kraft")

def collect_windows(d):
    """Pre-pass: turn every "window" block into a global polygon. On board it becomes a real CUT (and a film patch);
    on clear or metallised film it's an unprinted, un-whited area. Findings go to d.art_qa."""
    art = d.p["art"]
    sub = art.get("substrate", "clear" if d.style in ("pouch", "flowwrap") else "board")
    d.art_substrate, d.windows, d.art_qa = sub, [], []
    pcfg = art.get("panels", {})
    patch = float(art.get("patch_margin", 12))
    zones = [(min(q[0] for q in z), min(q[1] for q in z), max(q[0] for q in z), max(q[1] for q in z)) for z in d.zones]
    for n, poly, sf, *up in d.panels:
        if n.startswith("Back-half"): continue
        cfg = match_panel(n, pcfg)
        if not cfg: continue
        up = up[0] if up else (0, -1)
        o, lx, ly, pw, ph = frame_axes(poly, up)
        sfe = sf if sf is not None else float(d.p.get("safe", 3))
        sw, sh = pw - 2 * sfe, ph - 2 * sfe
        for b in cfg.get("blocks", []):
            if b.get("type") != "window": continue
            x, y = sfe + b.get("x", 0.25) * sw, sfe + b.get("y", 0.3) * sh
            w, h = b.get("w", 0.5) * sw, b.get("h", 0.3) * sh
            loc = shape_poly(x, y, w, h, b.get("shape", "round"), float(b.get("r", 4)))
            glob = [(o[0] + u * lx[0] + v * ly[0], o[1] + u * lx[1] + v * ly[1]) for u, v in loc]
            gx0, gy0 = min(q[0] for q in glob), min(q[1] for q in glob)
            gx1, gy1 = max(q[0] for q in glob), max(q[1] for q in glob)
            win = {"panel": n, "local": loc, "poly": glob, "bbox": (gx0, gy0, gx1, gy1), "label": b.get("label", "WINDOW")}
            d.windows.append(win)
            qa = d.art_qa
            if sub == "board":
                d.holes.append(glob)
                win["patch"] = (gx0 - patch, gy0 - patch, gx1 + patch, gy1 + patch)
                edge = min(x, y, pw - (x + w), ph - (y + h))
                if edge < 0: qa.append(("P1", n, "window crosses a crease or cut: keep it inside one panel"))
                elif edge < 15: qa.append(("P2", n, f"window only {edge:.1f} mm from a crease/cut: converters want ~10–15 mm for the film patch's glue and board strength"))
                if edge >= 0 and edge < patch: qa.append(("P2", n, f"the film patch ({patch:g} mm margin) would run into a crease or the glue flap: shrink the window or the margin"))
                if w * h > 0.5 * pw * ph: qa.append(("P3", n, "window over half the panel: the panel loses stiffness (bulging, crush on shelf); test a white sample"))
            elif sub == "white":
                qa.append(("P1", n, "window on an opaque white film is impossible: switch to clear film with a white underlay, or drop the window"))
            else:
                if sub == "metallised":
                    qa.append(("P2", n, "metallised film: a clear window needs a non-metallised area in the laminate (registered metallisation or a clear-film window). Ask the converter; it costs more"))
                for zx0, zy0, zx1, zy1 in zones:
                    if gx0 < zx1 and gx1 > zx0 and gy0 < zy1 and gy1 > zy0:
                        qa.append(("P1", n, "window runs into a seal or zipper zone: seals distort and may not seal through clear areas reliably")); break
                if d.style == "pouch" and b.get("y", 0.3) < 0.35:
                    qa.append(("P3", n, "high window: granular and loose products settle, so the top of the window will show headspace. Place it where the product sits after transit"))
            if art.get("light_sensitive"):
                qa.append(("P2", n, "light-sensitive product (fats, oils, vitamins, colours): a window lets light in and shortens shelf life. Confirm with the food technologist and shelf-life tests"))


class PanelArt:
    """Builds one panel's content in its upright frame (0..pw, 0..ph) and records QA findings."""
    def __init__(self, name, pw, ph, safe, cfg, art, base_dir, qa):
        self.n, self.pw, self.ph, self.s, self.cfg, self.art, self.dir, self.qa = name, pw, ph, safe, cfg or {}, art, base_dir, qa
        self.bg = token(self.cfg.get("bg") or art.get("bg"), "#FFFFFF")
        self.ink = token(art.get("ink"), "#1A1A1A")
        self.sx0, self.sy0 = safe, safe
        self.sw, self.sh = max(pw - 2 * safe, 1), max(ph - 2 * safe, 1)
        self.fills = []                           # (x0, y0, x1, y1, colour) in paint order, for real contrast checks

    def under(self, x, y):
        """Colour actually behind a point: the last fill painted there, else the panel background."""
        for x0, y0, x1, y1, c in reversed(self.fills):
            if x0 <= x <= x1 and y0 <= y <= y1: return c
        return self.bg

    def X(self, f): return self.sx0 + f * self.sw
    def Y(self, f): return self.sy0 + f * self.sh

    def flag(self, level, msg): self.qa.append((level, self.n, msg))

    def check_box(self, x0, y0, x1, y1, what):
        e = 0.3
        if x0 < self.sx0 - e or y0 < self.sy0 - e or x1 > self.sx0 + self.sw + e or y1 > self.sy0 + self.sh + e:
            self.flag("P2", f"{what} crosses the safe area (3–5 mm from folds and cuts)")

    def svg(self, background=True):
        o = []
        if background and self.cfg.get("bg"):
            o.append(f'<rect x="0" y="0" width="{self.pw:.3f}" height="{self.ph:.3f}" fill="{self.bg}"/>')
        for b in self.cfg.get("blocks", []):
            t = b.get("type", "text")
            fn = getattr(self, "b_" + t, None)
            if fn: o.append(fn(b))
            else: self.flag("P3", f"unknown block type '{t}'")
        return "".join(o)

    def colour(self, b, key="color", default=None):
        return token(b.get(key), default or self.ink)

    def b_text(self, b):
        size, font = float(b.get("size", 4)), b.get("font", "text")
        col = self.colour(b)
        x, y, anc, track = self.X(b.get("x", 0)), self.Y(b.get("y", 0)), b.get("anchor", "start"), float(b.get("track", 0))
        w = tw(b["text"], size, font, track)
        x0 = x - (w if anc == "end" else w / 2 if anc == "middle" else 0)
        self.check_box(x0, y - size * 0.75, x0 + w, y + size * 0.25, f"'{b['text'][:24]}'")
        pt = size * 2.835
        if pt < 5: self.flag("P1", f"'{b['text'][:24]}' is {pt:.1f} pt: below the ~5–6 pt print minimum")
        elif pt < 6 and font not in ("display",): self.flag("P2", f"'{b['text'][:24]}' is {pt:.1f} pt: check the printer's minimum")
        behind = self.under(x0 + w / 2, y - size * 0.3)
        if behind.startswith("url("): behind = "#FFFFFF"
        cr = contrast(col, behind)
        need = 3.0 if size >= 4 else 4.5
        if cr < need: self.flag("P1" if cr < 2 else "P2", f"'{b['text'][:24]}' contrast {cr:.2f}:1 on its background (aim ≥ {need}:1)")
        if b.get("role") == "netqty" and b.get("y", 0) < 0.7:
            self.flag("P2", "net quantity is not in the bottom 30% of the principal display panel (US FDA rule; check your market)")
        return text_svg(b["text"], x, y, size, font, col, anc, track, b.get("opacity", 1))

    def b_para(self, b):
        size, font = float(b.get("size", 2.4)), b.get("font", "text")
        col, lead = self.colour(b), float(b.get("lead", 1.32))
        x, y, w = self.X(b.get("x", 0)), self.Y(b.get("y", 0)), float(b.get("w", 1)) * self.sw
        rows = wrap(b["text"], size, w, font)
        bottom = y + (len(rows) - 1) * size * lead
        if bottom > self.sy0 + self.sh: self.flag("P1", f"paragraph overflows the panel by {bottom - self.sy0 - self.sh:.1f} mm: cut copy or enlarge the panel")
        if size * 2.835 < 5.5: self.flag("P2", f"body copy at {size * 2.835:.1f} pt; most markets and printers want ≥ 6 pt (bold sans for tiny legal)")
        behind = self.under(x + w / 2, y)
        behind = "#FFFFFF" if behind.startswith("url(") else behind
        if contrast(col, behind) < 4.5: self.flag("P2", f"body copy contrast {contrast(col, behind):.2f}:1 (aim ≥ 4.5:1)")
        return "".join(text_svg(r, x, y + i * size * lead, size, font, col) for i, r in enumerate(rows))

    def b_band(self, b):
        if b.get("full", True):     # full bands run edge to edge (and into bleed), measured on the whole panel
            x0, w, y, h = -0.01, self.pw + 0.02, float(b.get("y", 0)) * self.ph, float(b.get("h", 0.1)) * self.ph
        else:
            x0, w = self.X(b.get("x", 0)), float(b.get("w", 1)) * self.sw
            y, h = self.Y(b.get("y", 0)), float(b.get("h", 0.1)) * self.sh
        c = self.colour(b, "fill", token("accent")); self.fills.append((x0, y, x0 + w, y + h, c))
        return f'<rect x="{x0:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="{c}"/>'

    def b_rect(self, b):
        x, y = self.X(b.get("x", 0)), self.Y(b.get("y", 0))
        w, h = float(b.get("w", 0.2)) * self.sw, float(b.get("h", 0.2)) * self.sh
        c = self.colour(b, "fill", token("accent")); self.fills.append((x, y, x + w, y + h, c))
        return f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" rx="{b.get("r", 0)}" fill="{c}"/>'

    def b_circle(self, b):
        cx, cy, r, c = self.X(b.get("x", 0.5)), self.Y(b.get("y", 0.5)), float(b.get("r", 5)), self.colour(b, "fill", token("accent"))
        self.fills.append((cx - r * 0.7, cy - r * 0.7, cx + r * 0.7, cy + r * 0.7, c))
        return f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="{c}"/>'

    def b_rule(self, b):
        y = self.Y(b.get("y", 0.5)); x0, x1 = self.X(b.get("x", 0)), self.X(b.get("x", 0) + b.get("w", 1))
        sw = float(b.get("weight", 0.3))
        if sw < 0.1: self.flag("P2", "rule thinner than ~0.25 pt will break up in print")
        return f'<line x1="{x0:.3f}" y1="{y:.3f}" x2="{x1:.3f}" y2="{y:.3f}" stroke="{self.colour(b)}" stroke-width="{sw}"/>'

    def b_logo(self, b):
        try: href, ar = image_href(b["src"], self.dir)
        except Exception as e:
            self.flag("P1", f"logo file not found ({b.get('src')}): use the client's exact artwork, never a redraw")
            return self.b_placeholder({"label": "LOGO (client file)", "x": b.get("x", 0.5) - b.get("w", 0.5) / 2, "y": b.get("y", 0.2) - 0.06, "w": b.get("w", 0.5), "h": 0.12})
        w = float(b.get("w", 0.5)) * self.sw; h = w * ar
        x = self.X(b.get("x", 0.5)) - (w / 2 if b.get("anchor", "middle") == "middle" else 0)
        y = self.Y(b.get("y", 0.2)) - (h / 2 if b.get("valign", "middle") == "middle" else 0)
        self.check_box(x, y, x + w, y + h, "logo")
        if w < 10: self.flag("P2", f"logo only {w:.1f} mm wide: check the mark's minimum size in its guidelines")
        return f'<image x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" href="{href}" preserveAspectRatio="xMidYMid meet"/>'

    def b_window(self, b): return ""          # drawn on top globally (see collect_windows)

    def b_placeholder(self, b):
        x, y = self.X(b.get("x", 0)), self.Y(b.get("y", 0))
        w, h = float(b.get("w", 1)) * self.sw, float(b.get("h", 0.2)) * self.sh
        self.check_box(x, y, x + w, y + h, f"placeholder '{b.get('label', '')[:20]}'")
        sz = clamp(min(w, h) * 0.12, 1.6, 3.2)
        return (f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="#ffffff" fill-opacity="0.85" stroke="{COL["DIM"]}" stroke-width="0.2" stroke-dasharray="1 0.7"/>'
                f'<line x1="{x:.3f}" y1="{y:.3f}" x2="{x + w:.3f}" y2="{y + h:.3f}" stroke="{COL["DIM"]}" stroke-width="0.1"/>'
                f'<line x1="{x + w:.3f}" y1="{y:.3f}" x2="{x:.3f}" y2="{y + h:.3f}" stroke="{COL["DIM"]}" stroke-width="0.1"/>'
                + text_svg(b.get("label", "client copy"), x + w / 2, y + h / 2 + sz * 0.35, sz, "label", COL["DIM"], "middle"))

    def b_barcode(self, b):
        mag = float(b.get("mag", 1.0))
        w, h = 37.29 * mag, 25.93 * mag                    # GS1 EAN-13 at 100% incl. quiet zones
        x, y = self.X(b.get("x", 0.5)) - w / 2, self.Y(b.get("y", 0.8)) - h / 2
        if mag < 0.8: self.flag("P1", f"barcode at {mag:.0%}: below the 80% minimum for retail EAN-13")
        if w > self.sw + 0.1 or h > self.sh + 0.1: self.flag("P1", "barcode doesn't fit this panel's safe area: move it to a bigger flat panel")
        else: self.check_box(x, y, x + w, y + h, "barcode")
        bars, bx = [], x + 3.63 * mag
        import random
        rnd = random.Random(7)
        while bx < x + w - 2.31 * mag:
            bw = rnd.choice((0.33, 0.33, 0.66, 0.99)) * mag
            bars.append(f'<rect x="{bx:.3f}" y="{y + 1:.3f}" width="{bw:.3f}" height="{h - 5 * mag:.3f}" fill="#000"/>'); bx += bw + rnd.choice((0.33, 0.66)) * mag
        return (f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="#ffffff"/>' + "".join(bars)
                + text_svg(f"EAN-13 PLACEHOLDER · {mag:.0%}", x + w / 2, y + h - 1.2 * mag, 1.8 * mag, "label", "#000", "middle"))


def global_pattern(d, art):
    pat = art.get("pattern")
    if not pat: return ""
    x0, y0, x1, y1 = d.bbox()
    col, op = token(pat.get("color", "accent")), pat.get("opacity", 1)
    cx, cy, R = (x0 + x1) / 2, (y0 + y1) / 2, math.hypot(x1 - x0, y1 - y0) / 2 + 10
    out = []
    if pat.get("type", "stripes") == "stripes":
        pitch, w = float(pat.get("pitch", 9)), float(pat.get("width", 3))
        k = -R
        while k < R:
            out.append(f'<rect x="{cx - R:.2f}" y="{cy + k:.2f}" width="{2 * R:.2f}" height="{w:.2f}" fill="{col}" fill-opacity="{op}"/>'); k += pitch
        return f'<g transform="rotate({pat.get("angle", 45)} {cx:.2f} {cy:.2f})">{"".join(out)}</g>'
    if pat["type"] == "dots":
        pitch, r = float(pat.get("pitch", 8)), float(pat.get("r", 1.2))
        yy = y0 - 5
        while yy < y1 + 5:
            xx = x0 - 5
            while xx < x1 + 5:
                out.append(f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="{r}" fill="{col}" fill-opacity="{op}"/>'); xx += pitch
            yy += pitch
        return "".join(out)
    return ""


def render_art(d, out):
    from dieline import Drawing  # noqa
    art = d.p["art"]
    base_dir = d.p.get("_base_dir", os.getcwd())
    bleed, safe_def = float(d.p.get("bleed", 3)), float(d.p.get("safe", 3))
    qa = list(getattr(d, "art_qa", []))
    if not HAVE_LIB: qa.append(("P3", "engine", f"nazar-core lib not loaded ({LIB_ERR.__class__.__name__}); system fonts used, widths estimated"))
    x0, y0, x1, y1 = d.bbox()
    m, tb = 18 + bleed, 26
    W, H = (x1 - x0) + 2 * m, (y1 - y0) + 2 * m + tb
    ox, oy = m - x0, m - y0
    bg = "url(#chk)" if art.get("bg") == "clear" else token(art.get("bg"), "#FFFFFF")   # clear film: unprinted = see-through
    clip = "".join(f'<path d="{path_d(o)}"/>' for o in d.outlines)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W:.2f}mm" height="{H:.2f}mm" viewBox="0 0 {W:.3f} {H:.3f}">',
         f'<defs><clipPath id="die">{clip}</clipPath>'
         f'<pattern id="kh" patternUnits="userSpaceOnUse" width="1.4" height="1.4" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.4" stroke="#9a9a9a" stroke-width="0.3"/></pattern>'
         '<pattern id="chk" patternUnits="userSpaceOnUse" width="4" height="4"><rect width="4" height="4" fill="#ffffff"/>'
         '<rect width="2" height="2" fill="#d9d9d9"/><rect x="2" y="2" width="2" height="2" fill="#d9d9d9"/></pattern></defs>',
         f'<rect width="{W:.3f}" height="{H:.3f}" fill="#F4F4F2"/>', f'<g transform="translate({ox:.3f},{oy:.3f})">']
    # base colour, with bleed: a 2×bleed stroke around every outline plus the fill
    stroke = "none" if bg.startswith("url(") else bg          # cairo can't stroke with a pattern
    s.append("".join(f'<path d="{path_d(o)}" fill="{bg}" stroke="{stroke}" stroke-width="{2 * bleed:.3f}" stroke-linejoin="miter"/>' for o in d.outlines))
    s.append(f'<g clip-path="url(#die)">{global_pattern(d, art)}')
    faces = {}
    pcfg = art.get("panels", {})
    seen_principal = False
    for n, poly, sf, *up in d.panels:
        if n.startswith("Back-half"): continue      # the flow-wrap back is drawn once, split across the web (below)
        up = up[0] if up else (0, -1)
        tr, pw, ph = panel_frame(poly, up)
        cfg = match_panel(n, pcfg) or art.get("default")
        pa = PanelArt(n, pw, ph, sf if sf is not None else safe_def, cfg, art, base_dir, qa)
        body = pa.svg()
        if cfg and (n in PRINCIPAL or n.split(" ")[0] in ("Front", "FRONT", "Label")): seen_principal = True
        s.append(f'<g transform="{tr}">{body}</g>')
        faces.setdefault(n, (pa, pw, ph))
    sb = getattr(d, "split_back", None)
    if sb and match_panel("Back", pcfg):
        pa = PanelArt("Back", sb["W"], sb["h"], safe_def, match_panel("Back", pcfg), art, base_dir, qa)
        body = pa.svg()
        for b in (match_panel("Back", pcfg) or {}).get("blocks", []):
            if b.get("type") in ("text", "barcode", "logo", "para") and abs(pa.X(b.get("x", 0)) - sb["W"] / 2) < sb["fin"] + 2:
                qa.append(("P2", "Back", f"{b.get('type')} sits on the back's centre line, under the folded fin seal: move it off-centre"))
            if b.get("type") == "window": qa.append(("P3", "Back", "windows on a split flow-wrap back aren't drawn by the engine: place them on the FRONT"))
        H_ = sb["h"]
        for x0, shift in ((sb["BR"], 0), (sb["BL"], sb["W"] / 2)):
            cid = f"sb{int(x0 * 10)}"
            s.append(f'<clipPath id="{cid}"><rect x="{x0:.3f}" y="{sb["y0"]:.3f}" width="{sb["W"] / 2:.3f}" height="{H_:.3f}"/></clipPath>'
                     f'<g clip-path="url(#{cid})"><g transform="translate({x0 - shift:.3f},{sb["y0"]:.3f})">{body}</g></g>')
    s.append("</g>")
    s.append(windows_svg(d, art))
    for k, v in pcfg.items():                  # the glue flap isn't a print panel: any art aimed at it is an error
        if "glue" in k.lower() and (v or {}).get("blocks"):
            qa.append(("P1", k, "artwork aimed at the glue flap: glue areas take no ink or varnish (not drawn)"))
    # knockouts and the dieline on top
    s.append("".join(f'<path d="{path_d(g)}" fill="#ffffff"/><path d="{path_d(g)}" fill="url(#kh)"/>' for g in d.glue))
    s.append('<g class="note">' + "".join(f'<path d="{path_d(z)}" fill="#ffffff" fill-opacity="0.35"/><path d="{path_d(z)}" fill="url(#kh)" fill-opacity="0.6"/>' for z in d.zones) + '</g>')
    s.append("".join(f'<path d="{path_d(l, False)}" fill="none" stroke="{COL["CREASE"]}" stroke-width="0.25" stroke-dasharray="3 1.5" stroke-opacity="0.9"/>' for l in d.lines["CREASE"]))
    s.append("".join(f'<path d="{path_d(l, False)}" fill="none" stroke="{COL["PERF"]}" stroke-width="0.25" stroke-dasharray="1 1"/>' for l in d.lines["PERF"]))
    s.append("".join(f'<path d="{path_d(o)}" fill="none" stroke="{COL["CUT"]}" stroke-width="0.3"/>' for o in d.outlines + d.holes))
    s.append("</g>")
    ty = H - tb + 6
    s.append(f'<line x1="10" y1="{ty - 3}" x2="{W - 10:.2f}" y2="{ty - 3}" stroke="#1A1A1A" stroke-width="0.3"/>'
             + text_svg(f"{d.name} · DRAFT ARTWORK ON CONCEPT DIELINE", 12, ty + 3, 3.4, "label", "#1A1A1A")
             + text_svg("MVP for review only. Final art goes on the converter's dieline; legal copy, barcodes and claims come from the client.", 12, ty + 9, 2.2, "label", "#C8102E"))
    s.append("</svg>")
    if not seen_principal: qa.append(("P2", "pack", "no artwork on the principal panel (Front / Lid): the brand block is missing"))
    svg = "".join(s)
    base = os.path.join(out, d.name + "_art")
    open(base + ".svg", "w").write(svg)
    _export(svg, base, W)
    if getattr(d, "art_substrate", "board") in ("clear", "metallised"):
        white_plate(d, svg, base, W, H, ox, oy, bleed)
    box = box_view(d, art, faces)
    if box:
        open(os.path.join(out, d.name + "_box.svg"), "w").write(box[0])
        _export(box[0], os.path.join(out, d.name + "_box"), box[1], pdf=False)
    write_qa(d, qa, base + "_qa.md")
    for lv, n, msg in qa:
        if lv == "P1": print(f"  ! {d.name} art [{n}]: {msg}")
    return base


def _export(svg, base, W, pdf=True):
    try:
        import cairosvg
        if pdf: cairosvg.svg2pdf(bytestring=svg.encode(), write_to=base + ".pdf")
        cairosvg.svg2png(bytestring=svg.encode(), write_to=base + ".png", output_width=int(min(3000, W * 8)))
    except Exception as e:
        print(f"  ! PNG/PDF skipped for {os.path.basename(base)}: {e.__class__.__name__}")


def box_view(d, art, faces):
    """Oblique (cabinet-style) technical view of the folded pack: front true size, side and top foreshortened.
    A diagram of the real panels, not a render."""
    spec = BOXVIEW.get(d.style)
    if not spec: return None
    fn, sn, tn = spec
    if fn not in faces or sn not in faces: return None
    k, ang = 0.6, math.radians(30)
    cx, sy = k * math.cos(ang), k * math.sin(ang)
    fpa, fw, fh = faces[fn]; spa, sw, sh = faces[sn]
    tpa = faces.get(tn) if tn else None
    tdep = sw if not tpa else tpa[2]
    m = 20
    W = fw + sw * cx + 2 * m
    top_h = tdep * sy
    H = fh + top_h + 2 * m + 12
    bg = token(art.get("bg"), "#FFFFFF")
    def face(pa, pw, ph, matrix, shade):
        keep, pa.qa = pa.qa, []                # already checked on the flat; don't double-report
        body = pa.svg(background=False)
        pa.qa = keep
        for w in getattr(d, "windows", []):
            if w["panel"] == pa.n: body += f'<path d="{path_d(w["local"])}" fill="{show_fill(art)}"/>'
        bgc = pa.bg if pa.cfg.get("bg") else bg
        return (f'<g transform="matrix({matrix})"><clipPath id="c{id(pa)}"><rect width="{pw:.3f}" height="{ph:.3f}"/></clipPath>'
                f'<g clip-path="url(#c{id(pa)})"><rect width="{pw:.3f}" height="{ph:.3f}" fill="{bgc}"/>{body}'
                f'<rect width="{pw:.3f}" height="{ph:.3f}" fill="{shade[0]}" fill-opacity="{shade[1]}"/></g>'
                f'<rect width="{pw:.3f}" height="{ph:.3f}" fill="none" stroke="#1A1A1A" stroke-width="0.25"/></g>')
    X0, Y0 = m, m + top_h
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}mm" height="{H:.2f}mm" viewBox="0 0 {W:.3f} {H:.3f}">',
         f'<rect width="{W:.3f}" height="{H:.3f}" fill="#F4F4F2"/>']
    o.append(face(fpa, fw, fh, f"1,0,0,1,{X0:.3f},{Y0:.3f}", ("#000", 0)))
    o.append(face(spa, sw, sh, f"{cx:.4f},{-sy:.4f},0,1,{X0 + fw:.3f},{Y0:.3f}", ("#000", 0.12)))
    if tpa:
        pa, pw, ph = tpa
        # local y = 0 is the hinge (back edge); y = ph is the front edge, which meets the front face's top
        o.append(face(pa, pw, ph, f"1,0,{-cx * (sw / ph):.4f},{sy * (sw / ph):.4f},{X0 + cx * sw:.3f},{Y0 - sy * sw:.3f}", ("#fff", 0.08)))
    else:
        o.append(f'<path d="M{X0:.3f},{Y0:.3f} L{X0 + cx * sw:.3f},{Y0 - sy * sw:.3f} L{X0 + fw + cx * sw:.3f},{Y0 - sy * sw:.3f} L{X0 + fw:.3f},{Y0:.3f} Z" fill="{bg}" stroke="#1A1A1A" stroke-width="0.25"/>')
    o.append(text_svg(f"{d.name} · folded view (oblique diagram, not a render)", m, H - 6, 2.4, "label", "#555555"))
    o.append("</svg>")
    return "".join(o), W


def write_qa(d, qa, path):
    order = {"P1": 0, "P2": 1, "P3": 2}
    qa = sorted(qa, key=lambda q: order.get(q[0], 3))
    md = [f"# {d.name}: draft artwork checks", "",
          "Automatic checks on the MVP. P1 = fix before showing anyone, P2 = fix before the converter, P3 = note.", ""]
    md += [f"- **{lv}** · {n}: {msg}" for lv, n, msg in qa] or ["- No automatic issues found. Now do the human checks below."]
    md += ["", "## Human checks (the engine can't see these)",
           "- [ ] Fold a printed paper proof: every panel reads the right way up; the brand reads from 2–3 m",
           "- [ ] Shelf line-up: the pack among real competitors, in greyscale, at 2–3 m (nazar-packaging qa.md)",
           "- [ ] The 30-second AI-tell test (nazar-core ai_tells.md): no default gradients, glows or centred-everything",
           "- [ ] Elements that cross folds still look right at ±1 mm drift",
           "- [ ] Mandatory copy sized from the client's real text, not placeholders"]
    open(path, "w").write("\n".join(md) + "\n")


def show_fill(art):
    st = art.get("show_through")
    return token(st) if st else "url(#chk)"

def windows_svg(d, art):
    """Windows on top of the art: the product's colour (or a transparency checker) shows through. Board windows also
    show the film patch glued inside."""
    if not getattr(d, "windows", None): return ""
    o = []
    for w in d.windows:
        o.append(f'<path d="{path_d(w["poly"])}" fill="{show_fill(art)}" fill-opacity="{0.92 if art.get("show_through") else 1}"/>')
        o.append(f'<path d="{path_d(w["poly"])}" fill="none" stroke="{COL["GUIDE"]}" stroke-width="0.25" stroke-dasharray="1 0.6"/>')
        x0, y0, x1, y1 = w["bbox"]
        lab = w["label"] + (" · die-cut" if d.art_substrate == "board" else " · no ink, no white")
        o.append('<g class="note">' + text_svg(lab, (x0 + x1) / 2, (y0 + y1) / 2 + 0.8, 2.0, "label", "#333333", "middle") + '</g>')
        if "patch" in w:
            px0, py0, px1, py1 = w["patch"]
            o.append(f'<rect x="{px0:.3f}" y="{py0:.3f}" width="{px1 - px0:.3f}" height="{py1 - py0:.3f}" fill="none" stroke="{COL["GUIDE"]}" stroke-width="0.2" stroke-dasharray="2 1"/>')
            o.append('<g class="note">' + text_svg("film patch (glued inside)", px0 + 1, py0 - 1, 1.8, "label", COL["GUIDE"]) + '</g>')
    return "".join(o)

def white_plate(d, art_svg, base, W, H, ox, oy, bleed):
    """White-ink plate preview for clear / metallised film. Black = white ink under the colours; paper = no white
    (windows and unprinted clear film). Built from the artwork's own coverage, clipped to the die (+ bleed)."""
    try:
        import cairosvg, io
        from PIL import Image, ImageChops
    except ImportError:
        return
    mk = art_svg.replace('fill="#F4F4F2"/>', 'fill="none"/>', 1)
    mk = re.sub(r'<g class="note">.*?</g>', '', mk, flags=re.S)                  # annotations aren't ink
    mk = mk.replace("url(#chk)", "#FF00FF")                                      # clear areas
    mk = re.sub(r'fill="#[0-9A-Fa-f]{6}" fill-opacity="0.92"', 'fill="#FF00FF"', mk)   # windows with show-through colour
    mk = re.sub(r'<path d="[^"]+" fill="#ffffff"/><path d="[^"]+" fill="url\(#kh\)"/>', '', mk)  # glue: no ink, no white
    mk = re.sub(r'<path d="[^"]+" fill="none" stroke="[^"]+"[^>]*/>', '', mk)    # dieline and window outlines
    mk = re.sub(r'<rect x="[^"]+" y="[^"]+" width="[^"]+" height="[^"]+" fill="none" stroke="[^"]+"[^>]*/>', '', mk)
    wpx = int(min(2400, W * 6))
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=mk.encode(), output_width=wpx))).convert("RGBA")
    die = "".join(f'<path d="{path_d(o)}" fill="#000" stroke="#000" stroke-width="{2 * bleed:.3f}"/>' for o in d.outlines)
    msvg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}mm" height="{H:.2f}mm" viewBox="0 0 {W:.3f} {H:.3f}"><g transform="translate({ox:.3f},{oy:.3f})">{die}</g></svg>'
    mask = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=msvg.encode(), output_width=wpx))).convert("RGBA").split()[3].resize(im.size)
    r, g, b, a = im.split()
    ink = a.point(lambda v: 255 if v > 40 else 0)
    mag = ImageChops.multiply(ImageChops.multiply(r.point(lambda v: 255 if v > 200 else 0), g.point(lambda v: 255 if v < 60 else 0)), b.point(lambda v: 255 if v > 200 else 0))
    white = ImageChops.multiply(ImageChops.subtract(ink, mag), mask.point(lambda v: 255 if v > 40 else 0))
    plate = ImageChops.invert(white).convert("RGB")
    # die outline for orientation
    out = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=msvg.replace('fill="#000" stroke="#000"', 'fill="none" stroke="#E6007E" stroke-opacity="0.8"').replace(f'stroke-width="{2 * bleed:.3f}"', 'stroke-width="0.3"').encode(), output_width=wpx))).convert("RGBA").resize(im.size)
    plate.paste(out, (0, 0), out)
    plate.save(base.replace("_art", "_white") + ".png")
