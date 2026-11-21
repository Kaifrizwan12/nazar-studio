"""Deck engine: presentation and case-study decks as SVG pages (1920 x 1080), rendered with cairosvg.

    from deck import Deck, couple, fan, toss, bleed
    d = Deck(tokens, out_dir)             # tokens: dict or path to a JSON file (see TOKENS below)
    b = d.top("The brief", "One line, said once.")
    b += d.img("pack_front.png", 900, 250, 900, 760)
    d.page(b, device="split: text left, pack right")
    d.build()                             # PDF of JPEG pages + contact sheet, or Behance panels + covers

What it guards (the build fails, it never ships a broken page):
  - fit()/para(): text wider (or taller) than its box is logged as an overflow.
  - img(): an image off the page, or two placed images overlapping. Compose overlaps upstream as ONE RGBA
    (couple / fan / toss / bleed) so a page never stacks two flattened pictures.
  - device: every page names its layout device; a repeat is warned (one device per page, never twice).

Type is outlined through the nazar-core engine (harfbuzz shaping + fontTools outlines, RTL-safe): no installed
fonts, sharp at any size. Sizes are CAP HEIGHT in px, so a 72 title has 72 px tall capitals at its baseline.

Behance mode (Deck(..., behance=True) or env BEHANCE=1): the same pages written as numbered PNG panels with no
folios, a contact strip, and cover fallbacks at 1616x1264, 808x632 and 768x576 (4:3).
"""
import os, io, re, sys, json, hashlib, functools
import cairosvg
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.normpath(os.path.join(HERE, "..", "..", "nazar-core", "engine"))
if CORE not in sys.path: sys.path.insert(0, CORE)
import lib as _core                                  # nazar-core engine: shaping, outlines, ink bounds

W, H = 1920, 1080

# Brand tokens: the only brand-specific input. Font paths are absolute or relative to the tokens file.
TOKENS = {
    "name": "Example Co.",
    "folio": "Example Co. · case study · Nazar Studio",
    "colours": {"paper": "#EFE9DF", "ink": "#1B1A17", "mute": "#6B655B", "accent": "#E8572A", "dark": "#26211E"},
    "fonts": {"display": os.path.join(CORE, "fonts", "Anton-Regular.ttf"),
              "text": os.path.join(CORE, "fonts", "SpaceGrotesk-Regular.ttf"),
              "bold": os.path.join(CORE, "fonts", "SpaceGrotesk-Medium.ttf"),
              "label": os.path.join(CORE, "fonts", "SpaceMono-Regular.ttf")},
}


def load_tokens(t=None):
    """Merge a dict or JSON path over the defaults; resolve font paths."""
    base = os.path.dirname(os.path.abspath(t)) if isinstance(t, str) else os.getcwd()
    if isinstance(t, str): t = json.load(open(t, encoding="utf-8"))
    out = json.loads(json.dumps(TOKENS)); t = t or {}
    for k, v in t.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict): out[k].update(v)
        else: out[k] = v
    out["fonts"] = {r: (p if os.path.isabs(p) else os.path.normpath(os.path.join(base, p))) for r, p in out["fonts"].items()}
    return out


# ---------------------------------------------------------------- type (through the core engine)
def _role(path):
    """Register a font file with the core engine under its own key; returns the key."""
    key = "deck:" + path
    _core.FONT[key] = path                           # os.path.join(FONTS, abs) == abs, so the core loads it as is
    return key


@functools.lru_cache(None)
def _cap_ratio(key):
    x0, y0, x1, y1 = _core.bounds(key, "H", 1000); return (y1 - y0) / 1000 if y1 > y0 else 0.7


def _em(key, cap): return cap / _cap_ratio(key)


def _ink(key, s, size):
    x0, _, x1, _ = _core.bounds(key, s, size) if s.strip() else (0, 0, 0, 0)
    return x0, x1


