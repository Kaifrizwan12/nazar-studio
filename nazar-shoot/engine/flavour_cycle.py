"""Flavour-cycle film engine: one short product film that cycles through every item of a range.

For any brand and any range (pouches, bottles, boxes, tins): each item gets its own tint ground with its name set
huge in slow, soft-focus marquee rows, the real pack render (transparent PNG) eased in with a small sway, a soft
plus a tight contact shadow (the tight one keeps seal teeth and notches readable), a light sweep masked to the
pack, vignette and grain. Items change with a crisp diagonal light-edge wipe (cinematic) or a hard cut on the beat
(snap), then the film lands on an end card. Outputs MP4 (H.264 High, yuv420p, faststart, no edit list), GIF,
optional animated WebP, a contact strip, review stills and a QA report (timing, platform spec, flash safety).

Why the wipe is crisp: a wide feathered blend shows two packs at once and doubles their type. The edge is a few
pixels wide; the glow on it is light, not a mix of the two frames (the self-test measures both).

CLI
  python flavour_cycle.py job.json [--out DIR] [--stills] [--aspect 9:16] [--platform tiktok] [--style snap]
  python flavour_cycle.py --pack a.png --pack b.png --title "BRAND" --tagline "One line." [options]
  python flavour_cycle.py --platforms           list platform presets (size, fps, safe zones, limits)
  python flavour_cycle.py --selftest            synthetic pouches, every check, PASS/FAIL (about 60 s)

Job file (plain JSON; relative paths resolve against the job file):
  {"items":   [{"name": "Mango", "pack": "renders/mango.png", "tint": "auto", "label": ["MANGO"]}, ...],
   "brand":   {"title": "BRAND", "tagline": "ONE LINE ABOUT THE RANGE", "sign": "",
               "font_display": null, "font_text": null, "paper": "#F4F1EA", "ink": "#1C1A17"},
   "options": {"aspect": "4:5", "platform": null, "fps": 30, "style": "cinematic", "rounds": null,
               "loop": false, "endcard": true, "music": null, "bpm": null, "gif": true, "webp": false,
               "name": "flavour-cycle", "out": "out/motion"}}
  tint      "#RRGGBB" or "auto" (dominant print colour sampled from the pack's opaque pixels)
  label     marquee lines behind the pack (default: the name in capitals)
  aspect    "4:5" "1:1" "9:16" "16:9", any "a:b", or "WxH" in pixels (made even for yuv420p)
  platform  a preset from PLATFORMS: sets size, fps cap, safe zone, bitrate and the duration limit it checks
  style     cinematic: 36-frame shots (1.2 s at 30 fps), 12-frame light-edge wipe centred on the beat, one round
            snap:      hard cut every 14 frames, second round 4 frames faster, 96.5 -> 100% pop
  loop      end on the exact first frame, so a looping player (GIF, muted autoplay) has no jump; no hero repeat
  bpm       cut on the music's beat: each shot is a whole number of beats nearest the style's own length
  music     audio file muxed as AAC-LC 48 kHz, padded or trimmed to the film, 0.5 s fade out. Silent by default.

Library
  from flavour_cycle import Film
  Film(job_dict_or_path).render(out_dir)    # returns the QA report dict

Flash safety (WCAG 2.3.1 / 2.3.2 general and red flash thresholds) is analysed on every render; a shot is never
shorter than fps/3 frames (at most three cuts a second, i.e. at most 1.5 flashes a second even between a dark and a
light tint). The analyser is a guard, not a certified Harding/PEAT test: for broadcast, run one of those too.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.normpath(os.path.join(HERE, "..", "..", "nazar-core", "engine", "fonts"))
FONT_DISPLAY = os.path.join(FONTS, "Anton-Regular.ttf")              # SIL OFL
FONT_TEXT = os.path.join(FONTS, "SpaceGrotesk-Medium.ttf")           # SIL OFL

# Platform presets (sources and dates: ../references/research_flavour_cycle.md). Safe zone = fractions of the
# frame kept free of key content: (top, bottom, left, right). max_s = the longest film this engine lets through
# without a warning (the conservative figure where sources disagree). kbps = target video bitrate (None: CRF 18).
PLATFORMS = {
    "instagram-feed":    dict(size=(1080, 1350), fps=30, safe=(0.05, 0.05, 0.05, 0.05), max_s=90,  kbps=None),
    "instagram-reels":   dict(size=(1080, 1920), fps=30, safe=(0.14, 0.35, 0.06, 0.06), max_s=90,  kbps=None),
    "instagram-stories": dict(size=(1080, 1920), fps=30, safe=(0.14, 0.35, 0.06, 0.06), max_s=60,  kbps=None),
    "tiktok":            dict(size=(1080, 1920), fps=30, safe=(0.125, 0.344, 0.111, 0.111), max_s=600, kbps=None),
    "youtube-shorts":    dict(size=(1080, 1920), fps=30, safe=(0.14, 0.35, 0.06, 0.12), max_s=180, kbps=8000),
    "youtube":           dict(size=(1920, 1080), fps=60, safe=(0.05, 0.05, 0.05, 0.05), max_s=None, kbps=8000),
    "linkedin":          dict(size=(1920, 1080), fps=30, safe=(0.05, 0.05, 0.05, 0.05), max_s=1800, kbps=None),
    "linkedin-square":   dict(size=(1080, 1080), fps=30, safe=(0.05, 0.05, 0.05, 0.05), max_s=1800, kbps=None),
    "behance":           dict(size=(1280, 720),  fps=30, safe=(0.04, 0.04, 0.04, 0.04), max_s=None, kbps=None),
    "x":                 dict(size=(1280, 720),  fps=60, safe=(0.05, 0.05, 0.05, 0.05), max_s=140, kbps=5000),
    "x-portrait":        dict(size=(720, 1280),  fps=60, safe=(0.05, 0.12, 0.05, 0.05), max_s=140, kbps=5000),
    "x-square":          dict(size=(720, 720),   fps=60, safe=(0.05, 0.05, 0.05, 0.05), max_s=140, kbps=5000),
}
GIF_LIMITS = dict(frames=350, mb=15, w=1280, h=1080)                  # X's animated-GIF limits: a sane web ceiling

STYLES = {   # frame counts at 30 fps; scaled to the film's fps
    "cinematic": dict(beat=36, wipe=12, fast=0, rounds=1),
    "snap":      dict(beat=14, wipe=0,  fast=4, rounds=2),
}
HOLD, FADE, END = 30, 12, 40          # hero hold, fade into the end card, end card hold (frames at 30 fps)
GLOW = 26                             # light-edge glow peak (8-bit levels): a thin light edge, not a flare
SWEEP = 0.0                           # no light sweep over the pack by default: a white band read as a cheap glaze (real review)

DEMO_NOTE = "DEMO ONLY: the owner's stand-in range, used as an example; not part of the engine."


# ------------------------------------------------------------------ small helpers

def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgbhex(c):
    return "#%02x%02x%02x" % tuple(int(v) for v in c[:3])


def srgb_to_lin(a):
    a = np.asarray(a, np.float32) / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def rel_lum(rgb):
    """WCAG relative luminance of an (..., 3) sRGB uint8 array."""
    l = srgb_to_lin(rgb)
    return l[..., 0] * 0.2126 + l[..., 1] * 0.7152 + l[..., 2] * 0.0722


def mix(c, target, k):
    return tuple(int(round(a + (b - a) * k)) for a, b in zip(c, target))


def ease(t):
    """Cosine ease in-out (slow in, slow out)."""
    return 0.5 - 0.5 * math.cos(math.pi * min(1.0, max(0.0, t)))


def ease_out_cubic(t):
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** 3


def parse_size(aspect, platform=None):
    """'4:5' -> (1080, 1350); '16:9' -> (1920, 1080); '1280x720' -> (1280, 720). Always even (yuv420p)."""
    if not aspect:
        return PLATFORMS[platform]["size"] if platform else (1080, 1350)
    s = str(aspect).lower().replace(" ", "")
    if "x" in s:
        w, h = (int(float(v)) for v in s.split("x"))
    else:
        a, b = (float(v) for v in s.split(":"))
        if a <= b:
            w, h = 1080, 1080 * b / a
        else:
            w, h = 1080 * a / b, 1080
            if a / b >= 16 / 9 - 1e-6:
                w, h = 1920 * (a / b) / (16 / 9), 1080
    w, h = int(round(w)), int(round(h))
    return w - w % 2, h - h % 2


def font(path, size):
    return ImageFont.truetype(path, max(4, int(round(size))))


def cap_size(path, cap_px):
    """Font size whose capital H is cap_px tall."""
    f = font(path, 200)
    b = f.getbbox("H")
    return 200 * cap_px / max(1, b[3] - b[1])


def draw_tracked(d, text, cx, base_y, f, fill, track=0.0):
    """Centred text on a baseline, with letter spacing (track = fraction of the font size)."""
    sp = f.size * track
    widths = [f.getlength(ch) for ch in text]
    total = sum(widths) + sp * max(0, len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        d.text((x, base_y), ch, font=f, fill=fill, anchor="ls")
        x += w + sp
    return total


def auto_tint(img):
    """The pack's dominant print colour: opaque pixels, median-cut, ranked by area and saturation."""
    im = img.convert("RGBA")
    s = 96 / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    a = np.asarray(im)
    px = a[a[..., 3] > 200][:, :3]
    if len(px) < 10:
        return "#c8c8c8"
    q = Image.fromarray(px[None].astype(np.uint8)).quantize(colors=8, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    best, best_s = None, -1
    for count, idx in q.getcolors():
        c = tuple(pal[idx * 3: idx * 3 + 3])
        lum = float(rel_lum(np.array(c, np.uint8)))
        sat = (max(c) - min(c)) / 255
        score = count * (0.3 + sat) * (0.05 if lum < 0.04 or lum > 0.90 else 1)
        if score > best_s:
            best, best_s = c, score
    return rgbhex(best)


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


# ------------------------------------------------------------------ flash safety

class FlashMeter:
    """WCAG 2.3.1 general and red flash check on a coarse grid (approximation of a Harding-style analyser).

    general transition: relative luminance moves >= 0.10 from the last extreme, the darker state < 0.80
    red transition:     a cell enters or leaves saturated red (R/(R+G+B) >= 0.8) with a chroma swing
    flash = a pair of opposing transitions; fail = more than 3 flashes (7+ transitions) inside any one second over
    an area >= 25% of a 10-degree field (341 x 256 on 1024 x 768 = 11.1% of the frame; whole-frame viewing).
    """
    AREA = 341 * 256 / (1024 * 768)

    def __init__(self, fps, grid=48):
        self.fps, self.grid = fps, grid
        self.ext = self.trend = self.red = None
        self.hist, self.rhist = [], []

    def add(self, img):
        g = self.grid
        w, h = img.size
        small = np.asarray(img.convert("RGB").resize((g, max(2, int(g * h / w))), Image.BOX), np.uint8)
        L = rel_lum(small)
        lin = srgb_to_lin(small)
        red = (lin[..., 0] / np.maximum(lin.sum(-1), 1e-6) >= 0.8) & ((lin[..., 0] - lin[..., 1] - lin[..., 2]) * 320 > 20)
        if self.ext is None:
            self.ext, self.trend, self.red = L.copy(), np.zeros(L.shape, np.int8), red
            self.hist.append(np.zeros(L.shape, bool)); self.rhist.append(np.zeros(L.shape, bool))
            return
        d = L - self.ext
        dark = np.minimum(L, self.ext) < 0.80
        up = (d >= 0.10) & dark & (self.trend <= 0)
        down = (d <= -0.10) & dark & (self.trend >= 0)
        tr = up | down
        self.trend = np.where(up, 1, np.where(down, -1, self.trend)).astype(np.int8)
        ext_new = np.where(tr, L, self.ext)
        ext_new = np.where((self.trend > 0) & (L > ext_new), L, ext_new)      # keep riding the extreme
        ext_new = np.where((self.trend < 0) & (L < ext_new), L, ext_new)
        self.ext = ext_new
        self.hist.append(tr)
        self.rhist.append(red != self.red)
        self.red = red

    def report(self):
        if not self.hist:
            return dict(max_flashes_per_s=0.0, max_red_flashes_per_s=0.0, ok=True)
        win = max(1, int(round(self.fps)))
        out = {}
        for key, hist in (("max_flashes_per_s", self.hist), ("max_red_flashes_per_s", self.rhist)):
            a = np.stack(hist).astype(np.int16)
            c = np.cumsum(a, 0)
            c = np.concatenate([np.zeros((1,) + a.shape[1:], np.int16), c], 0)
            n = len(a)
            counts = c[win:] - c[:-win] if n >= win else c[-1:] - c[:1]
            # transitions per window over the worst area of the threshold size
            k = max(1, int(math.ceil(self.AREA * counts[0].size)))
            worst = np.sort(counts.reshape(len(counts), -1), axis=1)[:, -k] if len(counts) else np.array([0])
            out[key] = round(float(worst.max()) / 2, 2)
        out["ok"] = out["max_flashes_per_s"] <= 3 and out["max_red_flashes_per_s"] <= 3
        return out


# ------------------------------------------------------------------ the film

class Film:
    def __init__(self, job, base=None, **override):
        if isinstance(job, str):
            base = base or os.path.dirname(os.path.abspath(job))
            with open(job, encoding="utf-8") as fh:
                job = json.load(fh)
        self.base = base or os.getcwd()
        self.job = job
        o = dict(job.get("options", {}))
        o.update({k: v for k, v in override.items() if v is not None})
        self.opt = o
        self.platform = o.get("platform")
        if self.platform and self.platform not in PLATFORMS:
            raise SystemExit(f"unknown platform {self.platform!r}; see --platforms")
        P = PLATFORMS.get(self.platform, {})
        self.W, self.H = parse_size(o.get("aspect"), self.platform)
        fps = int(o.get("fps") or 30)
        self.warnings = []
        if P and fps > P["fps"]:
            self.warnings.append(f"fps {fps} above the {self.platform} cap; using {P['fps']}")
            fps = P["fps"]
        self.fps = fps
        self.style = o.get("style", "cinematic")
        if self.style not in STYLES:
            raise SystemExit(f"style must be one of {list(STYLES)}")
        self.loop = bool(o.get("loop", False))
        self.endcard = bool(o.get("endcard", True))
        safe = P.get("safe", (0.05, 0.05, 0.05, 0.05))
        if o.get("safe"):
            safe = tuple(float(v) for v in o["safe"])
        t, b, l, r = safe
        self.safe = (int(self.W * l), int(self.H * t), int(self.W * (1 - r)), int(self.H * (1 - b)))
        br = dict(job.get("brand", {}))
        self.brand = dict(title=br.get("title", ""), tagline=br.get("tagline", ""), sign=br.get("sign", ""),
                          paper=hexrgb(br.get("paper", "#F4F1EA")), ink=hexrgb(br.get("ink", "#1C1A17")))
        self.font_display = self._path(br.get("font_display")) or FONT_DISPLAY
        self.font_text = self._path(br.get("font_text")) or FONT_TEXT
        self.items = [self._item(it) for it in job["items"]]
        if not self.items:
            raise SystemExit("no items")
        self._plan()
        yy, xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        cine = self.style == "cinematic"
        self.vig = (1 - (0.34 if cine else 0.22) * (((xx - self.W / 2) / (self.W * 0.62)) ** 2 + ((yy - self.H / 2) / (self.H * 0.62)) ** 2)).clip(0.55 if cine else 0.7, 1)[..., None]
        self.key = (0.88 + 0.12 * np.exp(-(((xx - self.W * 0.44) / (self.W * 0.30)) ** 2 + ((yy - self.H * 0.40) / (self.H * 0.36)) ** 2)))[..., None].astype(np.float32)
        self.grain = np.random.default_rng(7).normal(0, 1, (4, self.H, self.W)).astype(np.float32) * (4.0 * self.H / 1350 + 1.0)
        self.edge = ((xx + yy * 0.35) / (self.W + self.H * 0.35)).astype(np.float32)
        self._cache = {}

    # ---------- inputs
    def _path(self, p):
        if not p:
            return None
        return p if os.path.isabs(p) else os.path.normpath(os.path.join(self.base, p))

    def _item(self, it):
        path = self._path(it.get("pack"))
        if not path or not os.path.exists(path):
            raise SystemExit(f"pack render not found: {path}")
        pack = Image.open(path).convert("RGBA")
        bb = pack.split()[3].getbbox()
        if bb:
            pack = pack.crop(bb)
        tint = it.get("tint", "auto")
        tint = hexrgb(auto_tint(pack) if tint in (None, "", "auto") else tint)
        name = it.get("name") or os.path.splitext(os.path.basename(path))[0]
        label = it.get("label") or [name.upper()]
        if isinstance(label, str):
            label = [label]
        return dict(name=name, pack=pack, tint=tint, label=[str(s) for s in label], path=path)

    # ---------- timeline
    def _plan(self):
        S = STYLES[self.style]
        k = self.fps / 30
        beat = max(2, round(S["beat"] * k))
        wipe = int(round(S["wipe"] * k / 2)) * 2
        min_shot = max(int(math.ceil(self.fps / 3)), wipe + 2)          # never more than 3 cuts a second
        fast = max(min_shot, beat - round(S["fast"] * k))
        rounds = int(self.opt.get("rounds") or S["rounds"])
        n = len(self.items)
        bpm = self.opt.get("bpm")
        seq = [i for _ in range(rounds) for i in range(n)]
        lens = []
        if bpm:
            period = self.fps * 60 / float(bpm)
            kb = max(1, round(beat / period))
            while kb * period < min_shot:
                kb += 1
            kb2 = max(1, round(kb * 0.7)) if S["fast"] else kb
            if kb2 * period < min_shot:
                kb2 = kb
            beats = [kb if j < n else kb2 for j in range(len(seq))]
            acc = np.cumsum([0] + beats) * period                      # boundaries on the beat, no drift
            lens = [int(round(acc[j + 1])) - int(round(acc[j])) for j in range(len(seq))]
            self.beat_frames = (kb * period, kb2 * period)
        else:
            lens = [beat if j < n else fast for j in range(len(seq))]
            self.beat_frames = (beat, fast)
        hold = round(HOLD * k)
        if not self.loop:
            seq.append(0)
            lens.append(beat + hold)
        self.seq, self.lens, self.wipe_n = seq, lens, wipe
        self.starts = [0] + [int(v) for v in np.cumsum(lens)]
        self.S = int(self.starts[-1])
        self.fade = round(FADE * k) if self.endcard else 0
        self.endhold = round(END * k) if self.endcard else 0
        self.tail = (wipe if wipe else 1) if self.loop else 0
        self.total = self.S + self.fade + self.endhold + self.tail
        # readability: the marquee words must be readable inside one shot (about 3 words a second + 0.5 s)
        for it in self.items:
            words = sum(len(s.split()) for s in it["label"])
            need = 0.5 + words / 3.0
            if min(lens[:n]) / self.fps < need:
                self.warnings.append(f"'{it['name']}': {words} words need about {need:.1f} s; shots are "
                                     f"{min(lens[:n]) / self.fps:.2f} s (shorten the label or use cinematic)")

    def keyframes(self):
        """Mid-shot frame of each item's first appearance, then the end card (for the strip)."""
        ks = []
        for j in range(min(len(self.items), len(self.seq))):
            ks.append(int(self.starts[j] + self.lens[j] // 2))
        ks.append(self.total - 1 - self.tail if self.endcard else self.total - 1)
        return ks

    # ---------- per-item assets
    def _assets(self, idx):
        if idx in self._cache:
            return self._cache[idx]
        it = self.items[idx]
        sx0, sy0, sx1, sy1 = self.safe
        sw, sh = sx1 - sx0, sy1 - sy0
        ar = it["pack"].width / it["pack"].height
        ph = min(0.72 * self.H, 0.84 * sh, 0.78 * sw / ar)
        base = it["pack"].resize((max(1, int(ph * ar)), max(1, int(ph))), Image.LANCZOS)
        # marquee: one seamless, pre-blurred row per label line, tone on tone
        tint = it["tint"]
        lum = float(rel_lum(np.array(tint, np.uint8)))
        ink = mix(tint, (0, 0, 0), 0.10) if lum > 0.62 else mix(tint, (255, 255, 255), 0.28)
        cap = 0.185 * self.H
        pitch = int(round(cap * 1.27))
        f = font(self.font_display, cap_size(self.font_display, cap))
        rows = []
        for line in it["label"]:
            word = line.upper() + "  "
            unit = f.getlength(word)
            reps = int(math.ceil(self.W * 2 / unit)) + 3
            strip = Image.new("RGB", (int(unit * reps) + 2, pitch), tint)
            ImageDraw.Draw(strip).text((0, pitch / 2 + cap / 2), word * reps, font=f, fill=ink, anchor="ls")
            rows.append((strip.filter(ImageFilter.GaussianBlur(4.0 * self.H / 1080)), unit))   # shallow depth of field
        self._cache[idx] = (base, rows, pitch)
        return self._cache[idx]

    # ---------- frames
    def background(self, idx, gi):
        base, rows, pitch = self._assets(idx)
        c = Image.new("RGB", (self.W, self.H), self.items[idx]["tint"])
        nrows = int(math.ceil(self.H / pitch)) + 1
        y0 = (self.H - nrows * pitch) // 2
        for r in range(nrows):
            strip, unit = rows[r % len(rows)]
            sp = (2.2 + 0.8 * (r % 2)) * self.H / 1350
            off = (gi * sp + unit * 0.37 * r) % unit
            x = -int(off) if r % 2 == 0 else -int(unit - off)
            c.paste(strip, (x - int(unit), y0 + r * pitch))
        return c

    def shot(self, idx, t, gi, pop=None, pack=True, info=None):
        """One frame of item idx at shot time t (0..1), global frame gi. Returns an RGB image."""
        base, _, _ = self._assets(idx)
        c = self.background(idx, gi).convert("RGBA")
        sx0, sy0, sx1, sy1 = self.safe
        if pack:
            if self.style == "cinematic":
                sc = 0.93 + 0.07 * ease(t)
                ang = 1.2 * math.sin(t * math.pi * 0.9 + 0.4)
            else:
                sc = 0.965 + 0.035 * ease_out_cubic(pop if pop is not None else t)
                ang = 0.0
            ph = max(2, int(base.height * sc))
            p = base.resize((max(1, int(base.width * sc)), ph), Image.BICUBIC)
            if ang:
                p = p.rotate(ang, Image.BICUBIC, expand=True)
            px = int((sx0 + sx1) / 2 - p.width / 2)
            py = int(sy0 + 0.51 * (sy1 - sy0) - p.height / 2)
            a = np.asarray(p.split()[3], np.float32) / 255
            kk = ph / 1000
            for m, blur, (dx, dy) in ((135, 34, (22, 38)), (150, 3, (6, 9))):      # soft drop + tight contact
                sh = Image.fromarray((a * m).astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(0.6, blur * kk)))
                blk = Image.new("RGBA", p.size, (0, 0, 0, 0))
                blk.putalpha(sh)
                c.alpha_composite(blk, (px + int(dx * kk), py + int(dy * kk)))
            if self.style == "cinematic" and SWEEP > 0:                          # optional light sweep (off by default)
                yy, xx = np.mgrid[0:p.height, 0:p.width].astype(np.float32)
                pos = (-0.4 + 1.8 * ease(t)) * (p.width + p.height)
                band = np.exp(-(((xx + yy * 0.6) - pos) / (p.width * 0.16)) ** 2) * a * SWEEP
                pa = np.asarray(p, np.float32).copy()
                pa[..., :3] += (255 - pa[..., :3]) * band[..., None]
                p = Image.fromarray(pa.clip(0, 255).astype(np.uint8))
            if self.style == "cinematic":
                p = p.filter(ImageFilter.UnsharpMask(radius=1.4 * kk + 0.6, percent=55, threshold=2))   # crisp print detail
            c.alpha_composite(p, (px, py))
            if info is not None:
                info.update(box=(px, py, p.width, p.height), alpha=a)
        im = np.asarray(c.convert("RGB"), np.float32)
        if self.style == "cinematic":                     # key-light pool (never brighter than the tint) + S-curve grade
            im = np.clip(im * self.key, 0, 255); im = (im / 255.0 - 0.06 * np.sin(2 * np.pi * im / 255.0)) * 255.0
        im = im * self.vig + self.grain[gi % 4][..., None]
        return Image.fromarray(im.clip(0, 255).astype(np.uint8))

    def wipe(self, a_im, b_im, t, glow=GLOW):
        """Crisp diagonal reveal of B over A with a soft light on the edge (never a blend of two frames)."""
        if t >= 1:
            return b_im.copy()
        d = ease(t) * 1.1 - self.edge
        m = np.clip(d / 0.006 + 0.5, 0, 1)[..., None]
        g = (np.exp(-(d / 0.015) ** 2) * glow)[..., None]
        out = np.asarray(a_im, np.float32) * (1 - m) + np.asarray(b_im, np.float32) * m + g
        return Image.fromarray(out.clip(0, 255).astype(np.uint8))

    def end_card(self):
        if "end" in self._cache:
            return self._cache["end"]
        W, H = self.W, self.H
        c = Image.new("RGB", (W, H), self.brand["paper"])
        d = ImageDraw.Draw(c)
        n = len(self.items)
        bar = max(4, int(H * 0.044))
        for i, it in enumerate(self.items):
            d.rectangle([int(i * W / n), H - bar, int((i + 1) * W / n), H], fill=it["tint"])
        sx0, sy0, sx1, sy1 = self.safe
        sw, sh = sx1 - sx0, sy1 - sy0
        cx = (sx0 + sx1) / 2
        ink = self.brand["ink"]
        title = self.brand["title"]
        if title:
            cap = min(0.16 * min(W, sh), 0.30 * sh)
            f = font(self.font_display, cap_size(self.font_display, cap))
            while f.getlength(title) > 0.82 * sw and f.size > 8:
                f = font(self.font_display, f.size * 0.92)
            capr = f.getbbox("H")[3] - f.getbbox("H")[1]
            ty = sy0 + 0.50 * sh
            d.text((cx, ty), title, font=f, fill=ink, anchor="ms")
        else:
            capr, ty = 0, sy0 + 0.5 * sh
        if self.brand["tagline"]:
            tcap = max(6, 0.024 * min(W, H))
            ft = font(self.font_text, cap_size(self.font_text, tcap))
            while ft.getlength(self.brand["tagline"]) * 1.12 > 0.86 * sw and ft.size > 6:
                ft = font(self.font_text, ft.size * 0.92)
            draw_tracked(d, self.brand["tagline"], cx, ty + max(capr * 0.30, tcap * 2.4), ft, ink, 0.12)
        if self.brand["sign"]:
            fs = font(self.font_text, cap_size(self.font_text, max(5, 0.016 * min(W, H))))
            draw_tracked(d, self.brand["sign"], cx, sy1 - 0.04 * sh, fs, ink, 0.18)
        self._cache["end"] = c
        return c

    def _shot_at(self, j, g):
        """Item frame for timeline shot j at global frame g (handles shot time and wipes' overlap)."""
        h = self.wipe_n // 2
        a = self.starts[j] - (h if j > 0 else 0)
        last = j == len(self.seq) - 1
        b = self.starts[j + 1] + (0 if last else self.wipe_n - h)
        t = (g - a) / max(1, b - a)
        pop = (g - self.starts[j]) / max(1, self.lens[j])
        return self.shot(self.seq[j], t, g, pop=pop)

    def frame(self, g):
        """Global frame g of the film."""
        if g == 0 or (self.loop and g == self.total - 1):
            if "f0" not in self._cache:
                self._cache["f0"] = self._shot_at(0, 0)
            if g == 0 or self.tail:
                return self._cache["f0"].copy()
        if g < self.S:
            j = int(np.searchsorted(self.starts, g, side="right") - 1)
            h = self.wipe_n // 2
            if self.wipe_n:
                for jb in (j, j + 1):                   # a boundary within half a wipe of g
                    if 0 < jb < len(self.seq) and self.starts[jb] - h <= g < self.starts[jb] + (self.wipe_n - h):
                        tt = (g - (self.starts[jb] - h) + 1) / self.wipe_n
                        return self.wipe(self._shot_at(jb - 1, g), self._shot_at(jb, g), tt)
            return self._shot_at(j, g)
        e0 = self.S + self.fade
        if g < e0:
            return Image.blend(self._shot_at(len(self.seq) - 1, g), self.end_card(), (g - self.S + 1) / self.fade)
        if g < e0 + self.endhold:
            return self.end_card().copy()
        src = self.end_card() if self.endcard else self._shot_at(len(self.seq) - 1, g)
        if self.wipe_n:
            return self.wipe(src, self._cache["f0"] if "f0" in self._cache else self.frame(0), (g - (e0 + self.endhold) + 1) / self.wipe_n)
        return self.frame(0)

    def frames(self):
        for g in range(self.total):
            yield g, self.frame(g)

    # ---------- outputs
    def stills(self, out_dir, name=None):
        """Review stills before any video: start, mid-shot, mid-wipe (or last frame before the cut), next shot,
        end card, plus the safe zone drawn on the mid-shot. One sheet."""
        os.makedirs(out_dir, exist_ok=True)
        name = name or self.opt.get("name", "flavour-cycle")
        s1 = self.starts[1] if len(self.starts) > 2 else self.lens[0] // 2
        picks = [("start", 0), ("mid-shot", self.lens[0] // 2),
                 ("mid-wipe" if self.wipe_n else "before cut", s1 if self.wipe_n else s1 - 1),
                 ("next shot", min(self.total - 1, s1 + self.wipe_n)), ("end card", self.keyframes()[-1])]
        ims = []
        for lab, g in picks:
            im = self.frame(g)
            if lab == "mid-shot":
                im = im.copy()
                ImageDraw.Draw(im).rectangle(self.safe, outline=(255, 0, 80), width=max(2, self.W // 400))
            ims.append((lab, im))
        tw = 360
        th = int(tw * self.H / self.W)
        sheet = Image.new("RGB", (tw * len(ims) + 10 * (len(ims) + 1), th + 44), (24, 24, 24))
        d = ImageDraw.Draw(sheet)
        lf = font(FONT_TEXT, 16)
        for i, (lab, im) in enumerate(ims):
            x = 10 + i * (tw + 10)
            sheet.paste(im.resize((tw, th), Image.LANCZOS), (x, 10))
            d.text((x, th + 18), f"{lab}  (frame {picks[i][1]})", font=lf, fill=(230, 230, 230))
        p = os.path.join(out_dir, name + "_stills.jpg")
        sheet.save(p, quality=90)
        return p

    def render(self, out_dir=None, name=None, quiet=False):
        out_dir = out_dir or self._path(self.opt.get("out")) or os.path.join(self.base, "out", "motion")
        os.makedirs(out_dir, exist_ok=True)
        name = name or self.opt.get("name", "flavour-cycle")
        ff = ffmpeg_exe()
        if not ff:
            raise SystemExit("ffmpeg not found: pip install imageio-ffmpeg, or put ffmpeg on the PATH")
        P = PLATFORMS.get(self.platform, {})
        mp4 = os.path.join(out_dir, name + ".mp4")
        rate = ["-b:v", f"{P['kbps']}k", "-maxrate", f"{int(P['kbps'] * 1.5)}k", "-bufsize", f"{P['kbps'] * 2}k"] \
            if P.get("kbps") else ["-crf", "18"]
        music = self._path(self.opt.get("music"))
        dur = self.total / self.fps
        cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{self.W}x{self.H}", "-r", str(self.fps), "-i", "-"]
        if music:
            cmd += ["-i", music, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-af", f"apad,afade=t=out:st={max(0, dur - 0.5):.3f}:d=0.5", "-t", f"{dur:.3f}"]
        cmd += ["-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-g", str(self.fps * 2), *rate,
                "-movflags", "+faststart", "-use_editlist", "0", mp4]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        meter = FlashMeter(self.fps)
        keys = set(self.keyframes())
        kept = {}
        for g, im in self.frames():
            proc.stdin.write(im.tobytes())
            meter.add(im)
            if g in keys:
                kept[g] = im
        proc.stdin.close()
        proc.wait()
        out = dict(mp4=mp4, frames=self.total, seconds=round(dur, 3), fps=self.fps, size=[self.W, self.H],
                   style=self.style, loop=self.loop, platform=self.platform)
        tw = 270 if self.H >= self.W else 384
        th = int(tw * self.H / self.W)
        ks = sorted(kept)
        strip = Image.new("RGB", (len(ks) * tw, th))
        for i, k in enumerate(ks):
            strip.paste(kept[k].resize((tw, th), Image.LANCZOS), (i * tw, 0))
        out["strip"] = os.path.join(out_dir, name + "_strip.jpg")
        strip.save(out["strip"], quality=88)
        if self.opt.get("gif", True):
            gw = min(540, self.W)
            gw -= gw % 2
            out["gif"] = os.path.join(out_dir, name + ".gif")
            subprocess.run([ff, "-y", "-i", mp4, "-vf", f"fps=15,scale={gw}:-1:flags=lanczos,split[a][b];"
                            "[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                            "-loop", "0", out["gif"]], stderr=subprocess.DEVNULL)
            gh = int(gw * self.H / self.W)
            nfr = int(math.ceil(dur * 15))
            mb = os.path.getsize(out["gif"]) / 1e6 if os.path.exists(out["gif"]) else 0
            if nfr > GIF_LIMITS["frames"] or mb > GIF_LIMITS["mb"] or gw > GIF_LIMITS["w"] or gh > GIF_LIMITS["h"]:
                self.warnings.append(f"GIF {gw}x{gh}, {nfr} frames, {mb:.1f} MB exceeds the web GIF ceiling "
                                     f"({GIF_LIMITS}); embed the MP4 (muted, autoplay, loop, playsinline)")
        if self.opt.get("webp"):
            out["webp"] = os.path.join(out_dir, name + ".webp")
            r = subprocess.run([ff, "-y", "-i", mp4, "-vf", f"fps=15,scale={min(540, self.W)}:-1:flags=lanczos",
                                "-c:v", "libwebp_anim", "-lossless", "0", "-q:v", "75", "-loop", "0", out["webp"]],
                               stderr=subprocess.DEVNULL)
            if r.returncode:
                self.warnings.append("animated WebP skipped: this ffmpeg has no libwebp_anim encoder")
                out.pop("webp")
        if P.get("max_s") and dur > P["max_s"]:
            self.warnings.append(f"{dur:.1f} s is longer than the {self.platform} limit used here ({P['max_s']} s)")
        out["flash"] = meter.report()
        out["warnings"] = self.warnings
        with open(os.path.join(out_dir, name + "_qa.json"), "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
        if not quiet:
            fl = out["flash"]
            print(f"{self.total} frames  {dur:.2f} s  {self.W}x{self.H} @ {self.fps}  {self.style}{'  loop' if self.loop else ''}")
            print(("PASS" if fl["ok"] else "FAIL") + f" flash safety: {fl['max_flashes_per_s']} general and "
                  f"{fl['max_red_flashes_per_s']} red flashes/s (limit 3)")
            for w in self.warnings:
                print("WARN", w)
            print(mp4)
        return out


# ------------------------------------------------------------------ self-test

def synthetic_pouch(path, tint, name, w=420, h=600):
    """A plain stand-up pouch (no real brand): top seal with teeth, tear notches, gusset, label panel."""
    s = 2
    W, H = w * s, h * s
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    body = [(int(W * 0.04), int(H * 0.06)), (int(W * 0.96), int(H * 0.06)), (int(W * 0.98), int(H * 0.93)),
            (int(W * 0.5), int(H * 0.985)), (int(W * 0.02), int(H * 0.93))]
    d.polygon(body, fill=tint + (255,))
    teeth = 26
    for i in range(teeth):                                   # serrated seal edge along the top
        x0 = W * 0.04 + i * (W * 0.92 / teeth)
        d.polygon([(x0, H * 0.06), (x0 + W * 0.92 / teeth / 2, H * 0.035), (x0 + W * 0.92 / teeth, H * 0.06)], fill=tint + (255,))
    dark = mix(tint, (0, 0, 0), 0.25)
    d.rectangle([int(W * 0.04), int(H * 0.06), int(W * 0.96), int(H * 0.12)], fill=dark + (255,))
    for side in (0, 1):                                      # tear notches cut out of both sides
        x = W * 0.04 if side == 0 else W * 0.96
        dx = W * 0.035 * (1 if side == 0 else -1)
        d.polygon([(x - 2 * (1 if side == 0 else -1), H * 0.14), (x + dx, H * 0.155), (x - 2 * (1 if side == 0 else -1), H * 0.17)], fill=(0, 0, 0, 0))
    d.rounded_rectangle([int(W * 0.16), int(H * 0.36), int(W * 0.84), int(H * 0.70)], radius=int(W * 0.04),
                        fill=mix(tint, (255, 255, 255), 0.75) + (255,))
    f = font(FONT_DISPLAY, cap_size(FONT_DISPLAY, H * 0.07))
    d.text((W / 2, H * 0.56), name, font=f, fill=dark + (255,), anchor="ms")
    im.resize((w, h), Image.LANCZOS).save(path)
    return path


def _strobe_fails():
    """The analyser must catch a real hazard: full-frame black/white at 30 fps."""
    m = FlashMeter(30)
    for i in range(45):
        m.add(Image.new("RGB", (64, 80), (0, 0, 0) if i % 2 else (255, 255, 255)))
    return not m.report()["ok"]


def selftest(out_dir=None):
    tmp = tempfile.mkdtemp(prefix="fcycle_")
    out_dir = out_dir or os.path.join(tmp, "out")
    tints = [(232, 168, 40), (198, 58, 72), (120, 170, 64)]
    names = ["ALPHA", "BETA", "GAMMA"]
    items = [dict(name=n, pack=synthetic_pouch(os.path.join(tmp, f"p{i}.png"), t, n), tint="auto" if i == 0 else rgbhex(t))
             for i, (n, t) in enumerate(zip(names, tints))]
    brand = dict(title="SAMPLE", tagline="THREE FLAVOURS. ONE SHELF.", sign="studio signature")
    small = "216x270"
    checks = []

    def job(**o):
        return dict(items=items, brand=brand, options=dict(o))

    # 1. timing per style (frames at 30 fps, see the docstring for the parts)
    c = Film(job(aspect=small, style="cinematic"), base=tmp)
    checks.append(("cinematic: 3 shots x 36 + hero 66 + fade 12 + end 40 = 226 frames", c.total == 226))
    s = Film(job(aspect=small, style="snap"), base=tmp)
    checks.append(("snap: 3x14 + 3x10 (faster round) + hero 44 + 12 + 40 = 168 frames", s.total == 168))
    lp = Film(job(aspect=small, style="cinematic", loop=True), base=tmp)
    checks.append(("cinematic loop: 3x36 + 12 + 40 + 12-frame wipe home = 172 frames", lp.total == 172))
    b = Film(job(aspect=small, style="snap", bpm=128), base=tmp)
    per = 30 * 60 / 128
    on_beat = all(abs(st / per - round(st / per)) < 0.5 / per + 1e-6 for st in b.starts[:len(b.seq) - 1])
    checks.append((f"bpm 128: every cut within half a frame of a beat, no shot under fps/3", on_beat and min(b.lens) >= 10))
    f60 = Film(job(aspect=small, style="cinematic", fps=60), base=tmp)
    checks.append(("60 fps keeps the same seconds (226 -> 452 frames)", f60.total == 452))
    # 2. dims per aspect
    want = {"4:5": (1080, 1350), "1:1": (1080, 1080), "9:16": (1080, 1920), "16:9": (1920, 1080), "1281x721": (1280, 720)}
    checks.append(("sizes: 4:5 1:1 9:16 16:9 and WxH (made even)", all(parse_size(a) == v for a, v in want.items())))
    for a in ("9:16", "16:9"):
        im = Film(job(aspect=a), base=tmp).frame(5)
        checks.append((f"frame size {a} = {want[a]}", im.size == want[a]))
    pr = Film(job(platform="tiktok"), base=tmp)
    checks.append(("platform preset: tiktok -> 1080x1920, safe zone applied", (pr.W, pr.H) == (1080, 1920) and pr.safe[3] < 0.66 * 1920 + 2))
    # 3. wipe never blends two packs over more than a thin band
    A, B = c.shot(0, 0.9, 30), c.shot(1, 0.1, 30)
    fa, fb = np.asarray(A, np.float32), np.asarray(B, np.float32)
    differ = np.abs(fa - fb).max(-1) > 24
    mid = np.asarray(c.wipe(A, B, 0.5, glow=0), np.float32)
    neither = (np.abs(mid - fa).max(-1) > 8) & (np.abs(mid - fb).max(-1) > 8) & differ
    ghost = neither.sum() / max(1, differ.sum())
    checks.append((f"wipe: pixels mixing A and B mid-wipe {ghost:.2%} (< 2%)", ghost < 0.02))
    midg = np.asarray(c.wipe(A, B, 0.5), np.float32)
    lit = ((np.abs(midg - fa).max(-1) > 8) & (np.abs(midg - fb).max(-1) > 8)).mean()
    checks.append((f"wipe: glow band {lit:.2%} of the frame (< 7%), peak +{GLOW} levels", lit < 0.07))
    # 4. contact shadow at the pack's bottom edge
    info = {}
    shot = np.asarray(c.shot(0, 0.5, 8, info=info), np.float32).mean(-1)
    bare = np.asarray(c.shot(0, 0.5, 8, pack=False), np.float32).mean(-1)
    px, py, pw, ph = info["box"]
    al = info["alpha"]
    rows = np.where(al[:, pw // 3: 2 * pw // 3].max(1) > 0.5)[0]
    yb = py + int(rows.max())
    band = slice(yb + 1, yb + 4)
    xs = slice(px + pw * 2 // 5, px + pw * 3 // 5)
    ratio = shot[band, xs].mean() / max(1, bare[band, xs].mean())
    checks.append((f"contact shadow: just under the base {ratio:.2f} of the bare ground (< 0.85)", ratio < 0.85))
    # 5. end card present, loop closes on frame 0
    last = np.asarray(c.frame(c.total - 1), np.float32)
    paper = np.array(hexrgb("#F4F1EA"), np.float32)
    on_paper = (np.abs(last - paper).max(-1) < 10).mean()
    inked = (last.mean(-1) < 80)[: int(c.H * 0.8)].mean()
    checks.append((f"end card: {on_paper:.0%} paper, title ink present", on_paper > 0.6 and inked > 0.005))
    f0 = np.asarray(lp.frame(0))
    fl = np.asarray(lp.frame(lp.total - 1))
    checks.append(("loop: last frame == first frame (pixel exact)", np.array_equal(f0, fl)))
    # 6. flash safety on every style, and the analyser catches a real strobe
    checks.append(("flash analyser fails a 30 fps black/white strobe", _strobe_fails()))
    reports = {}
    for lab, film in (("cinematic", c), ("snap", s), ("loop", lp), ("bpm", b)):
        res = film.render(os.path.join(out_dir, lab), name=f"fc_{lab}", quiet=True)
        reports[lab] = res
        fl_ = res["flash"]
        checks.append((f"flash safety {lab}: {fl_['max_flashes_per_s']} general, {fl_['max_red_flashes_per_s']} red /s (<= 3)", fl_["ok"]))
    # 7. the encode: frame count and duration survive the MP4
    try:
        import imageio_ffmpeg
        nf, secs = imageio_ffmpeg.count_frames_and_secs(reports["cinematic"]["mp4"])
        checks.append((f"MP4: {nf} frames, {secs:.2f} s (226, 7.53 s)", nf == 226 and abs(secs - 226 / 30) < 0.05))
    except ImportError:
        checks.append(("MP4 written", os.path.getsize(reports["cinematic"]["mp4"]) > 1000))
    checks.append(("GIF and strip written", all(os.path.exists(reports["cinematic"][k]) for k in ("gif", "strip"))))
    checks.append(("stills sheet written", os.path.exists(c.stills(os.path.join(out_dir, "stills"), "fc"))))
    for k, v in checks:
        print(("PASS " if v else "FAIL ") + k)
    print("outputs:", out_dir)
    return all(v for _, v in checks)


# ------------------------------------------------------------------ CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description="Render a flavour-cycle product film from a job file or packs.")
    ap.add_argument("job", nargs="?", help="job JSON (items, brand, options)")
    ap.add_argument("--pack", action="append", help="pack render PNG (repeat; instead of a job file)")
    ap.add_argument("--tint", action="append", help="tint per --pack (#hex or auto)")
    ap.add_argument("--title"); ap.add_argument("--tagline"); ap.add_argument("--sign")
    ap.add_argument("--font-display"); ap.add_argument("--font-text")
    ap.add_argument("--aspect"); ap.add_argument("--platform"); ap.add_argument("--fps", type=int)
    ap.add_argument("--style", choices=list(STYLES)); ap.add_argument("--rounds", type=int)
    ap.add_argument("--loop", action="store_true", default=None); ap.add_argument("--no-endcard", action="store_true")
    ap.add_argument("--music"); ap.add_argument("--bpm", type=float)
    ap.add_argument("--webp", action="store_true", default=None); ap.add_argument("--no-gif", action="store_true")
    ap.add_argument("--name"); ap.add_argument("--out")
    ap.add_argument("--stills", action="store_true", help="review stills only, no video")
    ap.add_argument("--platforms", action="store_true"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest(a.out) else 1
    if a.platforms:
        for k, v in PLATFORMS.items():
            print(f"{k:18s} {v['size'][0]}x{v['size'][1]}  fps<={v['fps']}  safe t/b/l/r {v['safe']}  "
                  f"max {v['max_s'] or '-'} s  {str(v['kbps']) + ' kbps' if v['kbps'] else 'CRF 18'}")
        return 0
    if a.job:
        job, base = a.job, None
    elif a.pack:
        tints = a.tint or []
        job = dict(items=[dict(pack=os.path.abspath(p), tint=tints[i] if i < len(tints) else "auto") for i, p in enumerate(a.pack)],
                   brand=dict(title=a.title or "", tagline=a.tagline or "", sign=a.sign or "",
                              font_display=a.font_display, font_text=a.font_text), options={})
        base = os.getcwd()
    else:
        ap.error("give a job file or --pack (or --selftest / --platforms)")
    ov = dict(aspect=a.aspect, platform=a.platform, fps=a.fps, style=a.style, rounds=a.rounds, loop=a.loop,
              music=a.music, bpm=a.bpm, webp=a.webp, name=a.name)
    if a.no_endcard:
        ov["endcard"] = False
    if a.no_gif:
        ov["gif"] = False
    film = Film(job, base=base, **ov)
    out = os.path.abspath(a.out) if a.out else None
    if a.stills:
        print(film.stills(out or film._path(film.opt.get("out")) or os.path.join(film.base, "out", "motion")))
        return 0
    res = film.render(out)
    return 0 if res["flash"]["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
