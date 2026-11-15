#!/usr/bin/env python3
"""
nazar-type/engine/type_check.py: the type kit's QA checklist, run on real font files.

Reads each font with fontTools and reports what the kit's rules ask for:
  - identity and LICENCE as the font itself declares it (name table IDs 0, 9, 13, 14)
  - EMBEDDING permissions (OS/2 fsType): can it go in a PDF or an app?
  - COVERAGE per script/set, as a share of the codepoints that set needs:
    basic Latin, transliteration diacritics, packaging symbols (Rs, (c), %, fractions),
    Urdu letters, Urdu digits, Sindhi extra letters, Devanagari
  - SHAPING: does GSUB carry the Arabic-script features (init/medi/fina/isol/liga/calt/rlig)?
    Without them a font can have the glyphs and still set Urdu wrongly
  - KERNING: is there a GPOS kern/mark feature?
  - SMALL TYPE: x-height as a share of the em, and the smallest size at which the
    x-height reaches 1.2 mm (EU 1169/2011 Art. 13) and 0.9 mm (packs under 80 cm2)

It checks the FILE. It cannot judge design quality, and a coverage % says nothing
about whether the shapes are good. See ../references/type.md section 5.

    python type_check.py font.ttf [font2.ttf ...] [--json]
"""
import json
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

PT_MM = 25.4 / 72  # one typographic point in millimetres

SETS = {
    "basic Latin": [chr(c) for c in list(range(0x41, 0x5B)) + list(range(0x61, 0x7B)) + list(range(0x30, 0x3A))] + list(".,:;!?'\"()-/&@#"),
    "transliteration (ā ī ū ṭ ḍ ṇ ṣ ḥ ñ)": list("āīūṭḍṇṣḥñĀĪŪṬḌṆṢḤÑ"),
    "pack symbols (₨ © ® ™ % ½ ¼ ¾ × ·)": list("₨©®™%½¼¾×·"),
    "Urdu letters": list("ابپتٹثجچحخدڈذرڑزژسشصضطظعغفقکگلمنںوہھءیےۓ"),
    "Urdu digits ۰–۹": [chr(c) for c in range(0x06F0, 0x06FA)],
    "Sindhi extra letters": list("ڄڃڇڏڙڪڻٻڀڦڱڳڌڍڊ"),
    "Devanagari (core)": list("कखगघचजटडणतदनपबमयरलवशषसहािीुूेैोौं"),
}
ARABIC_FEATURES = ["init", "medi", "fina", "isol", "liga", "calt", "rlig", "locl"]
FSTYPE = [(0x0002, "restricted: no embedding"), (0x0004, "preview & print only"), (0x0008, "editable embedding"),
          (0x0100, "no subsetting"), (0x0200, "bitmap embedding only")]


def name(font, i):
    r = font["name"].getName(i, 3, 1, 0x409) or font["name"].getName(i, 1, 0, 0)
    return str(r).strip() if r else None


def glyph_height(font, ch):
    cmap = font.getBestCmap()
    gn = cmap.get(ord(ch))
    if not gn:
        return None
    gs = font.getGlyphSet()
    bp = BoundsPen(gs)
    gs[gn].draw(bp)
    return bp.bounds[3] if bp.bounds else None


def features(font, table):
    if table not in font or not getattr(font[table].table, "FeatureList", None):
        return set()
    return {fr.FeatureTag for fr in font[table].table.FeatureList.FeatureRecord}


def check(path):
    f = TTFont(path)
    upm = f["head"].unitsPerEm
    cmap = f.getBestCmap() or {}
    ver = (name(f, 5) or "").replace("Version ", "").split(";")[0].strip()
    res = {"file": path.split("/")[-1], "family": name(f, 16) or name(f, 1), "style": name(f, 17) or name(f, 2), "designer": name(f, 9),
           "licence": (name(f, 13) or "not stated in the font file (check the OFL/licence file that ships with it)")[:120],
           "licence_url": name(f, 14), "version": ver}
    fs = f["OS/2"].fsType
    res["embedding"] = "installable (no restrictions)" if fs == 0 else "; ".join(t for bit, t in FSTYPE if fs & bit) or f"fsType={fs}"
    res["coverage"] = {k: round(sum(1 for ch in v if ord(ch) in cmap) / len(v), 2) for k, v in SETS.items()}
    res["missing"] = {k: "".join(ch for ch in v if ord(ch) not in cmap) for k, v in SETS.items()}
    gsub, gpos = features(f, "GSUB"), features(f, "GPOS")
    res["arabic_shaping"] = [t for t in ARABIC_FEATURES if t in gsub]
    res["kerning"] = "kern" in gpos
    res["mark_positioning"] = "mark" in gpos
    xh, cap = glyph_height(f, "x"), glyph_height(f, "H")
    res["x_height_em"] = round(xh / upm, 3) if xh else None
    res["cap_height_em"] = round(cap / upm, 3) if cap else None
    if xh:
        r = xh / upm
        res["min_pt_for_1.2mm_xheight"] = round(1.2 / (r * PT_MM), 1)
        res["min_pt_for_0.9mm_xheight"] = round(0.9 / (r * PT_MM), 1)
    return res


def verdict(r):
    c = r["coverage"]
    latin = c["basic Latin"] >= 0.99
    urdu = c["Urdu letters"] >= 0.95 and len(r["arabic_shaping"]) >= 3
    out = []
    if latin and not urdu:
        out.append("Latin only: cannot set Urdu")
    if urdu:
        out.append("sets Urdu" + (" and Latin" if latin else ", no Latin"))
        if c["Sindhi extra letters"] < 1.0:
            miss = round((1 - c["Sindhi extra letters"]) * len(SETS["Sindhi extra letters"]))
            out.append(f"not for Sindhi: {miss} of {len(SETS['Sindhi extra letters'])} extra letters missing")
    if latin and c["pack symbols (₨ © ® ™ % ½ ¼ ¾ × ·)"] < 1.0:
        miss = [ch for ch in SETS["pack symbols (₨ © ® ™ % ½ ¼ ¾ × ·)"] if ord(ch) not in TTFont(r["_path"]).getBestCmap()]
        out.append("missing pack symbols: " + " ".join(miss))
    if "x_height_em" in r and r["x_height_em"] and r["x_height_em"] < 0.45:
        out.append("small x-height: needs a larger size for legal text")
    return out


if __name__ == "__main__":
    paths = [a for a in sys.argv[1:] if not a.startswith("--")]
    rows = []
    for p in paths:
        r = check(p); r["_path"] = p; r["verdict"] = verdict(r); rows.append(r)
    for r in rows:
        r.pop("_path")
    if "--json" in sys.argv:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        for r in rows:
            print(f"\n{r['family']} {r['style']}  ({r['file']})  v{r['version']}")
            for k, m in r["missing"].items():
                if m:
                    print(f"  missing in {k}: {m}")
            print(f"  licence: {r['licence']}")
            print(f"  embedding: {r['embedding']}")
            for k, v in r["coverage"].items():
                print(f"  {k:38} {v:>4.0%}")
            print(f"  arabic shaping features: {', '.join(r['arabic_shaping']) or 'none'} | kerning: {r['kerning']} | marks: {r['mark_positioning']}")
            print(f"  x-height {r['x_height_em']} em  ->  1.2 mm needs {r.get('min_pt_for_1.2mm_xheight')} pt, 0.9 mm needs {r.get('min_pt_for_0.9mm_xheight')} pt")
            print("  verdict:", "; ".join(r["verdict"]) or "no flags")
