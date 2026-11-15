#!/usr/bin/env python3
"""
nazar-voiceprint/engine/video.py: an editor's or director's cutting habits.

  cuts           frame-to-frame colour-histogram change with an adaptive
                 threshold (the content-detector idea in PySceneDetect); or pass
                 --cuts a text/CSV file of cut times in seconds (from an EDL or
                 an NLE export) and skip decoding entirely
  shot length    MEDIAN and distribution, not just the mean: Salt (1974) and
                 Tsivian's Cinemetrics report average shot length (ASL), and
                 Redfern shows ASL alone is statistically weak on skewed data
  rhythm         does the cutting speed up or slow down over the piece; and the
                 log-log slope of the shot-length power spectrum: Cutting,
                 DeLong & Nothelfer (Psych Science, 2010) found later films'
                 shot sequences approach 1/f (slope near -1), independent of ASL
  grade          grade.py on the middle frame of each shot: is the look one
                 consistent habit, or does it change shot to shot

Decoding uses the ffmpeg bundled with `pip install imageio-ffmpeg`.

    python video.py clip.mp4 [--json]
    python video.py --cuts cuts.txt --duration 312.5 [--json]
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def frames(path, width=160):
    import imageio_ffmpeg as iio
    gen = iio.read_frames(path, output_params=["-vf", f"scale={width}:-2"])
    meta = next(gen)
    w, h = meta["size"]
    fps = float(meta.get("fps") or 25)
    for raw in gen:
        yield fps, np.frombuffer(raw, np.uint8).reshape(h, w, 3)


def hist(fr, bins=16):
    q = (fr // (256 // bins)).reshape(-1, 3).astype(np.int32)
    idx = q[:, 0] * bins * bins + q[:, 1] * bins + q[:, 2]
    hh = np.bincount(idx, minlength=bins ** 3).astype(np.float32)
    return hh / hh.sum()


def detect(path, min_shot_s=0.3):
    prev, diffs, mids, fps, kept = None, [], [], 25.0, []
    for i, (fps, fr) in enumerate(frames(path)):
        hcur = hist(fr)
        diffs.append(0.0 if prev is None else float(np.abs(hcur - prev).sum() / 2))
        prev = hcur
        kept.append(fr)
    d = np.array(diffs)
    n = len(d)
    cuts = []
    min_gap = max(1, int(min_shot_s * fps))
    for i in range(1, n):
        lo, hi = max(1, i - 12), min(n, i + 12)
        local = np.median(d[lo:hi])
        if d[i] > max(0.35, 4 * local) and (not cuts or i - cuts[-1] >= min_gap):
            cuts.append(i)
    bounds = [0] + cuts + [n]
    shots = [(bounds[k], bounds[k + 1]) for k in range(len(bounds) - 1)]
    mid_frames = [kept[(a + b) // 2] for a, b in shots]
    return fps, n, [(b - a) / fps for a, b in shots], mid_frames


def rhythm(lengths):
    L = np.array(lengths, float)
    out = {
        "shots": len(L),
        "median_s": round(float(np.median(L)), 2),
        "mean_ASL_s": round(float(L.mean()), 2),
        "quartiles_s": [round(float(q), 2) for q in np.percentile(L, [25, 75])],
        "share_under_2s": round(float((L < 2).mean()), 2),
        "share_over_10s": round(float((L > 10).mean()), 2),
        "skew_mean_over_median": round(float(L.mean() / max(np.median(L), 1e-6)), 2),
    }
    if len(L) >= 4:
        x = np.arange(len(L))
        slope = np.polyfit(x, np.log(L), 1)[0]
        out["pace_trend"] = "accelerating (shots get shorter)" if slope < -0.03 else \
                            "decelerating (shots get longer)" if slope > 0.03 else "steady"
    if len(L) >= 32:
        z = L - L.mean()
        p = np.abs(np.fft.rfft(z)) ** 2
        f = np.fft.rfftfreq(len(z))
        keep = f > 0
        out["spectrum_slope"] = round(float(np.polyfit(np.log(f[keep]), np.log(p[keep] + 1e-12), 1)[0]), 2)
        out["spectrum_note"] = "near -1 = 1/f rhythm (Cutting 2010); near 0 = shot lengths independent of each other"
    else:
        out["spectrum_slope"] = None
        out["spectrum_note"] = "needs 32+ shots"
    return out


def reading(r, grade_summary=None):
    out = []
    m = r["median_s"]
    out.append("fast cutter: median shot under 2.5 s" if m < 2.5 else
               "long-take habit: median shot over 8 s" if m > 8 else f"measured cutting: median shot {m} s")
    if r["skew_mean_over_median"] > 1.5:
        out.append("a few long holds among quick cuts (mean well above median)")
    if r.get("pace_trend") and r["pace_trend"] != "steady":
        out.append(f"pace {r['pace_trend']}")
    if grade_summary:
        out.append(grade_summary)
    return out


def grade_across(mid_frames):
    import grade
    looks = [set(grade.analyse(Image.fromarray(f))["looks"]) for f in mid_frames]
    if not looks:
        return None
    counts = {}
    for s in looks:
        for l in s:
            counts[l] = counts.get(l, 0) + 1
    steady = [l for l, c in counts.items() if c / len(looks) >= 0.7]
    return ("consistent grade across shots: " + "; ".join(steady)) if steady else "grade changes shot to shot (no single look)"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?")
    ap.add_argument("--cuts", help="text/CSV of cut times in seconds")
    ap.add_argument("--duration", type=float, help="total length in seconds (with --cuts)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    gsum = None
    if a.cuts:
        import re
        times = sorted(float(x) for x in re.findall(r"\d+(?:\.\d+)?", open(a.cuts).read()))
        end = a.duration or (times[-1] if times else 0)
        bounds = [0.0] + [t for t in times if 0 < t < end] + [end]
        lengths = [b - a_ for a_, b in zip(bounds, bounds[1:]) if b > a_]
        info = {"source": "cut list"}
    else:
        fps, n, lengths, mids = detect(a.video)
        info = {"source": "detected", "fps": fps, "frames": n}
        gsum = grade_across(mids)
    r = rhythm(lengths)
    res = {**info, "rhythm": r, "shot_lengths_s": [round(x, 2) for x in lengths], "reading": reading(r, gsum)}
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(json.dumps({k: v for k, v in res.items() if k != "reading"}, indent=1))
        for line in res["reading"]:
            print("  -", line)
