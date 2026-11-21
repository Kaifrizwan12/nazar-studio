"""Self-check for flavour_cycle.py (synthetic pouches, temp folder only): python test_flavour_cycle.py  (or pytest)
Covers timing per style and fps, beat sync, sizes per aspect and platform, the crisp wipe (no two-pack blend),
contact shadow, end card, pixel-exact loop, flash safety (and that the analyser catches a strobe), the MP4 encode."""
import os, shutil, sys, tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import flavour_cycle as fc  # noqa: E402

TMP = tempfile.mkdtemp(prefix="fc_test_")
TINTS = [(232, 168, 40), (198, 58, 72), (60, 90, 160)]
ITEMS = [dict(name=n, pack=fc.synthetic_pouch(os.path.join(TMP, f"{n}.png"), t, n), tint=fc.rgbhex(t))
         for n, t in zip(["ONE", "TWO", "THREE"], TINTS)]
BRAND = dict(title="SAMPLE", tagline="A RANGE OF THREE", sign="signature")


def film(**o):
    o.setdefault("aspect", "216x270")
    return fc.Film(dict(items=ITEMS, brand=BRAND, options=o), base=TMP)


def test_timing_per_style():
    assert film(style="cinematic").total == 3 * 36 + 66 + 12 + 40
    assert film(style="snap").total == 3 * 14 + 3 * 10 + 44 + 12 + 40
    assert film(style="cinematic", loop=True).total == 3 * 36 + 12 + 40 + 12
    assert film(style="snap", loop=True, endcard=False).total == 3 * 14 + 3 * 10 + 1
    assert film(style="cinematic", fps=24).total == round(36 * 0.8) * 3 + (round(36 * 0.8) + 24) + round(12 * 0.8) + 32


def test_never_more_than_three_cuts_a_second():
    for bpm in (60, 128, 174, 240):
        f = film(style="snap", bpm=bpm)
        assert min(f.lens) >= 10, (bpm, f.lens)


def test_beat_sync_on_the_beat():
    f = film(style="cinematic", bpm=100)
    per = 30 * 60 / 100
    for s in f.starts[1:len(f.seq)]:
        assert abs(s / per - round(s / per)) * per <= 0.5 + 1e-6


def test_sizes():
    assert fc.parse_size("4:5") == (1080, 1350) and fc.parse_size("9:16") == (1080, 1920)
    assert fc.parse_size("16:9") == (1920, 1080) and fc.parse_size("1:1") == (1080, 1080)
    assert fc.parse_size("999x555") == (998, 554)
    assert film(aspect="16:9").frame(3).size == (1920, 1080)
    p = fc.Film(dict(items=ITEMS, brand=BRAND, options=dict(platform="instagram-reels")), base=TMP)
    assert (p.W, p.H) == (1080, 1920) and p.safe[1] >= int(0.14 * 1920) and p.safe[3] <= int(0.65 * 1920)


def test_platform_fps_cap():
    p = fc.Film(dict(items=ITEMS, brand=BRAND, options=dict(platform="linkedin", fps=60)), base=TMP)
    assert p.fps == 30 and any("fps" in w for w in p.warnings)


def test_wipe_is_crisp():
    f = film()
    a, b = f.shot(0, 0.9, 30), f.shot(1, 0.1, 30)
    fa, fb = np.asarray(a, np.float32), np.asarray(b, np.float32)
    differ = np.abs(fa - fb).max(-1) > 24
    for t in (0.3, 0.5, 0.7):
        mid = np.asarray(f.wipe(a, b, t, glow=0), np.float32)
        neither = (np.abs(mid - fa).max(-1) > 8) & (np.abs(mid - fb).max(-1) > 8) & differ
        assert neither.sum() / differ.sum() < 0.02, t
    assert f.wipe(a, b, 1.0).tobytes() == b.tobytes()


def test_contact_shadow():
    f = film(aspect="432x540")
    info = {}
    shot = np.asarray(f.shot(0, 0.5, 4, info=info), np.float32).mean(-1)
    bare = np.asarray(f.shot(0, 0.5, 4, pack=False), np.float32).mean(-1)
    px, py, pw, ph = info["box"]
    rows = np.where(info["alpha"][:, pw // 3: 2 * pw // 3].max(1) > 0.5)[0]
    yb = py + int(rows.max())
    xs = slice(px + pw * 2 // 5, px + pw * 3 // 5)
    assert shot[yb + 1:yb + 4, xs].mean() < 0.85 * bare[yb + 1:yb + 4, xs].mean()


def test_end_card_and_loop():
    f = film()
    last = np.asarray(f.frame(f.total - 1), np.int16)
    assert (np.abs(last - np.array(fc.hexrgb("#F4F1EA"))).max(-1) < 10).mean() > 0.6
    lp = film(loop=True)
    assert np.array_equal(np.asarray(lp.frame(0)), np.asarray(lp.frame(lp.total - 1)))
    ls = film(style="snap", loop=True)
    assert np.array_equal(np.asarray(ls.frame(0)), np.asarray(ls.frame(ls.total - 1)))


def test_auto_tint():
    t = fc.hexrgb(fc.auto_tint(Image.open(ITEMS[2]["pack"])))
    assert sum(abs(a - b) for a, b in zip(t, TINTS[2])) < 60, t


def test_flash_meter():
    m = fc.FlashMeter(30)
    for i in range(40):
        m.add(Image.new("RGB", (64, 64), (255, 255, 255) if i % 2 else (0, 0, 0)))
    assert not m.report()["ok"]
    r = fc.FlashMeter(30)
    for i in range(40):
        r.add(Image.new("RGB", (64, 64), (255, 0, 0) if i % 2 else (0, 0, 0)))
    assert r.report()["max_red_flashes_per_s"] > 3
    calm = fc.FlashMeter(30)
    for i in range(60):
        calm.add(Image.new("RGB", (64, 64), (100 + i, 100, 100)))
    assert calm.report()["ok"]


def test_render_outputs_and_flash():
    out = os.path.join(TMP, "render")
    for style in ("cinematic", "snap"):
        res = film(style=style, loop=True).render(out, name="t_" + style, quiet=True)
        assert res["flash"]["ok"], res["flash"]
        assert all(os.path.getsize(res[k]) > 500 for k in ("mp4", "gif", "strip"))
    import imageio_ffmpeg
    n, _ = imageio_ffmpeg.count_frames_and_secs(os.path.join(out, "t_cinematic.mp4"))
    assert n == film(style="cinematic", loop=True).total


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    bad = 0
    for t in tests:
        try:
            t(); print("PASS", t.__name__)
        except AssertionError as e:
            bad += 1; print("FAIL", t.__name__, e)
    shutil.rmtree(TMP, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
