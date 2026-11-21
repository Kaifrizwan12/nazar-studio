#!/usr/bin/env python3
"""Tests for social_lint.py with Roman Urdu.   python nazar-social/engine/test_social_lint.py   (or pytest)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from social_lint import lint  # noqa: E402


def kinds(text):
    return [k for k, _ in lint(text)["hits"]]


def test_mixed_english_roman_urdu_is_clean():
    for t in ["Verify karo, phir share karo.", "Pehle aap, phir baaki sab.", "Chai thandi ho gayi? Koi baat nahi, dobara banao.",
              "Bilkul fresh, bohat mazay ka. Order karo abhi."]:
        r = lint(t)
        assert r["hits"] == [], (t, r["hits"])
        assert r["roman_urdu_share"] > 0.3, (t, r["roman_urdu_share"])


def test_inconsistent_spelling_flagged():
    r = lint("Nahi yaar, aaj nahin. Kal bhi nai.")
    sp = [m for k, m in r["hits"] if k == "spelling"]
    assert len(sp) == 1 and "nahi" in sp[0] and "nahin" in sp[0] and "nai" in sp[0], r["hits"]
    assert "spelling" in kinds("Bohat acha, bahut acha")


def test_consistent_spelling_and_meaning_pairs_not_flagged():
    assert "spelling" not in kinds("Nahi yaar, aaj nahi.")
    assert "spelling" not in kinds("Yeh kya hai? Sab theek hain.")          # hai "is" and hain "are" are two words
    assert "spelling" not in kinds("Go to the shop and buy chai.")           # English "to" alone is not Roman Urdu


def test_generic_copy_still_flagged():
    k = kinds("Elevate your journey. Unlock a seamless experience!!")
    assert k.count("phrase") >= 3 and "tone" in k
    assert "structure" in kinds("Yeh not just chai, but a ritual hai.")


def test_typo_only_against_the_piece_itself():
    assert "typo" in kinds("Verify karo. Phir verfy karo.")
    assert "typo" not in kinds("Share karo, shake karo.")                  # a substitution between two real words is left alone
    assert "typo" not in kinds("Waala aur waali dono.")                     # Roman Urdu forms are never typos


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("social_lint: all tests pass")
