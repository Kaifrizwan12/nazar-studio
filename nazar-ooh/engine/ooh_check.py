#!/usr/bin/env python3
"""
nazar-ooh/engine/ooh_check.py: can this copy be read from the road? (stdlib only)

Only numbers with a basis are hard checks; folklore is labelled as such.
  letter height   min_in = distance_ft / LI.  LI = 30 ft per inch (US MUTCD legibility index),
                  or 40 (FHWA/Clearview research, 20/20 drivers). x0.83 for a moderately
                  busy layout, x0.67 for a busy one (USSC, via a secondary summary).
  eye-chart floor a 20/20 letter subtends 5 arcmin: height = 2 d tan(2.5'). That is the
                  threshold, not a design target.
  contrast        WCAG 2 ratio; 4.5:1 is the floor, 7:1 a house rule for far viewing
                  (NOT a cited outdoor standard).
  words           "7 words" is an industry convention with no primary source: warn above 7,
                  fail above 10, and say so.
  read time       ~0.5 s per word (a figure from a sign-research bibliography, secondary)
                  against the time the sign is in view = sight distance / speed. An ESTIMATE.
Viewing distance and speed are INPUTS: no authoritative outdoor figure was found.

    python ooh_check.py "COPY" --distance-ft 300 --speed-mph 45 --cap-height-in 14 [--fg #hex --bg #hex]
"""
import argparse
import json
import math

ARC = math.radians(1 / 60)


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def check(copy, distance_ft, speed_mph, cap_height_in, fg=None, bg=None, li=30, busy="moderate"):
    n = len(copy.split())
    mult = {"clean": 1.0, "moderate": 0.83, "busy": 0.67}[busy]
    need_in = distance_ft / (li * mult)
    floor_in = 2 * distance_ft * 12 * math.tan(2.5 * ARC)
    sight_s = distance_ft / (speed_mph * 5280 / 3600)
    read_s = n * 0.5
    out = {"words": n, "distance_ft": distance_ft, "cap_height_in": cap_height_in,
           "min_cap_in": round(need_in, 1), "eye_chart_floor_in": round(floor_in, 2),
           "in_view_s": round(sight_s, 1), "read_s_est": round(read_s, 1), "checks": []}
    c = out["checks"]
    c.append(("words", "fail" if n > 10 else "warn" if n > 7 else "ok",
              f"{n} words (convention: ≤7; no primary source)"))
    c.append(("letter height", "ok" if cap_height_in >= need_in else "fail",
              f"{cap_height_in:g} in cap height vs {need_in:.1f} in needed at {distance_ft} ft (LI {li}{'' if mult == 1 else f' x{mult}'})"))
    c.append(("read time", "ok" if read_s <= sight_s else "fail",
              f"~{read_s:.1f} s to read vs {sight_s:.1f} s in view at {speed_mph} mph (estimate)"))
    if fg and bg:
        r = contrast(fg, bg)
        c.append(("contrast", "ok" if r >= 7 else "warn" if r >= 4.5 else "fail", f"{r:.1f}:1 (4.5 floor, 7 house rule for far viewing)"))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("copy"); ap.add_argument("--distance-ft", type=float, default=300); ap.add_argument("--speed-mph", type=float, default=45)
    ap.add_argument("--cap-height-in", type=float, required=True); ap.add_argument("--fg"); ap.add_argument("--bg")
    ap.add_argument("--li", type=int, default=30); ap.add_argument("--busy", default="moderate"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = check(a.copy, a.distance_ft, a.speed_mph, a.cap_height_in, a.fg, a.bg, a.li, a.busy)
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        for name, v, msg in r["checks"]:
            print(f"  [{v:4}] {name}: {msg}")
