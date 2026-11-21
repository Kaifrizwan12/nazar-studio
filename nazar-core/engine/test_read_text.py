#!/usr/bin/env python3
"""Test read_text.py on rendered slides (dark type on light, light type on dark) and its no-OCR message.
    python nazar-core/engine/test_read_text.py   (or pytest)
Needs an OCR engine (macOS Vision, tesseract, or pytesseract); without one the reading tests are skipped, not failed."""
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import read_text  # noqa: E402

FONT = os.path.join(HERE, "fonts", "SpaceGrotesk-Medium.ttf")
LINES = ["Verify karo", "phir share karo"]


def render(path, ground, ink):
    im = Image.new("RGB", (1080, 1350), ground)
    d = ImageDraw.Draw(im)
    d.text((90, 160), LINES[0], font=ImageFont.truetype(FONT, 110), fill=ink)
    d.text((90, 1100), LINES[1], font=ImageFont.truetype(FONT, 48), fill=ink)       # small, far from the headline
    im.save(path)


def _words(lines):
    return " ".join(t for _, t, *_ in lines).lower().split()


def test_reads_light_and_dark_slides():
    if not read_text.engine():
        print("skip: no OCR engine on this machine"); return
    with tempfile.TemporaryDirectory() as d:
        for name, ground, ink in (("light.png", (236, 233, 226), (20, 20, 20)), ("dark.png", (18, 22, 40), (245, 245, 245))):
            p = os.path.join(d, name); render(p, ground, ink)
            got = read_text.read_boxes([p])[p]
            words = _words(got)
            for w in "verify karo phir share".split():
                assert w in words, (name, read_text.engine(), got)
            first = got[0]
            assert "verify" in first[1].lower() and first[2] is not None and first[2][1] < 0.25, (name, first)


def test_folder_to_copy_json():
    if not read_text.engine():
        print("skip: no OCR engine on this machine"); return
    with tempfile.TemporaryDirectory() as d:
        render(os.path.join(d, "s1.png"), (255, 255, 255), (0, 0, 0))
        out = os.path.join(d, "copy.json")
        r = subprocess.run([sys.executable, os.path.join(HERE, "read_text.py"), d, out], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        import json
        assert "karo" in json.load(open(out, encoding="utf-8"))["s1.png"].lower()


def test_clear_message_without_ocr():
    code = ("import sys, os; sys.path.insert(0, %r); os.environ['PATH']=''; os.environ.pop('TESSERACT_CMD', None); import read_text as r; "
            "r.sys.platform='linux'; r.WIN_PATHS=[]; r._pytesseract=lambda: None; r.read(%r)")
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "s.png"); render(p, (255, 255, 255), (0, 0, 0))
        res = subprocess.run([sys.executable, "-c", code % (HERE, p)], capture_output=True, text=True)
        assert res.returncode != 0 and "no OCR available" in res.stderr and "Tesseract-OCR" in res.stderr, res.stderr


if __name__ == "__main__":
    print("OCR engine:", read_text.engine())
    test_reads_light_and_dark_slides(); test_folder_to_copy_json(); test_clear_message_without_ocr()
    print("read_text: all tests pass")
