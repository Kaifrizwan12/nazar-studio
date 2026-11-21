"""ENGINE NOTE (generic copy of a worked example).
Written for the BAGH project. It imports project modules (`art`: tokens, FONT, page sizes; `line_chips_kitchen`:
quad_warp, threeq, gusset_render, KSKUS) and reads that project's renders from out/ (<sku>_pouch-front.png,
<sku>_pouch-back.png, <sku>_print-art.png, chips/<sku>-chips_bag.png, ...). To reuse: edit the paths and the
rows near the end (one row per structure: a list of FRONT, BACK, SIDE, BASE, 3/4 images), and supply your own render
and print-art PNGs. The structure logic is in references/views.md. Nothing here uses AI or a 3D package.
"""
"""Every pack from every side: FRONT, BACK, SIDE, BASE, 3/4, one sheet per structure, all from our own renders and print art.
No AI and no 3D package: the sides and bases are built from the structure (doypack, pillow, side gusset, box pouch) and
the real art, warped by code. Schematic where a face is unprinted film; labelled honestly where a face isn't designed yet.
    python views.py            -> out/views/views_<structure>.jpg + views_all.jpg
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import art
from line_chips_kitchen import quad_warp, threeq, gusset_render, KSKUS

HERE = art.HERE; OUT = os.path.join(HERE, "out"); DST = os.path.join(OUT, "views"); os.makedirs(DST, exist_ok=True)
BG = (243, 238, 229); INK = (30, 26, 23); MUTE = (111, 102, 94)
FR = ["mango", "strawberry", "kiwi", "apricot", "mulberry"]; CH = ["mango", "apple", "banana"]; KI = ["onion", "tomato", "methi"]


def o(p): return os.path.join(OUT, p)
def rgba(p): return Image.open(o(p)).convert("RGBA")


def tint_of(im):
    a = np.asarray(im, float); m = a[..., 3] > 200; px = a[m][:, :3]
    return np.median(px, axis=0) / 255.0


def font(sz, bold=True):
    for f in ("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf"):
        try: return ImageFont.truetype(f, sz)
        except OSError: pass
    return ImageFont.load_default()


# ---------- side profiles ----------
def doypack_side(h, depth, top, tint, seal=True):
    """Edge-on doypack: thin at the top seal, bulging with product, base as deep as the opened gusset.
    The side seal is a flat fin seen edge-on: a light line down the middle."""
    w = int(depth * 1.25) + 8; cx = w / 2; im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ys = np.linspace(0, 1, 200)
    half = np.where(ys < 0.04, 0.10, np.where(ys < top, 0.10 + 0.12 * (ys - 0.04) / (top - 0.04),
                    0.22 + 0.78 * np.sin(np.clip((ys - top) / (0.97 - top), 0, 1) * np.pi * 0.55) ** 0.75))
    half = half * depth / 2
    pts = [(cx - hw, y * h) for y, hw in zip(ys, half)] + [(cx + hw, y * h) for y, hw in zip(ys[::-1], half[::-1])]
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    xx = (np.arange(w)[None, :] - cx) / (depth / 2 + 1e-6)
    shade = 0.58 + 0.42 * np.cos(np.clip(xx, -1, 1) * np.pi / 2) ** 0.6
    yy = np.linspace(0, 1, h)[:, None]; shade = shade * (0.92 + 0.08 * yy)
    col = (np.clip(tint[None, None, :] * shade[..., None], 0, 1) * 255).astype(np.uint8)
    out = Image.fromarray(np.dstack([col, np.asarray(m)]), "RGBA")
    d = ImageDraw.Draw(out)
    if seal: d.line([(cx, h * 0.01), (cx, h * 0.985)], fill=(255, 255, 255, 120), width=max(2, w // 40))
    d.rectangle([cx - half[0] - 1, 0, cx + half[0] + 1, int(h * 0.035)], fill=tuple(int(c * 200) for c in tint) + (255,))
    return out


def gusset_side(art_png, h, top_mm, total_mm, opaque=True, tint=None, bottom_mm=None):
    """Side gusset as printed: centre crease (valley + lit edge, far half a touch darker) and the top pinch, where the
    gusset folds in and is trapped flat in the top seal (a V that closes to nothing at the seal)."""
    g = (art_png if isinstance(art_png, Image.Image) else Image.open(o(art_png))).convert("RGB"); g = g.resize((int(g.width * h / g.height), h))
    a = np.asarray(g, float) / 255.0; H_, W_ = a.shape[:2]; yy, xx = np.mgrid[0:H_, 0:W_]
    k = H_ / total_mm; d = (xx - W_ / 2) / (0.9 * k); vy = 1 - 0.45 * np.sin(np.pi * yy / H_)
    a = a * (1 - 0.26 * vy * np.exp(-d * d))[..., None]; d2 = (xx - W_ / 2 - 1.4 * k) / (0.8 * k); a = a + (0.08 * vy * np.exp(-d2 * d2))[..., None]
    a = a * (1 - 0.06 * np.clip((xx - W_ / 2) / (2 * k), 0, 1))[..., None]
    e = np.minimum(xx, W_ - 1 - xx) / (4 * k); a = a * (0.84 + 0.16 * np.clip(e, 0, 1))[..., None]
    alpha = np.ones((H_, W_))
    vt = top_mm * k; vb = vt + 26 * k                                   # V: fully pinched at the seal, open 26 mm lower
    for y in range(int(vb)):
        frac = np.clip((y - vt) / (vb - vt), 0, 1) if y > vt else 0.0
        half_open = W_ / 2 * frac; dx = np.abs(xx[y] - W_ / 2)
        shut = dx > half_open
        a[y, shut] = a[y, shut] * 0.62                                  # folded-in plies in shadow
    d3 = np.abs(np.abs(xx - W_ / 2) - np.clip((yy - vt) / (vb - vt), 0, 1) * W_ / 2); fold = (yy < vb) & (yy > vt) & (d3 < 1.6)
    a[fold] = a[fold] * 0.5
    if bottom_mm is not None:                                           # crimped base too: the same V, upside down
        a = a[::-1].copy(); a_top = gusset_v(a, bottom_mm * k, W_, xx, yy); a = a_top[::-1].copy()
    return Image.fromarray((np.dstack([np.clip(a, 0, 1), alpha]) * 255).astype(np.uint8), "RGBA")


def gusset_v(a, vt, W_, xx, yy):
    vb = vt + 26 * (a.shape[0] / 240)
    for y in range(int(vb)):
        frac = np.clip((y - vt) / (vb - vt), 0, 1) if y > vt else 0.0
        shut = np.abs(xx[y] - W_ / 2) > W_ / 2 * frac; a[y, shut] = a[y, shut] * 0.62
    d3 = np.abs(np.abs(xx - W_ / 2) - np.clip((yy - vt) / (vb - vt), 0, 1) * W_ / 2); fold = (yy < vb) & (yy > vt) & (d3 < 1.6)
    a[fold] = a[fold] * 0.5
    return a


def pillow_side(h, depth, tint):
    """Pillow bag edge-on: crimped end seals top and bottom, the body a lens that bulges with air."""
    w = int(depth * 1.2) + 8; cx = w / 2; im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ys = np.linspace(0, 1, 200); crimp = 0.06
    half = depth / 2 * np.where((ys < crimp) | (ys > 1 - crimp), 0.08, 0.08 + 0.92 * np.sin(np.clip((ys - crimp) / (1 - 2 * crimp), 0, 1) * np.pi) ** 0.55)
    pts = [(cx - hw, y * h) for y, hw in zip(ys, half)] + [(cx + hw, y * h) for y, hw in zip(ys[::-1], half[::-1])]
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    xx = (np.arange(w)[None, :] - cx) / (depth / 2); shade = 0.55 + 0.45 * np.cos(np.clip(xx, -1, 1) * np.pi / 2) ** 0.5
    col = (np.clip(tint[None, None, :] * shade[..., None] * np.ones((h, 1, 1)), 0, 1) * 255).astype(np.uint8)
    out = Image.fromarray(np.dstack([col, np.asarray(m)]), "RGBA"); d = ImageDraw.Draw(out)
    for y0 in (0, h * (1 - crimp)):
        for i in range(0, int(h * crimp), 5): d.line([(cx - half[0] - 2, y0 + i), (cx + half[0] + 2, y0 + i)], fill=(0, 0, 0, 60), width=1)
    return out


# ---------- bases ----------
def lens_base(gus_img, w, d):
    """Doypack base from below: the opened gusset as an eye shape, its own print on it, crease through the middle,
    side-seal corners holding the fold."""
    im = Image.new("RGBA", (w, d), (0, 0, 0, 0)); m = Image.new("L", (w, d), 0)
    ys = np.linspace(0, 1, 120); top = [(x * w, d / 2 - d / 2 * np.sin(x * np.pi)) for x in ys]; bot = [(x * w, d / 2 + d / 2 * np.sin(x * np.pi)) for x in ys[::-1]]
    ImageDraw.Draw(m).polygon(top + bot, fill=255)
    g = gus_img.convert("RGBA").resize((w, d)); im.paste(g, (0, 0), m)
    dr = ImageDraw.Draw(im); dr.line(top + bot + [top[0]], fill=INK + (255,), width=3)
    dr.line([(6, d / 2), (w - 6, d / 2)], fill=INK + (130,), width=2)
    for x0, s in ((0, 1), (w, -1)): dr.polygon([(x0, d / 2), (x0 + s * w * 0.1, d / 2 - d * 0.13), (x0 + s * w * 0.1, d / 2 + d * 0.13)], fill=INK + (70,))
    return im


def box_base(w, d, tint, label_gussets=True):
    """Box pouch base: a flat rectangle (front edge, back edge, the two gussets folded under), four corner seals."""
    im = Image.new("RGBA", (w, d), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    c = tuple(int(v * 255 * 0.9) for v in tint) + (255,); dr.rectangle([0, 0, w - 1, d - 1], fill=c, outline=INK + (255,), width=3)
    b = max(8, d // 22); dr.rectangle([b, b, w - 1 - b, d - 1 - b], outline=tuple(int(v * 255 * 0.7) for v in tint) + (255,), width=b)   # perimeter seal
    for x, y in ((0, 0), (w - 1, 0), (0, d - 1), (w - 1, d - 1)): dr.ellipse([x - b, y - b, x + b, y + b], fill=INK + (90,))         # corner seals
    return im


def crimp_base(w, d, tint, gussets=False):
    """Pillow / gusseted chips bag from below: the crimped end seal across, gussets tucked as a W at each end."""
    im = Image.new("RGBA", (w, d), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    c = tuple(int(v * 255 * 0.85) for v in tint) + (255,)
    if gussets: dr.rectangle([0, 0, w - 1, d - 1], fill=c, outline=INK + (255,), width=3)
    else: dr.ellipse([0, 0, w - 1, d - 1], fill=c, outline=INK + (255,), width=3)
    ch = max(10, d // 6) if gussets else max(6, d // 14); dr.rectangle([w * 0.02, d / 2 - ch / 2, w * 0.98, d / 2 + ch / 2], fill=tuple(int(v * 255 * 0.7) for v in tint) + (255,))
    for x in range(int(w * 0.02), int(w * 0.98), 6): dr.line([(x, d / 2 - ch / 2), (x, d / 2 + ch / 2)], fill=(0, 0, 0, 70), width=1)
    if gussets:
        for x0, s in ((0, 1), (w, -1)): dr.line([(x0, 0), (x0 + s * d * 0.5, d / 2), (x0, d)], fill=INK + (150,), width=2)
    return im


def three_quarter(front, side, ang=27.0, kind="gusset"):
    if kind == "gusset": return threeq(front, side, ang)
    import math
    ca = math.cos(math.radians(ang)); H = front.height; fw = front.width * ca; pad = int(H * 0.04)
    Wc, Hc = int(fw + pad * 2 + H * 0.03), int(H * 1.04); x0, y0 = pad, int(H * 0.02)
    q = [(x0, y0), (x0 + fw, y0 + H * 0.012), (x0 + fw, y0 + H * 0.988 - H * 0.004), (x0, y0 + H)]
    F = np.asarray(quad_warp(front, q, (Wc, Hc)), float); xx = np.arange(Wc)[None, :, None]
    t = np.clip((xx - (x0 + fw * 0.62)) / (fw * 0.38), 0, 1); F[..., :3] *= (1 - 0.30 * t ** 1.6)   # surface curving away
    out = Image.fromarray(F.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(out)
    if kind == "doypack":                                                                          # the side seal fin, edge-on
        d.line([(x0 + fw + 2, y0 + H * 0.02), (x0 + fw + 2, y0 + H * 0.97)], fill=(255, 255, 255, 150), width=max(2, int(H * 0.006)))
    return out


# ---------- sheets ----------
COLS = ["FRONT", "BACK", "SIDE", "BASE (from below)", "3/4"]


def sheet(title, sub, rows, note):
    CH_ = 520; pad = 34; colw = [420, 420, 220, 460, 560]
    W = sum(colw) + pad * (len(colw) + 1); H = 190 + len(rows) * (CH_ + 70) + 70
    sh = Image.new("RGB", (W, H), BG); dr = ImageDraw.Draw(sh)
    dr.text((pad, 34), title, font=font(46), fill=INK); dr.text((pad, 96), sub, font=font(22, False), fill=MUTE)
    x = pad
    for c, cw in zip(COLS, colw): dr.text((x, 148), c, font=font(20), fill=MUTE); x += cw + pad
    y = 190
    for name, cells in rows:
        dr.text((pad, y), name, font=font(22), fill=INK); y += 34; x = pad
        for cell, cw in zip(cells, colw):
            if cell is None:
                dr.rectangle([x, y, x + cw, y + CH_], outline=MUTE, width=1); dr.text((x + 14, y + CH_ / 2 - 12), "not designed yet", font=font(18, False), fill=MUTE)
            else:
                im = cell.copy(); im.thumbnail((cw, CH_), Image.LANCZOS)
                sh_ = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh_.putalpha(im.getchannel("A").point(lambda v: v * 0.22).filter(ImageFilter.GaussianBlur(10)))
                px, py = x + (cw - im.width) // 2, y + (CH_ - im.height) // 2
                sh.paste((60, 50, 40), (px + 8, py + 12), sh_.getchannel("A")); sh.paste(im, (px, py), im)
            x += cw + pad
        y += CH_ + 36
    dr.text((pad, H - 50), note, font=font(17, False), fill=MUTE)
    return sh


def gus_strip(print_png, HP_, G_, W_):
    f = Image.open(o(print_png)).convert("RGB"); k = f.height / (2 * HP_ + G_ + 6)
    return f.crop((int(3 * k), int((3 + HP_) * k), int((3 + W_) * k), int((3 + HP_ + G_) * k)))


def build():
    sheets = {}
    # D1 fruit pouch 100 g: doypack, 140 x 185 + 80 base gusset
    rows = []
    for s in FR:
        fr, bk = rgba(f"{s}_pouch-front.png"), rgba(f"{s}_pouch-back.png"); t = tint_of(fr)
        side = doypack_side(fr.height, fr.height * (40 / 185) * 1.0, 0.14, t)
        base = lens_base(gus_strip(f"{s}_print-art.png", art.HP, art.G, art.W), 900, 380)
        rows.append((f"D1  {s.capitalize()} 100 g", [fr, bk, side, base, three_quarter(fr, side, 30, "doypack")]))
    sheets["d1"] = sheet("D1 fruit pouch 100 g, every side", "Stand-up doypack: sealed side edges, one base gusset that folds in and out to make the foot.", rows,
                         "Front/back: our film renders. Side and 3/4 side: drawn from the structure (doypack has no side panel, only the seal edge). Base: the real gusset print. Concept, converter dieline governs.")
    # D2 single 30 g: doypack, 110 x 176 + 64
    rows = []
    for s in FR:
        fr, bk = rgba(f"fruit_line/d2_{s}_pouch-front.png"), rgba(f"fruit_line/d2_{s}_pouch-back.png"); t = tint_of(fr)
        side = doypack_side(fr.height, fr.height * (32 / 176), 0.16, t)
        base = lens_base(gus_strip(f"fruit_line/d2_{s}_print-art.png", 176, 64, 110), 900, 360)
        rows.append((f"D2  {s.capitalize()} 30 g", [fr, bk, side, base, three_quarter(fr, side, 30, "doypack")]))
    sheets["d2"] = sheet("D2 single serve 30 g, every side", "The same doypack, bag-pocket size.", rows, "Same method as D1. Concept, converter dieline governs.")
    # D3 chips 25 g: pillow bag (no back art designed: honest blank)
    rows = []
    for c in CH:
        fr = rgba(f"chips/{c}-chips_bag.png"); t = tint_of(fr)
        side = pillow_side(fr.height, fr.height * 0.17, t)
        rows.append((f"D3  {c.capitalize()} chips 25 g", [fr, rgba(f"chips/{c}-chips_bag-back.png"), side, crimp_base(900, 200, t), three_quarter(fr, side, 30, "pillow")]))
    sheets["d3"] = sheet("D3 fruit chips 25 g, every side", "Pillow bag: crimped end seals top and bottom, a fin seal down the back, puffed with air.", rows,
                         "Back: fin seal down the middle, both columns 3 mm clear of it. Side and base drawn from the pillow structure. Concept.")
    # D4 sharing 70 g: side-gusset bag, 160 x 240 + 35 gussets, opaque print
    rows = []
    for c in CH:
        fr, bk = rgba(f"chips_sharing/{c}-chips_bag-front.png"), rgba(f"chips_sharing/{c}-chips_bag-back.png"); t = tint_of(fr)
        side = gusset_side(f"chips_sharing/{c}-chips_gusset-art.png", fr.height, 12, 240, bottom_mm=12)
        rows.append((f"D4  {c.capitalize()} sharing 70 g", [fr, bk, side, crimp_base(900, int(900 * 35 / 160), t, gussets=True), three_quarter(fr, side, 30)]))
    sheets["d4"] = sheet("D4 sharing bag 70 g, every side", "Side-gusset bag: the sides fold in at the crimped top and bottom seals and open into printed walls below.", rows,
                         "Side: the real gusset print with its centre crease and the V where it pinches into the seal. Concept.")
    # D8 kitchen 250 g: box pouch, 130 x 200 + 70 gussets, flat base
    rows = []
    for k, sku in zip(KI, [next(x for x in KSKUS if x["id"] == i) for i in KI]):
        fr, bk = rgba(f"kitchen/{k}_pouch-front.png"), rgba(f"kitchen/{k}_pouch-back.png"); t = tint_of(fr)
        side = gusset_side(gusset_render(sku, o(f"kitchen/{k}_gusset-art.png"), seed=3), fr.height, 10, 200)   # frosted film, like the front
        rows.append((f"D8  {k.capitalize()} 250 g", [fr, bk, side, box_base(900, int(900 * 70 / 130), t), three_quarter(fr, side, 27)]))
    sheets["d8"] = sheet("D8 kitchen box pouch 250 g, every side", "Box pouch: sealed flat at the top (gussets trapped in the seal), open sides below, a flat rectangular base.", rows,
                         "Side: the real gusset print, crease and top pinch. Base: flat, gussets folded under, four corner seals. Concept, converter dieline governs.")
    for n, im in sheets.items():
        p = os.path.join(DST, f"views_{n}.jpg"); im.save(p, quality=88); print(p, im.size)


if __name__ == "__main__":
    build()
