#!/usr/bin/env python3
"""Known-answer test: a project uses its own brand.json through NAZAR_BRAND, without copying the engine.

Real case: a project had to copy the whole engine folder to change brand.json; the copy then broke qa_views.py (it imports a
sibling kit) and would never receive engine fixes. Here a temp project holds only brand.json + one page module, builds a page,
and nothing is written into the skills folder.  Run: python test_brand_env.py
"""
import json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def run():
    proj = tempfile.mkdtemp(prefix="nazar_brand_env_")
    b = json.load(open(os.path.join(HERE, "brand.json"), encoding="utf-8"))
    b.update(name="Envco", fonts_dir=os.path.join(HERE, "fonts"), logos={}, page_modules=["pages_env"], reveal_pid=None, exports="exports")
    json.dump(b, open(os.path.join(proj, "brand.json"), "w"), indent=1)
    open(os.path.join(proj, "pages_env.py"), "w").write(
        "from lib import *\n"
        "def one():\n"
        "    p = Page('01.1', 'One', '01 · TEST', LIGHT)\n"
        "    p.add(text(BRAND['name'], M, 400, 60, 'display', BASE))\n"
        "    return p\n"
        "PAGES = [one]\n")
    before = set(os.listdir(HERE))
    out_before = set(os.listdir(os.path.join(HERE, "out"))) if os.path.isdir(os.path.join(HERE, "out")) else None
    env = dict(os.environ, NAZAR_BRAND=os.path.join(proj, "brand.json"))
    chk = subprocess.run([sys.executable, "-c", "import lib; print(lib.BRAND['name']); print(lib._path('exports'))"],
                         cwd=HERE, env=env, capture_output=True, text=True)
    assert chk.returncode == 0, chk.stderr
    name, exp = chk.stdout.split()
    assert name == "Envco" and exp == os.path.join(proj, "exports"), chk.stdout
    r = subprocess.run([sys.executable, os.path.join(HERE, "build.py")], cwd=proj, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-800:]
    assert os.path.exists(os.path.join(proj, "exports", "pages", "01_01.1.png")) or any(
        f.endswith(".png") for f in os.listdir(os.path.join(proj, "exports", "pages"))), os.listdir(os.path.join(proj, "exports"))
    assert os.path.isdir(os.path.join(proj, "out")), "svg/out should live beside the project's brand.json"
    assert set(os.listdir(HERE)) - before <= {"__pycache__"}, set(os.listdir(HERE)) - before
    now_out = set(os.listdir(os.path.join(HERE, "out"))) if os.path.isdir(os.path.join(HERE, "out")) else None
    assert now_out == out_before, "the engine's own out/ was written to"
    # default behaviour unchanged: without NAZAR_BRAND the engine's own brand.json is used
    env.pop("NAZAR_BRAND")
    d = subprocess.run([sys.executable, "-c", "import lib; print(lib.BRAND['name'])"], cwd=HERE, env=env, capture_output=True, text=True)
    assert d.stdout.strip() == json.load(open(os.path.join(HERE, "brand.json")))["name"], d.stdout
    shutil.rmtree(proj)
    print("PASS test_brand_env")


if __name__ == "__main__":
    run()
