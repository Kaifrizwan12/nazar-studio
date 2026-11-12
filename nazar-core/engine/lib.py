"""Kaif brand book engine: tokens from brand.json, outlined type, exact logos, maps, page furniture.

Everything brand-specific lives in brand.json. Pages are plain functions returning a Page (see pages_example.py).
"""
import json, math, os, re, functools
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = json.load(open(os.path.join(HERE, "brand.json")))
def _path(p): return p if os.path.isabs(p) else os.path.normpath(os.path.join(HERE, p))

PG = BRAND["page"]
W, H = PG["w"], PG["h"]
M = PG["margin"]
COLS, GUTTER = PG.get("columns", 12), PG.get("gutter", 24)
COL = (W - 2 * M - (COLS - 1) * GUTTER) / COLS
def col_x(n):
    """x of the left edge of column n (0-11)."""
    return M + n * (COL + GUTTER)

# ---------------- tokens ----------------
C = {k: v["hex"] for k, v in BRAND["colours"].items()}
BASE, LIGHT_, SEC, ACCENT = C["base"], C["light"], C["secondary"], C["accent"]
SEC_D = C.get("secondary_dark", SEC)

FONTS = _path(BRAND["fonts_dir"])
FONT = BRAND["fonts"]                       # role -> file name

# ---------------- type ----------------
@functools.lru_cache(None)
def _font(key):
    path = os.path.join(FONTS, FONT[key])
    tt = TTFont(path)
    return tt, hb.Font(hb.Face(hb.Blob.from_file_path(path))), tt["head"].unitsPerEm

def _run(key, chars):
    tt, font, upm = _font(key)
    buf = hb.Buffer(); buf.add_str(chars); buf.guess_segment_properties()
    hb.shape(font, buf, {})
    return tt, buf, upm

def missing(key, chars):
    """Characters the font can't draw. QA: call this on every string you set in an unusual face."""
    cmap = _font(key)[0].getBestCmap()
    return sorted({ch for ch in chars if ch.strip() and ord(ch) not in cmap})

@functools.lru_cache(4096)
def _shape(key, chars, track_em):
    tt, buf, upm = _run(key, chars)
    gs, order = tt.getGlyphSet(), tt.getGlyphOrder()
    pen, x = SVGPathPen(gs), 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gs[order[info.codepoint]].draw(TransformPen(pen, (1, 0, 0, -1, x + pos.x_offset, -pos.y_offset)))
        x += pos.x_advance + track_em * upm
    return pen.getCommands(), x - track_em * upm, upm

def bounds(key, chars, size):
    """Ink bounds (x0, y0, x1, y1) at size, baseline at y = 0, y down."""
    tt, buf, upm = _run(key, chars)
    gs, order = tt.getGlyphSet(), tt.getGlyphOrder()
    bp, x = BoundsPen(gs), 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gs[order[info.codepoint]].draw(TransformPen(bp, (1, 0, 0, -1, x + pos.x_offset, -pos.y_offset)))
        x += pos.x_advance
    k = size / upm
    return tuple(v * k for v in bp.bounds)

def width(key, chars, size, track=0):
    """track is in em (0.1 = +100 tracking)."""
    _, adv, upm = _shape(key, chars, track)
    return adv * size / upm

def text(chars, x, y, size=14, key="label", fill=None, op=1, track=0, anchor="start"):
    """Outlined text; (x, y) is the baseline start. RTL scripts shape correctly via harfbuzz."""
    if not chars: return ""
    d, adv, upm = _shape(key, chars, track)
    s = size / upm; w = adv * s
    if anchor == "end": x -= w
    elif anchor == "middle": x -= w / 2
    return f'<path transform="translate({x:.2f},{y:.2f}) scale({s:.6f})" d="{d}" fill="{fill or BASE}" fill-opacity="{op}"/>'

def wrap(chars, size, maxw, key="text", track=0):
    lines_, cur = [], ""
    for word in chars.split(" "):
        t = (cur + " " + word).strip()
        if cur and width(key, t, size, track) > maxw:
            lines_.append(cur); cur = word
        else:
            cur = t
    if cur: lines_.append(cur)
    return lines_

def para(chars, x, y, size, maxw, key="text", fill=None, op=1, lead=1.35, track=0):
    """Wrapped paragraph; returns (svg, bottom_y)."""
    out = ""
    for p in chars.split("\n"):
        for ln in wrap(p, size, maxw, key, track):
            out += text(ln, x, y, size, key, fill, op, track); y += size * lead
    return out, y

def lines(rows, x, y, size, key="text", fill=None, op=1, lead=1.3, track=0, anchor="start"):
    out = ""
    for r in rows:
        out += text(r, x, y, size, key, fill, op, track, anchor); y += size * lead
    return out

# ---------------- logo ----------------
@functools.lru_cache(None)
def _svg(name):
    s = open(_path(BRAND["logos"][name])).read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', s).group(1).replace(",", " ").split()]
    return re.search(r"<svg[^>]*>(.*)</svg>", s, re.S).group(1), vb

