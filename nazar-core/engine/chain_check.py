#!/usr/bin/env python3
"""
nazar-core/engine/chain_check.py: run the kit's engines in order on a folder of finished slides.

colour (contrast of the text and of the accent on the ground)
-> language (share of Hindustani function words in the copy, Roman or script)
-> layout (alignment and structure) -> copy lint (stock phrases, triads, em-dashes)
-> pattern score (size, ground, palette, accent against a measured pattern).
One line per slide. It judges what can be measured; it doesn't judge whether a piece is good.

    python chain_check.py slides_folder copy.json pattern.json
copy.json: {"slide1.png": "all the text on slide 1", ...}     pattern.json: from score_pattern.py --build
"""
import glob, json, os, sys
import numpy as np
from PIL import Image
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
for p in ("nazar-colour/engine", "nazar-voiceprint/engine", "nazar-social/engine"):
    sys.path.insert(0, os.path.join(ROOT, p))
import palette_check as pc, analyze, layout, social_lint, score_pattern  # noqa: E402

if len(sys.argv) < 4 or sys.argv[1] in ('-h', '--help'):
    sys.exit(__doc__)
folder, copyf, patf = [os.path.abspath(a) for a in sys.argv[1:4]]
for f_ in (copyf, patf):
    if not os.path.isfile(f_):
        sys.exit(f'missing file: {f_} (the copy.json is {{"slide.png": "all its text"}}; build pattern.json with score_pattern.py --build)')
