"""Static backdrops for routine (non-festive) posts, from the brand's tokens in nazar-core/engine/brand.json.

    python engine/backdrops.py templates/backdrops.json

Writes <out>/<brand>_<format>_<role>_<mode>.png, a _guide.png twin with safe zones and content zones, and sheet.png.
One skeleton everywhere: the anchor corner, margin ratio, edge band and handle never move; modes only swap colour.
"""
import os, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "nazar-core", "engine")))
from lib import *          # noqa: E402  (tokens, text, logo, rect, contrast… from the shared engine)

# name: (w, h, kind). Mirrors references/formats.md: verify specs in-app before final export.
FORMATS = {
    "feed_4x5": (1080, 1350, "feed"), "feed_3x4": (1080, 1440, "feed"), "feed_1x1": (1080, 1080, "feed"),
    "story": (1080, 1920, "story"), "reel_cover": (1080, 1920, "reel"),
    "linkedin": (1200, 1200, "feed"), "x_post": (1600, 900, "wide"), "yt_thumb": (1280, 720, "yt"),
    "highlight": (1080, 1920, "highlight"), "avatar": (1080, 1080, "avatar"),
}
ROLES_FOR = {"feed": ["single", "cover", "text", "image", "end", "quote", "stat"],
             "story": ["story"], "reel": ["reel_cover"], "wide": ["single"], "yt": ["single"],
             "highlight": ["highlight"], "avatar": ["avatar"]}

def modes():
    """Colour sets per mode. The accent mode is only offered when its text passes 4.5:1."""
    m = {"dark": {"bg": BASE, "ink": LIGHT_, "sub": SEC, "band": ACCENT},
         "light": {"bg": LIGHT_, "ink": BASE, "sub": SEC_D, "band": ACCENT}}
    ink = BASE if contrast(ACCENT, BASE) >= contrast(ACCENT, LIGHT_) else LIGHT_
    if contrast(ACCENT, ink) >= 4.5:
        m["accent"] = {"bg": ACCENT, "ink": ink, "sub": ink, "band": ink}
    return m

def logo_name(spec, mode):
    base = spec.get("logo", "mark")
    alt = f"{base}_on_dark"
    return alt if mode in ("dark",) and alt in BRAND["logos"] else base

