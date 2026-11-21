#!/usr/bin/env python3
"""Test composers.py on synthetic products (no brands): the full self-test, plus the CLI and the contact sheet.
    python nazar-story/engine/test_composers.py      (or pytest nazar-story/engine/test_composers.py)"""
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import composers as C  # noqa: E402


def test_selftest_all_pass():
    assert C.selftest(verbose=False) == []


def test_every_composer_on_the_sheet():
    out = os.path.join(tempfile.mkdtemp(), "sheet.jpg")
    comps = C.demo_set()
    assert {c.device for _, c in comps} >= {"hand of cards", "front-back pair", "overlap row", "scale lineup", "standing row",
                                             "cascade", "stack", "hero bleed", "specimen grid", "scatter", "extended plate"}
    C.sheet(out, comps)
    im = Image.open(out)
    assert im.width > 1000 and im.height > 1000


def test_one_light_across_the_sheet():
    signs = {(np.sign(dx), np.sign(dy)) for _, c in C.demo_set() for dx, dy in c.meta.get("shadow_offsets", [])}
    assert len(signs) == 1


def test_device_log_reads_a_deck_and_warns():
    class FakeDeck: devices = [(1, "hero bleed"), (2, "front-back pair"), (5, "hero bleed")]
    log = C.DeviceLog(); log.add_deck(FakeDeck())
    rep = log.report(warn=False)
    assert rep == ["device 'hero bleed' repeats: p1 and p5"]


def test_cli_compose_row_true_scale():
    d = tempfile.mkdtemp(); paths = []
    for i, (k, h) in enumerate([("sachet", 300), ("pouch", 500)]):
        p = os.path.join(d, f"p{i}.png"); C.synthetic(k, h, C.PALETTE[i]).save(p); paths.append(p)
    out = os.path.join(d, "row.png")
    r = subprocess.run([sys.executable, os.path.join(HERE, "composers.py"), "compose", "row", *paths, "-o", out,
                        "--mm", "90,180", "--height", "360", "--overlap", "-0.1"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "scale lineup" in r.stdout and Image.open(out).mode == "RGBA"


def test_cli_selftest_exit_code():
    r = subprocess.run([sys.executable, os.path.join(HERE, "composers.py"), "--selftest"], capture_output=True, text=True)
    assert r.returncode == 0 and "ALL PASS" in r.stdout, r.stdout[-800:]


if __name__ == "__main__":
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try: fn(); print("PASS", name)
            except AssertionError as e: fails += 1; print("FAIL", name, e)
    print("ALL PASS" if not fails else f"{fails} FAIL"); sys.exit(1 if fails else 0)
