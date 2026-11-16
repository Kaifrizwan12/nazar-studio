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

folder, copyf, patf = sys.argv[1], sys.argv[2], sys.argv[3]
copy = json.load(open(copyf)); pat = json.load(open(patf))
def suggest_accent(acc_hex, ground_rgb, target=3.0):
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
    a=np.asarray(im.resize((64,64)),float)
    band=np.concatenate([a[:3].reshape(-1,3),a[-3:].reshape(-1,3)])  # top and bottom bands
    top=np.median(a[:3].reshape(-1,3),0); bot=np.median(a[-3:].reshape(-1,3),0)
    # 1 colour: smallest contrast between the page's darkest/lightest ink and the ground at the headline height
    mid=np.median(a[16:30,:6].reshape(-1,3),0)                 # ground beside the headline
    ink=np.asarray(im.resize((256,256)),float).reshape(-1,3)
    dark=ink[ink.sum(1).argmin()]; light=ink[ink.sum(1).argmax()]
    cr_text=max(pc.contrast(dark/255,mid/255),pc.contrast(light/255,mid/255))
    cr_acc=pc.contrast(np.array(hexrgb(pat['accent']))/255,mid/255)
    # 2 language
    toks=analyze.tokenize(text); hi=analyze.hi_ur_profile(toks) if toks else {}
    # 3 layout
    lay=layout.analyse(im.resize((1080,int(1080*im.height/im.width))))
    # 4 lint + 5 score
    lint=social_lint.lint(text) if text else {"hits":[]}
    sc=score_pattern.score(f,pat,refs)
    sug = suggest_accent(pat["accent"], mid) if cr_acc < 3.0 else None
    out.append({"file":name,"suggest":sug,"size":list(im.size),"text_contrast":round(cr_text,1),"accent_on_ground":round(cr_acc,1),
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
        print(f"   text {r['text_contrast']}:1 {'ok' if r['text_contrast'] >= 4.5 else 'LOW'} | accent on ground {acc}:1 "
              + ("ok for any size" if acc >= 4.5 else "large type only (24px+, or 18.7px bold)" if acc >= 3 else f"FAILS: below 3:1, even large type. For new type, {r.get('suggest') or 'a darker accent'} reaches 3:1 on this ground"))
        print(f"   Hindustani words {r['roman_urdu_share']} | words {r['words']} | lint {r['lint'] or 'clean'} | layout {r['layout']}")
