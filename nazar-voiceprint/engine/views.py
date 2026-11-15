#!/usr/bin/env python3
"""
nazar-voiceprint/engine/views.py: prepare the views a vision model needs to see
a designer's or illustrator's patterns (numpy + Pillow only).

Why: vision-language models are weak at fine detail, counting and small spatial
relations ("Vision language models are blind", Rahmanzadehgervi et al. 2024),
and good at gestalt. So don't hand them one flattened thumbnail and ask for
"the style". Hand them purpose-built views, each answering one question:

  squint      blurred and tiny: what survives the squint test? (hierarchy, mass, focal point)
  grey        luminance only: does it still read without hue? (value structure)
  flat        posterised to 4 colours: the real palette logic and figure-ground
  edges       edge map: line quality, contour vs fill, where detail lives
  crops       the four corners and the centre at full detail: terminals, hands, eyes,
              lettering, edge treatments, signatures: the habitual minor details
              (Morelli's method; Ginzburg, "Clues", 1979)

Output: one study sheet per piece, plus contact.jpg (the whole body of work at once,
to see what recurs). Read them with the image tool, then follow references/vlm_protocol.md.

    python views.py image_or_folder out_dir
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "..", "nazar-core", "engine", "fonts", "SpaceMono-Regular.ttf")


def font(s):
    try:
        return ImageFont.truetype(FONT, s)
    except OSError:
        return ImageFont.load_default()


def squint(im, size=64):
    g = im.convert("RGB").filter(ImageFilter.GaussianBlur(max(im.size) / 28))
    g.thumbnail((size, size))
    return g.resize((size * 5, int(size * 5 * g.height / g.width)), Image.NEAREST)


def flat(im, k=4):
    p = im.convert("RGB").quantize(colors=k, method=Image.MEDIANCUT, dither=Image.NONE)
    return p.convert("RGB")


def edges(im):
    g = ImageOps.autocontrast(im.convert("L").filter(ImageFilter.GaussianBlur(0.8)))
    e = np.asarray(g.filter(ImageFilter.FIND_EDGES), np.float32)
    e = np.clip(e * 3, 0, 255).astype(np.uint8)
    return ImageOps.invert(Image.fromarray(e)).convert("RGB")


def crops(im, size=300):
    w, h = im.size
    c = min(w, h) // 3
    boxes = {"top-left": (0, 0), "top-right": (w - c, 0), "bottom-left": (0, h - c), "bottom-right": (w - c, h - c),
             "centre": ((w - c) // 2, (h - c) // 2)}
    return [(n, im.crop((x, y, x + c, y + c)).resize((size, size), Image.LANCZOS)) for n, (x, y) in boxes.items()]


def sheet(path, out_dir):
    im = Image.open(path).convert("RGB")
    base = im.copy(); base.thumbnail((640, 640))
    panels = [("original", base), ("squint 64px", squint(im)), ("grey", ImageOps.grayscale(base).convert("RGB")),
              ("flat 4 colours", flat(base)), ("edges", edges(base))]
    cs = crops(im)
    pw = 330
    row1 = [(n, p.resize((pw, int(pw * p.height / p.width)))) for n, p in panels]
    rh = max(p.height for _, p in row1)
    W = pw * 5 + 60
    H = rh + 40 + 300 + 70
    s = Image.new("RGB", (W, H), "#F2EEE6")
    d = ImageDraw.Draw(s)
    for i, (n, p) in enumerate(row1):
        s.paste(p, (10 + i * (pw + 10), 30)); d.text((12 + i * (pw + 10), 8), n, font=font(14), fill="#1C1B19")
    y = rh + 70
    for i, (n, p) in enumerate(cs):
        p = p.resize((300, 300))
        s.paste(p, (10 + i * 310, y)); d.text((12 + i * 310, y - 22), "crop: " + n, font=font(14), fill="#1C1B19")
    name = os.path.splitext(os.path.basename(path))[0] + "_study.jpg"
    s.save(os.path.join(out_dir, name), quality=88)
    return name


def contact(paths, out_dir, cell=260, cols=6):
    rows = (len(paths) + cols - 1) // cols
    s = Image.new("RGB", (cols * (cell + 8) + 8, rows * (cell + 8) + 8), "#F2EEE6")
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGB"); im.thumbnail((cell, cell))
        s.paste(im, (8 + (i % cols) * (cell + 8), 8 + (i // cols) * (cell + 8)))
    s.save(os.path.join(out_dir, "contact.jpg"), quality=88)


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    files = [src] if os.path.isfile(src) else sorted(os.path.join(src, f) for f in os.listdir(src) if os.path.splitext(f)[1].lower() in EXTS)
    for f in files:
        print("study sheet:", sheet(f, out))
    if len(files) > 1:
        contact(files, out)
        print("contact sheet: contact.jpg (read this first: what recurs across the whole body of work?)")
