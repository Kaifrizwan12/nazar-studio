#!/usr/bin/env python3
"""
nazar-voiceprint/engine/exif_habits.py: a photographer's camera habits from
EXIF, across a body of work (Pillow only).

Focal length (35mm-equivalent where the camera records it), aperture,
shutter, ISO, flash, orientation, camera and lens bodies. Distributions, not
averages: a person who shoots 35mm at f/1.8 70% of the time has a habit; a mean
of "52mm at f/4.6" describes nobody.

Baseline for comparison: a large-scale study of millions of photos found about
half of shots fall at normal to slightly wide focal lengths (Image Engineering,
"statistic analysis of millions of photos"). UCSB work (Hingorani) mapped EXIF
tags to individual photographers' preferences. See
../references/creative_disciplines.md.

Missing EXIF is common (exports, screenshots, social re-saves). Those files
are counted and left out, never guessed.

    python exif_habits.py folder [--json]
"""
import json
import os
from collections import Counter

from PIL import Image, ExifTags

EXTS = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".webp", ".heic"}
TAGS = {v: k for k, v in ExifTags.TAGS.items()}


def _num(v):
    try:
        if isinstance(v, tuple) and len(v) == 2:          # some writers store rationals as (num, den)
            return float(v[0]) / float(v[1])
        return float(v.numerator) / float(v.denominator) if hasattr(v, "numerator") else float(v)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def read(path):
    try:
        im = Image.open(path)
        ex = im.getexif()
        sub = ex.get_ifd(0x8769) if ex else {}
    except Exception:
        return None
    if not ex and not sub:
        return None
    g = lambda name: sub.get(TAGS[name], ex.get(TAGS[name]))
    f35 = _num(g("FocalLengthIn35mmFilm")) or None
    f = _num(g("FocalLength"))
    w, h = im.size
    return {
        "focal_35mm": f35, "focal_mm": f,
        "aperture": _num(g("FNumber")),
        "shutter_s": _num(g("ExposureTime")),
        "iso": _num(g("ISOSpeedRatings") if TAGS.get("ISOSpeedRatings") else g("PhotographicSensitivity")),
        "flash_fired": (int(g("Flash")) & 1 == 1) if g("Flash") is not None else None,
        "camera": " ".join(str(x).strip() for x in (ex.get(TAGS["Make"]), ex.get(TAGS["Model"])) if x),
        "lens": str(g("LensModel")).strip() if g("LensModel") else None,
        "orientation": "portrait" if h > w else "landscape" if w > h else "square",
    }


def bucket_focal(f):
    if f is None:
        return None
    for limit, name in ((20, "ultra-wide <20"), (30, "wide 20-29"), (45, "normal-wide 30-44"), (60, "normal 45-59"),
                        (100, "short tele 60-99"), (200, "tele 100-199")):
        if f < limit:
            return name
    return "long tele 200+"


def bucket_ap(a):
    if a is None:
        return None
    return "wide open ≤f/2" if a <= 2 else "f/2.1-4" if a <= 4 else "f/4.1-8" if a <= 8 else "stopped down >f/8"


def bucket_sh(s):
    if s is None:
        return None
    return "slow ≥1/30" if s >= 1 / 30 else "1/31-1/250" if s >= 1 / 250 else "fast <1/250"


def habits(folder):
    files = sorted(os.path.join(folder, f) for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in EXTS)
    rows, missing = [], 0
    for p in files:
        r = read(p)
        if r is None or all(r[k] is None for k in ("focal_mm", "aperture", "shutter_s", "iso")):
            missing += 1
            continue
        rows.append(r)
    n = len(rows)
    if n == 0:
        return {"n_with_exif": 0, "n_without_exif": missing}

    def dist(key, fn):
        c = Counter(fn(r[key]) for r in rows if fn(r[key]) is not None)
        tot = sum(c.values())
        return {k: round(v / tot, 2) for k, v in c.most_common()} if tot else {}

    focal = [r["focal_35mm"] or r["focal_mm"] for r in rows]
    out = {
        "n_with_exif": n, "n_without_exif": missing,
        "focal": dist("focal_35mm", bucket_focal) if any(r["focal_35mm"] for r in rows) else
                 {k: v for k, v in Counter(bucket_focal(f) for f in focal if f).items()},
        "focal_is_35mm_equivalent": any(r["focal_35mm"] for r in rows),
        "aperture": dist("aperture", bucket_ap),
        "shutter": dist("shutter_s", bucket_sh),
        "flash_share": round(sum(1 for r in rows if r["flash_fired"]) / n, 2),
        "orientation": dict(Counter(r["orientation"] for r in rows)),
        "cameras": dict(Counter(r["camera"] for r in rows if r["camera"]).most_common(3)),
        "lenses": dict(Counter(r["lens"] for r in rows if r["lens"]).most_common(3)),
    }
    if not out["focal_is_35mm_equivalent"]:
        tot = sum(out["focal"].values()) or 1
        out["focal"] = {k: round(v / tot, 2) for k, v in out["focal"].items()}
        out["note"] = "focal lengths are actual mm, not 35mm-equivalent; buckets assume full frame"
    return out


def reading(h):
    if not h.get("n_with_exif"):
        return ["no EXIF found (exports and social re-saves strip it); ask the person about their kit instead"]
    out = []
    top = lambda d: max(d.items(), key=lambda kv: kv[1]) if d else (None, 0)
    f, fs = top(h["focal"])
    if fs >= 0.5:
        out.append(f"lens habit: {fs:.0%} of shots at {f}")
    a, as_ = top(h["aperture"])
    if as_ >= 0.5:
        out.append(f"aperture habit: {as_:.0%} {a}")
    if h["flash_share"] >= 0.3:
        out.append(f"flash in {h['flash_share']:.0%} of shots: a direct-flash habit")
    if h["orientation"].get("portrait", 0) > h["orientation"].get("landscape", 0):
        out.append("shoots vertical more than horizontal")
    return out or ["no single dominant camera habit; settings follow the subject"]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    h = habits(a.folder)
    if a.json:
        print(json.dumps({"habits": h, "reading": reading(h)}, indent=2))
    else:
        print(json.dumps(h, indent=2))
        for line in reading(h):
            print("  -", line)
