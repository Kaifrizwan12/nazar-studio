#!/usr/bin/env python3
"""
nazar-motion/engine/motion_check.py: measure how a clip actually moves (numpy + imageio).

Reads a video (or a list of per-frame values) and reports what the eye feels:
  speed curve   mean absolute change between consecutive frames, per frame
  easing        'slow in and slow out' (Thomas & Johnston, *The Illusion of Life*, 1981, one of
                the 12 principles): the ratio of peak speed to the speed in the first and last
                10% of the move. ~1 = linear (mechanical); well above 1 = eased.
  duration      length of the moving part (frames above 5% of peak speed) in ms
  stillness     time held at the start and end
It measures; it doesn't prescribe durations. No authoritative duration norms were verified, so
judge those against the brief and the medium.

    python motion_check.py clip.mp4 [--json]
"""
import json
import sys

import numpy as np


def frames_speed(path, width=160):
    import imageio_ffmpeg as iio
    gen = iio.read_frames(path, output_params=["-vf", f"scale={width}:-2"])
    meta = next(gen); w, h = meta["size"]; fps = float(meta.get("fps") or 25)
    prev, sp = None, []
    for raw in gen:
        fr = np.frombuffer(raw, np.uint8).reshape(h, w, 3).astype(np.float32)
        if prev is not None:
            sp.append(float(np.abs(fr - prev).mean()))
        prev = fr
    return np.array(sp), fps


def analyse(speed, fps):
    pk = speed.max()
    if pk < 1e-6:
        return {"verdict": "no motion"}
    moving = np.where(speed > 0.05 * pk)[0]
    a, b = moving[0], moving[-1] + 1
    seg = speed[a:b]
    k = max(1, len(seg) // 10)
    ends = (seg[:k].mean() + seg[-k:].mean()) / 2
    ratio = float(seg.max() / max(ends, 1e-6))
    return {"duration_ms": round(len(seg) / fps * 1000), "hold_start_ms": round(a / fps * 1000),
            "hold_end_ms": round((len(speed) - b) / fps * 1000), "peak_to_end_speed": round(ratio, 1),
            "speed_cv": round(float(seg.std() / seg.mean()), 2),
            "verdict": "linear, mechanical" if ratio < 1.8 else "eased: slow in and slow out" if ratio < 8 else "strongly eased"}


if __name__ == "__main__":
    sp, fps = frames_speed(sys.argv[1])
    r = analyse(sp, fps)
    print(json.dumps(r, indent=1) if "--json" in sys.argv else r)
