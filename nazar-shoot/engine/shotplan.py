#!/usr/bin/env python3
"""shotplan.py - plan the shot before any prompt (numpy + Pillow only).

A photographer decides camera, lens, lights and reflections on paper before the first frame. This engine does the same
from a small JSON spec and returns numbers, a lighting diagram, a plate prompt and the composite.py arguments, so the
plate is briefed with physics instead of mood words.

What it computes (each is plain geometry or optics; sources in ../references/research_realism.md):
- Framing: field of view from sensor + focal length, how much of the frame the product fills, camera tilt.
- Perspective: how much the product's verticals converge (feeds composite.py --persp).
- Depth of field: hyperfocal, near and far limits; warns when the product is deeper than the zone of focus.
- Each light: angular size -> hard / medium / soft; shadow length and direction on the ground; penumbra width at the
  shadow tip; falloff across the product (inverse square); key-to-fill ratio in stops; colour-temperature clash in mired.
- Reflections ("family of angles", Hunter, Biver & Fuqua, Light - Science & Magic): for a glossy, satin, foil or
  frosted face it samples the face and finds where each light is mirrored straight into the lens (glare that eats
  print). If the key glares, it searches for the nearest light position that does not.
- Glossy floors: Fresnel (Schlick) reflectance at the camera's grazing angle -> how strong the product's mirror image is.
- Output: plan.json, plan.md, plan_diagram.png (top and side view), a plate prompt (no product in it) and
  composite.py arguments (--light dx,dy --persp).

What it cannot do: it does not see the plate. A generated plate may ignore the brief; read the plate's real shadows
afterwards (nazar-study/engine/look.py) and pass what you measured. Pouch curvature is modelled as a simple bend.

CLI:
  python shotplan.py plan spec.json [-o outdir]
  python shotplan.py example > spec.json          # a commented starting spec
  python shotplan.py --selftest                   # known-answer tests
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SENSORS = {"ff": (36.0, 24.0), "apsc": (23.5, 15.6), "m43": (17.3, 13.0), "mf": (43.8, 32.9), "4x5": (127.0, 102.0),
           "phone": (9.8, 7.3)}
FINISH_GLOSS = {"matte": 0.0, "satin": 0.35, "frosted": 0.45, "gloss": 0.9, "foil": 1.0, "glass": 1.0, "mirror": 1.0}
# angular half-width (deg) of the highlight lobe: a satin surface spreads a reflection; a mirror does not
FINISH_LOBE = {"matte": 0.0, "satin": 14.0, "frosted": 18.0, "gloss": 4.0, "foil": 6.0, "glass": 1.5, "mirror": 0.5}
R0 = {"gloss": 0.04, "glass": 0.04, "satin": 0.04, "frosted": 0.04, "foil": 0.6, "mirror": 0.9, "matte": 0.0}

EXAMPLE = {
    "_how": "Angles: az 0 = light beside the camera, -90 = camera-left, +90 = camera-right, 180 = behind the product. "
            "el = degrees above the horizon. Metres for distances. finish: matte|satin|frosted|gloss|foil|glass.",
    "scene": "a steel kiryana shelf at 7 pm under one tube light",
    "frame": {"aspect": "4:5", "px": [1080, 1350]},
    "camera": {"sensor": "ff", "focal_mm": 85, "distance_m": 1.4, "height_m": 0.42, "f_number": 8, "coc_mm": 0.03},
    "subject": {"name": "stand-up pouch", "w_m": 0.16, "h_m": 0.23, "d_m": 0.06, "finish": "satin",
                "face_tilt_deg": 4, "bend_deg": 12, "base_height_m": 0.30},
    "surface": {"material": "chipped grey-painted steel shelf", "finish": "satin"},
    "lights": [
        {"role": "key", "kind": "strip", "az": -55, "el": 38, "distance_m": 1.1, "size_m": 0.6, "cct_k": 5000, "power": 1.0},
        {"role": "fill", "kind": "bounce", "az": 60, "el": 10, "distance_m": 1.3, "size_m": 1.0, "cct_k": 5000, "power": 0.35},
        {"role": "rim", "kind": "bare", "az": 160, "el": 30, "distance_m": 1.2, "size_m": 0.12, "cct_k": 3400, "power": 0.5}
    ],
    "never": ["no product, no packs, no text, no logos, no shop names, no faces"],
    "grade": "shot on a 35 mm film camera, natural grain, no HDR"
}


# ---------------------------------------------------------------------------------------------- geometry helpers
def _v(*a):
    return np.array(a, dtype=float)


def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def light_dir(az, el):
    """Unit vector from the subject toward a light. Camera sits on -z looking +z, x to the right, y up."""
    a, e = math.radians(az), math.radians(el)
    return _unit(_v(math.sin(a) * math.cos(e), math.sin(e), -math.cos(a) * math.cos(e)))


def fov_deg(focal, sensor_mm):
    return math.degrees(2 * math.atan(sensor_mm / (2 * focal)))


def dof(focal, n, coc, s_m):
    """Near and far limits of acceptable focus (m) by the thin-lens formulas; far = inf beyond the hyperfocal."""
    f = focal / 1000.0
    c = coc / 1000.0
    H = f * f / (n * c) + f
    near = s_m * (H - f) / (H + s_m - 2 * f)
    far = s_m * (H - f) / (H - s_m) if s_m < H else float("inf")
    return H, near, far


def hardness(angular_deg):
    if angular_deg < 2:
        return "hard"
    if angular_deg < 20:
        return "medium"
    return "soft"


def fresnel(cos_theta, r0):
    """Schlick's approximation of Fresnel reflectance; cos_theta is between the view ray and the surface normal."""
    return r0 + (1 - r0) * (1 - cos_theta) ** 5


