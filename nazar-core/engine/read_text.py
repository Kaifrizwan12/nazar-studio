#!/usr/bin/env python3
"""
nazar-core/engine/read_text.py: read the text on finished slides, so the language and copy checks have something to read.

    python read_text.py slides_folder copy.json        # writes {"slide.png": "all its text"} for chain_check / studio.py
    python read_text.py slide.png                      # prints the lines with their confidence

Uses what the machine already has, in this order: macOS's built-in Vision recogniser (compiled once from
ocr_mac.swift into ~/.cache/nazar, offline, nothing installed), then `tesseract` if it is on the PATH. On other
machines without tesseract it says so and stops: install tesseract, or write copy.json by hand.
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
    if sys.platform == "darwin":
        b = mac_binary()
        if b:
            r = subprocess.run([b, *paths], capture_output=True, text=True)
            out, cur = {p: [] for p in paths}, None
            for ln in r.stdout.splitlines():
                if ln.startswith("#FILE\t"):
                    cur = ln.split("\t", 1)[1]; out.setdefault(cur, []); continue
                c, _, t = ln.partition("\t")
                try:
                    if cur is not None:
                        out[cur].append((float(c), t.strip()))
                except ValueError:
                    pass
            return out
    return {p: read(p) for p in paths}


def read(path):
    """Returns a list of (confidence, line) from top to bottom."""
    if sys.platform == "darwin":
        b = mac_binary()
        if b:
            return read_many([path])[path]
    if shutil.which("tesseract"):
        r = subprocess.run(["tesseract", path, "-", "--psm", "6"], capture_output=True, text=True)
        return [(1.0, ln.strip()) for ln in r.stdout.splitlines() if ln.strip()]
    sys.exit("no OCR available: macOS Vision needs swiftc, otherwise install tesseract, or write copy.json by hand")


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
