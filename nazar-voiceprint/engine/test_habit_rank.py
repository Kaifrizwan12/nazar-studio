#!/usr/bin/env python3
"""HABIT ranking test on fixtures: a small synthetic archive with a clear habit (left-aligned headline and subline on an
off-white ground, ink type, a blue chat bubble in most pieces, a small blue accent), then four candidates whose order a
designer would agree on:
  good      the habit, with the bubble
  plain     the habit without the device (on-brand, but plainer than the archive)
  slop      on-palette, but centred, a pill badge above the headline and three equal cards (AI tells)
  gradient  centred type on a purple-blue gradient (the best-known AI tell)
The old gate can't separate good from plain (both pass every check); HABIT must order good > plain > slop, gradient.
    python nazar-voiceprint/engine/test_habit_rank.py   (or pytest)"""
import os
import random
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import score_pattern  # noqa: E402

FONT = os.path.join(HERE, "..", "..", "nazar-core", "engine", "fonts", "SpaceGrotesk-Medium.ttf")
GROUND, INK, BLUE, WHITE = (236, 233, 226), (24, 24, 24), (51, 138, 233), (255, 255, 255)
HEADS = ["Pehle aap", "Verify karo", "Sach bolo", "Chai pe baat", "Seedhi baat", "Kal milte hain", "Ek line kaafi", "Bas itna hi",
         "Socho phir", "Asli cheez"]


def designer(path, head, seed, bubble=True):
    rnd = random.Random(seed)
    im = Image.new("RGB", (1080, 1350), GROUND)
    d = ImageDraw.Draw(im)
    x, y = 90 + rnd.randint(-10, 10), 140 + rnd.randint(0, 120)
    d.text((x, y), head, font=ImageFont.truetype(FONT, 104 + rnd.randint(-8, 8)), fill=INK)
    d.text((x, y + 150), "seedhi baat, apni zubaan", font=ImageFont.truetype(FONT, 44), fill=INK)
    if bubble:
        by = 640 + rnd.randint(0, 160)
        d.rounded_rectangle((x, by, x + 600, by + 220), 44, fill=BLUE)
        d.polygon([(x + 30, by + 180), (x + 110, by + 180), (x + 10, by + 280)], fill=BLUE)
        d.text((x + 50, by + 80), "haan, yehi", font=ImageFont.truetype(FONT, 40), fill=WHITE)
    else:
        d.rectangle((x, 1150, x + 160, 1190), fill=BLUE)                 # the small accent block
    im.save(path)


def slop(path):
    im = Image.new("RGB", (1080, 1350), GROUND)
    d = ImageDraw.Draw(im)
    f, fs = ImageFont.truetype(FONT, 96), ImageFont.truetype(FONT, 40)
    d.rounded_rectangle((420, 150, 660, 210), 30, fill=INK)              # a pill badge above the headline
    d.text((540, 180), "NEW", font=ImageFont.truetype(FONT, 30), fill=WHITE, anchor="mm")
    d.text((540, 300), "Elevate your", font=f, fill=INK, anchor="mm")
    d.text((540, 420), "chai journey", font=f, fill=INK, anchor="mm")
    d.text((540, 520), "seamless and robust", font=fs, fill=INK, anchor="mm")
    for i in range(3):                                                  # three equal cards
        d.rounded_rectangle((80 + i * 320, 700, 360 + i * 320, 1100), 30, fill=WHITE)
    d.rectangle((480, 1200, 600, 1212), fill=BLUE)
    im.save(path)


def gradient(path):
    im = Image.new("RGB", (1080, 1350))
    px = im.load()
    for yy in range(1350):
        for xx in range(0, 1080, 4):
            t = (xx / 1080 + yy / 1350) / 2
            c = (int(110 + 40 * t), int(40 + 30 * t), int(220 - 30 * t))
            for k in range(4):
                px[xx + k, yy] = c
    d = ImageDraw.Draw(im)
    d.text((540, 560), "Unlock your", font=ImageFont.truetype(FONT, 96), fill=WHITE, anchor="mm")
    d.text((540, 680), "next level", font=ImageFont.truetype(FONT, 96), fill=WHITE, anchor="mm")
    im.save(path)


def fixtures(root):
    arch, cand = os.path.join(root, "archive"), os.path.join(root, "candidates")
    os.makedirs(arch); os.makedirs(cand)
    for i, h in enumerate(HEADS):
        designer(os.path.join(arch, f"a{i:02d}.png"), h, i, bubble=i % 5 != 4)    # bubble in 8 of 10 pieces
    designer(os.path.join(cand, "good.png"), "Doodh patti", 101)
    designer(os.path.join(cand, "plain.png"), "Doodh patti", 101, bubble=False)
    slop(os.path.join(cand, "slop.png"))
    gradient(os.path.join(cand, "gradient.png"))
    return arch, cand


def test_habit_ranks_good_work():
    with tempfile.TemporaryDirectory() as d:
        arch, cand = fixtures(d)
        pat = score_pattern.build(arch)
        assert pat["habit"]["devices"].get("chat bubble", 0) >= 0.6, pat["habit"]
        assert pat["habit"]["alignment"]["left"] >= 0.8, pat["habit"]
        copy = {"slop.png": "NEW Elevate your chai journey. Seamless and robust."}
        rows = score_pattern.rank(pat, cand, copy)
        order = [r["file"] for r in rows]
        by = {r["file"]: r for r in rows}
        for r in rows:
            print(f"   {r['file']:<13} HABIT {r['habit']:.2f}  gate {r['gate']:.2f}  {' | '.join(r['why'])}")
        assert order[:2] == ["good.png", "plain.png"], order
        assert by["good.png"]["gate"] == by["plain.png"]["gate"], "the gate alone should not separate these"
        assert by["plain.png"]["habit"] - max(by["slop.png"]["habit"], by["gradient.png"]["habit"]) >= 0.15, order
        assert "everything centred" in by["slop.png"]["measures"]["tells"]
        assert "pill badge above the headline" in by["slop.png"]["measures"]["tells"]
        assert "three-card skeleton" in by["slop.png"]["measures"]["tells"]
        assert "purple-blue gradient" in by["gradient.png"]["measures"]["tells"]


def test_archive_tell_is_not_penalised():
    """A tell the designer's own archive uses (here: centred type) costs nothing."""
    hs = {"devices": {}, "alignment": {"left": 0.1, "centre": 0.9, "right": 0.0}, "lines": [1, 2, 4],
          "tells": {t: 0.0 for t in score_pattern.TELLS}}
    hs["tells"]["everything centred"] = 0.9
    with tempfile.TemporaryDirectory() as d:
        _, cand = fixtures(d)
        pat = {"format": [1080, 1350], "grounds": ["#ECE9E2"], "swatches": ["#181818", "#FFFFFF"], "accent": "#338AE9", "habit": hs}
        refs = {"grounds": score_pattern.lab_of_hex(pat["grounds"]), "accent": score_pattern.lab_of_hex([pat["accent"]]),
                "swatches": score_pattern.lab_of_hex(pat["swatches"] + pat["grounds"] + [pat["accent"]])}
        r = score_pattern.habit_score(os.path.join(cand, "slop.png"), pat, refs)
        assert not any("everything centred" in w for w in r["why"]), r["why"]


if __name__ == "__main__":
    test_habit_ranks_good_work(); test_archive_tell_is_not_penalised()
    print("habit rank: all tests pass")
