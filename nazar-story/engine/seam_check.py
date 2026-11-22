"""Seams between stacked Behance panels (modules sit with no gap: the bottom of one panel touches the top of the next).

  python seam_check.py <panels folder> [--min-air 140] [--sheet out.jpg]

For each adjacent pair (in file-name order), at 1920 wide:
  - grounds: the colour of panel N's bottom rows and panel N+1's top rows. If they are the same, the two panels read as
    one page, so the air across the seam (N's empty bottom + N+1's empty top) must be at least --min-air, or it looks
    cramped and accidental.
  - ink at the edge: content touching or within 24 px of the edge that meets the next panel (unless both sides are
    full-bleed images, which is a deliberate cut).
  - air rhythm: lists each seam's air so the stack has an even beat (the spread is reported).
Writes an optional sheet of every seam (bottom strip of N over the top strip of N+1) to look at.
Exit code 1 if any seam is flagged.
"""
import glob, os, sys
import numpy as np
from PIL import Image, ImageDraw


def _load(f):
    im = Image.open(f).convert("RGB"); s = 1920 / im.width
    return np.asarray(im.resize((1920, round(im.height * s)))).astype(int)


def edge_info(a, side):
    """Ground colour at that edge, empty rows from the edge, and whether the edge is an image (busy) rather than a flat ground."""
    rows = a[:12] if side == "top" else a[-12:]
    ground = np.median(rows.reshape(-1, 3), 0)
    busy = float(np.abs(rows - ground).max(-1).mean()) > 18
    seq = a if side == "top" else a[::-1]
    diff = (np.abs(seq - ground).max(-1) > 26)[:, 40:-40].sum(1) > 3
    air = int(np.argmax(diff)) if diff.any() else a.shape[0]
    return ground, air, busy


def main(args):
    folder = args[0]
    mn = int(args[args.index("--min-air") + 1]) if "--min-air" in args else 140
    sheet = args[args.index("--sheet") + 1] if "--sheet" in args else None
    files = sorted(f for f in glob.glob(os.path.join(folder, "*.jpg")) + glob.glob(os.path.join(folder, "*.png"))
                   if __import__("re").search(r"_\d{2}\.(jpg|png)$", os.path.basename(f)))
    flags, airs, strips = 0, [], []
    for f1, f2 in zip(files, files[1:]):
        a, b = _load(f1), _load(f2)
        g1, air1, busy1 = edge_info(a, "bottom"); g2, air2, busy2 = edge_info(b, "top")
        same = not busy1 and not busy2 and np.abs(g1 - g2).max() <= 6
        msg = []
        if same and air1 + air2 < mn:
            msg.append(f"same ground, only {air1 + air2}px of air across the seam (< {mn})")
        if not (busy1 and busy2):
            if not busy1 and 0 < air1 < 24:                     # 0 = a full-bleed edge: a deliberate cut
                msg.append(f"ink {air1}px from the bottom edge")
            if not busy2 and 0 < air2 < 24:
                msg.append(f"ink {air2}px from the top edge")
        if same:
            airs.append(air1 + air2)
        flags += bool(msg)
        print(f"{os.path.basename(f1)[-6:-4]}|{os.path.basename(f2)[-6:-4]}  "
              f"{'same' if same else 'cut '}  air {air1:4d}+{air2:<4d} {'  ' + '; '.join(msg) if msg else ''}")
        if sheet:
            strips.append((os.path.basename(f1)[-6:-4] + "|" + os.path.basename(f2)[-6:-4],
                           np.vstack([a[-180:], np.full((2, 1920, 3), 255), b[:180]]).astype(np.uint8), bool(msg)))
    if airs:
        print(f"same-ground seams: air {min(airs)}..{max(airs)}px (an even beat keeps the stack calm)")
    if sheet and strips:
        cols = 3; tw = 640; th = int(362 * tw / 1920) + 26
        sh = Image.new("RGB", (cols * (tw + 10) + 10, ((len(strips) + cols - 1) // cols) * (th + 10) + 10), "#888"); d = ImageDraw.Draw(sh)
        for i, (lab, arr, bad) in enumerate(strips):
            x, y = 10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 10)
            im = Image.fromarray(arr).resize((tw, th - 26)); sh.paste(im, (x, y + 26))
            d.text((x + 4, y + 4), lab + ("  FLAG" if bad else ""), fill="#F33" if bad else "#FFF")
        sh.save(sheet, quality=86); print(sheet)
    print(f"{flags} seam(s) flagged"); return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
