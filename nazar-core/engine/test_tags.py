#!/usr/bin/env python3
"""Known-answer tests for the brief step (tags.py, studio.py brief). Run: python test_tags.py

Cases come from real runs where the brief step under-read a long, multi-job brief:
- the prompt was cut at 300 characters with no marker, so the reader could not tell it was cut;
- auto-tagging kept only the first two jobs, so a full identity brief lost packaging, campaign, web and motion;
- there was no campaign tag, so posters and campaign work fell through.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("NAZAR_HOME", os.path.join(os.path.dirname(os.path.abspath(__file__)), "_test_home_does_not_exist"))
import tags, studio

FULL = ("Full studio job for a new spice brand: design a new logo and a brand book, packaging for five jars with dielines, "
        "a launch campaign with three posters, social posts for Instagram, a landing page website, an animated logo sting, "
        "a product shoot and a Behance case study.")


def test_prompt_shown_whole_or_visibly_cut():
    assert tags.prompt_line("short prompt") == "Prompt: short prompt"
    long = "word " * 200                                             # 1000 characters
    line = tags.prompt_line(long)
    assert "characters not shown; the whole prompt was read" in line, line[-120:]
    assert len(line) < 720


def test_full_brief_keeps_every_job():
    tg, _, _ = tags.auto_tags(FULL)
    for need in ("logo", "packaging", "campaign", "post", "web", "motion", "shoot", "casestudy"):
        assert need in tg, (need, tg)


def test_specific_format_still_wins_over_post():
    tg, _, _ = tags.auto_tags("6 slides for a carousel about our new menu")
    assert "carousel" in tg and "post" not in tg, tg


def test_campaign_tag_resolves():
    out = tags.expand("three posters and a key visual #campaign")
    assert "Job: a campaign" in out and "nazar-ooh" in out, out[:400]


def test_studio_brief_uses_full_prompt():
    out = studio.brief(FULL)
    assert "Job: a campaign" in out and "Job: packaging" in out and "Job: a website" in out, out[:600]


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print("ok", name)
    print(f"PASS {n} tests")
