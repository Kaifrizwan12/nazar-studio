#!/usr/bin/env python3
"""proxy.py - the proxy route: let the image model light a blank stand-in, then put our exact pack in its place.

Why: a model asked to draw the real pack redraws its type and logo (rule 1 of nazar-shoot). A model asked for an
empty plate gives no contact, no bounce, no reflection of the pack in the scene. The VFX answer is a stand-in: a
plain matte white (or 18% grey) object of the same shape and size, lit inside the scene ("shadow catcher", "light
probe" in Debevec 1998). Ask the model for the scene WITH a blank, unprinted proxy pack in it. Every shadow, floor
reflection and bounce in that image is then physically tied to a pack-shaped object. This engine:

1. fits our render (RGBA) into the proxy's box, base on base;
2. reads the proxy's shading (low-frequency luminance and light colour) and multiplies it onto our print, so our
   pixels carry the scene's light; optionally carries the proxy's specular highlights (real reflections of the
   scene's sources) as a capped screen;
3. leaves everything outside the silhouette as the model made it (its shadows and reflections stay);
4. matches the plate's grain and stamps the output.

Our print is never regenerated: the type contrast is kept (the self-test checks it), and shading is clipped so it
never crushes or blows the print.

CLI:
  python proxy.py --plate gen.jpg --product pack.png --box x0,y0,x1,y1 --out out.jpg [--spec 0.5] [--strength 0.9]
  python proxy.py --selftest
The box is the proxy's bounding box in the generated image (read it off the image; a tight box matters).
Hand-held shots: add --occlude (fingers, a basket rim in front of a neutral proxy stay the model's) and/or
--keep mask.png for neutral occluders. Ask the model for an UNPRINTED matte white or light-grey proxy so colour
separates the hand from the pack.
What it cannot do: fix a proxy the model drew in the wrong perspective or shape; reject that generation.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from composite import gblur, noise_sigma  # noqa: E402

STAMP = "AI-generated plate and lighting · product is the real artwork render · concept"


def _lum(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def fit(product, box, grow=0.01):
    """Scale the RGBA render to the proxy box (base on base, centred), slightly oversized so no proxy edge shows."""
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    p = product.convert("RGBA")
    a = np.asarray(p)[..., 3]
    ys, xs = np.nonzero(a > 8)
    p = p.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    s = min(bw / p.width, bh / p.height) * (1 + grow)
    w, h = max(1, round(p.width * s)), max(1, round(p.height * s))
    p = p.resize((w, h), Image.LANCZOS)
    px = int(round(x0 + bw / 2 - w / 2))
    py = int(round(y1 - h + bh * grow * 0.5))
    return p, px, py


def _coeffs(dst, src):
    """PIL perspective coefficients mapping output (dst) points back to input (src) points."""
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]; b += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(b, float)).tolist()


def fit_quad(product, quad):
    """Warp the render onto the proxy's four corners (TL, TR, BR, BL) read off the image: tilted, rotated, held packs."""
    p = product.convert("RGBA")
    a = np.asarray(p)[..., 3]
    ys, xs = np.nonzero(a > 8)
    p = p.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    q = np.array(quad, float)
    px, py = int(np.floor(q[:, 0].min())), int(np.floor(q[:, 1].min()))
    w, h = int(np.ceil(q[:, 0].max())) - px + 1, int(np.ceil(q[:, 1].max())) - py + 1
    dst = [(x - px, y - py) for x, y in q]
    src = [(0, 0), (p.width, 0), (p.width, p.height), (0, p.height)]
    out = p.transform((w, h), Image.PERSPECTIVE, _coeffs(dst, src), resample=Image.BICUBIC)
    return out, px, py


