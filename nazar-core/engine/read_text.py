#!/usr/bin/env python3
"""
nazar-core/engine/read_text.py: read the text on finished slides, so the language and copy checks have something to read.

    python read_text.py slides_folder copy.json        # writes {"slide.png": "all its text"} for chain_check / studio.py
    python read_text.py slide.png                      # prints the lines with their confidence

Uses what the machine already has, in this order: macOS's built-in Vision recogniser (compiled once from
ocr_mac.swift into ~/.cache/nazar, offline, nothing installed); then the `tesseract` program (on the PATH, in
$TESSERACT_CMD, or at the Windows installer's default folder "C:/Program Files/Tesseract-OCR"); then the
`pytesseract` package if it is installed and can reach a tesseract. With none of them it stops with what to install.
Before tesseract the slide is prepared the way its documentation advises (references/research_ocr.md): light type on a
dark ground is inverted (tesseract 4+ expects dark on light), small images are scaled up so the type is large enough,
and a 10 px border is added; slides are read as sparse text (--psm 11), which finds scattered headlines and labels that
the default page mode skips. Tesseract gives a confidence and a box per line here too.
It does not "correct" words (Roman Urdu is not English). OCR drops or splits words on stylised type, so check its
output against the slide, especially for small text; it is a first draft of copy.json, not the truth.
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.expanduser("~/.cache/nazar")
EXTS = (".png", ".jpg", ".jpeg", ".webp")


def mac_binary():
    out = os.path.join(CACHE, "ocr_mac")
    src = os.path.join(HERE, "ocr_mac.swift")
    if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(src):
        return out
    if not shutil.which("swiftc"):
        return None
    os.makedirs(CACHE, exist_ok=True)
    r = subprocess.run(["swiftc", "-O", src, "-o", out], capture_output=True, text=True)
    return out if r.returncode == 0 else None


def read_many(paths):
    """{path: [(confidence, line), ...]} in one pass (macOS: one process, the model loads once)."""
    return {p: [(c, t) for c, t, _ in rows] for p, rows in read_boxes(paths).items()}


def read_boxes(paths):
    """{path: [(confidence, line, (x, y, w, h)), ...]}: where each line sits, as fractions of the image from the top-left."""
    if sys.platform == "darwin":
        b = mac_binary()
        if b:
            r = subprocess.run([b, *paths], capture_output=True, text=True)
            out, cur = {p: [] for p in paths}, None
            for ln in r.stdout.splitlines():
                if ln.startswith("#FILE	"):
                    cur = ln.split("	", 1)[1]; out.setdefault(cur, []); continue
                parts = ln.split("	", 5)
                try:
                    if cur is not None and len(parts) == 6:
                        out[cur].append((float(parts[0]), parts[5].strip(), tuple(float(v) for v in parts[1:5])))
                    elif cur is not None and len(parts) == 2:
                        out[cur].append((float(parts[0]), parts[1].strip(), None))
                except ValueError:
                    pass
            return out
    return {p: tesseract_lines(p) for p in paths}


WIN_PATHS = [os.path.join(r"C:\Program Files", "Tesseract-OCR", "tesseract.exe"),
             os.path.join(r"C:\Program Files (x86)", "Tesseract-OCR", "tesseract.exe"),
             os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe")]


def tesseract_cmd():
    """The tesseract program: $TESSERACT_CMD, the PATH, then the Windows installer's default folders."""
    env = os.environ.get("TESSERACT_CMD")
    if env and os.path.isfile(env):
        return env
    w = shutil.which("tesseract")
    if w:
        return w
    for p in WIN_PATHS:
        if p and os.path.isfile(p):
            return p
    return None


def _pytesseract():
    try:
        import pytesseract
    except ImportError:
        return None
    try:
        pytesseract.get_tesseract_version()
        return pytesseract
    except Exception:      # noqa: BLE001  installed, but it cannot reach a tesseract program
        return None


NO_OCR = ("no OCR available. Install one of: tesseract (Windows: the UB Mannheim installer, which puts it in "
          r"C:\Program Files\Tesseract-OCR; macOS: brew install tesseract; Linux: apt install tesseract-ocr), or set "
          "TESSERACT_CMD to tesseract.exe; on macOS, swiftc (Xcode command line tools) for the built-in Vision reader. "
          "Or write copy.json by hand: {\"slide.png\": \"all its text\"}.")


