#!/usr/bin/env python3
"""
nazar-core/engine/place_asset.py: place a brand's exact files without redrawing them (every agent re-wrote this and got the
edges wrong).

  backdrop  fit a supplied backdrop to a format:
              python place_asset.py backdrop in.png out.png 4:5
            Larger than the format: cropped from the top-left, never scaled (900x1600 -> 900x1125 for 4:5).
            Square or smaller (1080x1080 -> 4:5): needs an upscale and a side crop. That is resampling, so it is done
            uniformly (never stretched), the pixels are otherwise untouched, and it prints a warning: ask for the 4:5 source.
  mascot    place a mascot or sticker that sits on white paper, keeping its own colours:
              python place_asset.py mascot slide.png mascot.png x y height [out.png]
            Removes only the white paper connected to the border (a flood fill), so eye whites and highlights inside the artwork
            stay, and the original pixels are pasted untouched. Multiply would turn yellow shoes olive on a blue ground.
            Works on light or dark slides.
  logo      paste a logo that sits on white paper, onto a light slide:
              python place_asset.py logo slide.png logo.jpg x y height [out.png]
            Crops to the visible mark with a threshold (JPEG noise leaves a halo around exact white, which makes the logo
            look small and off the margin), then blends with multiply so the paper drops out and the artwork's own
            pixels are untouched. Light grounds only: there is no light-on-dark version unless one is supplied.
"""
import sys

from PIL import Image, ImageChops


def backdrop(src, out, ratio):
    rw, rh = (int(v) for v in ratio.split(":"))
    im = Image.open(src).convert("RGB"); w, h = im.size
    target_h = round(w * rh / rw)
    if target_h <= h:                          # taller than needed: crop, never scale
        res = im.crop((0, 0, w, target_h)); note = "cropped, not scaled"
    else:                                      # too short for the ratio at this width
        scale = target_h / h
        big = im.resize((round(w * scale), target_h), Image.LANCZOS)
        new_w = round(target_h * rw / rh)
        res = big.crop((big.width - new_w, 0, big.width, target_h))
        note = (f"WARNING: {w}x{h} is too small for {ratio}: upscaled {scale:.2f}x (uniform) and side-cropped. "
                "That is resampling: label it, and ask for the original 4:5 file (or use a taller story-size backdrop, cropped, if it has no baked-in text)")
    res.save(out); print(f"{out}: {res.size[0]}x{res.size[1]}  {note}")


def mascot(slide, art_path, x, y, height, out=None):
    from PIL import ImageDraw
    im = Image.open(slide).convert("RGB")
    art = Image.open(art_path).convert("RGB")
    near_white = art.convert("L").point(lambda v: 255 if v > 238 else 0)
    # flood the paper from the four corners and edges: only white connected to the border is background
    paper = near_white.copy()
    w, h = paper.size
    for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)):
        if paper.getpixel(seed) == 255:
            ImageDraw.floodfill(paper, seed, 128)
    bg = paper.point(lambda v: 255 if v == 128 else 0)           # the paper, connected to the border
    alpha = ImageChops.invert(bg)
    box = alpha.getbbox()
    art, alpha = art.crop(box), alpha.crop(box)
    sc = height / art.height
    size = (round(art.width * sc), height)
    art, alpha = art.resize(size, Image.LANCZOS), alpha.resize(size, Image.LANCZOS)
    im.paste(art, (x, y), alpha)
    im.save(out or slide); print(f"{out or slide}: mascot {size[0]}x{size[1]} at ({x},{y}), paper removed by flood fill, colours untouched")


def logo(slide, logo_path, x, y, height, out=None):
    im = Image.open(slide).convert("RGB")
    lg = Image.open(logo_path).convert("RGB")
    diff = ImageChops.difference(lg, Image.new("RGB", lg.size, (255, 255, 255))).convert("L").point(lambda v: 255 if v > 60 else 0)
    lg = lg.crop(diff.getbbox())
    lg = lg.resize((round(lg.width * height / lg.height), height), Image.LANCZOS)
    region = im.crop((x, y, x + lg.width, y + height))
    im.paste(ImageChops.multiply(region, lg), (x, y))
    im.save(out or slide); print(f"{out or slide}: logo {lg.width}x{lg.height} at ({x},{y}), multiply-blended")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 4 and a[0] == "backdrop":
        backdrop(a[1], a[2], a[3])
    elif len(a) >= 6 and a[0] == "mascot":
        mascot(a[1], a[2], int(a[3]), int(a[4]), int(a[5]), a[6] if len(a) > 6 else None)
    elif len(a) >= 6 and a[0] == "logo":
        logo(a[1], a[2], int(a[3]), int(a[4]), int(a[5]), a[6] if len(a) > 6 else None)
    else:
        sys.exit(__doc__)