# ---------------------------------------------------------------- the deck
class Deck:
    def __init__(self, tokens=None, out_dir="out", name=None, behance=None, size=(1920, 1080)):
        self.T = load_tokens(tokens); c = self.T["colours"]
        self.PAPER, self.INK, self.MUTE = c["paper"], c["ink"], c["mute"]
        self.ACCENT = c.get("accent", self.INK); self.DARK = c.get("dark", self.INK)
        self.F = {r: _role(p) for r, p in self.T["fonts"].items()}
        self.W, self.H = size
        self.name = name or re.sub(r"[^A-Za-z0-9]+", "_", self.T["name"]).strip("_") or "deck"
        self.behance = bool(os.environ.get("BEHANCE")) if behance is None else behance
        self.out = os.path.abspath(out_dir); os.makedirs(self.out, exist_ok=True)
        self.cache = os.path.join(self.out, "_cache"); os.makedirs(self.cache, exist_ok=True)
        self.pages, self.devices, self.over, self.rects = [], [], [], []

    # ------------------------------------------------ text
    def wid(self, s, size, role="display"):
        """Ink width of s at cap height size."""
        if not s: return 0.0
        k = self.F[role]; a, b = _ink(k, s, _em(k, size)); return b - a

    def tx(self, s, x, y, size, role="display", anchor="start", fill=None, track=0.0):
        """Outlined text; (x, y) = left ink edge (or anchor) on the baseline; size = cap height."""
        if not s: return ""
        k = self.F[role]; em = _em(k, size); a, b = _ink(k, s, em)
        if track: b = a + _core.width(k, s, em, track)
        x0 = x - ((b - a) if anchor == "end" else (b - a) / 2 if anchor == "middle" else 0) - a
        return _core.text(s, x0, y, em, k, fill or self.INK, 1, track)

    def _n(self): return len(self.pages) + 1

    def fit(self, s, x, y, size, maxw, role="display", anchor="start", fill=None, track=0.0, floor=0.5):
        """Fit-or-fail: shrink to maxw (never below floor x size); still too wide = logged overflow, build fails."""
        w = self.wid(s, size, role)
        if w > maxw: size = max(size * floor, size * maxw / w)
        if self.wid(s, size, role) > maxw + 1: self.over.append((self._n(), f"too wide: {s[:60]}"))
        return self.tx(s, x, y, size, role, anchor, fill, track)

    def lines(self, s, size, width, role="text"):
        out, line = [], ""
        for word in s.split():
            t = (line + " " + word).strip()
            if line and self.wid(t, size, role) > width: out.append(line); line = word
            else: line = t
        if line: out.append(line)
        for ln in out:
            if self.wid(ln, size, role) > width + 1: self.over.append((self._n(), f"word wider than column: {ln[:40]}"))
        return out

    def para(self, s, x, y, size, width, role="text", fill=None, lead=2.0, maxh=None):
        """Measured wrap; line step = size x lead (cap height units). Returns (svg, next_y). maxh guards height."""
        out, yy = [], y
        for ln in self.lines(s, size, width, role): out.append(self.tx(ln, x, yy, size, role, fill=fill)); yy += size * lead
        if maxh is not None and (yy - size * lead) - (y - size) > maxh + 1:
            self.over.append((self._n(), f"paragraph taller than {maxh}px: {s[:40]}"))
        return "".join(out), yy

    # ------------------------------------------------ page furniture
    def top(self, kicker, title, ink=None, maxw=1760, x=80, size=72):
        """Kicker + title; a long title breaks into two balanced lines before it shrinks."""
        ink = ink or self.INK
        k = self.tx(kicker.upper(), x, 88, 16, "label", fill=ink, track=0.14)
        if self.wid(title, size) <= maxw: return k + self.fit(title, x, 200, size, maxw, fill=ink)
        words = title.split(); best = None
        for i in range(1, len(words)):
            a, b = " ".join(words[:i]), " ".join(words[i:]); w = max(self.wid(a, size), self.wid(b, size))
            if best is None or w < best[0]: best = (w, a, b)
        if best is None: return k + self.fit(title, x, 200, size, maxw, fill=ink)
        return k + self.fit(best[1], x, 200, size, maxw, fill=ink) + self.fit(best[2], x, 200 + size * 1.32, size, maxw, fill=ink)

    def label(self, t, x, y, fill=None, anchor="middle", size=13):
        return self.tx(t.upper(), x, y, size, "label", anchor, fill=fill or self.MUTE, track=0.16)

    def foot(self, s, x=80, ink=None): return self.tx(s, x, self.H - 80, 16, "text", fill=ink or self.MUTE)

    def rect(self, x, y, w, h, fill, rx=0, op=1):
        return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" fill-opacity="{op}"/>'

    # ------------------------------------------------ images
    def img(self, path, x, y, w, h, bg=None, fit="meet", guard=True):
        """Place an image. PNG alpha is flattened onto the page colour into a cached JPEG (light PDFs).
        fit: meet | slice | slice-top | slice-bottom | slice-left | slice-right. 'meet' boxes are guarded:
        off-page or overlapping another guarded box fails the build. Use guard=False only for full-bleed plates."""
        bg = bg or self.PAPER; n = self._n(); base = os.path.basename(str(path))
        if guard and fit == "meet":
            if x < -0.5 or y < -0.5 or x + w > self.W + 0.5 or y + h > self.H + 0.5: self.over.append((n, f"image off page: {base}"))
            for (a, b, c, d) in self.rects:
                if x < c - 0.5 and a < x + w - 0.5 and y < d - 0.5 and b < y + h - 0.5: self.over.append((n, f"images overlap: {base}"))
            self.rects.append((x, y, x + w, y + h))
        if not os.path.exists(path):
            self.over.append((n, f"missing image: {base}")); return self.rect(x, y, w, h, "#ddd")
        h_ = hashlib.md5(os.path.abspath(path).encode()).hexdigest()[:10]
        key = os.path.join(self.cache, f"{os.path.splitext(base)[0]}_{h_}_{bg.lstrip('#')}.jpg")
        if not os.path.exists(key) or os.path.getmtime(key) < os.path.getmtime(path):
            im = Image.open(path).convert("RGBA"); b = Image.new("RGBA", im.size, bg); b.alpha_composite(im)
            b = b.convert("RGB"); b.thumbnail((1800, 1800), Image.LANCZOS); b.save(key, quality=88)
        par = {"meet": "xMidYMid meet", "slice": "xMidYMid slice", "slice-top": "xMidYMin slice", "slice-bottom": "xMidYMax slice",
               "slice-left": "xMinYMid slice", "slice-right": "xMaxYMid slice"}[fit]
        uri = "file:///" + key.replace("\\", "/")
        return f'<image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" preserveAspectRatio="{par}" href="{uri}"/>'

    def svg_file(self, path, x, y, w, h, fill=None):
        """Place an exact SVG file (a logo, a mark) inline; optional single-colour override."""
        s = open(path, encoding="utf-8").read(); vb = re.search(r'viewBox="([^"]+)"', s).group(1)
        inner = s[s.index(">") + 1:s.rindex("</svg>")]
        if fill: inner = re.sub(r'fill="#[0-9A-Fa-f]{3,6}"', f'fill="{fill}"', inner)
        return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}" preserveAspectRatio="xMinYMid meet">{inner}</svg>'

    # ------------------------------------------------ pages
    def page(self, body, device, bg=None, folio=True, ink=None):
        """Add a page. device = the layout device this page uses ("hero crop", "fan of backs", "dark split"...)."""
        bg = bg or self.PAPER; ink = ink or self.INK; n = self._n()
        self.rects.clear()
        if not device: print(f"WARN p{n}: page declares no device")
        self.devices.append((n, (device or "").strip().lower()))
        f = ""
        if folio and not self.behance:
            f = self.tx(f"{n:02d}", self.W - 60, self.H - 40, 12, "label", "end", fill=ink) + self.tx(self.T.get("folio", self.T["name"]), 60, self.H - 40, 12, "label", fill=ink)
        self.pages.append(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {self.W} {self.H}" '
                          f'width="{self.W}" height="{self.H}"><rect width="{self.W}" height="{self.H}" fill="{bg}"/>{body}{f}</svg>')
        return n

    def device_report(self):
        seen, rep = {}, []
        for n, d in self.devices:
            if d and d in seen: rep.append(f"device '{d}' repeats: p{seen[d]} and p{n}")
            seen.setdefault(d, n)
        return rep

    def render(self, svg, scale=1.0):
        png = cairosvg.svg2png(bytestring=svg.encode("utf-8"), unsafe=True, output_width=int(self.W * scale), output_height=int(self.H * scale))
        return Image.open(io.BytesIO(png)).convert("RGB")

    def contact(self, ims, path, cols=4, tw=480):
        th = int(tw * self.H / self.W); rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (tw + 10) + 10, rows * (th + 10) + 10), (40, 40, 40))
        for i, t in enumerate(ims): sheet.paste(t.resize((tw, th), Image.LANCZOS), (10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 10)))
        sheet.save(path, quality=85); return path

    def covers(self, source=None, bg=None):
        """Behance covers: 1616x1264 (2x), 808x632 (the minimum) and a 768x576 4:3 crop.
        source: an image path (cover-cropped, no text: Behance prints the title) or None = page 1, cropped."""
        d = os.path.join(self.out, "behance"); os.makedirs(d, exist_ok=True)
        im = Image.open(source).convert("RGB") if source else self.render(self.pages[0], 1.5)
        k = max(1616 / im.width, 1264 / im.height); im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        l, t = (im.width - 1616) // 2, (im.height - 1264) // 2; c = im.crop((l, t, l + 1616, t + 1264))
        out = [os.path.join(d, f"00_COVER_1616x1264.png"), os.path.join(d, "00_COVER_808x632.jpg"), os.path.join(d, "00_COVER_768x576_4x3.jpg")]
        c.save(out[0], optimize=True); c.resize((808, 632), Image.LANCZOS).save(out[1], quality=92)
        t4 = (c.height - c.width * 3 // 4) // 2; c.crop((0, t4, c.width, t4 + c.width * 3 // 4)).resize((768, 576), Image.LANCZOS).save(out[2], quality=92)
        return out

    def build(self, cover=None):
        """Fail on overflow/overlap; warn on repeated devices; write the PDF + contact sheet, or Behance panels + covers."""
        for w in self.device_report(): print("WARN", w)
        if self.over:
            raise SystemExit("LAYOUT GUARD FAILED: " + "; ".join(f"p{p}: {s}" for p, s in self.over))
        if self.behance:
            d = os.path.join(self.out, "behance"); os.makedirs(d, exist_ok=True)
            for f in os.listdir(d):
                if re.fullmatch(re.escape(self.name) + r"_behance_\d+\.png", f): os.remove(os.path.join(d, f))
            ims = []
            for i, svg in enumerate(self.pages):
                im = self.render(svg, 1.5); im.save(os.path.join(d, f"{self.name}_behance_{i + 1:02d}.png"), optimize=True); ims.append(im)
            strip = Image.new("RGB", (480, 270 * len(ims)))
            for i, t in enumerate(ims): strip.paste(t.resize((480, 270), Image.LANCZOS), (0, i * 270))
            strip.save(os.path.join(d, "_behance_contact.jpg"), quality=85)
            cv = self.covers(cover)
            print(len(ims), "behance panels +", len(cv), "covers ->", d); return d
        ims = [self.render(s) for s in self.pages]
        path = os.path.join(self.out, f"{self.name}.pdf")
        ims[0].save(path, "PDF", save_all=True, append_images=ims[1:], resolution=144, quality=86)
        sheet = self.contact(ims, os.path.join(self.out, f"{self.name}_contact.jpg"))
        print(path, len(ims), "pages", f"{os.path.getsize(path) / 1e6:.1f} MB", "| contact sheet:", sheet); return path


# ---------------------------------------------------------------- compose helpers: overlaps as ONE RGBA
def _cached(cache, tag, srcs, params):
    os.makedirs(cache, exist_ok=True)
    h = hashlib.md5((tag + repr([os.path.abspath(s) for s in srcs]) + repr(params)).encode()).hexdigest()[:12]
    dst = os.path.join(cache, f"{tag}_{h}.png")
    fresh = os.path.exists(dst) and os.path.getmtime(dst) > max(os.path.getmtime(s) for s in srcs)
    return dst, fresh


def _shadow(im, k=0.35, blur=30, col=(20, 14, 8)):
    s = Image.new("RGBA", im.size, col + (0,)); s.putalpha(im.getchannel("A").point(lambda v: int(v * k)))
    pad = int(blur * 3); big = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    big.alpha_composite(s, (pad, pad)); return big.filter(ImageFilter.GaussianBlur(blur)), pad


def couple(front, back, cache, dx=0.40, dy=0.08, turn=4.0, shadow=0.35):
    """Front leading, its own back tucked behind (up-right, turned a touch); the front's soft shadow lands only on the back."""
    dst, fresh = _cached(cache, "couple", [front, back], (dx, dy, turn, shadow))
    if fresh: return dst
    f = Image.open(front).convert("RGBA"); bk = Image.open(back).convert("RGBA")
    if bk.size != f.size: bk = bk.resize(f.size, Image.LANCZOS)
    w, h = f.size; bk = bk.rotate(-turn, resample=Image.BICUBIC, expand=True)
    W_, H_ = int(w * (1 + dx) + (bk.width - w)), int(h * (1 + dy) + (bk.height - h))
    out = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); fx, fy = 0, H_ - h
    out.alpha_composite(bk, (W_ - bk.width, 0))
    sh = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); s = Image.new("RGBA", f.size, (20, 14, 8, 255))
    s.putalpha(f.getchannel("A").point(lambda v: int(v * shadow)))
    sh.alpha_composite(s, (fx + int(w * 0.035), fy - int(h * 0.01))); sh = sh.filter(ImageFilter.GaussianBlur(w * 0.03))
    m = np.minimum(np.asarray(sh.getchannel("A")), np.asarray(out.getchannel("A")))
    sh.putalpha(Image.fromarray(m.astype(np.uint8))); out.alpha_composite(sh); out.alpha_composite(f, (fx, fy))
    out.save(dst); return dst


