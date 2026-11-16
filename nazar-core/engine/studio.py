#!/usr/bin/env python3
"""
nazar-core/engine/studio.py: the fast path. Two commands cover a brand-asset job (social slides, posts, banners).

  learn   measure a folder of the person's finished pieces and write the pattern:
              python studio.py learn train_folder out_folder [exact_asset_files...]
          writes out_folder/pattern.json, prompt.md and contact sheets, and prints: the measured habits
          (format, grounds, palette, accent, layout), the held-in score, the archive's own voice (handle, length, language mix, recurring
          words, sample lines, read by OCR) and the prompt block to work from, with a reminder to look at the contact sheet for devices.
  nearest for ONE brief, find the archive's closest real pieces and their measured geometry, to adapt instead of inventing:
              python studio.py nearest out_folder "verified student: one ID check, no fake codes" [k]
  devices record the archive's devices after looking at the sheets (one command, no file editing):
              python studio.py devices out_folder "chat bubble; translate card; mascot with phone; outline stars"
  check   check finished slides against the pattern, in one pass (it also writes compare_*.jpg: each slide beside its closest real piece, for a craft pass):
              python studio.py check slides_folder copy.json pattern.json [sheet.jpg]
          prints per slide: pattern score, contrast of text and accent type on their own ground (with a darker
          suggestion for NEW type only), language, copy lint, and the QA measurements (edges, margins, gaps,
          small text); writes the QA sheet (full size, squint, phone size). If copy.json does not exist it is created by
          reading the text on the slides (read_text.py: macOS Vision, or tesseract). Then look at the sheet.
It runs the engines in nazar-voiceprint, nazar-core and nazar-colour; it adds no judgement of its own.
One call each replaces about ten, so a job reads less and calls less. `learn` also writes devices.md (fill it in after looking at the
contact sheets) and `check` asks for it: the numbers cannot see the brand's recurring devices. Everything else (concept, copy, the font
question via nazar-type/engine/font_match.py) is still yours.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PY = sys.executable
run = lambda args: subprocess.run([PY, *args], capture_output=True, text=True)


def contact_sheets(train, out):
    """Two or more contact sheets of the archive: the numbers can't see recurring devices, a look at the sheet can."""
    from PIL import Image
    fs = sorted(f for f in os.listdir(train) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")))
    paths = []
    for k in range(0, len(fs), 14):
        sh = Image.new("RGB", (1400, 1200), "white")
        for j, f in enumerate(fs[k:k + 14]):
            im = Image.open(os.path.join(train, f)).convert("RGB"); im.thumbnail((190, 238))
            sh.paste(im, ((j % 7) * 200, (j // 7) * 300))
        path = os.path.join(out, f"contact_{k // 14 + 1}.jpg"); sh.save(path, quality=88); paths.append(path)
    return paths


def voice(train, out):
    """Read the archive's own copy (OCR) so new copy imitates its voice: the handle, the length, the language mix, the words that recur."""
    import collections
    import re
    cj = os.path.join(out, "train_copy.json")
    r = run([f"{ROOT}/nazar-core/engine/read_text.py", train, cj])
    if r.returncode or not os.path.isfile(cj):
        return "VOICE: the slide text could not be read (" + ((r.stderr or r.stdout).strip().splitlines() or ["no OCR"])[-1][:90] + "). Ask for the captions and slide copy as text."
    sys.path.insert(0, f"{ROOT}/nazar-voiceprint/engine")
    import analyze
    texts = list(json.load(open(cj)).values())
    handles = collections.Counter(h.lower().rstrip(".") for t in texts for h in set(re.findall(r"@[\w.]+", t)))
    words = [re.findall(r"[a-z']+", t.lower()) for t in texts]
    per = sorted(len(w) for w in words)[len(words) // 2]
    flat = [w for ws in words for w in ws]
    hi = analyze.hi_ur_profile(flat).get("share_of_text_matched") if flat else 0
    stop = set("the and for you your are with that this have from what they will not but all can our was has its who how why".split())
    common = [w for w, c in collections.Counter(w for ws in words for w in set(ws) if len(w) > 3 and w not in stop).most_common(14)]
    samples = [t[:80] for t in sorted(texts, key=len) if 3 <= len(t.split()) <= 14][:6]
    lines = ["VOICE (read from your pieces by OCR, a first draft: check it)",
             f"  Handle seen on the pieces: {', '.join(f'{h} (in {n})' for h, n in handles.most_common(3)) or 'none found'}. Use it, not a placeholder.",
             f"  About {per} words per piece (median). Hindustani function words: {hi:.0%} of the words, so this is the language mix to write in.",
             f"  Words that recur across pieces: {', '.join(common)}",
             "  Real lines from the archive (match the voice, never copy the words): " + " | ".join(samples)]
    return "\n".join(lines)


def learn(train, out, assets):
    os.makedirs(out, exist_ok=True)
    pj = os.path.join(out, "pattern.json")
    json.dump({"train": train}, open(os.path.join(out, "learn.json"), "w"))
    print("learn: measuring the archive (about 40 s), then reading its text (about 40 s)...", flush=True)
    print(run([f"{ROOT}/nazar-voiceprint/engine/portfolio.py", train]).stdout.strip(), flush=True)
    r = run([f"{ROOT}/nazar-voiceprint/engine/score_pattern.py", "--build", train, pj, *assets])
    if r.returncode:
        sys.exit(r.stderr)
    print("\nHeld-in score:", run([f"{ROOT}/nazar-voiceprint/engine/score_pattern.py", pj, train]).stdout.strip())
    block = run([f"{ROOT}/nazar-voiceprint/engine/score_pattern.py", "--prompt", pj]).stdout.strip()
    open(os.path.join(out, "prompt.md"), "w").write(block + "\n")
    v = voice(train, out)
    sheets = contact_sheets(train, out)
    block += ("\nVARIETY: blind judges named every generated slide as generated because the set was too tidy and formulaic (the same polished layout, mascot and props "
              "every time). Real work is blunter, messier and more varied. Vary layout, density and device across the set, include at least one plain or text-led slide, "
              "never reuse one template, and let some slides be rougher than others. For EACH brief run `studio.py nearest <out> \"<the brief>\"`: real designers adapt compositions from their own archive, so rebuild the closest real piece's ground, headline scale, position and device with your copy instead of inventing a layout.")
    sys.path.insert(0, f"{ROOT}/nazar-voiceprint/engine")
    import devices
    _, _n, dlines = devices.write(train, out)      # writes devices_sheet.jpg and devices.txt (about 4 s)
    print("\n" + "\n".join(dlines[:8]) + f"\nLook at {out}/devices_sheet.jpg and name each device in devices.md (the sheet is candidates, not a verdict).", flush=True)
    dev = os.path.join(out, "devices.md")
    if not os.path.exists(dev):
        open(dev, "w").write("# Devices and visual vocabulary that recur in 3 or more of the archive's pieces\n"
                             "<!-- Fill this in AFTER you look at the contact sheets. One line each: name - how many pieces - how it is drawn.\n"
                             "     Think: mascot or character, stickers and doodles (stars, arrows), cards and tickets, chat bubbles or UI, charts, badges, partner logos, texture. -->\n")
    block += "\n" + v + f"\nLOOK FIRST: open the contact sheet(s) {', '.join(sheets)} and fill in {dev} (the devices that recur in 3 or more pieces and how the archive draws them) before you make anything. The numbers cannot see them, and slides that skip them read plainer than the archive. `check` will ask for that file."
    open(os.path.join(out, "prompt.md"), "w").write(block + "\n")
    print("\nPrompt block (also in prompt.md):\n" + block)
    print(f"\npattern.json: {pj}")


def devices_note(pattern):
    dev = os.path.join(os.path.dirname(pattern), "devices.md")
    if not os.path.isfile(dev):
        return "WARNING: no devices.md next to the pattern. Run `learn`, look at devices_sheet.jpg and the contact sheets and list the archive's recurring devices (mascot, stickers, cards, chat or UI, charts, badges...) before judging these slides: pieces that skip them read plainer than the archive.\n"
    lines = [ln for ln in open(dev).read().splitlines() if ln.strip() and not ln.startswith(("#", "<!--", "     Think"))]
    if len(lines) < 2:
        return "WARNING: devices.md is still empty. Look at the contact sheets and list the archive's recurring devices; then compare each slide with that list. Pieces that skip them read plainer than the archive.\n"
    return "Archive devices (from devices.md): " + " | ".join(l.strip("- ").strip()[:60] for l in lines[:8]) + "\n=> Does each slide use the habitual ones, drawn the archive's way?\n"


def compare(slides, pattern, outdir):
    """The craft pass: each slide beside its structurally closest real piece, so the differences (density, scale, devices, roughness) can be SEEN
    and fixed. A no-skill run that iterated like this looked closer to the brand in blind judging."""
    sys.path.insert(0, f"{ROOT}/nazar-voiceprint/engine")
    import numpy as np
    import score_pattern
    from PIL import Image, ImageDraw
    pat = json.load(open(pattern))
    typ = pat.get("typ") or {}
    lj = os.path.join(os.path.dirname(pattern), "learn.json")
    if not typ.get("names") or not os.path.isfile(lj):
        return "compare: needs a pattern from `learn` (with at least 8 flat pieces)."
    train = json.load(open(lj))["train"]
    lab = score_pattern.lab_of_hex([pat["accent"]])
    Z = np.array(typ["z"]); mu, sd = np.array(typ["mu"]), np.array(typ["sd"])
    os.makedirs(outdir, exist_ok=True)
    outs = []
    for f in sorted(os.listdir(slides)):
        if not f.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        im = Image.open(os.path.join(slides, f)).convert("RGB")
        v = score_pattern.typ_vector(im, lab)
        if v is None:
            continue
        j = int(np.argmin(np.linalg.norm(Z - (np.array(v) - mu) / sd, axis=1)))
        ref = Image.open(os.path.join(train, typ["names"][j])).convert("RGB")
        a, b = im.copy(), ref.copy(); a.thumbnail((520, 650)); b.thumbnail((520, 650))
        sh = Image.new("RGB", (1080, 700), "white"); sh.paste(a, (10, 40)); sh.paste(b, (550, 40))
        d = ImageDraw.Draw(sh); d.text((12, 8), f"YOURS: {f}", fill=(0, 0, 0)); d.text((552, 8), f"CLOSEST REAL: {typ['names'][j]}", fill=(0, 0, 0))
        p = os.path.join(outdir, f"compare_{os.path.splitext(f)[0]}.jpg"); sh.save(p, quality=88); outs.append(p)
    return ("CRAFT PASS: look at each compare_*.jpg in " + outdir + " (your slide left, its closest real piece right). For each, name the 3 biggest differences in "
            "density, scale, devices and roughness, fix the two biggest, then look again. Real work is blunter and messier than a tidy set.\n  " + "\n  ".join(outs))


def check(slides, copy, pattern, sheet):
    print(devices_note(pattern))
    if not os.path.isfile(copy):      # no copy.json yet: read the text on the slides (a first draft: check it)
        r = run([f"{ROOT}/nazar-core/engine/read_text.py", slides, copy])
        print((r.stdout or r.stderr).strip() + "\n")
        if r.returncode:
            sys.exit("copy.json is missing and slide text could not be read: write it by hand as {\"slide.png\": \"all its text\"}")
    print(run([f"{ROOT}/nazar-core/engine/chain_check.py", slides, copy, pattern]).stdout.strip())
    print("\nQA measurements:")
    r = run([f"{ROOT}/nazar-core/engine/qa_views.py", slides, sheet])
    print(r.stdout.strip() or r.stderr.strip())
    print("\n" + compare(slides, pattern, os.path.join(os.path.dirname(os.path.abspath(sheet)), "compare")))


def nearest(out, brief, k=3):
    """For one brief, the archive's closest real pieces and the geometry to adapt: real designers reuse their own compositions,
    and blind judges named invented layouts as generated ("too tidy, formulaic")."""
    import re
    sys.path.insert(0, f"{ROOT}/nazar-voiceprint/engine")
    import score_pattern
    from PIL import Image, ImageDraw, ImageFont
    meta = json.load(open(os.path.join(out, "learn.json")))
    train = meta["train"]
    pat = json.load(open(os.path.join(out, "pattern.json")))
    copy = json.load(open(os.path.join(out, "train_copy.json"))) if os.path.isfile(os.path.join(out, "train_copy.json")) else {}
    words = lambda t: {w[:5] for w in re.findall(r"[a-z]{3,}", t.lower())}
    hints = {"chat": ["chat", "message", "dm", "bubble", "reply"], "card": ["card", "verified", "id", "means", "buzzword"], "receipt": ["receipt", "price", "paying", "full"],
             "event": ["event", "community", "pop"], "launch": ["app", "launch", "soon", "waitlist", "store"], "partner": ["partner", "brand", "logos", "onboard"]}
    bw = words(brief)
    lab = score_pattern.lab_of_hex([pat["accent"]])
    scored = []
    for f in sorted(os.listdir(train)):
        if not f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue
        im = Image.open(os.path.join(train, f)).convert("RGB")
        if score_pattern.is_photo(im):
            continue
        overlap = len(bw & words(copy.get(f, "")))
        feat = score_pattern.features(im, lab)
        if feat:
            scored.append((overlap, f, im, feat))
    scored.sort(key=lambda r: -r[0])
    top = scored[:k]
    W, Hh = pat["format"]
    lines = [f"Closest real pieces to: \"{brief}\"  (adapt the composition; do not invent a layout)"]
    sheet = Image.new("RGB", (k * 330, 440), "white")
    for i, (ov, f, im, feat) in enumerate(top):
        g = np_mean_lum(im)
        lines.append(f"  {i + 1}. {f}  [{'light' if g >= 110 else 'dark'} ground, text overlap {ov}]  text: {copy.get(f, '')[:70]!r}")
        lines.append(f"     recipe at {W}x{Hh}: headline cap height ~{feat['headline_h'] * Hh:.0f}px, subline ~{feat['subline_h'] * Hh:.0f}px, {feat['n_lines']:.0f} text lines, "
                     f"text starts x~{feat['left_x'] * W:.0f}px, first line y~{feat['top_y'] * Hh:.0f}px, widest line {feat['widest'] * 100:.0f}% of the width, accent {feat['accent_share'] * 100:.1f}% of the area")
        t = im.copy(); t.thumbnail((320, 400)); sheet.paste(t, (i * 330 + 5, 30))
        ImageDraw.Draw(sheet).text((i * 330 + 8, 6), f"{i + 1}. {f[:28]}", fill=(0, 0, 0))
    path = os.path.join(out, "nearest.jpg"); sheet.save(path, quality=88)
    lines.append("Careful: reference pieces carry their own dates, numbers and claims. Adapt the composition, never the facts or the words.")
    lines.append(f"Look at {path}, then rebuild the same ground, headline scale, position, device and spacing with your own copy, and give it the archive's roughness.")
    print("\n".join(lines))


def np_mean_lum(im):
    import numpy as np
    a = np.asarray(im.resize((64, 64)), float)
    band = np.concatenate([a[:4].reshape(-1, 3), a[-4:].reshape(-1, 3), a[:, :4].reshape(-1, 3), a[:, -4:].reshape(-1, 3)])
    return float(np.median(band, 0) @ [0.2126, 0.7152, 0.0722])


def set_devices(out, listing):
    """studio.py devices <out_folder> "chat bubble; translate card; mascot with phone; outline stars": records what you saw on the contact sheets."""
    items = [x.strip() for x in listing.replace("\n", ";").split(";") if x.strip()]
    path = os.path.join(out, "devices.md")
    open(path, "w").write("# Devices and visual vocabulary that recur in 3 or more of the archive's pieces\n" + "\n".join(f"- {x}" for x in items) + "\n")
    print(f"{path}: {len(items)} devices recorded")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if a[0] == "devices" and len(a) >= 3:
        set_devices(os.path.abspath(a[1]), " ; ".join(a[2:]))
    elif a[0] == "nearest" and len(a) >= 3:
        nearest(os.path.abspath(a[1]), a[2], int(a[3]) if len(a) > 3 else 3)
    elif a[0] == "learn" and len(a) >= 3:
        learn(os.path.abspath(a[1]), os.path.abspath(a[2]), [os.path.abspath(x) for x in a[3:]])
    elif a[0] == "check" and len(a) >= 4:
        sheet = os.path.abspath(a[4]) if len(a) > 4 else os.path.join(os.path.abspath(a[1]), "qa_sheet.jpg")
        check(os.path.abspath(a[1]), os.path.abspath(a[2]), os.path.abspath(a[3]), sheet)
    else:
        sys.exit(__doc__)