def logo(name, x, y, w, op=1):
    """Exact client artwork, never redrawn. (x, y) = top-left of its viewBox, w = rendered width."""
    inner, (vx, vy, vw, vh) = _svg(name)
    s = w / vw
    return f'<g transform="translate({x:.2f},{y:.2f}) scale({s:.6f}) translate({-vx},{-vy})" opacity="{op}">{inner}</g>'

def logo_size(name, w):
    _, (_, _, vw, vh) = _svg(name)
    return w, w * vh / vw

def logo_centered(name, cx, cy, w, **kw):
    """Optically centre the viewBox on (cx, cy). Crop the SVG viewBox tight to the visible mark first."""
    _, h = logo_size(name, w)
    return logo(name, cx - w / 2, cy - h / 2, w, **kw)

# ---------------- primitives ----------------
def hair(x1, y1, x2, y2, col, op=0.12, w=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-opacity="{op}" stroke-width="{w}"{d}/>'

def rect(x, y, w, h, fill, op=1, rx=0, stroke=None, sw=1, sop=1):
    st = f' stroke="{stroke}" stroke-width="{sw}" stroke-opacity="{sop}"' if stroke else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" fill-opacity="{op}"{st}/>'

def circle(cx, cy, r, fill="none", op=1, stroke=None, sw=1, sop=1, dash=None):
    st = f' stroke="{stroke}" stroke-width="{sw}" stroke-opacity="{sop}"' if stroke else ""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" fill-opacity="{op}"{st}{d}/>'

def leader(x1, y1, x2, y2, col, op=0.4):
    """Dotted leader line for exploded diagrams and callouts."""
    return hair(x1, y1, x2, y2, col, op, 1, "1 4") + circle(x1, y1, 2.5, col, op)

def dimension(x1, y, x2, label, col, op=0.6):
    """Horizontal dimension line with end ticks and a mono label: spec sheets."""
    return (hair(x1, y, x2, y, col, op) + hair(x1, y - 6, x1, y + 6, col, op) + hair(x2, y - 6, x2, y + 6, col, op)
            + text(label, (x1 + x2) / 2, y - 10, 11, "label", col, op, 0.08, "middle"))

def halftone_defs(pid="ht", pitch=42, r=7.5, col="#ffffff", op=0.09, angle=18):
    return (f'<pattern id="{pid}" width="{pitch}" height="{pitch}" patternUnits="userSpaceOnUse" patternTransform="rotate({angle})">'
            f'<circle cx="{pitch/2}" cy="{pitch/2}" r="{r}" fill="{col}" fill-opacity="{op}"/></pattern>')

@functools.lru_cache(None)
def grain_uri():
    """256 px tile of ±4% noise: film grain that also kills gradient banding."""
    import random, io, base64
    from PIL import Image
    rnd = random.Random(7)
    im = Image.new("LA", (256, 256))
    im.putdata([(255 if rnd.random() < 0.5 else 0, rnd.randint(0, 20)) for _ in range(256 * 256)])
    buf = io.BytesIO(); im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def contrast(a, b):
    """WCAG contrast ratio between two hex colours."""
    def lum(h):
        r, g, b_ = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b_)
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

# ---------------- maps (OpenStreetMap via fetch_map.sh) ----------------
CLASS = {"motorway": "major", "trunk": "major", "primary": "major", "secondary": "major", "tertiary": "mid",
         "primary_link": "mid", "secondary_link": "mid", "trunk_link": "mid",
         "residential": "minor", "unclassified": "minor", "living_street": "minor", "service": "lane",
         "pedestrian": "lane", "footway": "foot", "path": "foot", "steps": "foot"}

class Proj:
    """lat/lon -> page px. span_lat = how many degrees of latitude fill height h."""
    def __init__(self, lat, lon, w=W, h=H, span_lat=0.028, x0=0, y0=0):
        self.lat, self.lon, self.w, self.h, self.x0, self.y0 = lat, lon, w, h, x0, y0
        self.k = math.cos(math.radians(lat)); self.sc = h / span_lat
    def __call__(self, la, lo):
        return (self.x0 + self.w / 2 + (lo - self.lon) * self.k * self.sc,
                self.y0 + self.h / 2 - (la - self.lat) * self.sc)
    def m_to_px(self, m):
        return self.sc / 111320 * m

@functools.lru_cache(None)
def _osm(name):
    return json.load(open(os.path.join(HERE, "osm", f"{name}.json")))["elements"]