def mired(k):
    return 1e6 / k


# ---------------------------------------------------------------------------------------------- the plan
class Plan:
    def __init__(self, spec):
        self.s = spec
        self.cam = spec["camera"]
        self.sub = spec["subject"]
        self.lights = spec.get("lights", [])
        self.warn = []
        self.out = {}

    # ---- camera
    def camera(self):
        c, s = self.cam, self.sub
        sw, sh = SENSORS.get(c.get("sensor", "ff"), SENSORS["ff"])
        px = self.s.get("frame", {}).get("px", [1080, 1350])
        portrait = px[1] > px[0]
        long_fov = fov_deg(c["focal_mm"], max(sw, sh))
        short_fov = fov_deg(c["focal_mm"], min(sw, sh))
        hfov, vfov = (short_fov, long_fov) if portrait else (long_fov, short_fov)
        d = c["distance_m"]
        base = s.get("base_height_m", 0.0)
        mid_y = base + s["h_m"] / 2
        tilt = math.degrees(math.atan2(c["height_m"] - mid_y, d))           # + = camera looks down
        frame_h_m = 2 * d * math.tan(math.radians(vfov) / 2)
        fill = s["h_m"] / frame_h_m
        # verticals converge: the top and bottom of the product are at different distances along the view
        t = math.radians(tilt)
        lean = math.radians(s.get("face_tilt_deg", 0))                       # a pouch leaning back puts its top further away
        top = _v(0, base + s["h_m"] * math.cos(lean) - c["height_m"], d + s["h_m"] * math.sin(lean))
        bot = _v(0, base - c["height_m"], d)
        view = _v(0, -math.sin(t), math.cos(t))
        dt, db = float(top @ view), float(bot @ view)
        # signed: + = top narrower (low camera or a pack leaning back), - = top wider (camera above an upright pack)
        persp = (1 - db / dt) if dt > 0 else 0.0
        H, near, far = dof(c["focal_mm"], c.get("f_number", 8), c.get("coc_mm", 0.03), d)
        front, back = d - s.get("d_m", 0.05) / 2, d + s.get("d_m", 0.05) / 2
        in_focus = near <= front and far >= back
        eq = c["focal_mm"] * 43.27 / math.hypot(sw, sh)                     # 35 mm equivalent
        o = dict(hfov_deg=round(hfov, 2), vfov_deg=round(vfov, 2), focal_35mm_equiv=round(eq, 1),
                 tilt_deg=round(tilt, 2), product_frame_fill=round(fill, 3), persp=round(persp, 4),
                 hyperfocal_m=round(H, 2), dof_near_m=round(near, 3), dof_far_m=(round(far, 3) if far != float("inf") else "inf"),
                 dof_depth_mm=(round((far - near) * 1000) if far != float("inf") else "inf"), product_in_focus=in_focus)
        if eq < 40:
            self.warn.append(f"Lens is {eq:.0f} mm equivalent: wide lenses bend verticals near the edges and a flat render will not match. Use 50-100 mm for product plates.")
        if not in_focus:
            self.warn.append(f"Depth of field {o['dof_depth_mm']} mm is less than the product depth {s.get('d_m',0.05)*1000:.0f} mm: front or back of the pack goes soft. Stop down or step back.")
        if fill < 0.18:
            self.warn.append(f"Product fills only {fill:.0%} of the frame height: print will not read; move closer or use a longer lens.")
        if fill > 0.85:
            self.warn.append(f"Product fills {fill:.0%} of the frame height: no air for the shadow and the surface.")
        self.out["camera"] = o
        self.tilt = tilt
        return o

    # ---- lights
    def light_table(self):
        s = self.sub
        rows = []
        for L in self.lights:
            ang = math.degrees(2 * math.atan(L["size_m"] / (2 * L["distance_m"])))
            el = max(L["el"], 1.0)
            Lshadow = s["h_m"] / math.tan(math.radians(el))                  # ground shadow length from a vertical edge
            a = math.radians(L["az"])
            dx_w, dz_w = -math.sin(a) * Lshadow, math.cos(a) * Lshadow       # shadow runs away from the light
            pen = Lshadow * L["size_m"] / L["distance_m"]                    # penumbra width at the tip (similar triangles)
            # inverse-square falloff across the product: near and far face from this light
            ld = light_dir(L["az"], L["el"])
            near_d = L["distance_m"] - abs(ld[0]) * s["w_m"] / 2 - abs(ld[2]) * s.get("d_m", 0.05) / 2
            far_d = L["distance_m"] + abs(ld[0]) * s["w_m"] / 2 + abs(ld[2]) * s.get("d_m", 0.05) / 2
            sun = L.get("kind") == "sun" or L["distance_m"] > 1e4           # parallel light: no falloff across a set
            fall = 0.0 if sun else 2 * math.log2(far_d / max(near_d, 1e-3))
            front = max(0.0, float(ld @ _v(0, 0, -1)))                      # how much it lights the face the camera sees
            # sun: 'power' is its illuminance at the subject relative to a 1 m lamp of power 1 (inverse square would give ~0)
            E = L.get("power", 1.0) if sun else L.get("power", 1.0) / L["distance_m"] ** 2
            side = ("front" if abs(L["az"]) < 30 else "side" if abs(L["az"]) <= 120 else "back")
            rows.append(dict(role=L.get("role", "light"), kind=L.get("kind", ""), az=L["az"], el=L["el"],
                             angular_size_deg=round(ang, 1), quality=hardness(ang), position=side,
                             shadow_len_x_product_h=round(Lshadow / s["h_m"], 2),
                             shadow_dir=("right" if dx_w > 0.01 else "left" if dx_w < -0.01 else "straight") +
                                        (" and back" if dz_w > 0.01 else " and toward camera" if dz_w < -0.01 else ""),
                             penumbra_at_tip_mm=round(pen * 1000), falloff_across_product_stops=round(fall, 2),
                             illum_on_face=round(E * front, 6), illum=round(E, 6), cct_k=L.get("cct_k", 5600),
                             _dx=dx_w / s["h_m"], _dz=dz_w / s["h_m"]))
        self.rows = rows
        keys = [r for r in rows if r["role"] == "key"] or rows[:1]
        if keys:
            k = keys[0]
            for r in rows:
                if r is k or r["illum"] <= 0:
                    continue
                r["ratio_to_key_stops"] = round(math.log2(k["illum"] / r["illum"]), 2)
            # two strong lights from opposite sides make two shadows
            for r in rows:
                if r is k:
                    continue
                if r.get("ratio_to_key_stops", 9) < 1.0 and r["position"] != "back" and math.copysign(1, r["az"]) != math.copysign(1, k["az"]) and r["el"] > 15:
                    self.warn.append(f"The {r['role']} is within 1 stop of the key from the other side: two shadows on the surface (an AI and amateur tell). Drop it 1.5 stops or make it a low bounce.")
            # colour temperature clash
            for r in rows:
                dm = abs(mired(r["cct_k"]) - mired(k["cct_k"]))
                r["mired_vs_key"] = round(dm)
                if r is not k and dm > 30:
                    self.warn.append(f"The {r['role']} is {dm:.0f} mired from the key ({r['cct_k']} K vs {k['cct_k']} K): a visible warm/cool split. Keep it only if the story motivates it (a tungsten practical, dusk sky).")
            if k["position"] == "front" and k["el"] < 25:
                self.warn.append("The key is flat and frontal: no modelling on the pack, the film looks like a scan. Move it to 35-60 degrees off axis.")
            if k["position"] == "back":
                self.warn.append("The key is behind the product: the printed face goes dark. Use the back light as a rim and put the key in front.")
        self.out["lights"] = [{k2: v for k2, v in r.items() if not k2.startswith("_")} for r in rows]
        return rows

    # ---- reflections on the product face (family of angles)
    def face_normals(self, n=11):
        """Sample points and normals on the product's camera face: tilted back by face_tilt_deg, bent left-right by bend_deg."""
        s = self.sub
        tilt = math.radians(s.get("face_tilt_deg", 0))
        bend = math.radians(s.get("bend_deg", 0))
        base = s.get("base_height_m", 0.0)
        pts, nrm, uv = [], [], []
        for j in range(n):
            for i in range(n):
                u, v = i / (n - 1) - 0.5, j / (n - 1)                     # u across, v up the face
                a = u * 2 * bend                                          # normal swings with the bend
                nn = _v(math.sin(a), math.sin(tilt) * math.cos(a), -math.cos(tilt) * math.cos(a))
                pts.append(_v(u * s["w_m"], base + v * s["h_m"], 0.0))
                nrm.append(_unit(nn))
                uv.append((u + 0.5, v))
        return pts, nrm, uv

    def glare(self, L, cam=None):
        """Fraction of the face where light L is mirrored into the lens, and where (u, v in 0-1, v up)."""
        s = self.sub
        fin = s.get("finish", "matte")
        if FINISH_GLOSS.get(fin, 0) == 0:
            return 0.0, None
        lobe = FINISH_LOBE.get(fin, 5.0)
        c = cam or self.cam
        C = _v(0, c["height_m"], -c["distance_m"])
        pts, nrm, uv = self.face_normals()
        hit, where = 0, []
        Lpos_dir = light_dir(L["az"], L["el"])
        half_src = math.degrees(math.atan(L["size_m"] / (2 * L["distance_m"])))
        for p, nn, q in zip(pts, nrm, uv):
            toC = _unit(C - p)
            if toC @ nn <= 0:
                continue
            r = _unit(2 * (toC @ nn) * nn - toC)                          # where the camera's ray goes after the mirror
            Lp = _unit(Lpos_dir * L["distance_m"] - p)
            ang = math.degrees(math.acos(max(-1, min(1, float(r @ Lp)))))
            if ang <= half_src + lobe:
                hit += 1
                where.append(q)
        frac = hit / len(pts)
        if not where:
            return frac, None
        u = float(np.mean([w[0] for w in where]))
        v = float(np.mean([w[1] for w in where]))
        return frac, (round(u, 2), round(v, 2))

    def reflections(self):
        s = self.sub
        fin = s.get("finish", "matte")
        res = []
        for L, r in zip(self.lights, self.rows):
            frac, where = self.glare(L)
            r["glare_frac"] = round(frac, 3)
            r["glare_at_uv"] = where
            res.append(dict(role=r["role"], glare_on_face=f"{frac:.0%}", where=self._where(where)))
            if frac > 0.04 and r["role"] in ("key", "fill"):
                fix = self.fix_glare(L)
                msg = f"The {r['role']} mirrors into the lens over {frac:.0%} of the {fin} face ({self._where(where)}): glare will eat the print."
                if fix:
                    msg += f" Nearest clean position: az {fix[0]}, el {fix[1]} (or flag the light, or use a polariser if the reflection is from a dielectric)."
                self.warn.append(msg)
        # the surface: a mirror image of the product on gloss, a soft sheen on satin, nothing on matte
        surf = self.s.get("surface", {})
        sf = surf.get("finish", "matte")
        theta = math.radians(90 - max(self.tilt, 0.5))                   # view ray to the floor normal
        # Fresnel gives a perfect surface; a satin or frosted surface spreads (and so weakens) the image by its gloss
        refl = fresnel(math.cos(theta), R0.get(sf, 0.0)) * FINISH_GLOSS.get(sf, 0.0) if sf in R0 and sf != "matte" else 0.0
        floor = dict(finish=sf, mirror_reflection_strength=round(refl, 3),
                     note=("a sharp, mirrored copy of the product under its base" if sf in ("gloss", "glass", "mirror")
                           else "a soft, blurred sheen under the base, no sharp mirror image" if sf in ("satin",)
                           else "no mirror image; only contact shadow and a little colour bounce"))
        if sf in ("gloss", "glass", "mirror") and refl > 0.25:
            floor["note"] += f"; at this low camera the floor reflects {refl:.0%}: the reflection is a big part of the picture"
        self.out["reflections"] = dict(product_face=res, floor=floor,
                                       family_of_angles="a light inside the family of angles of a shiny face shows as a mirror image of the source on that face; move it outside to keep print readable, or put a large soft source inside it on purpose for a controlled gradient")
        return res

    @staticmethod
    def _where(uv):
        if uv is None:
            return "none"
        u, v = uv
        h = "left" if u < 0.4 else "right" if u > 0.6 else "centre"
        vv = "low" if v < 0.35 else "high" if v > 0.65 else "middle"
        return f"{vv} {h}"

    def fix_glare(self, L):
        best = None
        for daz in range(0, 95, 5):
            for sgn in (1, -1):
                for el in sorted({L["el"], L["el"] + 10, L["el"] + 20, L["el"] - 10, 60, 70}):
                    if el < 5 or el > 80:
                        continue
                    az = L["az"] + sgn * daz
                    if abs(az) > 150:
                        continue
                    T = dict(L, az=az, el=el)
                    f, _ = self.glare(T)
                    if f <= 0.02:
                        cost = daz + abs(el - L["el"]) * 0.7
                        if best is None or cost < best[2]:
                            best = (az, el, cost)
            if best:
                break
        return (best[0], best[1]) if best else None

    # ---- composite.py args and the prompt
    def composite_args(self):
        keys = [r for r in self.rows if r["role"] == "key"] or self.rows[:1]
        if not keys:
            return {}
        k = keys[0]
        squash = max(math.sin(math.radians(max(self.tilt, 0))), 0.08)
        dx = float(np.clip(k["_dx"], -1.2, 1.2))
        dy = float(np.clip(k["_dz"] * squash, -0.6, 0.6))
        a = dict(light=f"{dx:.2f},{dy:.2f}", persp=round(float(np.clip(self.out["camera"]["persp"], -0.08, 0.08)), 3))
        self.out["composite"] = dict(args=f"--light {a['light']} --persp {a['persp']}",
                                     note="dx = shadow offset to the right, dy = how far it falls back, both as a fraction of product height in the image (dy foreshortened by the camera tilt)")
        return a

    def prompt(self):
        s, c, cam = self.s, self.cam, self.out["camera"]
        sub = self.sub
        side = lambda az: ("from camera-left" if az < -15 else "from camera-right" if az > 15 else "from beside the camera")
        lines = []
        for L, r in zip(self.lights, self.rows):
            height = "high" if L["el"] > 50 else "at mid height" if L["el"] > 20 else "low"
            where = side(L["az"]) if r["position"] != "back" else ("behind the subject, " + side(L["az"]).replace("from ", "toward "))
            lines.append(f"{r['role']}: {r['quality']} {L.get('kind', 'light')} {where}, {height} ({abs(L['az'])} degrees off axis, {L['el']} degrees up), about {L.get('cct_k', 5600)} K")
        key = (self.rows[[r['role'] for r in self.rows].index('key')] if any(r['role'] == 'key' for r in self.rows) else self.rows[0]) if self.rows else None
        shadow = (f"Shadows fall {key['shadow_dir']}, about {key['shadow_len_x_product_h']} times as long as a "
                  f"{sub['h_m']*100:.0f} cm object is tall, {'crisp' if key['quality']=='hard' else 'with a soft edge' if key['quality']=='soft' else 'with a clear but soft-edged'} "
                  f"penumbra about {key['penumbra_at_tip_mm']} mm wide at the tip.") if key else ""
        surf = s.get("surface", {})
        floor = self.out["reflections"]["floor"]
        gap = f"{sub['w_m']*100*1.6:.0f} cm"
        pr = (
            f"Purpose: an empty background plate for a product added later in post, {s.get('frame', {}).get('aspect', '4:5')}.\n"
            f"Scene: {s.get('scene', 'a real place, one moment')}.\n"
            f"Camera: {cam['focal_35mm_equiv']:.0f} mm lens (35 mm equivalent), {c['distance_m']:.1f} m from the empty spot, lens at "
            f"{c['height_m']*100:.0f} cm, tilted {abs(cam['tilt_deg']):.0f} degrees {'down' if cam['tilt_deg'] >= 0 else 'up'}, f/{c.get('f_number', 8)}; "
            f"the zone of sharp focus is about {cam['dof_depth_mm']} mm deep around the empty spot and the background falls off naturally. "
            + ("Verticals straight, no wide-angle bulge.\n" if abs(cam['tilt_deg']) <= 12 else
               f"A steep {'upward' if cam['tilt_deg'] < 0 else 'downward'} view: verticals converge naturally, no fisheye bulge.\n") +
            f"Light: " + "; ".join(lines) + ".\n"
            f"{shadow}\n"
            f"Surface: {surf.get('material', 'a real surface')}, {surf.get('finish', 'matte')} finish: {floor['note']}.\n"
            f"The empty spot: a clear patch of surface about {gap} wide where the product will stand, "
            f"at the lower-middle third of the frame, the surface continuing unbroken under it and the light reaching it.\n"
            f"Texture: real wear, dust and tiny imperfections on every surface; nothing melted or plastic.\n"
            f"Grade: {s.get('grade', 'natural colour, fine film grain, no HDR, no bloom')}.\n"
            f"Keep out of frame: " + "; ".join(s.get("never", ["no product, no text, no logos, no faces"])) + "."
        )
        self.out["plate_prompt"] = pr
        return pr

    def run(self):
        self.camera()
        self.light_table()
        self.reflections()
        self.composite_args()
        self.prompt()
        self.out["warnings"] = self.warn
        return self.out