class Canvas:
    def __init__(self, w, h, spec, mode, pal):
        self.w, self.h, self.spec, self.mode, self.p = w, h, spec, mode, pal
        s = min(w, h)
        self.s = s
        self.m = round(s * spec.get("margin", 0.067))
        self.band = max(6, round(s * spec.get("band_ratio", 0.012)))
        self.lw = round(s * spec.get("logo_ratio", 0.15))
        self.small = max(22, round(s * 0.026))
        self.rtl = spec.get("rtl", False)
        self.top, self.bottom = 0, 0                     # extra insets for platform UI (story)
        self.o, self.g = [], []                          # backdrop layer, guide layer
    def X(self, x, w=0):
        """Mirror x for right-to-left brands: the skeleton flips, the artwork doesn't."""
        return self.w - x - w if self.rtl else x
    def add(self, *s): self.o.extend(s)
    def guide(self, *s): self.g.extend(s)

    # --- static parts ---
    def background(self):
        self.add(rect(0, 0, self.w, self.h, self.p["bg"]))
        if self.spec.get("grain"):
            self.add(f'<defs><pattern id="gr" width="256" height="256" patternUnits="userSpaceOnUse"><image width="256" height="256" href="{grain_uri()}"/></pattern></defs>'
                     f'<rect width="{self.w}" height="{self.h}" fill="url(#gr)" opacity="0.5"/>')
    def edge(self):
        side = self.spec.get("band", "left")
        if side == "none": return
        if side in ("left", "right"):
            left = (side == "left") != self.rtl
            self.add(rect(0 if left else self.w - self.band, 0, self.band, self.h, self.p["band"]))
        else:
            self.add(rect(0, 0 if side == "top" else self.h - self.band, self.w, self.band, self.p["band"]))
    def mark(self, scale=1.0, y=None):
        name = logo_name(self.spec, self.mode)
        lw = self.lw * scale
        _, lh = logo_size(name, lw)
        y = self.m + self.top if y is None else y
        self.add(logo(name, self.X(self.m + self.band, lw), y, lw))
        return lh
    def handle(self):
        h = self.spec.get("handle")
        if not h: return
        y = self.h - self.m - self.bottom
        anchor = "end" if self.rtl else "start"
        self.add(text(h, self.X(self.m + self.band), y, self.small, "label", self.p["sub"], track=0.06, anchor=anchor))
    def counter(self, i, n, cue=False):
        y = self.h - self.m - self.bottom
        x = self.m if self.rtl else self.w - self.m
        anchor = "start" if self.rtl else "end"
        self.add(text(f"{i:02d}/{n:02d}", x, y, self.small, "label", self.p["ink"], 0.85, track=0.08, anchor=anchor))
        if cue:   # swipe cue: a short rule with an arrowhead, before the counter
            cw = width("label", f"{i:02d}/{n:02d}", self.small, 0.08)
            ax = (x + cw + 26) if self.rtl else (x - cw - 26)
            d = -1 if self.rtl else 1
            yy = y - self.small * 0.35
            self.add(hair(ax - d * 70, yy, ax, yy, self.p["band"], 1, 3),
                     f'<path d="M{ax},{yy} l{-d * 14},-9 l0,18 z" fill="{self.p["band"]}"/>')
    def continuity(self, i, n):
        """A line at the same height on every slide; it runs off the edge where the next slide continues it."""
        if not self.spec.get("continuity"): return
        y = self.h * 0.86
        x0 = 0 if i > 1 else self.m + self.band
        x1 = self.w if i < n else self.w - self.m
        self.add(hair(x0, y, x1, y, self.p["band"], 0.9, 3))

    # --- guide parts ---
    def zone(self, x, y, w, h, label):
        c = self.p["ink"]
        self.guide(rect(x, y, w, h, c, 0.04, stroke=c, sw=2, sop=0.35),
                   text(label.upper(), x + 16, y + 34, 20, "label", c, 0.6, track=0.1))
    def no_go(self, x, y, w, h, label):
        self.guide(rect(x, y, w, h, "#E5484D", 0.14),
                   text(label.upper(), x + 16, y + h / 2 + 8, 20, "label", "#E5484D", 0.9, track=0.1))
    def crop(self, cw, ch, label):
        x, y = (self.w - cw) / 2, (self.h - ch) / 2
        self.guide(rect(x, y, cw, ch, "none", stroke="#E5484D", sw=3, sop=0.8),
                   text(label.upper(), x + 12, y + ch - 14, 18, "label", "#E5484D", 0.9, track=0.1))

    def svg(self, with_guide):
        g = "".join(self.g) if with_guide else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'{"".join(self.o)}{g}</svg>')