def map_paths(name, proj, ink=None, ops=None, widths=None, highlight=None, hl_fill=None):
    """Street grid, one path per road class. highlight = set of street names drawn bright."""
    ink = ink or LIGHT_
    ops = ops or {"foot": 0.0, "lane": 0.06, "minor": 0.13, "mid": 0.22, "major": 0.34, "hl": 0.85}
    widths = widths or {"foot": 0.5, "lane": 0.75, "minor": 1, "mid": 1.25, "major": 1.75, "hl": 2}
    buckets = {k: [] for k in ops}
    for w_ in _osm(name):
        g, t = w_.get("geometry"), w_.get("tags", {})
        if not g: continue
        cls = "hl" if highlight and t.get("name") in highlight else CLASS.get(t.get("highway"))
        if cls not in buckets or ops.get(cls, 0) <= 0: continue
        buckets[cls].append("M" + "L".join("%.1f,%.1f" % proj(p["lat"], p["lon"]) for p in g))
    out = ""
    for cls in ("foot", "lane", "minor", "mid", "major", "hl"):
        if buckets.get(cls):
            col = hl_fill if (cls == "hl" and hl_fill) else ink
            out += (f'<path d="{"".join(buckets[cls])}" fill="none" stroke="{col}" stroke-opacity="{ops[cls]}" '
                    f'stroke-width="{widths[cls]}" stroke-linecap="round" stroke-linejoin="round"/>')
    return out

def fmt_ll(la, lo, dp=3):
    """Rounded coordinates. Keep dp <= 3 for anything near a private address."""
    return f"{la:.{dp}f}° N   {lo:.{dp}f}° E"

# ---------------- page ----------------
DARK = {"bg": BASE, "ink": LIGHT_, "sub": SEC, "hair": LIGHT_, "dev_op": 0.12}
LIGHT = {"bg": LIGHT_, "ink": BASE, "sub": SEC_D, "hair": BASE, "dev_op": 0.13}

# Heading system, the same on every content page; set per project in brand.json "page" (references/04_book_anatomy.md)
_HD = PG.get("heading", {})
Y_RUN = _HD.get("running", M - 28)
Y_KICK, Y_TITLE, LINE2 = _HD.get("kicker", M + 32), _HD.get("title", M + 92), _HD.get("title_lead", 62)

class Page:
    def __init__(self, pid, title, section, theme=DARK, stamp=None):
        self.pid, self.title, self.section, self.t, self.stamp = pid, title, section, theme, stamp
        self.body, self.defs, self.dev_pos = [], [], None
        self.furniture, self.grain = True, False
    def add(self, *svg):
        self.body.extend(svg); return self
    def defs_(self, *d):
        self.defs.extend(d); return self
    def device(self, x, y, size=14):
        """Place this page's hidden device (brand.json "device": an SVG file). Recorded for the reveal page."""
        self.dev_pos = (x, y, size); return self
    def heading(self, kicker, title, sub=None, x=M):
        """kicker (mono, accent) / title (text 48, one or two lines split by \\n) / subtitle. Returns y below the block."""
        t, out, y = self.t, text(kicker.upper(), x, Y_KICK, 13, "label", ACCENT, track=0.08), Y_TITLE
        rows = title.split("\n")
        out += lines(rows, x, Y_TITLE, 48, "text", t["ink"], lead=LINE2 / 48)
        y = Y_TITLE + (len(rows) - 1) * LINE2
        if sub:
            y += 42; out += text(sub, x, y, 19, "text", t["sub"])
        self.add(out)
        return y + 40
    def svg(self, number):
        t = self.t
        bg = f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>'
        if self.grain:
            self.defs.append(f'<pattern id="grain" width="256" height="256" patternUnits="userSpaceOnUse"><image width="256" height="256" href="{grain_uri()}"/></pattern>')
            bg += f'<rect width="{W}" height="{H}" fill="url(#grain)" opacity="0.5"/>'
        fur = ""
        if self.furniture:
            fur += text(self.section, M, Y_RUN, 14, "label", t["sub"])
            fur += text(f"{number:02d}", W - M, H - M + 34, 14, "label", t["sub"], anchor="end")
            if self.stamp:   # optional per-page stamp: a story value (place, hour, batch...)
                fur += text(f"{self.stamp} · {self.pid}", M, H - M + 34, 11, "label", t["sub"], 0.8, track=0.08)
        dev = device_svg(*self.dev_pos, t["ink"], t["dev_op"]) if self.dev_pos else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
                f'<defs>{"".join(self.defs)}</defs>{bg}{"".join(self.body)}{fur}{dev}</svg>')

def device_svg(x, y, size, fill, op):
    """The brand's hidden device, drawn as a flat silhouette in one colour."""
    if "device" not in BRAND.get("logos", {}): return ""
    inner, (vx, vy, vw, vh) = _svg("device")
    inner = re.sub(r'fill="(?!none)[^"]*"', f'fill="{fill}"', inner)
    s = size / vw
    return f'<g transform="translate({x:.2f},{y:.2f}) scale({s:.6f}) translate({-vx},{-vy})" opacity="{op}">{inner}</g>'

def page_numbers():
    """{pid: page number} from the previous build (run build.py twice so contents are right)."""
    p = os.path.join(HERE, "out", "pages.json")
    return json.load(open(p)) if os.path.exists(p) else {}