def fan(paths, cache, step=0.62, angle=6.0, arc=22, shadow=0.30):
    """A hand of cards: items overlap left to right, the outer ones turned out and dropped on an arc."""
    dst, fresh = _cached(cache, "fan", paths, (step, angle, arc, shadow))
    if fresh: return dst
    ims = [Image.open(p).convert("RGBA") for p in paths]; bw, bh = ims[0].size
    ims = [im if im.size == (bw, bh) else im.resize((bw, bh), Image.LANCZOS) for im in ims]
    n = len(ims); mid = (n - 1) / 2; st = int(bw * step); pad = 400
    cv = Image.new("RGBA", (bw + (n - 1) * st + 2 * pad, bh + 2 * pad), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        r = im.rotate((mid - i) * angle, resample=Image.BICUBIC, expand=True)
        x = pad + i * st + bw // 2 - r.width // 2; y = pad + int(abs(mid - i) ** 2 * arc) + bh // 2 - r.height // 2
        s, p = _shadow(r, shadow, 30); cv.alpha_composite(s, (x - p - 30, y - p + 30)); cv.alpha_composite(r, (x, y))
    cv.crop(cv.getbbox()).save(dst); return dst


def toss(paths, cache, seed=7, spread=0.55, max_turn=14, shadow=0.40):
    """Items thrown loosely on a surface: seeded turns and offsets, each casting its own shadow."""
    dst, fresh = _cached(cache, "toss", paths, (seed, spread, max_turn, shadow))
    if fresh: return dst
    rng = np.random.default_rng(seed); ims = [Image.open(p).convert("RGBA") for p in paths]
    bh = max(im.height for im in ims); n = len(ims); cols = int(np.ceil(np.sqrt(n * 1.6))); rows = int(np.ceil(n / cols))
    cw = int(max(im.width for im in ims) * (1 - spread * 0.5)); ch = int(bh * 0.8); pad = 400
    cv = Image.new("RGBA", (cols * cw + 2 * pad + cw, rows * ch + 2 * pad + bh), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        r = im.rotate(float(rng.uniform(-max_turn, max_turn)), resample=Image.BICUBIC, expand=True)
        x = pad + (i % cols) * cw + int(rng.uniform(-0.15, 0.15) * cw) + ((i // cols) % 2) * cw // 2
        y = pad + (i // cols) * ch + int(rng.uniform(-0.12, 0.12) * ch)
        s, p = _shadow(r, shadow, 24); cv.alpha_composite(s, (x - p + 24, y - p + 34)); cv.alpha_composite(r, (x, y))
    cv.crop(cv.getbbox()).save(dst); return dst


def bleed(path, cache, box_w, box_h, scale_h, cx, cy, angle=-9, shadow=0.45):
    """One item, turned and scaled, cropped to a box that sits flush with the page edge, so it bleeds off the page
    without tripping the off-page guard. Place it with img(dst, page_w - box_w, 0, box_w, box_h)."""
    dst, fresh = _cached(cache, "bleed", [path], (box_w, box_h, scale_h, cx, cy, angle, shadow))
    if fresh: return dst
    im = Image.open(path).convert("RGBA"); k = scale_h / im.height
    im = im.resize((int(im.width * k), int(scale_h)), Image.LANCZOS); r = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    big = Image.new("RGBA", (box_w + 2 * r.width, box_h + 2 * r.height), (0, 0, 0, 0))
    ox, oy = r.width + cx - r.width // 2, r.height + cy - r.height // 2
    s, p = _shadow(r, shadow, 40, (10, 0, 20)); big.alpha_composite(s, (ox - p + 40, oy - p + 50)); big.alpha_composite(r, (ox, oy))
    big.crop((r.width, r.height, r.width + box_w, r.height + box_h)).save(dst); return dst


def ar(path):
    with Image.open(path) as im: return im.width / im.height