# ---------------------------------------------------------------------------------------------- diagram
def _font(sz):
    for f in ("DejaVuSans.ttf", "arial.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def diagram(plan, path, W=1400, H=700):
    """Top view (left) and side view (right): camera, product, every light with its size, shadow direction, family of angles."""
    s, c = plan.s, plan.cam
    im = Image.new("RGB", (W, H), (246, 243, 236))
    d = ImageDraw.Draw(im)
    ink, mute, red = (30, 26, 23), (140, 132, 120), (196, 52, 40)
    f, fs = _font(20), _font(15)
    # ---------- top view
    cx, cy, sc = W // 4, H // 2 + 40, 190 / max(c["distance_m"], 1.0)
    d.text((24, 18), "TOP VIEW", fill=ink, font=f)
    w = s["subject"]["w_m"] * sc
    dd = max(s["subject"].get("d_m", 0.05) * sc, 4)
    d.rectangle([cx - w / 2, cy - dd / 2, cx + w / 2, cy + dd / 2], fill=(214, 120, 48))
    camx, camy = cx, cy + c["distance_m"] * sc
    d.polygon([(camx, camy - 10), (camx - 12, camy + 12), (camx + 12, camy + 12)], fill=ink)
    d.text((camx + 16, camy - 4), f"camera {c['focal_mm']} mm", fill=ink, font=fs)
    hf = math.radians(plan.out["camera"]["hfov_deg"] / 2)
    for sg in (-1, 1):
        d.line([camx, camy, camx + sg * math.tan(hf) * c["distance_m"] * sc * 1.25, camy - c["distance_m"] * sc * 1.25], fill=mute, width=1)
    for L, r in zip(plan.lights, plan.rows):
        ld = light_dir(L["az"], L["el"])
        hd = math.hypot(ld[0], ld[2]) or 1e-6
        # camera sits below the product on the page, so world -z (toward the camera) is page-down
        dd = min(L["distance_m"], 1.6 * max(c["distance_m"], 1.0))   # the sun (or any far light) sits at the diagram's edge
        lx, ly = cx + ld[0] / hd * dd * sc * math.cos(math.radians(L["el"])), cy - ld[2] / hd * dd * sc * math.cos(math.radians(L["el"]))
        size = min(max(L["size_m"] * sc, 6), 40)   # the sun would cover the page
        ang = math.atan2(ly - cy, lx - cx) + math.pi / 2
        p1 = (lx + math.cos(ang) * size / 2, ly + math.sin(ang) * size / 2)
        p2 = (lx - math.cos(ang) * size / 2, ly - math.sin(ang) * size / 2)
        col = red if r.get("glare_frac", 0) > 0.04 else ink
        d.line([p1, p2], fill=col, width=7)
        d.line([lx, ly, cx, cy], fill=col, width=1)
        d.text((lx + 10, ly - 22), f"{r['role']} {r['quality']}", fill=col, font=fs)
        if r["role"] == "key" or len(plan.rows) == 1:
            sx, sy = cx + r["_dx"] * s["subject"]["h_m"] * sc, cy + (-r["_dz"]) * s["subject"]["h_m"] * sc
            d.line([cx, cy, sx, sy], fill=(90, 84, 76), width=9)
            d.text((sx + 6, sy), "shadow", fill=(90, 84, 76), font=fs)
    # ---------- side view
    ox, oy, ss = W // 2 + 120, H - 140, 300 / max(c["distance_m"], 1.0)
    d.text((W // 2 + 24, 18), "SIDE VIEW", fill=ink, font=f)
    base = s["subject"].get("base_height_m", 0.0)
    d.line([W // 2 + 30, oy - base * ss, W - 30, oy - base * ss], fill=mute, width=2)
    ph = s["subject"]["h_m"] * ss
    px0 = ox + c["distance_m"] * ss
    d.rectangle([px0 - 6, oy - base * ss - ph, px0 + 6, oy - base * ss], fill=(214, 120, 48))
    cyy = oy - c["height_m"] * ss
    d.polygon([(ox, cyy), (ox - 14, cyy - 9), (ox - 14, cyy + 9)], fill=ink)
    d.line([ox, cyy, px0, oy - (base + s["subject"]["h_m"] / 2) * ss], fill=mute, width=1)
    d.text((ox - 60, cyy + 14), f"lens {c['height_m']*100:.0f} cm, tilt {plan.out['camera']['tilt_deg']:.0f} deg", fill=ink, font=fs)
    for L, r in zip(plan.lights, plan.rows):
        ld = light_dir(L["az"], L["el"])
        sign = -1 if ld[2] < 0 else 1
        dd = min(L["distance_m"], 2.5)
        lx = px0 + sign * math.cos(math.radians(L["el"])) * dd * ss * 0.8
        ly = oy - base * ss - ph / 2 - math.sin(math.radians(L["el"])) * dd * ss * 0.8
        col = red if r.get("glare_frac", 0) > 0.04 else ink
        d.ellipse([lx - 7, ly - 7, lx + 7, ly + 7], fill=col)
        d.line([lx, ly, px0, oy - base * ss - ph / 2], fill=col, width=1)
        d.text((lx + 10, ly - 8), f"{r['role']} {L['el']} deg", fill=col, font=fs)
    y = H - 60
    d.text((24, y), "red = mirrors into the lens on the product face (family of angles)", fill=red, font=fs)
    d.text((24, y + 22), f"DoF {plan.out['camera']['dof_depth_mm']} mm at f/{c.get('f_number', 8)} · product fills {plan.out['camera']['product_frame_fill']:.0%} of frame height · composite {plan.out['composite']['args']}", fill=ink, font=fs)
    im.save(path)
    return path


def write_md(out, path):
    L = ["# Shot plan", "", "## Camera"]
    L += [f"- {k}: {v}" for k, v in out["camera"].items()]
    L += ["", "## Lights", "| role | quality | where | shadow | penumbra at tip | falloff across pack | vs key | mired vs key | glare on face |", "|---|---|---|---|---|---|---|---|---|"]
    for r in out["lights"]:
        L.append(f"| {r['role']} | {r['quality']} ({r['angular_size_deg']} deg) | az {r['az']}, el {r['el']} ({r['position']}) | {r['shadow_dir']}, {r['shadow_len_x_product_h']}x h | {r['penumbra_at_tip_mm']} mm | {r['falloff_across_product_stops']} stops | {r.get('ratio_to_key_stops', '-')} stops | {r.get('mired_vs_key', 0)} | {r.get('glare_frac', 0):.0%} |")
    fl = out["reflections"]["floor"]
    L += ["", "## Reflections", f"- Floor ({fl['finish']}): strength {fl['mirror_reflection_strength']}; {fl['note']}",
          f"- Family of angles: {out['reflections']['family_of_angles']}", "", "## Composite", f"`composite.py ... {out['composite']['args']}`",
          "", "## Warnings"] + ([f"- {w}" for w in out["warnings"]] or ["- none"]) + ["", "## Plate prompt", "```", out["plate_prompt"], "```"]
    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return path


def plan_file(spec_path, outdir):
    spec = json.load(open(spec_path, encoding="utf-8"))
    p = Plan(spec)
    out = p.run()
    os.makedirs(outdir, exist_ok=True)
    json.dump(out, open(os.path.join(outdir, "plan.json"), "w", encoding="utf-8"), indent=2)
    write_md(out, os.path.join(outdir, "plan.md"))
    diagram(p, os.path.join(outdir, "plan_diagram.png"))
    open(os.path.join(outdir, "plate_prompt.txt"), "w", encoding="utf-8").write(out["plate_prompt"] + "\n")
    return out


# ---------------------------------------------------------------------------------------------- self-test
def selftest():
    ok = True

    def check(name, cond, info=""):
        nonlocal ok
        ok &= bool(cond)
        print(("PASS " if cond else "FAIL ") + name + (f"  ({info})" if info else ""))

    check("50 mm on full frame: horizontal FOV 39.6 deg", abs(fov_deg(50, 36) - 39.6) < 0.1, f"{fov_deg(50, 36):.2f}")
    H, n, f = dof(50, 8, 0.03, 3.0)
    check("DoF 50 mm f/8 at 3 m: hyperfocal ~10.5 m, near ~2.34 m, far ~4.18 m", abs(H - 10.47) < 0.1 and abs(n - 2.34) < 0.03 and abs(f - 4.18) < 0.05, f"H {H:.2f} n {n:.2f} f {f:.2f}")
    check("Sun (0.53 deg) is hard; 1 m softbox at 1 m is soft", hardness(0.53) == "hard" and hardness(math.degrees(2 * math.atan(0.5))) == "soft")
    check("Fresnel at normal incidence = R0 (0.04), at grazing -> 1", abs(fresnel(1.0, 0.04) - 0.04) < 1e-9 and fresnel(0.0, 0.04) > 0.99)
    base = json.loads(json.dumps(EXAMPLE))
    base["lights"] = [dict(role="key", kind="softbox", az=-45, el=45, distance_m=1.0, size_m=0.5, cct_k=5600, power=1)]
    p = Plan(base); o = p.run()
    r = p.rows[0]
    check("Key from camera-left 45/45: shadow falls right and back, length = h", r["_dx"] > 0.69 and r["_dz"] > 0.69 and abs(r["shadow_len_x_product_h"] - 1.0) < 0.02, r["shadow_dir"])
    g = json.loads(json.dumps(base)); g["subject"]["finish"] = "gloss"; g["subject"]["bend_deg"] = 0; g["subject"]["face_tilt_deg"] = 0
    g["lights"] = [dict(role="key", kind="softbox", az=0, el=2, distance_m=0.3, size_m=0.6, cct_k=5600, power=1)]
    g["camera"]["height_m"] = g["subject"]["base_height_m"] + g["subject"]["h_m"] / 2
    pg = Plan(g); pg.run()
    check("Gloss face, big light right behind the camera: glare on the face", pg.rows[0]["glare_frac"] > 0.2, f"{pg.rows[0]['glare_frac']:.0%}")
    g["lights"] = [dict(role="key", kind="softbox", az=-90, el=20, distance_m=1.0, size_m=0.4, cct_k=5600, power=1)]
    pg2 = Plan(g); pg2.run()
    check("Gloss face, light at 90 deg side: no glare", pg2.rows[0]["glare_frac"] == 0.0)
    m = json.loads(json.dumps(g)); m["subject"]["finish"] = "matte"
    m["lights"] = [dict(role="key", kind="softbox", az=0, el=2, distance_m=0.3, size_m=0.6, cct_k=5600, power=1)]
    pm = Plan(m); pm.run()
    check("Matte face never glares", pm.rows[0]["glare_frac"] == 0.0)
    fx = Plan(json.loads(json.dumps(g)))
    fx.lights = [dict(role="key", kind="softbox", az=-10, el=10, distance_m=1.0, size_m=0.5, cct_k=5600, power=1)]
    fx.camera(); fx.light_table()
    fix = fx.fix_glare(fx.lights[0])
    ok2 = fix is not None and fx.glare(dict(fx.lights[0], az=fix[0], el=fix[1]))[0] <= 0.02
    check("Glare fixer finds a clean position", ok2, str(fix))
    two = json.loads(json.dumps(base))
    two["lights"] = [dict(role="key", kind="softbox", az=-50, el=40, distance_m=1.0, size_m=0.5, cct_k=5600, power=1),
                     dict(role="fill", kind="softbox", az=50, el=40, distance_m=1.0, size_m=0.5, cct_k=3200, power=0.9)]
    pt = Plan(two); ot = pt.run()
    check("Warns on two shadows and on a 134-mired clash", any("two shadows" in w for w in ot["warnings"]) and any("mired" in w for w in ot["warnings"]))
    lo = json.loads(json.dumps(base)); lo["camera"]["height_m"] = 1.5; lo["subject"]["face_tilt_deg"] = 0
    pl = Plan(lo); pl.run()
    lw = json.loads(json.dumps(lo)); lw["camera"]["height_m"] = 0.05; lw["subject"]["base_height_m"] = 0.3
    pw = Plan(lw); pw.run()
    check("Camera above an upright pack -> top wider (persp < 0); camera below -> top narrower (> 0)",
          pl.out["camera"]["persp"] < -0.01 and pw.out["camera"]["persp"] > 0.01, f"{pl.out['camera']['persp']} / {pw.out['camera']['persp']}")
    check("Plate prompt never asks for the product or text", "Keep out of frame" in o["plate_prompt"] and "no product" in o["plate_prompt"])
    import tempfile
    tdir = tempfile.mkdtemp()
    sp = os.path.join(tdir, "spec.json"); json.dump(EXAMPLE, open(sp, "w"))
    out = plan_file(sp, tdir)
    check("plan writes json, md, diagram and prompt", all(os.path.isfile(os.path.join(tdir, n)) for n in ("plan.json", "plan.md", "plan_diagram.png", "plate_prompt.txt")))
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", choices=["plan", "example"])
    ap.add_argument("spec", nargs="?")
    ap.add_argument("-o", "--out", default="shotplan_out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    if a.cmd == "example":
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if a.cmd == "plan" and a.spec:
        out = plan_file(a.spec, a.out)
        print(open(os.path.join(a.out, "plan.md"), encoding="utf-8").read())
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