def build(fmt, role, mode, spec, i=1, n=5):
    w, h, kind = FORMATS[fmt]
    c = Canvas(w, h, spec, mode, modes()[mode])
    c.background(); c.edge()
    m, b = c.m, c.band
    inner_w = w - 2 * m - b
    if kind == "story":
        c.top = c.bottom = round(h * 0.13)
        c.no_go(0, 0, w, c.top, "platform UI · keep clear"); c.no_go(0, h - c.bottom, w, c.bottom, "platform UI · keep clear")
    if kind == "reel":
        c.top = c.bottom = (h - w * 4 / 3) / 2 + 20
        c.crop(w, w * 4 / 3, "grid crop 3:4")
        c.no_go(0, h - h * 0.35, w, h * 0.35 - c.bottom + 20, "playback UI")
    if kind in ("highlight", "avatar"):
        r = w * (0.33 if kind == "highlight" else 0.5)
        c.add(rect(0, 0, w, h, c.p["bg"]))           # no band: circles crop it away
        lw = r * (0.95 if kind == "avatar" else 0.9)
        name = logo_name(spec, mode)
        c.add(logo_centered(name, w / 2, h / 2, lw))
        c.guide(circle(w / 2, h / 2, r, stroke="#E5484D", sw=3, sop=0.8),
                text("SHOWN AS A CIRCLE", w / 2, h / 2 + r + 40, 20, "label", "#E5484D", 0.9, 0.1, "middle"))
        return c
    lh = c.mark(1.35 if role == "end" else 1.0, y=None if role != "end" else h * 0.42)
    if role not in ("text", "image"): c.handle()
    if role in ("cover", "text", "image", "end"):
        c.counter(i, n, cue=(role == "cover" and spec.get("swipe_cue", True)))
        c.continuity(i, n)
    if kind == "feed" and fmt != "feed_3x4":
        c.crop(h * 3 / 4, h, "profile grid crop 3:4")
    if kind == "yt":
        c.no_go(w - 200, h - 80, 190, 64, "timestamp")
    # content zones (guide only)
    top = m + c.top + lh + m * 0.8
    foot = h - m - c.bottom - c.small * 2.4
    zx = c.X(m + b, inner_w)
    if role == "image":
        win_h = (foot - top) * 0.78
        c.add(rect(zx, top, inner_w, win_h, c.p["ink"], 0.06))
        c.zone(zx, top, inner_w, win_h, "image window · real photo only")
        c.zone(zx, top + win_h + 24, inner_w, foot - top - win_h - 24, "caption")
    elif role == "quote":
        c.add(text("“", c.X(m + b - 6, 0), top + c.s * 0.2, c.s * 0.26, "text", c.p["band"]))
        c.zone(zx, top + c.s * 0.22, inner_w, foot - top - c.s * 0.22, "quote + name")
    elif role == "stat":
        c.zone(zx, top, inner_w, (foot - top) * 0.62, "one number")
        c.zone(zx, top + (foot - top) * 0.66, inner_w, (foot - top) * 0.34, "one line")
    elif role == "end":
        c.zone(zx, h * 0.42 + lh + m, inner_w, foot - (h * 0.42 + lh + m), "takeaway + call to action")
    elif role == "cover":
        c.zone(zx, top, inner_w, foot - top, "hook · big title")
    else:
        split = top + (foot - top) * 0.48
        c.zone(zx, top, inner_w, split - top - 16, "title")
        c.zone(zx, split, inner_w, foot - split, "body / photo")
    return c

def main(cfg_path):
    import cairosvg
    spec = json.load(open(cfg_path))
    out = spec.get("out") or os.path.join(os.getcwd(), "exports", "backdrops")
    os.makedirs(out, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "", BRAND["name"].lower()) or "brand"
    have = modes()
    for want in spec.get("modes", ["dark", "light"]):
        if want not in have: print(f"! mode '{want}' skipped: the accent fails 4.5:1 contrast with both base and light")
    pngs = []
    n = spec.get("carousel_slides", 5)
    for fmt in spec.get("formats", list(FORMATS)):
        kind = FORMATS[fmt][2]
        roles = [r for r in spec.get("roles", ROLES_FOR[kind]) if r in ROLES_FOR[kind]] or ROLES_FOR[kind]
        for role in roles:
            i = {"cover": 1, "text": 2, "image": 3, "end": n}.get(role, 1)
            for mode in [m for m in spec.get("modes", ["dark", "light"]) if m in have]:
                if mode == "accent" and role not in ("cover", "quote", "stat", "single"): continue
                c = build(fmt, role, mode, spec, i, n)
                base = os.path.join(out, f"{slug}_{fmt.replace('_', '')}_{role}_{mode}")
                for guide in (False, True):
                    p = base + ("_guide" if guide else "") + ".png"
                    cairosvg.svg2png(bytestring=c.svg(guide).encode(), write_to=p)
                    if not guide: pngs.append(p)
    # contact sheet of the clean backdrops
    from PIL import Image
    th = 300; ims = [Image.open(p).convert("RGB") for p in pngs]
    ims = [im.resize((round(im.width * th / im.height), th)) for im in ims]
    cols = 8; rows = (len(ims) + cols - 1) // cols
    cw = max(im.width for im in ims) + 24
    sheet = Image.new("RGB", (cols * cw + 24, rows * (th + 24) + 24), (128, 128, 128))
    for k, im in enumerate(ims):
        sheet.paste(im, (24 + (k % cols) * cw, 24 + (k // cols) * (th + 24)))
    sheet.save(os.path.join(out, "sheet.png"))
    print(f"{len(pngs)} backdrops (+ guides) → {out}")
    for k in ("ink", "sub"):
        for mn, pal in have.items():
            r = contrast(pal[k], pal["bg"])
            if r < (4.5 if k == "ink" else 3.0): print(f"! {mn}: {k} on bg is {r:.2f}:1")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "templates", "backdrops.json"))
