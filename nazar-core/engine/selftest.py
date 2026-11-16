#!/usr/bin/env python3
"""
nazar-core/engine/selftest.py: check that the studio's tools run on this machine (about 20 seconds, no network, none of your files).

    python nazar-core/engine/selftest.py

Builds a few synthetic slides in a temp folder, runs each tool on them and prints OK or FAIL with a hint. A FAIL names the missing
piece (a pip package, a font, swiftc or tesseract for reading slide text). Run it after installing, and again if a tool
misbehaves, before blaming the archive.
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ENGINE = os.path.join(ROOT, "nazar-core", "engine")
results = []


def step(name, fn, hint=""):
    try:
        results.append((name, True, fn() or ""))
    except Exception as e:      # noqa: BLE001
        results.append((name, False, f"{type(e).__name__}: {str(e)[:110]}  {hint}"))


def py(*args):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True, timeout=300)
    if r.returncode:
        msg = (r.stderr or r.stdout).strip().splitlines()
        raise RuntimeError(msg[-1] if msg else "non-zero exit")
    return r.stdout


def main():
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy  # noqa: F401
    except ImportError as e:
        sys.exit(f"FAIL: {e}. Run: pip install -r nazar-core/engine/requirements.txt")
    tmp = tempfile.mkdtemp(prefix="nazar_selftest_")
    font_path = os.path.join(ENGINE, "fonts", "Anton-Regular.ttf")
    if not os.path.exists(font_path):
        sys.exit("FAIL: nazar-core/engine/fonts/Anton-Regular.ttf is missing: copy the whole nazar-core folder, not just SKILL.md")
    train, slides, out = (os.path.join(tmp, n) for n in ("train", "slides", "out"))
    os.makedirs(train); os.makedirs(slides)
    big = ImageFont.truetype(font_path, 130)
    for i in range(8):               # a tiny "archive": 4:5, a light and a dark ground, one blue accent
        dark = i % 3 == 0
        im = Image.new("RGB", (540, 675), (16, 18, 24) if dark else (236, 236, 228))
        d = ImageDraw.Draw(im)
        d.text((30, 120), f"HEADLINE {i}", font=big, fill=(245, 245, 240) if dark else (14, 14, 16))
        d.text((30, 260), "ACCENT LINE", font=big, fill=(51, 138, 230))
        d.text((30, 600), "@brand", font=ImageFont.truetype(font_path, 22), fill=(120, 120, 120))
        im.save(os.path.join(train, f"p{i}.png"))
    Image.open(os.path.join(train, "p1.png")).save(os.path.join(slides, "s1.png"))
    json.dump({"s1.png": "HEADLINE 1 ACCENT LINE"}, open(os.path.join(tmp, "copy.json"), "w"))
    pattern = os.path.join(out, "pattern.json")

    def learn():
        py(f"{ENGINE}/studio.py", "learn", train, out)
        if not os.path.exists(pattern):
            raise RuntimeError("learn did not write pattern.json")
        return "pattern.json written"

    def check():
        py(f"{ENGINE}/studio.py", "check", slides, os.path.join(tmp, "copy.json"), pattern, os.path.join(tmp, "sheet.jpg"))
        return "contrast, language, lint, QA ran"

    crop = os.path.join(tmp, "crop.png")
    im = Image.new("RGB", (700, 190), (230, 232, 226)); ImageDraw.Draw(im).text((20, 20), "SAME BRANDS.", font=big, fill=(12, 12, 12)); im.save(crop)

    def font():
        if "Anton" not in py(f"{ROOT}/nazar-type/engine/font_match.py", crop, "SAME BRANDS.", "--top", "1"):
            raise RuntimeError("did not rank Anton first")
        return "found the font it was drawn in"

    def ocr():
        return "read: " + py(f"{ENGINE}/read_text.py", os.path.join(slides, "s1.png")).strip().replace("\n", " | ")[:60]

    step("studio.py learn (measure an archive)", learn, "needs numpy and Pillow")
    step("studio.py check (contrast, language, lint, QA)", check)
    step("font_match.py", font)
    step("qa_views.py", lambda: py(f"{ENGINE}/qa_views.py", slides, os.path.join(tmp, "qa.jpg")) and "ok")
    step("read_text.py (reads text on slides)", ocr, "needs macOS with swiftc, or tesseract on the PATH; otherwise write copy.json by hand")
    step("place_asset.py (crop a backdrop to 4:5)", lambda: py(f"{ENGINE}/place_asset.py", "backdrop", os.path.join(train, "p1.png"), os.path.join(tmp, "bd.png"), "4:5").strip()[:70])
    width = max(len(n) for n, _, _ in results)
    for n, ok, note in results:
        print(f"{'OK  ' if ok else 'FAIL'}  {n:<{width}}  {note}")
    bad = [n for n, ok, _ in results if not ok]
    print("\nAll tools run." if not bad else f"\n{len(bad)} problem(s): fix the hints above, then rerun.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