def shading(plate, px, py, w, h, mask, blur_frac=0.035):
    """Low-frequency shading and light colour read from the proxy inside the silhouette, normalised to its median."""
    reg = plate[py:py + h, px:px + w].astype(np.float32)
    L = reg.max(-1) if KEY else _lum(reg)
    m = mask > 0.5
    r = max(2, int(h * blur_frac))
    # blur only inside the mask (normalised convolution), so the background's dark does not bleed into the edge
    wsum = gblur(m.astype(np.float32), r) + 1e-4
    Ls = gblur(L * m, r) / wsum
    med = float(np.median(L[m])) if m.any() else 1.0
    S = np.clip(Ls / max(med, 1e-3), 0.18 if KEY else 0.45, 1.35)
    rgb = np.stack([gblur(reg[..., c] * m, r * 2) / wsum for c in range(3)], -1)
    tint = rgb / np.maximum(rgb.mean(-1, keepdims=True), 1e-3)
    tint = np.ones_like(tint) if KEY else np.clip(tint, 0.85, 1.15)
    spec = np.clip(L - Ls - 12, 0, None) * m                        # highlights above the smooth shading
    # crease layer: the stand-in's folds and crinkles (fine scale over broad scale). Without it the print reads as a
    # flat sticker on a crumpled pack - the owner's verdict on the first hand-held set.
    rf = max(1, int(h * 0.004))
    Lf = gblur(L * m, rf) / (gblur(m.astype(np.float32), rf) + 1e-4)
    D = np.clip(Lf / np.maximum(Ls, 1e-3), 0.55, 1.5)
    return S, tint, spec, D


KEY = None   # set to "green" when the stand-in is a chroma-green pouch (the reliable route for hand-held shots)


def standin_like(reg, chroma=0.14):
    """Colours a blank white/grey stand-in takes in a real scene (measured on two plates):
    lit: neutral (chroma < 0.14); in shade under sky: cool grey (b >= r, chroma < 0.40, e.g. 86,102,112);
    warm bounce from skin or a warm wall: bright and only mildly warm (lum > 120, chroma < 0.32).
    Lit skin is chroma 0.45-0.6, skin in shade is dark (lum < 100), open sky is chroma > 0.8."""
    mx, mn = reg.max(-1), reg.min(-1)
    c = (mx - mn) / np.maximum(mx, 1.0)
    if KEY == "green":                                            # chroma key: nothing else in a food scene is this green
        R, G, B = reg[..., 0], reg[..., 1], reg[..., 2]
        # green in deep shade under a blue sky turns teal (G ~ B), so allow G down to 0.92 B; open sky has B >> G
        key = (G > 1.25 * R) & (G > 0.92 * B) & (G > 10)   # deep hand-shadow green is still the stand-in
        key &= (B > 0.3 * G) | (G > 2.5 * R)                # #00B140 carries blue (B/G ~0.55) and almost no red; banana, leaf
                                                            # and lime green carry no blue but real red (R/G ~0.8): they stay in front.
                                                            # Deep stand-in creases lose blue too, but keep R near zero.
        return key, np.where(key, 0.0, 1.0)
    cool = (reg[..., 2] >= reg[..., 0]) & (c < 0.40)
    warm_bounce = (_lum(reg) > 120) & (c < 0.32)
    return (c < chroma) | cool | warm_bounce, c


