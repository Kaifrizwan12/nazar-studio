#!/usr/bin/env python3
"""Test ui_devices.py on synthetic slides: each UI device drawn alone (with text on and around it) must be found,
and a type-only slide must come back empty.   python nazar-voiceprint/engine/test_ui_devices.py   (or pytest)"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ui_devices  # noqa: E402

FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "nazar-core", "engine", "fonts", "SpaceGrotesk-Medium.ttf")
GROUND, INK, BLUE, RED, GREY, WHITE = (236, 233, 226), (20, 20, 20), (51, 138, 233), (225, 45, 45), (200, 200, 200), (255, 255, 255)


def slide(draw_fn):
    im = Image.new("RGB", (1080, 1350), GROUND)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 64)
    d.text((80, 90), "Pehle aap, phir", font=f, fill=INK)          # a headline on every slide: text must not read as a device
    draw_fn(d, ImageFont.truetype(FONT, 34))
    return im


def bubble(d, f):
    d.rounded_rectangle((120, 400, 760, 640), 48, fill=BLUE)
    d.polygon([(150, 600), (230, 600), (130, 700)], fill=BLUE)       # tail at the bottom-left corner
    d.text((170, 480), "Verify karo, phir share", font=f, fill=WHITE)


def button(d, f):
    d.rounded_rectangle((120, 700, 620, 800), 50, fill=BLUE)
    d.text((200, 728), "Abhi dekho", font=f, fill=WHITE)


def card(d, f):
    d.rounded_rectangle((100, 380, 980, 1000), 28, fill=WHITE)
    d.text((160, 440), "Translate card", font=f, fill=INK)
    d.text((160, 500), "Ek line, ek baat", font=f, fill=INK)


def progress(d, f):
    d.rounded_rectangle((120, 900, 960, 924), 12, fill=GREY)
    d.rounded_rectangle((120, 900, 560, 924), 12, fill=BLUE)


def badge(d, f):
    d.rectangle((300, 500, 520, 720), outline=INK, width=6)
    d.ellipse((490, 470, 550, 530), fill=RED)


def toggle(d, f):
    d.rounded_rectangle((400, 700, 600, 800), 50, fill=BLUE)
    d.ellipse((508, 708, 592, 792), fill=WHITE)


CASES = {"chat bubble": bubble, "button/pill": button, "card": card, "progress bar": progress, "badge": badge, "toggle": toggle}


def test_each_device_found():
    for kind, fn in CASES.items():
        got = ui_devices.summary(ui_devices.find(slide(fn)))
        assert kind in got, f"{kind}: found {got}"


def test_survives_jpeg():
    import io
    for kind, fn in CASES.items():
        b = io.BytesIO(); slide(fn).save(b, "JPEG", quality=80); b.seek(0)
        got = ui_devices.summary(ui_devices.find(Image.open(b)))
        assert kind in got, f"{kind} after JPEG: found {got}"


def test_type_only_slide_is_empty():
    got = ui_devices.summary(ui_devices.find(slide(lambda d, f: d.text((80, 400), "Sirf type, koi device nahi", font=f, fill=INK))))
    assert not got, got


def test_square_accent_block_is_not_a_button():
    got = ui_devices.summary(ui_devices.find(slide(lambda d, f: d.rectangle((90, 1150, 250, 1190), fill=BLUE))))
    assert "button/pill" not in got, got


def test_shares():
    s = ui_devices.shares([slide(bubble), slide(bubble), slide(button), slide(lambda d, f: None)])
    assert s["chat bubble"] == 0.5 and s["button/pill"] == 0.25, s


if __name__ == "__main__":
    for kind, fn in CASES.items():
        print(f"{kind:<13} -> {ui_devices.summary(ui_devices.find(slide(fn)))}")
    test_each_device_found(); test_survives_jpeg(); test_type_only_slide_is_empty(); test_square_accent_block_is_not_a_button(); test_shares()
    print("ui_devices: all tests pass")
