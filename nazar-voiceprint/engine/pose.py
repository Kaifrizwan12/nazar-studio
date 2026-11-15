#!/usr/bin/env python3
"""
nazar-voiceprint/engine/pose.py: how a photographer, director or illustrator
poses and frames people, from 2D body keypoints (COCO-17 order).

Precedent: Impett & Moretti, "Totentanz: Operationalizing Aby Warburg's
Pathosformeln" (Stanford Literary Lab Pamphlet 16; NLR II/107, 2017) turned
recurring expressive poses in art into quantitative operations. No study yet
classifies a photographer's pose habits, so these are standard geometric
measures, documented in ../references/creative_disciplines.md:

  torso turn      shoulder width / torso length (frontal vs 3/4 vs profile)
  tilts           shoulder line, eye line (head tilt)
  contrapposto    shoulder angle minus hip angle (weight shift)
  openness        convex hull of keypoints / torso length^2; arm extension
  symmetry        left vs mirrored right keypoints about the body midline
  hand placement  wrists raised / at chest / at hip / down
  gaze proxy      nose offset from the eye midpoint
  framing         crop point (which joints leave the frame), headroom, shot
                  scale (body height / frame), camera-height proxy

Keypoints come from any pose model. Built-in detection uses rtmlib (RTMPose
via ONNX, CPU-only), which installs on Intel Macs where MediaPipe and current
torch don't:  pip install "onnxruntime==1.23.2" rtmlib
Without it, pass a JSON of keypoints (--keypoints) exported from any tool.

    python pose.py photos/            (needs rtmlib)
    python pose.py --keypoints kp.json --size 1080x1350
"""
import json
import math
import os
import sys

import numpy as np

NOSE, LEYE, REYE, LEAR, REAR, LSH, RSH, LEL, REL, LWR, RWR, LHIP, RHIP, LKN, RKN, LAN, RAN = range(17)
MIRROR = [(LEYE, REYE), (LEAR, REAR), (LSH, RSH), (LEL, REL), (LWR, RWR), (LHIP, RHIP), (LKN, RKN), (LAN, RAN)]


def _ok(kp, i, conf=0.3):
    return kp[i, 2] >= conf


def _mid(kp, a, b):
    return (kp[a, :2] + kp[b, :2]) / 2


def _ang(kp, a, b):
    d = kp[b, :2] - kp[a, :2]
    return math.degrees(math.atan2(d[1], d[0]))


def _hull_area(pts):
    pts = sorted(map(tuple, pts))
    if len(pts) < 3:
        return 0.0
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    return 0.5 * abs(sum(hull[i][0] * hull[i - 1][1] - hull[i - 1][0] * hull[i][1] for i in range(len(hull))))