copy = json.load(open(copyf)); pat = json.load(open(patf))
def accent_text(im, pat):
    """Contrast of the colour actually used for accent type against the ground right beside it.
    Finds strongly coloured pixels in the accent's hue (darker or lighter variants included), then compares them with
    the ring of ground around them, in three vertical bands because a backdrop gradient changes under the type.
    Returns (worst contrast, accent_hex_used, the ground it was worst on) or None when the slide has no accent type."""
    t = im.resize((300, max(1, int(300 * im.height / im.width))))
    rgb = np.asarray(t, float) / 255.0
    lab = score_pattern.srgb_to_oklab(rgb.reshape(-1, 3)).reshape(t.height, t.width, 3)
    ref = score_pattern.lab_of_hex([pat["accent"]])[0]
    hue = np.arctan2(lab[..., 2], lab[..., 1]); ref_h = np.arctan2(ref[2], ref[1])
    dh = np.abs((hue - ref_h + np.pi) % (2 * np.pi) - np.pi)
    mask = (np.hypot(lab[..., 1], lab[..., 2]) > 0.12) & (dh < np.radians(25))
    if mask.sum() < 40:
        return None
    # accent TYPE is a wide, short line of letters; a mascot or logo in the same blue is a compact blob: keep only text-like lines
    boxes = [b for b in layout.components(layout.dilate_x(mask, 10))
             if (b[2] - b[0]) >= 2.2 * (b[3] - b[1]) and (b[3] - b[1]) < 0.2 * t.height and (b[2] - b[0]) > 0.08 * t.width
             and mask[b[1]:b[3], b[0]:b[2]].mean() < 0.7]     # a solid block (a chat bubble, a pill) is a shape, not type
    keep = np.zeros_like(mask)
    for x0, y0, x1, y1, _ in boxes:
        keep[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
    mask = keep
    if mask.sum() < 40:
        return None
    grown = mask.copy()
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            grown |= np.roll(np.roll(mask, dy, 0), dx, 1)
    inner = mask.copy()
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            inner |= np.roll(np.roll(mask, dy, 0), dx, 1)
    ring = grown & ~inner
    ys, xs = np.where(mask); y0, y1 = ys.min(), ys.max() + 1
    best, used, worst_ground, worst_acc = 99.0, np.median(rgb[mask], 0), None, None
    bands = []
    for k in range(3):
        a, b = y0 + (y1 - y0) * k // 3, y0 + (y1 - y0) * (k + 1) // 3
        m, r = mask[a:b], ring[a:b]
        if m.sum() < 20 or r.sum() < 20:
            continue
        g = np.median(rgb[a:b][r], 0); cr = pc.contrast(np.median(rgb[a:b][m], 0), g)
        bands.append((round(100 * a / t.height), round(100 * b / t.height), round(cr, 1)))
        if cr < best:
            best, worst_ground, worst_acc = cr, g, np.median(rgb[a:b][m], 0)
    return (best, pc.hexof(worst_acc), worst_ground * 255, bands) if best < 99 else None


def suggest_accent(acc_hex, ground_rgb, target=3.15):
    """Same hue and chroma, lower lightness, until the accent reaches `target`:1 on this ground. A suggestion for
    NEW type only: a client's logo and supplied artwork are never recoloured."""
    lab = pc.oklab(np.array([int(acc_hex[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0)
    for dl in np.arange(0, 0.5, 0.01):
        rgb = np.clip(pc.from_oklab(np.array([lab[0] - dl, lab[1], lab[2]])), 0, 1)
        if pc.contrast(rgb, ground_rgb / 255.0) >= target:
            return pc.hexof(rgb)
    return None


hexrgb=lambda h:[int(h[i:i+2],16) for i in (1,3,5)]
out=[]
refs={"grounds":score_pattern.lab_of_hex(pat["grounds"]),"accent":score_pattern.lab_of_hex([pat["accent"]]),"swatches":score_pattern.lab_of_hex(pat["swatches"]+pat.get("asset_swatches",[])+pat["grounds"]+[pat["accent"]])}
for f in sorted(glob.glob(folder + '/*.png')):
    name=os.path.basename(f); im=Image.open(f).convert('RGB'); text=copy.get(name,'')
    if not text: print(f'warning: no text for {name} in copy.json, language and lint are empty', file=sys.stderr)
    a=np.asarray(im.resize((64,64)),float)
    band=np.concatenate([a[:3].reshape(-1,3),a[-3:].reshape(-1,3)])  # top and bottom bands
    top=np.median(a[:3].reshape(-1,3),0); bot=np.median(a[-3:].reshape(-1,3),0)
    # 1 colour: smallest contrast between the page's darkest/lightest ink and the ground at the headline height
    mid=np.median(a[16:30,:6].reshape(-1,3),0)                 # ground beside the headline
    ink=np.asarray(im.resize((256,256)),float).reshape(-1,3)
    dark=ink[ink.sum(1).argmin()]; light=ink[ink.sum(1).argmax()]
    cr_text=max(pc.contrast(dark/255,mid/255),pc.contrast(light/255,mid/255))
    at = accent_text(im, pat)
    cr_acc = at[0] if at else None
    # 2 language
    toks=analyze.tokenize(text); hi=analyze.hi_ur_profile(toks) if toks else {}
    r_share=hi.get('share_of_text_matched') or 0
    # 3 layout
    lay=layout.analyse(im.resize((1080,int(1080*im.height/im.width))))
    # 4 lint + 5 score
    lint=social_lint.lint(text) if text else {"hits":[]}
    sc=score_pattern.score(f,pat,refs)
    sug = suggest_accent(at[1], at[2]) if at and cr_acc < 3.0 else None
    out.append({"file":name,"suggest":sug,"size":list(im.size),"text_contrast":round(cr_text,1),"accent_on_ground":round(cr_acc,1) if cr_acc else None,"accent_used":at[1] if at else None,"accent_bands":at[3] if at else None,"nonlinted_share":r_share,
                "roman_urdu_share":hi.get("share_of_text_matched"),"words":len(toks),
                "layout":layout.reading(lay)[:2] if lay else None,"lint":[h[1] for h in lint["hits"]],
                "score":sc["score"],"checks":sc["checks"]})
if "--json" in sys.argv:
    print(json.dumps(out, indent=1))
else:
    for r in out:
        fails = [k for k, v in r["checks"].items() if not v]
        acc = r["accent_on_ground"]
        print(f"{r['file']}  {r['size'][0]}x{r['size'][1]}  score {r['score']:.1f}" + (f"  FAILS: {', '.join(fails)}" if fails else "  all pattern checks pass"))
        print(f"   text {r['text_contrast']}:1 {'ok' if r['text_contrast'] >= 4.5 else 'LOW'} | accent type {r.get('accent_used')} on its ground {acc}:1 "
              + ("no accent type on this slide" if acc is None else "ok for any size" if acc >= 4.5 else "large type only (24px+, or 18.7px bold)" if acc >= 3 else "FAILS: below 3:1, even large type. Do NOT recolour the brand accent: move this line to where the ground is darker (see the bands below), or set it in the brand's ink"))
        if r.get('accent_bands') and acc is not None and acc < 4.5:
            bb = r['accent_bands']; best = max(bb, key=lambda t_: t_[2])
            print('   accent type by height: ' + ', '.join(f'{a_}-{b_}%: {v}:1' for a_, b_, v in bb) + f'  (best: {best[0]}-{best[1]}% of the height at {best[2]}:1; move the line there, or set it in the brand ink colour; never recolour the accent)')
        print(f"   Hindustani words {r['roman_urdu_share']} | words {r['words']} | lint {r['lint'] or 'clean'}{' (English-only: about ' + format(r['nonlinted_share'], '.0%') + ' of the words are Hindustani and were not linted)' if (r.get('nonlinted_share') or 0) > 0.1 else ''} | layout {r['layout']}")