def prepare(path):
    """The slide as tesseract reads best (tessdoc ImproveQuality): grey, dark type on light (invert a dark ground), type
    large enough (scale up to at least 1600 px on the long side), a 10 px border. Returns (image, scale, border)."""
    from PIL import Image, ImageOps
    im = Image.open(path).convert("L")
    w, h = im.size
    sm = im.copy(); sm.thumbnail((64, 64))
    px = sorted(sm.getdata())
    if px[len(px) // 2] < 110:                              # mostly dark: light type on a dark ground
        im = ImageOps.invert(im)
    sc = max(1.0, 1600 / max(w, h))
    if sc > 1:
        im = im.resize((round(w * sc), round(h * sc)), Image.LANCZOS)
    return ImageOps.expand(im, 10, fill=255), sc, 10


def _lines_from_tsv(tsv, size, sc, pad):
    w, h = size
    rows, order = {}, []
    for ln in tsv.splitlines()[1:]:
        f = ln.split("	")
        if len(f) < 12 or not f[11].strip():
            continue
        try:
            conf = float(f[10])
        except ValueError:
            continue
        if conf < 0:
            continue
        k = (f[2], f[3], f[4])
        if k not in rows:
            rows[k] = []; order.append(k)
        x, y, bw, bh = (int(v) for v in f[6:10])
        rows[k].append((conf, f[11].strip(), ((x - pad) / sc, (y - pad) / sc, bw / sc, bh / sc)))
    out = []
    for k in order:
        ws = rows[k]
        x0 = min(b[0] for _, _, b in ws); y0 = min(b[1] for _, _, b in ws)
        x1 = max(b[0] + b[2] for _, _, b in ws); y1 = max(b[1] + b[3] for _, _, b in ws)
        out.append((round(sum(c for c, _, _ in ws) / len(ws) / 100, 2), " ".join(t for _, t, _ in ws),
                    (max(0, x0) / w, max(0, y0) / h, (x1 - x0) / w, (y1 - y0) / h)))
    out.sort(key=lambda r: (round(r[2][1], 2), r[2][0]))   # top to bottom, then left to right
    return out


def tesseract_lines(path, psm=11):
    """[(confidence 0-1, line, box)] by the tesseract program, else pytesseract, else stop with what to install."""
    import tempfile
    from PIL import Image
    size = Image.open(path).size
    im, sc, pad = prepare(path)
    cmd = tesseract_cmd()
    if cmd:
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "slide.png"); im.save(src)
            r = subprocess.run([cmd, src, "-", "--psm", str(psm), "tsv"], capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0:
            return _lines_from_tsv(r.stdout, size, sc, pad)
    pt = _pytesseract()
    if pt:
        return _lines_from_tsv(pt.image_to_data(im, config=f"--psm {psm}"), size, sc, pad)
    sys.exit(NO_OCR)


def read(path):
    """Returns a list of (confidence, line) from top to bottom."""
    return [(c, t) for c, t, _ in read_boxes([path])[path]]


def engine():
    """Which reader this machine will use (for selftest and the docs)."""
    if sys.platform == "darwin" and mac_binary():
        return "macOS Vision"
    if tesseract_cmd():
        return "tesseract (" + tesseract_cmd() + ")"
    if _pytesseract():
        return "pytesseract"
    return None


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    target = sys.argv[1]
    if os.path.isdir(target):
        names = [f for f in sorted(os.listdir(target)) if f.lower().endswith(EXTS)]
        got = read_many([os.path.join(target, f) for f in names])
        out = {f: " ".join(t for _, t in got[os.path.join(target, f)]) for f in names}
        dest = sys.argv[2] if len(sys.argv) > 2 else os.path.join(target, "copy.json")
        json.dump(out, open(dest, "w"), indent=1, ensure_ascii=False)
        print(f"{dest}: text for {len(out)} slides. Check it against the slides before trusting it.")
    else:
        for c, t in read(target):
            print(f"{c:.2f}  {t}")