def person(kp, size):
    """kp: (17, 3) x, y, confidence in pixels. size: (width, height) of the frame."""
    kp = np.asarray(kp, float)
    W, H = size
    if not (_ok(kp, LSH) and _ok(kp, RSH)):
        return None
    sh_mid = _mid(kp, LSH, RSH)
    hips = _ok(kp, LHIP) and _ok(kp, RHIP)
    hip_mid = _mid(kp, LHIP, RHIP) if hips else None
    torso = float(np.linalg.norm(hip_mid - sh_mid)) if hips else float(np.linalg.norm(kp[LSH, :2] - kp[RSH, :2])) * 1.5
    torso = max(torso, 1e-6)
    turn = abs(kp[LSH, 0] - kp[RSH, 0]) / torso
    out = {"torso_turn": round(turn, 2),
           # adults run ~0.7 face-on; ~0.45 at a 50-degree turn; ~0 in profile
           "facing": "frontal" if turn > 0.45 else "three-quarter" if turn > 0.18 else "profile"}
    sh_ang = _ang(kp, RSH, LSH) if kp[LSH, 0] >= kp[RSH, 0] else _ang(kp, LSH, RSH)
    out["shoulder_tilt_deg"] = round(sh_ang, 1)
    if _ok(kp, LEYE) and _ok(kp, REYE):
        e = _ang(kp, REYE, LEYE) if kp[LEYE, 0] >= kp[REYE, 0] else _ang(kp, LEYE, REYE)
        out["head_tilt_deg"] = round(e, 1)
        inter = max(float(np.linalg.norm(kp[LEYE, :2] - kp[REYE, :2])), 1e-6)
        if _ok(kp, NOSE):
            g = (kp[NOSE, 0] - _mid(kp, LEYE, REYE)[0]) / inter
            out["gaze"] = "frame-left" if g < -0.25 else "frame-right" if g > 0.25 else "to camera"
    if hips:
        hip_ang = _ang(kp, RHIP, LHIP) if kp[LHIP, 0] >= kp[RHIP, 0] else _ang(kp, LHIP, RHIP)
        cp = sh_ang - hip_ang
        out["contrapposto_deg"] = round(cp, 1)
        out["weight_shift"] = abs(cp) > 6 and sh_ang * hip_ang < 0
    vis = [i for i in range(17) if _ok(kp, i)]
    out["openness"] = round(_hull_area(kp[vis, :2]) / torso ** 2, 2)
    ext = []
    for s_, e_, w_ in ((LSH, LEL, LWR), (RSH, REL, RWR)):
        if _ok(kp, s_) and _ok(kp, e_) and _ok(kp, w_):
            reach = np.linalg.norm(kp[w_, :2] - kp[s_, :2])
            length = np.linalg.norm(kp[e_, :2] - kp[s_, :2]) + np.linalg.norm(kp[w_, :2] - kp[e_, :2])
            ext.append(reach / max(length, 1e-6))
    if ext:
        out["arm_extension"] = round(float(np.mean(ext)), 2)
    mid_x = (sh_mid[0] + (hip_mid[0] if hips else sh_mid[0])) / 2
    pairs = [(a, b) for a, b in MIRROR if _ok(kp, a) and _ok(kp, b)]
    if pairs:
        d = [abs((kp[a, 0] - mid_x) + (kp[b, 0] - mid_x)) + abs(kp[a, 1] - kp[b, 1]) for a, b in pairs]
        out["asymmetry"] = round(float(np.mean(d)) / torso, 2)
    zones = []
    for s_, e_, w_, h_ in ((LSH, LEL, LWR, LHIP), (RSH, REL, RWR, RHIP)):
        if not _ok(kp, w_):
            continue
        y = kp[w_, 1]
        bent = True
        if _ok(kp, s_) and _ok(kp, e_):
            reach = np.linalg.norm(kp[w_, :2] - kp[s_, :2])
            length = np.linalg.norm(kp[e_, :2] - kp[s_, :2]) + np.linalg.norm(kp[w_, :2] - kp[e_, :2])
            bent = reach / max(length, 1e-6) < 0.85
        near_hip = _ok(kp, h_) and np.linalg.norm(kp[w_, :2] - kp[h_, :2]) < 0.35 * torso
        if y < sh_mid[1]:
            zones.append("raised")
        elif near_hip and bent:
            zones.append("on hip")
        elif not bent and hip_mid is not None and y > (sh_mid[1] + hip_mid[1]) / 2:
            zones.append("at sides")
        else:
            zones.append("chest / gesturing")
    out["hands"] = zones
    # framing
    inframe = lambda i: _ok(kp, i) and 0 <= kp[i, 0] < W and 0 <= kp[i, 1] < H
    if not (inframe(LAN) or inframe(RAN)):
        crop = "above the ankles"
        if not (inframe(LKN) or inframe(RKN)):
            crop = "above the knees"
            if not (inframe(LHIP) or inframe(RHIP)):
                crop = "above the waist (chest/close-up)"
    else:
        crop = "full figure"
    out["crop"] = crop
    if _ok(kp, NOSE) and _ok(kp, LEYE) and _ok(kp, REYE):
        eye_y = _mid(kp, LEYE, REYE)[1]
        top = kp[NOSE, 1] - 3.0 * abs(kp[NOSE, 1] - eye_y)
        out["headroom"] = round(float(top) / H, 3)
    ys = kp[vis, 1]
    out["subject_scale"] = round(float(ys.max() - min(ys.min(), out.get("headroom", 1) * H)) / H, 2)
    if _ok(kp, NOSE):
        head = abs(sh_mid[1] - kp[NOSE, 1])
        r = head / torso
        out["camera_height_proxy"] = "high angle" if r > 0.55 else "low angle" if r < 0.3 else "eye level"
    return out


