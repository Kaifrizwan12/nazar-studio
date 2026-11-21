"""Self-check for review_wall.py (no network, temp folder only): python test_review_wall.py
Covers the first build (unchanged behaviour), resolve / unresolve / new round, before/after on a changed sheet,
reopen on change, renumbering and the publish.json files map."""
import json, os, re, shutil, subprocess, sys, tempfile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import review_wall as rw  # noqa: E402


def img(path, colour):
    Image.new("RGB", (320, 180), colour).save(path)


def pages_of(out):
    s = open(os.path.join(out, "review.html"), encoding="utf-8").read()
    return json.loads(re.search(r"const PAGES = (.*?);\n", s).group(1).replace("<\\/", "</")), s


def main():
    tmp = tempfile.mkdtemp(prefix="wall_"); src = os.path.join(tmp, "src"); out = os.path.join(tmp, "out"); os.makedirs(src)
    try:
        img(os.path.join(src, "a_front.png"), "#C0392B"); img(os.path.join(src, "b_back.png"), "#2E86C1"); img(os.path.join(src, "c_box.png"), "#27AE60")

        # 1. first build via the CLI, exactly as before: 3 sheets, no resolved, no before images
        r = subprocess.run([sys.executable, os.path.join(HERE, "review_wall.py"), src, out, "--title", "Test review"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        pages, html = pages_of(out)
        assert [p[0] for p in pages] == ["01.jpg", "02.jpg", "03.jpg"] and [p[1] for p in pages] == ["a front", "b back", "c box"]
        assert not any(p[3] for p in pages) and not any(p[4] for p in pages)
        pub = json.load(open(os.path.join(out, "publish.json"), encoding="utf-8"))
        assert set(pub["files"]) == {"img/01.jpg", "img/02.jpg", "img/03.jpg"} and pub["capabilities"] == {"comments": {"composer_only": True}}
        assert "data-comment-target" in html and "Round 1" in html and 'data-f="res"' in html
        st = json.load(open(os.path.join(out, "wall.json"), encoding="utf-8")); assert st["round"] == 1 and len(st["sheets"]) == 3

        # 2. resolve by number and by file name; unresolve
        _, pages, _ = rw.build(src, out, resolve="1,b_back.png", quiet=True)
        assert [p[3] for p in pages] == [True, True, False]
        _, pages, _ = rw.build(src, out, unresolve="02", quiet=True)
        assert [p[3] for p in pages] == [True, False, False]
        # rebuild with no flags keeps state
        _, pages, _ = rw.build(src, out, quiet=True); assert [p[3] for p in pages] == [True, False, False]

        # 3. change sheet 01: before/after appears, the old image is kept byte for byte, resolved goes back to open
        old01 = open(os.path.join(out, "img", "01.jpg"), "rb").read()
        img(os.path.join(src, "a_front.png"), "#F1C40F")
        _, pages, pub = rw.build(src, out, quiet=True)
        assert pages[0][4] == "prev/01.jpg" and pages[0][5] == 1 and pages[1][4] is None
        assert open(os.path.join(out, "img", "prev", "01.jpg"), "rb").read() == old01
        assert open(os.path.join(out, "img", "01.jpg"), "rb").read() != old01
        assert pages[0][3] is False, "a changed sheet must reopen"
        assert "img/prev/01.jpg" in pub["files"]
        # resolve in the same build as a change sticks
        img(os.path.join(src, "a_front.png"), "#8E44AD")
        _, pages, _ = rw.build(src, out, resolve="1", quiet=True); assert pages[0][3] is True and pages[0][4] == "prev/01.jpg"

        # 4. new round clears resolved, bumps the round, keeps before images
        st, pages, _ = rw.build(src, out, new_round=True, quiet=True)
        assert st["round"] == 2 and not any(p[3] for p in pages) and pages[0][4] == "prev/01.jpg"
        assert "Round 2" in pages_of(out)[1]

        # 5. renumber: insert a sheet first; a_front moves to 02 and carries its before image
        prev_a = open(os.path.join(out, "img", "prev", "01.jpg"), "rb").read()
        img(os.path.join(src, "0_cover.png"), "#34495E")
        _, pages, pub = rw.build(src, out, quiet=True)
        assert [p[1] for p in pages] == ["0 cover", "a front", "b back", "c box"]
        assert pages[0][4] is None and pages[1][4] == "prev/02.jpg"
        assert open(os.path.join(out, "img", "prev", "02.jpg"), "rb").read() == prev_a
        assert not os.path.exists(os.path.join(out, "img", "prev", "01.jpg"))
        assert "img/prev/02.jpg" in pub["files"] and "img/prev/01.jpg" not in pub["files"]
        for k in pub["files"]: assert os.path.exists(os.path.join(out, k)), k

        # 6. bad sheet id fails loudly
        try:
            rw.build(src, out, resolve="9", quiet=True); raise AssertionError("expected exit")
        except SystemExit:
            pass
        print("review_wall self-check: OK (6 groups)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