def _touching_outside(cand, A):
    """Keep only candidate pixels connected to the outside of the fitted print: a finger always comes from a hand."""
    m = ((cand | (A < 0.05)) * 255).astype(np.uint8)
    pad = Image.new("L", (m.shape[1] + 2, m.shape[0] + 2), 255)
    pad.paste(Image.fromarray(m), (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 128)
    return (np.asarray(pad, np.uint8)[1:-1, 1:-1] == 128) & cand


def occluders(reg, A, chroma=0.16, keep=None):
    """What is IN FRONT of the proxy (fingers, a basket rim, a strap): the proxy is neutral (unprinted white or 18% grey),
    so anything inside its silhouette with real colour (skin, wicker, fabric) is an occluder and must stay the plate's.
    keep: optional float mask (1 = keep the plate) drawn by hand for neutral occluders the colour test cannot see.
    Returns a soft 0..1 mask over the region."""
    like, c = standin_like(reg, chroma)
    cand = (~like & (A > 0.5)) if KEY else ((c > chroma) & ~like & (A > 0.5))
    occ = _touching_outside(cand, A).astype(np.float32)        # enclosed warm patches are reflections, not fingers
    occ = (gblur(occ, 2) > 0.35).astype(np.float32)            # drop speckle, close pinholes
    if keep is not None:
        occ = np.maximum(occ, keep)
    if KEY:                                                    # key mode: edge pixels are part skin, part dark key; tuck the print under them
        occ = (gblur(occ, 1.5) > 0.72).astype(np.float32)
    return np.clip(gblur(occ, 1.0 if KEY else 1.2), 0, 1)       # a lens-soft edge round each finger


def silhouette(reg, A, chroma=0.14, min_lum=50):
    """The stand-in's exact outline as the model drew it: neutral, bright pixels inside the (oversized) fitted print,
    closed and hole-filled (wrinkle shadows inside stay in). Fingers crossing the edge connect to the outside, so they
    stay out. Clipping our print to this kills the white proxy fringe that eyeballed corners leave."""
    like, _ = standin_like(reg, chroma)
    m = (like & ((_lum(reg) > min_lum) | (KEY is not None)) & (A > 0.05)).astype(np.float32)
    m = (gblur(m, 2) > 0.5).astype(np.uint8) * 255               # close pinholes and wrinkle cracks
    pad = Image.new("L", (m.shape[1] + 2, m.shape[0] + 2), 0)
    pad.paste(Image.fromarray(m), (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 128)                         # everything reachable from outside
    f = np.asarray(pad, np.uint8)[1:-1, 1:-1]
    return ((f != 128)).astype(np.float32)                         # the outline plus any enclosed holes


def _displace(rgb, D, px):
    """Shift the print along the slope of the crease map (the Photoshop Displace step of a pro mockup): lines and type
    bend over folds instead of lying flat on top of them. px = largest shift in pixels (about 0.4% of pack height)."""
    hmap = gblur(D.astype(np.float32), 1.5)
    gy, gx = np.gradient(hmap)
    s = max(float(np.percentile(np.hypot(gx, gy), 99)), 1e-6)
    dx, dy = np.clip(gx / s, -1, 1) * px, np.clip(gy / s, -1, 1) * px
    h, w = D.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    sx, sy = np.clip(xx + dx, 0, w - 1.001), np.clip(yy + dy, 0, h - 1.001)
    x0, y0 = sx.astype(int), sy.astype(int); fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
    return (rgb[y0, x0] * (1 - fx) * (1 - fy) + rgb[y0, x0 + 1] * fx * (1 - fy)
            + rgb[y0 + 1, x0] * (1 - fx) * fy + rgb[y0 + 1, x0 + 1] * fx * fy)


def _grow_quad(q, g):
    q = np.array(q, float); c = q.mean(0)
    return [tuple(c + (p - c) * (1 + g)) for p in q]


def apply(plate_img, product_img, box, strength=0.9, spec_k=0.5, grow=0.01, stamp=STAMP, seed=7, occlude=False, keep_img=None, quad=None, clip=False, quad_grow=0.04, canvas=None, detail=0.0, soften=0.0, match=False, displace=0.0):
    """canvas: paint onto this image (earlier packs already in it) while every mask, shade and key test is read from
    the untouched plate; pixels an earlier pack already painted are never overwritten (composite front pack first)."""
    plate = np.asarray(plate_img.convert("RGB")).astype(np.float32)
    H, W = plate.shape[:2]
    base = plate if canvas is None else np.asarray(canvas.convert("RGB")).astype(np.float32)
    if quad and clip:
        quad = _grow_quad(quad, quad_grow)                         # oversize; the silhouette does the cutting (0 for a pack in front of others)
    p, px, py = fit_quad(product_img, quad) if quad else fit(product_img, box, grow)
    w, h = p.size
    x0c, y0c = max(px, 0), max(py, 0)
    x1c, y1c = min(px + w, W), min(py + h, H)
    pa = np.asarray(p).astype(np.float32)[y0c - py:y1c - py, x0c - px:x1c - px]
    rgb, A = pa[..., :3], pa[..., 3] / 255
    occ = np.zeros(A.shape, np.float32)
    if occlude or keep_img is not None:
        keep = None
        if keep_img is not None:
            keep = np.asarray(keep_img.convert("L").resize((W, H)), np.float32)[y0c:y1c, x0c:x1c] / 255
        occ = occluders(plate[y0c:y1c, x0c:x1c], A, keep=keep)
    if clip:
        A = A * silhouette(plate[y0c:y1c, x0c:x1c], A)
    taken = (np.abs(base[y0c:y1c, x0c:x1c] - plate[y0c:y1c, x0c:x1c]).sum(-1) > 30).astype(np.float32)
    A = A * (1 - taken)                                           # an earlier (front) pack keeps its pixels
    S, tint, spec, D = shading(plate, x0c, y0c, x1c - x0c, y1c - y0c, A * (1 - occ))   # read light from the visible proxy only
    if displace or soften:                                        # edge-extend first: transparent pixels are black in the PNG and
        A0 = pa[..., 3] / 255                                     # would bleed in as a dark rim (owner caught it on a bag edge)
        for rr in (3, 12, 40):
            wv = gblur(A0, rr) + 1e-4
            ext = np.stack([gblur(rgb[..., c] * A0, rr) for c in range(3)], -1) / wv[..., None]
            rgb = np.where((A0 < 0.99)[..., None], ext, rgb)
            A0 = np.maximum(A0, np.clip(wv * 4, 0, 1))
    if displace:                                                  # mockup-studio displacement map: the print bends over each crease
        rgb = _displace(rgb, D, displace)
    if soften:                                                    # the print is seen through the same lens as the plate
        rgb = np.stack([gblur(rgb[..., c], soften) for c in range(3)], -1)
    lit = rgb * (1 + strength * (S[..., None] * tint - 1))
    if detail:
        lit = lit * (D ** detail)[..., None]                      # creases and crinkles of the real pack
    if match:                                                     # pull the print into the photo grade around it
        ring = (gblur((A > 0.05).astype(np.float32), 25) > 0.02) & (A < 0.05)
        env = plate[y0c:y1c, x0c:x1c][ring] if ring.any() else plate.reshape(-1, 3)
        e_sat = float(np.median((env.max(-1) - env.min(-1)) / np.maximum(env.max(-1), 1)))
        m_ = A > 0.5
        p_sat = float(np.median((lit[m_].max(-1) - lit[m_].min(-1)) / np.maximum(lit[m_].max(-1), 1))) if m_.any() else e_sat
        k = float(np.clip(0.55 + 0.45 * e_sat / max(p_sat, 1e-3), 0.86, 1.0))   # only ever calms the print
        lum = lit.mean(-1, keepdims=True)
        lit = lum + (lit - lum) * k
        blk = np.percentile(env, 2, axis=0)
        wht = np.minimum(np.percentile(env, 99.5, axis=0), 255)
        lit = blk * 0.3 + lit * (wht - blk * 0.3) / 255          # the black floor and white ceiling of the photo
    lit = lit + spec_k * spec[..., None] * (1 - lit / 255)          # screen-like, never past white
    # grain: the plate's own noise, on our pixels only
    sig = noise_sigma(plate_img.convert("RGB"))
    rng = np.random.default_rng(seed)
    lit = lit + rng.normal(0, sig, lit.shape[:2])[..., None]
    lit = np.clip(lit, 0, 255)
    # a 1 px feather so the edge is a lens edge, not a vector edge
    Af = np.clip(gblur(A, 1) * 1.0, 0, 1) * (1 - occ)            # fingers and rims in front stay the model's
    out = base.copy()
    if KEY == "green":                                            # the green stand-in bounced green onto nearby skin
        r = out[y0c:y1c, x0c:x1c]
        near = (gblur((A > 0.05).astype(np.float32), 12) > 0.02) & (taken < 0.5)
        cap = np.minimum(np.maximum(r[..., 0], r[..., 2]), (r[..., 0] + r[..., 2]) / 2 + 4)   # skin keeps G below this (checked: lit, pale and shaded skin)
        r[..., 1] = np.where(near & (r[..., 1] > cap), cap, r[..., 1])
    reg = out[y0c:y1c, x0c:x1c]
    out[y0c:y1c, x0c:x1c] = reg * (1 - Af[..., None]) + lit * Af[..., None]
    if KEY == "green":                                            # last pass: any key green still showing at the pack's edge
        r = out[y0c:y1c, x0c:x1c]
        left, _ = standin_like(plate[y0c:y1c, x0c:x1c])           # read from the plate: our own art may be green
        left &= (gblur((A > 0.05).astype(np.float32), 6) > 0.05) & (Af < 0.5) & (taken < 0.5)
        if left.any():
            keepw = (~left).astype(np.float32)
            fill = np.stack([gblur(r[..., ch] * keepw, 6) for ch in range(3)], -1) / (gblur(keepw, 6)[..., None] + 1e-4)
            r[left] = fill[left]
    im = Image.fromarray(out.astype(np.uint8))
    if stamp:
        d = ImageDraw.Draw(im)
        try:
            f = ImageFont.truetype("DejaVuSans.ttf", max(11, H // 90))
        except OSError:
            f = ImageFont.load_default()
        d.text((int(W * 0.015), int(H * 0.975) - max(11, H // 90)), stamp, fill=(240, 240, 240), font=f)
    return im, dict(box=(px, py, px + w, py + h), grain_sigma=round(sig, 2), shade_range=(round(float(S.min()), 2), round(float(S.max()), 2)), occluded_pct=round(float(occ.mean()) * 100, 1))


def recolor_key(img, rgb, min_area_px=200, plate=None, region=None):
    """Loose bits of the green stand-in that are not the print face (a torn-off strip, a folded flap): repaint them in
    the pack's own band colour, keeping the stand-in's shading (its max channel over its median). Pass the plate when
    any placed art is green, so only pixels still equal to the plate's key are touched."""
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    if plate is not None:
        pl = np.asarray(plate.convert("RGB")).astype(np.float32)
        like, _ = standin_like(pl)
        like &= np.abs(a - pl).sum(-1) < 25
    else:
        like, _ = standin_like(a)
    if region is not None:                                         # only near the packs: green things in the scene stay
        x0, y0, x1, y1 = region; r = np.zeros_like(like); r[y0:y1, x0:x1] = True; like &= r
    if like.sum() < min_area_px:
        return img
    L = a.max(-1)
    med = float(np.median(L[like]))
    sh = np.clip(L / max(med, 1.0), 0.30, 1.12)                  # shine on film reads as a highlight, not neon colour
    grow = gblur(like.astype(np.float32), 2.0) > 0.08            # take the anti-aliased green rim too
    col = np.array(rgb, np.float32)[None, :] * sh[grow][:, None]
    spec = np.clip(L[grow] - med * 1.15, 0, None)[:, None] * 0.6  # keep real glints as near-white
    out = a.copy()
    out[grow] = np.clip(col + spec, 0, 255)
    soft = np.clip(gblur(grow.astype(np.float32), 0.8), 0, 1)[..., None]
    out = a * (1 - soft) + out * soft
    return Image.fromarray(out.astype(np.uint8))


# ---------------------------------------------------------------------------------------------- self-test
def _synthetic(W=1200, H=900):
    """A plate with a white proxy lit from the left, its cast shadow to the right, and a specular streak."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    bg = np.stack([200 - 0.03 * y, 190 - 0.03 * y, 175 - 0.03 * y], -1)
    table = y > H * 0.62
    bg[table] = np.array([150, 128, 104], np.float32) - 0.02 * (y[table, None] - H * 0.62)
    box = (520, 300, 760, 640)
    x0, y0, x1, y1 = box
    # shadow on the table to the right of the proxy
    sh = np.zeros((H, W), np.float32)
    sh[y1 - 30:y1 + 4, x1 - 10:x1 + 200] = 1
    sh = gblur(sh, 12)
    bg *= (1 - 0.45 * sh)[..., None]
    # the proxy: white, lit from the left (bright left, darker right), one specular streak near the left
    gx = (x[y0:y1, x0:x1] - x0) / (x1 - x0)
    prox = (235 - 95 * gx)[..., None] * np.array([1.0, 0.98, 0.94], np.float32)
    prox[:, 30:38] = np.clip(prox[:, 30:38] + 60, 0, 255)
    bg[y0:y1, x0:x1] = prox
    rng = np.random.default_rng(1)
    bg += rng.normal(0, 2.5, bg.shape[:2])[..., None]
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)), box, sh


def _product(w=480, h=680):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(222, 128, 38, 255))
    for i in range(8):                                   # print: dark stripes standing in for type
        d.rectangle([60, 120 + i * 50, w - 60, 140 + i * 50], fill=(40, 30, 25, 255))
    return im


def selftest(out_path=None):
    ok = True

    def check(name, cond, info=""):
        nonlocal ok
        ok &= bool(cond)
        print(("PASS " if cond else "FAIL ") + name + (f"  ({info})" if info else ""))

    plate, box, sh = _synthetic()
    prod = _product()
    out, meta = apply(plate, prod, box, spec_k=0.5)
    o = np.asarray(out).astype(np.float32)
    P = np.asarray(plate).astype(np.float32)
    bx0, by0, bx1, by1 = meta["box"]
    reg = _lum(o[by0 + 20:by1 - 20, bx0 + 20:bx1 - 20])
    half = reg.shape[1] // 2
    check("Scene light carried onto our print: left half brighter than right", reg[:, :half].mean() > reg[:, half:].mean() * 1.12,
          f"{reg[:, :half].mean():.0f} vs {reg[:, half:].mean():.0f}")
    m = sh > 0.3
    m[:, :box[2] + 20] = False
    check("The model's cast shadow outside the silhouette is untouched", np.abs(o[m] - P[m]).mean() < 1.0, f"{np.abs(o[m] - P[m]).mean():.2f}")
    # print contrast: stripe vs ground inside the product, before and after
    ref = np.asarray(prod.resize((bx1 - bx0, by1 - by0))).astype(np.float32)[..., :3]
    c0 = _lum(ref).std()
    c1 = _lum(o[by0:by1, bx0:bx1]).std()
    check("Print contrast kept (>= 70% of the render's)", c1 >= 0.7 * c0, f"{c1:.1f} vs {c0:.1f}")
    ring = np.zeros(o.shape[:2], bool)
    ring[by0 + 3:by1 - 3, bx0 + 2:bx0 + 5] = True
    edge = o[ring].mean(0)
    check("No white proxy edge showing at the silhouette", edge[2] < 150, f"edge RGB {edge.round()}")
    check("Stamp present bottom-left", np.abs(o[-30:, :300] - P[-30:, :300]).max() > 60)
    check("Our pack's hue survives (orange stays orange)", o[by0 + 60:by0 + 100, bx0 + 20:bx1 - 20, 0].mean() > o[by0 + 60:by0 + 100, bx0 + 20:bx1 - 20, 2].mean() + 60)
    # occlusion: a skin-coloured finger laid across the proxy must stay in front of our print
    P2 = np.asarray(plate).copy()
    fy0, fy1 = box[1] + (box[3] - box[1]) // 2, box[1] + (box[3] - box[1]) // 2 + 40
    P2[fy0:fy1, box[0] - 30:box[0] + (box[2] - box[0]) // 2] = (205, 150, 120)
    out2, meta2 = apply(Image.fromarray(P2), prod, box, occlude=True)
    o2 = np.asarray(out2).astype(np.float32)
    fing = o2[fy0 + 8:fy1 - 8, box[0] + 10:box[0] + (box[2] - box[0]) // 2 - 10]
    check("Occluder in front (finger) stays the plate's", np.abs(fing - np.array([205, 150, 120])).mean() < 12, f"{np.abs(fing - np.array([205, 150, 120])).mean():.1f}")
    below = o2[fy1 + 30:fy1 + 70, box[0] + 30:box[2] - 30]
    check("Print still replaces the proxy away from the finger", below[..., 0].mean() > below[..., 2].mean() + 60)
    # quad: a rotated proxy gets a rotated print (corner pixel lands where the quad says)
    q = [(box[0] + 40, box[1]), (box[2], box[1] + 40), (box[2] - 40, box[3]), (box[0], box[3] - 40)]
    pq, qx, qy = fit_quad(prod, q)
    aq = np.asarray(pq)[..., 3]
    check("Quad fit follows the four corners (top-left corner sits right of the box edge)",
          aq[2, :].nonzero()[0].size > 0 and aq[2, :].nonzero()[0].min() > 25 and aq[:, 2].nonzero()[0].min() > 25)
    # clip: with a quad 6% too small, the plain fit leaves a white fringe; clip must not
    small = _grow_quad([(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])], -0.06)
    o3 = np.asarray(apply(plate, prod, None, quad=small, clip=True, stamp="")[0]).astype(np.float32)
    o4 = np.asarray(apply(plate, prod, None, quad=small, clip=False, stamp="")[0]).astype(np.float32)
    band = (slice(box[1] + 60, box[3] - 60), slice(box[0] + 2, box[0] + 8))
    check("Clip covers the stand-in's own edge (no white fringe where the quad fell short)",
          _lum(o3[band]).mean() < _lum(o4[band]).mean() - 30, f"{_lum(o3[band]).mean():.0f} vs {_lum(o4[band]).mean():.0f} unclipped")
    # key mode: a green stand-in in warm shade beside a dark-skin finger (same colour family as warm-shaded white)
    global KEY
    G = np.asarray(plate).copy()
    G[box[1]:box[3], box[0]:box[2]] = (40, 150, 60)
    G[box[1]:box[3], box[0]:box[0] + (box[2] - box[0]) // 2] = (25, 95, 38)    # the stand-in's shaded half
    fy = box[1] + (box[3] - box[1]) // 3
    G[fy:fy + 36, box[0] - 40:box[0] + 120] = (89, 72, 63)                       # a finger in shade
    KEY = "green"
    try:
        o5 = np.asarray(apply(Image.fromarray(G), prod, box, stamp="", clip=True, occlude=True)[0]).astype(np.float32)
    finally:
        KEY = None
    f5 = o5[fy + 8:fy + 28, box[0] + 10:box[0] + 100]
    check("Green key: shaded finger stays in front", np.abs(f5 - np.array([89, 72, 63])).mean() < 10, f"{np.abs(f5 - np.array([89, 72, 63])).mean():.1f}")
    g5 = o5[box[1] + 30:box[3] - 30, box[0] + 20:box[2] - 20]
    green_left = ((g5[..., 1] > 1.18 * g5[..., 0]) & (g5[..., 1] > 1.08 * g5[..., 2])).mean()
    check("Green key: no green stand-in left showing, print not tinted green", green_left < 0.02 and g5[..., 0].mean() > g5[..., 2].mean(), f"{green_left*100:.1f}% green")
    # banana / leaf green in front of a green stand-in must stay in front (it ghosted see-through on a real basket)
    KEY = "green"
    try:
        kb, _ = standin_like(np.array([[[77, 94, 4], [187, 193, 64], [48, 70, 6], [35, 161, 95], [2, 144, 68], [3, 40, 11]]], np.float32))
    finally:
        KEY = None
    check("Green key: banana and leaf green are not key; stand-in green, teal and deep crease are",
          list(kb[0]) == [False, False, False, True, True, True], str(list(kb[0])))
    # transparent PNG pixels are black: displace/soften must not drag them in as a dark rim (caught on a bag edge)
    pr = np.zeros((200, 160, 4), np.uint8); pr[:, :, :3] = (200, 60, 40); pr[20:180, 20:140, 3] = 255; pr[~(pr[..., 3] > 0)] = 0
    o6 = np.asarray(apply(plate, Image.fromarray(pr), box, stamp="", soften=2.0, displace=3.0, detail=0.5)[0]).astype(np.float32)
    rim = o6[box[1] + 60:box[3] - 60, box[0] + 1:box[0] + 6]
    check("Soften/displace: no dark rim from transparent pixels", _lum(rim).mean() > 60, f"edge lum {_lum(rim).mean():.0f}")
    if out_path:
        sheet = Image.new("RGB", (plate.width * 2, plate.height), "white")
        sheet.paste(plate, (0, 0)); sheet.paste(out, (plate.width, 0))
        sheet.save(out_path, quality=90)
        print(out_path)
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plate"); ap.add_argument("--product"); ap.add_argument("--box")
    ap.add_argument("--out", default="proxy_out.jpg")
    ap.add_argument("--strength", type=float, default=0.9, help="how much of the proxy's shading reaches the print (0-1)")
    ap.add_argument("--spec", type=float, default=0.5, help="carry the proxy's specular highlights (0 off, cap 1)")
    ap.add_argument("--grow", type=float, default=0.01, help="oversize the render so no proxy edge shows")
    ap.add_argument("--stamp", default=STAMP)
    ap.add_argument("--occlude", action="store_true", help="keep coloured things in front of the neutral proxy (fingers, basket rim)")
    ap.add_argument("--quad", default=None, help="x,y x4 (TL TR BR BL) of a tilted / held proxy; replaces --box")
    ap.add_argument("--clip", action="store_true", help="cut the print to the stand-in's exact drawn outline (no white fringe)")
    ap.add_argument("--key", default=None, choices=["green"], help="the stand-in is chroma green (exact cut round fingers)")
    ap.add_argument("--keep", default=None, help="hand-drawn mask, white = keep the plate (neutral occluders)")
    ap.add_argument("--selftest", action="store_true"); ap.add_argument("--sheet", default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest(a.sheet) else 1
    global KEY
    KEY = a.key
    if not (a.plate and a.product and (a.box or a.quad)):
        ap.print_help(); return 1
    quad = None
    if a.quad:
        v = [float(t) for t in a.quad.replace(" ", ",").split(",") if t]; quad = list(zip(v[0::2], v[1::2]))
    box = tuple(int(v) for v in a.box.split(",")) if a.box else None
    im, meta = apply(Image.open(a.plate), Image.open(a.product), box, a.strength, min(a.spec, 1.0), a.grow, a.stamp,
                     occlude=a.occlude, keep_img=Image.open(a.keep) if a.keep else None, quad=quad, clip=a.clip)
    im.save(a.out, quality=93)
    print(a.out, meta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