def summarise(people):
    people = [p for p in people if p]
    if not people:
        return {}
    n = len(people)
    share = lambda key, val: round(sum(1 for p in people if p.get(key) == val) / n, 2)
    s = {"people": n,
         "facing": {v: share("facing", v) for v in ("frontal", "three-quarter", "profile")},
         "crop": {}, "weight_shift_share": round(sum(1 for p in people if p.get("weight_shift")) / n, 2),
         "median_openness": round(float(np.median([p["openness"] for p in people])), 2),
         "camera_height": {}}
    for p in people:
        s["crop"][p["crop"]] = s["crop"].get(p["crop"], 0) + 1 / n
        if "camera_height_proxy" in p:
            s["camera_height"][p["camera_height_proxy"]] = s["camera_height"].get(p["camera_height_proxy"], 0) + 1 / n
    s["crop"] = {k: round(v, 2) for k, v in s["crop"].items()}
    s["camera_height"] = {k: round(v, 2) for k, v in s["camera_height"].items()}
    return s


def reading(s):
    if not s:
        return ["no people found"]
    out = []
    f = max(s["facing"], key=s["facing"].get)
    out.append(f"{s['facing'][f]:.0%} of people posed {f}")
    if s["weight_shift_share"] >= 0.4:
        out.append(f"weight shift (contrapposto) in {s['weight_shift_share']:.0%}: relaxed, classical stance")
    c = max(s["crop"], key=s["crop"].get)
    out.append(f"usually framed {c}")
    out.append("open, expansive poses" if s["median_openness"] > 3.5 else "closed, contained poses" if s["median_openness"] < 2.2 else "neither open nor closed")
    if s["camera_height"]:
        ch = max(s["camera_height"], key=s["camera_height"].get)
        out.append(f"camera mostly at {ch} (approximate)")
    return out


def detect_folder(folder):
    try:
        from rtmlib import Body
        from PIL import Image
    except ImportError:
        sys.exit('pose detection needs: pip install "onnxruntime==1.23.2" rtmlib   (or pass --keypoints)')
    model = Body(mode="lightweight", backend="onnxruntime", device="cpu")
    people = []
    for f in sorted(os.listdir(folder)):
        if os.path.splitext(f)[1].lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        img = np.asarray(Image.open(os.path.join(folder, f)).convert("RGB"))[:, :, ::-1]
        kps, scores = model(img)
        for k, sc in zip(kps, scores):
            people.append(person(np.column_stack([k, sc]), (img.shape[1], img.shape[0])))
    return people


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", nargs="?")
    ap.add_argument("--keypoints", help="JSON: list of people, each a 17x3 list [x, y, conf]")
    ap.add_argument("--size", default="1000x1000", help="frame WxH for --keypoints")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.keypoints:
        W, H = map(int, a.size.lower().split("x"))
        people = [person(k, (W, H)) for k in json.load(open(a.keypoints))]
    else:
        people = detect_folder(a.folder)
    s = summarise(people)
    if a.json:
        print(json.dumps({"people": people, "summary": s, "reading": reading(s)}, indent=2))
    else:
        for p in people:
            print(p)
        print(json.dumps(s, indent=1))
        for line in reading(s):
            print("  -", line)
