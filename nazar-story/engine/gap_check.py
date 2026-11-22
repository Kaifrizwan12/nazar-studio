"""Air under headlines, measured on rendered panels.

  python gap_check.py <panels folder or files...> [--min 45]

For each panel (scaled to 1920 wide), it finds the headline (a text block ending in the top third) and the first ink
below it. It flags the panel when that gap is under --min px. A caption sitting on its own image is meant to be close,
so read the flags before changing anything. Exit code 1 if any panel is flagged.
"""
import glob, os, sys
import numpy as np
from PIL import Image


def gap(path):
    im = Image.open(path).convert("RGB"); s = 1920 / im.width
    a = np.asarray(im.resize((1920, round(im.height * s)))).astype(int); H = a.shape[0]
    bg = np.median(a[5:20, 1700:1900].reshape(-1, 3), 0)
    rows = (np.abs(a - bg).max(-1) > 28)[:, 60:1860].sum(1) > 3
    blocks, y = [], 0
    while y < H:
        if rows[y]:
            y0 = y
            while y < H and rows[y]:
                y += 1
            blocks.append((y0, y))
        y += 1
    hl = [b for b in blocks if 0.14 * H < b[1] < 0.31 * H and 35 < b[1] - b[0] < 120]
    if not hl:
        return None
    h = hl[-1]; nxt = [b for b in blocks if b[0] > h[1]]
    return (nxt[0][0] - h[1]) if nxt else None


def main(args):
    mn = int(args[args.index("--min") + 1]) if "--min" in args else 45
    files = []
    for x in [x for x in args if not x.startswith("--") and x != str(mn)]:
        files += sorted(glob.glob(os.path.join(x, "*.jpg")) + glob.glob(os.path.join(x, "*.png"))) if os.path.isdir(x) else [x]
    bad = 0
    for f in files:
        g = gap(f)
        if g is not None:
            flag = g < mn; bad += flag
            print(f"{os.path.basename(f):40s} gap {g:4d}px {'TIGHT' if flag else 'ok'}")
    print(f"{bad} tight"); return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
