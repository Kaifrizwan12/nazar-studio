#!/usr/bin/env python3
"""Brand files in profiles: a feed job asks up front for native 4:5 backdrops and a light-on-dark logo, and a profile
says which are missing or would be resampled or boxed.   python nazar-core/engine/test_profile_files.py   (or pytest)"""
import os
import sys
import tempfile

from PIL import Image

HOME = tempfile.mkdtemp()
os.environ["NAZAR_HOME"] = HOME
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tags  # noqa: E402


def test_new_job_asks_for_the_brand_files():
    qs = tags.questions("6 slides for the brand about chai", ["carousel"], [])
    text = " ".join(q for q, _ in qs)
    assert "native 4:5" in text and "light-on-dark logo" in text, text


def test_profile_reports_missing_and_wrong_files():
    d = tempfile.mkdtemp()
    sq = os.path.join(d, "square.png"); Image.new("RGB", (1080, 1080), "white").save(sq)
    ok = os.path.join(d, "dark45.png"); Image.new("RGB", (1080, 1350), "black").save(ok)
    logo = os.path.join(d, "logo.jpg"); Image.new("RGB", (400, 200), "white").save(logo)
    assets = {"backdrop_light": [sq], "backdrop_dark": [ok], "logo": [logo]}
    warn = " ".join(tags.check_files(assets))
    assert "not 4:5" in warn and "square.png" in warn and "dark45.png" not in warn, warn
    assert "no transparency" in warn, warn
    miss = tags.missing_files(assets)
    assert len(miss) == 1 and "light-on-dark" in miss[0], miss
    tags.set_assets("demo", f"backdrop_light={sq}; backdrop_dark={ok}; logo={logo}")
    assert "Brand files still needed" in tags.show("demo")
    qs = tags.questions("6 slides for @demo #carousel", ["carousel"], ["demo"])
    assert any("light-on-dark" in q and "native 4:5" not in q for q, _ in qs), qs   # only what is still missing


def test_complete_profile_asks_nothing_about_files():
    d = tempfile.mkdtemp()
    files = {}
    for role, size, mode in (("backdrop_light", (1080, 1350), "RGB"), ("backdrop_dark", (1080, 1350), "RGB"),
                             ("logo", (400, 200), "RGBA"), ("logo_on_dark", (400, 200), "RGBA")):
        p = os.path.join(d, role + ".png"); Image.new(mode, size).save(p); files[role] = p
    tags.set_assets("full", "; ".join(f"{k}={v}" for k, v in files.items()))
    assert tags.missing_files(tags.load("full")["assets"]) == []
    assert not tags.check_files(tags.load("full")["assets"])
    qs = tags.questions("6 slides for @full #carousel", ["carousel"], ["full"])
    assert not any("brand files" in q for q, _ in qs), qs


if __name__ == "__main__":
    test_new_job_asks_for_the_brand_files(); test_profile_reports_missing_and_wrong_files(); test_complete_profile_asks_nothing_about_files()
    print("profile brand files: all tests pass")
