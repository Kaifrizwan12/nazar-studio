"""Handover packager: one JSON manifest -> clean, versioned delivery folders, checksums, README, covers and zips.

    python handover.py build  manifest.json [--dry-run] [--target client] [--allow-stale] [--no-zip]
    python handover.py mark   manifest.json            # touch the build marker at the START of a render run
    python handover.py diff   OLD NEW                  # two releases (folder, .zip or SHA256SUMS.txt): what changed
    python handover.py --selftest                      # temp-dir self-check, no network

    from handover import build, release_diff
    report = build("manifest.json", dry_run=True)      # dict: per target added / changed / parked / same / warnings

What it does, per target (client, portfolio, press, social; any name you like):
  - copies each source to a human-readable, numbered name rendered from a template
    ("{group} {label} - {line|cap} {view}" -> "02 Fruit pouch 100 g - Mango front.png"), sanitised for Windows,
    macOS and Linux (reserved characters and device names, trailing dots/spaces, NFC, name and path length);
  - fails loudly on a missing source, a duplicate name, or a stale source (older than one of its declared inputs,
    or older than the build marker, i.e. not re-rendered in the last run);
  - makes platform covers (Behance 1616x1264 + 808x632, Dribbble 1600x1200, site 1200x630, social 1080x1350 ...);
  - writes README.txt (what is inside, formats, colour, fonts and licences, concept vs press-ready, AI disclosure)
    and SHA256SUMS.txt (sha256sum -c compatible);
  - NEVER deletes: a changed or removed file is moved to <release_root>/_parked/<timestamp>/<folder>/ first;
  - zips the folder (deterministic, UTF-8 name flag set by zipfile for non-ASCII names, media stored, text deflated)
    and reports sizes;
  - dry run prints the diff (added / changed / parked) and the portfolio panels to re-upload, touching nothing.

Manifest shape: see ../examples/handover_manifest.json and ../references/handover.md. Plain stdlib + Pillow
(Pillow only for covers and image facts). English only; no brand is hard-coded here.
"""
import argparse, fnmatch, glob, hashlib, io, itertools, json, os, re, shutil, sys, tempfile, unicodedata, zipfile
from datetime import date, datetime

SUMS, README = "SHA256SUMS.txt", "README.txt"

# Platform specs, checked 2026-11-21 (sources in ../references/research_handover.md). Re-check before a launch.
PLATFORMS = {
    "behance": {"covers": [(1616, 1264), (808, 632)], "cover_min": (808, 632), "image_max_w": 2800,
                "image_warn_bytes": 10_000_000, "image_max_bytes": 50_000_000, "cover_no_gif": True,
                "note": "Panels show 1400 px wide, up to 2800 px in the lightbox; JPEG/PNG 10 MB or less; GIF inside the "
                        "project only; embed films from a video host for full width. Cover at least 808x632 (shows 202x158)."},
    "dribbble": {"covers": [(1600, 1200)], "image_min_w": 1600, "image_max_bytes": 10_000_000,
                 "video_max_bytes": 20_000_000,
                 "note": "Shots at least 1600 px wide (1600x1200, 4:3, crops best as a thumbnail); PNG/JPG/GIF 10 MB; "
                         "MP4/MOV 20 MB."},
    "site": {"covers": [(1200, 630)], "note": "1200x630 share image (Open Graph convention)."},
    "social": {"covers": [(1080, 1350), (1080, 1080)], "note": "4:5 and 1:1 feed covers."},
}
KIND_TITLE = {"client": "Client files", "portfolio": "Portfolio upload", "press": "Press / printer pack",
              "social": "Social pack"}
RESERVED_CHARS = '<>:"/\\|?*'
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {p + d for p in ("COM", "LPT") for d in "123456789¹²³"}
STORED = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov", ".m4v", ".zip", ".mp3", ".aac", ".heic", ".avif"}
FONT_EXT = {".ttf", ".otf", ".woff", ".woff2"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff", ".bmp"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm"}
FORMAT_NOTES = {
    ".png": "PNG: lossless; transparent where the product is cut out. Screens, slides, web.",
    ".jpg": "JPG: compressed photo; no transparency. Screens, email, social.",
    ".jpeg": "JPG: compressed photo; no transparency. Screens, email, social.",
    ".gif": "GIF: short silent loop for web pages and portfolio modules (not covers).",
    ".pdf": "PDF: opens anywhere; press PDFs carry trim and bleed boxes (see the press notes).",
    ".svg": "SVG: vector for web and editing; scales without loss.",
    ".mp4": "MP4: video for phones, social and slides.",
    ".mov": "MOV: video master.",
    ".txt": "TXT: plain notes.",
}
DEFAULT_AI_LINE = ("Some images contain AI-generated background plates (empty scenes only), made with the client's written "
                   "approval; every product shown is the real artwork render. Those files are marked [AI plate].")


class HandoverError(Exception):
    """Raised with every problem found, so one run lists them all (missing, stale, duplicate, too long...)."""
    def __init__(self, problems):
        self.problems = list(problems); super().__init__("\n".join(self.problems))


# ---------------------------------------------------------------- names
_TPL = re.compile(r"\{(\w+)((?:\|\w+)*)\}")
FILTERS = {"cap": lambda s: s[:1].upper() + s[1:], "title": str.title, "upper": str.upper, "lower": str.lower,
           "words": lambda s: re.sub(r"[-_]+", " ", s).strip()}


def render(tpl, ctx, esc=False):
    """'{line|words|cap}' -> value with filters applied left to right. An unknown key fails loudly.
    esc=True (file names): a '/' or '\' inside a VALUE becomes '-', so only the template's own '/' makes a sub-folder."""
    def one(m):
        key = m.group(1)
        if key not in ctx: raise KeyError(f"template {tpl!r} uses {{{key}}}, which is not defined")
        v = str(ctx[key])
        for f in filter(None, m.group(2).split("|")):
            if f not in FILTERS: raise KeyError(f"template {tpl!r}: unknown filter |{f}")
            v = FILTERS[f](v)
        return v.replace("/", "-").replace("\\", "-") if esc else v
    return _TPL.sub(one, tpl)


def sanitize(name, naming="human", max_len=120):
    """One path component, safe on Windows, macOS and Linux.
    human: keeps spaces and accents (NFC), swaps reserved characters for '-'.  safe: ASCII letters, digits, . _ - only."""
    s = unicodedata.normalize("NFC", str(name))
    s = "".join(ch for ch in s if ord(ch) >= 32 and ch != "\x7f")
    s = s.replace(":", " -") if naming == "human" else s
    s = "".join("-" if ch in RESERVED_CHARS else ch for ch in s)
    if naming == "safe":
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
        s = re.sub(r"\s+", "_", s); s = re.sub(r"[^A-Za-z0-9._-]", "-", s)
        s = re.sub(r"([-_.])\1+", r"\1", s).strip("-_")
    s = re.sub(r"\s+", " ", s).strip().rstrip(". ")
    stem, ext = os.path.splitext(s)
    if len(ext) > 10 or " " in ext: stem, ext = s, ""
    if len(s) > max_len:
        stem = stem[: max(1, max_len - len(ext))].rstrip(". -_"); s = stem + ext
    if stem.split(".")[0].upper() in RESERVED_NAMES: s = "_" + s
    return s or "_"


def panel_no(rel):
    """The number a person uses to point at a file: a leading '02'/'09a', else the last digit run ('..._07')."""
    stem = os.path.splitext(os.path.basename(rel))[0]
    m = re.match(r"(\d+[a-z]?)(?![0-9A-Za-z])", stem) or re.match(r"(\d+)", stem)
    if m: return m.group(1)
    d = re.findall(r"\d+", stem); return d[-1] if d else None


# ---------------------------------------------------------------- facts
_SHA = {}


def sha256_file(path):
    st = os.stat(path); key = (os.path.abspath(path), st.st_size, st.st_mtime_ns)
    if key not in _SHA:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
        _SHA[key] = h.hexdigest()
    return _SHA[key]


def sha256_bytes(b): return hashlib.sha256(b).hexdigest()


def image_facts(path_or_bytes):
    """(width, height, 'RGBA sRGB IEC61966-2.1') or None. Pillow is optional for everything but covers."""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(path_or_bytes) if isinstance(path_or_bytes, bytes) else path_or_bytes)
        prof = ""
        if im.info.get("icc_profile"):
            try:
                from PIL import ImageCms
                prof = ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(im.info["icc_profile"]))).strip()
            except Exception: prof = "embedded ICC"
        return im.width, im.height, (im.mode + (" " + prof if prof else " (no profile: treat as sRGB)"))
    except Exception:
        return None


def pdf_facts(path):
    """'PDF/X-4' if the file declares a PDF/X version, else 'PDF (not PDF/X)'. Reads the head and tail only."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            data = f.read(4_000_000)
            if size > 8_000_000: f.seek(size - 4_000_000); data += f.read()
        m = re.search(rb"GTS_PDFXVersion\s*\(([^)]*)\)", data) or re.search(rb"pdfxid:GTS_PDFXVersion>([^<]*)<", data)
        return m.group(1).decode("latin-1").strip() if m else "PDF (not PDF/X)"
    except OSError:
        return "PDF"


def human_size(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1000 or u == "GB": return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1000


# ---------------------------------------------------------------- manifest
def load_manifest(m):
    """dict or path -> (manifest, base_dir). Validates the shape; every problem is listed."""
    base = os.path.dirname(os.path.abspath(m)) if isinstance(m, str) else os.getcwd()
    if isinstance(m, str):
        try:
            with open(m, encoding="utf-8") as f: m = json.load(f)
        except (OSError, ValueError) as e: raise HandoverError([f"manifest {os.path.basename(base and m)}: {e}"])
    probs = []
    for k in ("project", "version", "targets", "items"):
        if k not in m: probs.append(f"manifest: missing key '{k}'")
    for name, t in (m.get("targets") or {}).items():
        if t.get("platform") and t["platform"] not in PLATFORMS:
            probs.append(f"target {name}: unknown platform {t['platform']!r} (known: {', '.join(PLATFORMS)})")
    groups = m.get("groups", {})
    for i, it in enumerate(m.get("items", []), 1):
        if "src" not in it: probs.append(f"item {i}: missing 'src'")
        if "name" not in it and "names" not in it: probs.append(f"item {i}: missing 'name'")
        for t in _as_list(it.get("target", list(m.get("targets", {})))):
            if t not in m.get("targets", {}): probs.append(f"item {i}: unknown target {t!r}")
        if it.get("group") and it["group"] not in groups: probs.append(f"item {i}: unknown group {it['group']!r}")
    if probs: raise HandoverError(probs)
    return m, base


def _as_list(v): return v if isinstance(v, list) else [v]


def base_context(m):
    d = m.get("date") or date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d): raise HandoverError([f"manifest: date {d!r} is not ISO 8601 YYYY-MM-DD"])
    v = f"v{int(m['version']):02d}"
    ctx = {"project": m["project"], "slug": m.get("slug") or sanitize(m["project"], "safe").upper(),
           "version": int(m["version"]), "v": v, "date": d, "stamp": f"{v}_{d}"}
    ctx.update(m.get("vars", {})); return ctx


def expand(m, src_root, only=None):
    """Items -> entries (one per source file per target). Returns (entries, problems, skipped)."""
    ctx0 = base_context(m); groups = m.get("groups", {}); out, probs, skipped = [], [], []
    for i, it in enumerate(m["items"], 1):
        loops = it.get("for", {}); keys = list(loops)
        for row, combo in itertools.product(it.get("rows", [{}]), list(itertools.product(*[loops[k] for k in keys])) if keys else [()]):
            ctx = dict(ctx0)
            if it.get("group"):
                g = groups[it["group"]]; ctx.update(group=g.get("number", ""), label=g.get("label", ""))
            ctx.update(it.get("with", {})); ctx.update(row); ctx.update(zip(keys, combo))
            desc = [f"{k}={v}" for k, v in list(row.items()) + list(zip(keys, combo))]
            tag = f"item {i}" + (f" ({', '.join(desc)})" if desc else "")
            try: pat = render(it["src"], ctx)
            except KeyError as e: probs.append(f"{tag}: {e.args[0]}"); continue
            hits = sorted(h for h in glob.glob(os.path.join(src_root, pat)) if os.path.isfile(h)
                          and not any(fnmatch.fnmatch(os.path.basename(h), x) for x in it.get("exclude", []))
                          and "_parked" not in os.path.relpath(h, src_root).replace("\\", "/").split("/"))
            if not hits:
                (skipped if it.get("optional") else probs).append(f"{tag}: missing source {pat}"); continue
            for k, h in enumerate(hits, 1):
                c = dict(ctx); stem, ext = os.path.splitext(os.path.basename(h))
                c.update(stem=stem, ext=ext.lstrip("."), n=k, nn=f"{k:02d}", nnn=f"{k:03d}")
                if it.get("match"):
                    mm = re.search(it["match"], stem)
                    if not mm: probs.append(f"{tag}: {os.path.basename(h)} does not match {it['match']!r}"); continue
                    c.update(it.get("defaults", {})); c.update({a: b for a, b in mm.groupdict().items() if b})
                for var, spec in it.get("map", {}).items():
                    key = str(c.get(spec["from"], "")); c[var] = spec["values"].get(key, spec.get("default", key))
                for t in _as_list(it.get("target", list(m["targets"]))):
                    if only and t not in only: continue
                    try:
                        name = render(it.get("names", {}).get(t, it.get("name", "")), c, esc=True)
                        inputs = [render(x, c) for x in it.get("inputs", [])]
                    except KeyError as e: probs.append(f"{tag}: {e.args[0]}"); continue
                    out.append({"target": t, "src": os.path.abspath(h), "name": name,
                                "ext": (it.get("ext") or ext).lower(), "inputs": inputs, "static": it.get("static", False),
                                "status": it.get("status", m["targets"][t].get("status", "")), "ai": bool(it.get("ai")),
                                "group": c.get("group", ""), "label": c.get("label", ""), "note": it.get("note", ""),
                                "tag": tag})
    return out, probs, skipped


# ---------------------------------------------------------------- checks
def staleness(entries, src_root, marker):
    """Entries whose source is older than a declared input, or (unless static) older than the build marker."""
    out = []; mk = os.path.getmtime(marker) if marker and os.path.exists(marker) else None
    for e in entries:
        t = os.path.getmtime(e["src"])
        for pat in e["inputs"]:
            for p in glob.glob(os.path.join(src_root, pat)):
                if os.path.getmtime(p) > t + 1e-3:
                    out.append(f"stale: {os.path.relpath(e['src'], src_root)} is older than its input "
                               f"{os.path.relpath(p, src_root)} (re-render it)")
        if mk is not None and not e["static"] and t + 1e-3 < mk:
            out.append(f"stale: {os.path.relpath(e['src'], src_root)} predates the build marker "
                       f"(not re-rendered in the last run; mark it static if it never changes)")
    return sorted(set(out))


def platform_checks(rel, size, ext, facts, spec, is_cover=False):
    warn, err = [], []
    if not spec: return warn, err
    if ext in IMG_EXT:
        if spec.get("image_max_bytes") and size > spec["image_max_bytes"]:
            err.append(f"{rel}: {human_size(size)} is over the platform limit {human_size(spec['image_max_bytes'])}")
        elif spec.get("image_warn_bytes") and size > spec["image_warn_bytes"]:
            warn.append(f"{rel}: {human_size(size)} is over the recommended {human_size(spec['image_warn_bytes'])}")
        if facts and spec.get("image_max_w") and facts[0] > spec["image_max_w"] and not is_cover:
            warn.append(f"{rel}: {facts[0]} px wide; the platform shows at most {spec['image_max_w']} px")
        if facts and spec.get("image_min_w") and facts[0] < spec["image_min_w"] and not is_cover:
            warn.append(f"{rel}: {facts[0]} px wide; the platform wants at least {spec['image_min_w']} px")
    if ext in VIDEO_EXT and spec.get("video_max_bytes") and size > spec["video_max_bytes"]:
        warn.append(f"{rel}: video {human_size(size)} is over {human_size(spec['video_max_bytes'])}; embed it from a video host")
    return warn, err


def make_cover(src, w, h, fmt):
    """Centre-crop to w:h, resize (Lanczos), return bytes. Deterministic for the same source."""
    from PIL import Image
    im = Image.open(src); im = im.convert("RGBA" if fmt == "png" and im.mode in ("RGBA", "LA", "P") else "RGB")
    r = w / h
    if im.width / im.height > r: nw = round(im.height * r); box = ((im.width - nw) // 2, 0, (im.width - nw) // 2 + nw, im.height)
    else: nh = round(im.width / r); box = (0, (im.height - nh) // 2, im.width, (im.height - nh) // 2 + nh)
    im = im.crop(box).resize((w, h), Image.LANCZOS); b = io.BytesIO()
    if fmt == "png": im.save(b, "PNG", optimize=True)
    else: im.convert("RGB").save(b, "JPEG", quality=92, optimize=True)
    return b.getvalue(), (im.width < w)


# ---------------------------------------------------------------- README
def readme_text(m, tname, t, folder, plan, entries_by_rel, ctx):
    H = m.get("handover", {}); kind = t.get("kind", tname); L = []
    total = sum(p["size"] for p in plan.values())
    L += [f"{m['project']} - {t.get('title', KIND_TITLE.get(kind, tname.title()))} - {ctx['v']}, {ctx['date']}",
          f"Prepared by {H.get('studio', 'the studio')}" + (f" ({H['contact']})" if H.get("contact") else "") + ".", ""]
    if t.get("intro") or H.get("intro"): L += [t.get("intro") or H["intro"], ""]
    extra = 1 + (1 if t.get("checksums", True) else 0)
    L += [f"WHAT IS INSIDE ({len(plan) + extra} files including this note" + (f" and {SUMS}" if extra == 2 else "") + f", {human_size(total)})",
          "Files are numbered so they sort in reading order. Open them in name order."]
    by_group = {}
    for rel in sorted(plan):
        e = entries_by_rel.get(rel); key = (e["group"], e["label"]) if e else ("", "Generated")
        by_group.setdefault(key, []).append(rel)
    for (g, lab), rels in sorted(by_group.items(), key=lambda kv: (kv[0][0] == "", kv[0][0], kv[0][1])):
        L.append(""); L.append(f"{g}  {lab}".strip() if (g or lab) else "Other")
        for rel in rels:
            p = plan[rel]; e = entries_by_rel.get(rel); bits = [os.path.splitext(rel)[1].lstrip(".").upper() or "file"]
            if p.get("facts"): bits.append(f"{p['facts'][0]}x{p['facts'][1]} {p['facts'][2]}")
            if p.get("pdfx"): bits[0] = p["pdfx"] if p["pdfx"].startswith("PDF") else "PDF, " + p["pdfx"]
            bits.append(human_size(p["size"]))
            if e and e["status"]: bits.append(e["status"])
            if e and e["ai"]: bits.append("[AI plate]")
            L.append(f"  {rel}  -  {', '.join(bits)}" + (f"  ({e['note']})" if e and e["note"] else ""))
    exts = sorted({os.path.splitext(r)[1].lower() for r in plan} & set(FORMAT_NOTES))
    L += ["", "FILE FORMATS"] + [f"- {FORMAT_NOTES[x]}" for x in exts]
    L += ["", "COLOUR", "- " + (t.get("colour") or H.get("colour") or (
        "Screen files (PNG, JPG, MP4) are sRGB; a file with no embedded profile should be treated as sRGB. "
        "Print colour is set in the press PDFs and governed by the printer's profile and a signed proof."))]
    st = {}
    for rel, e in entries_by_rel.items():
        if e["status"]: st.setdefault(e["status"], []).append(rel)
    L += ["", "STATUS: CONCEPT VS PRESS-READY"]
    if st:
        for s in sorted(st): L.append(f"- {s}: {len(st[s])} file(s)" + (": " + "; ".join(sorted(st[s])[:6]) + (" ..." if len(st[s]) > 6 else "")))
    L.append("- " + H.get("status_note", "Concept files show the design; only files marked press-ready go to a printer, "
                                          "and the converter's dieline and proof replace any concept flat."))
    L += ["", "FONTS AND LICENCES"]
    fonts = H.get("fonts", [])
    if fonts:
        for f in fonts:
            L.append(f"- {f['name']}: {f.get('licence', 'licence not recorded')}; holder: {f.get('holder', 'not recorded')}"
                     + ("; font files included" if f.get("files_included") else "; font files not included (type is outlined or embedded)")
                     + (f"; {f['url']}" if f.get("url") else ""))
    else: L.append("- No fonts recorded. Add them to handover.fonts before sending.")
    if any(os.path.splitext(r)[1].lower() in FONT_EXT for r in plan):
        L.append("- Font files are in this delivery: each one ships with its licence file (SIL OFL requires the notice; "
                 "commercial fonts usually may not be passed on - the client buys their own seat).")
    stock = H.get("stock", [])
    L += ["", "THIRD-PARTY AND STOCK"] + ([f"- {s.get('what')}: {s.get('licence', '')}; holder: {s.get('holder', '')}" for s in stock]
                                          or ["- None: every image is the studio's own work or the client's supplied files."])
    if any(e["ai"] for e in entries_by_rel.values()) or H.get("ai", {}).get("line"):
        ai = H.get("ai", {})
        L += ["", "AI DISCLOSURE", "- " + ai.get("line", DEFAULT_AI_LINE)]
        if ai.get("tools"): L.append(f"- Tools: {ai['tools']}")
        L.append("- Keep this label (and any Content Credentials in the files) wherever these images are published.")
    if kind == "portfolio":
        spec = PLATFORMS.get(t.get("platform", ""), {})
        L += ["", "UPLOAD", "- Upload panels in name order; the 00_COVER file is the project cover (no text, subject central).",
              "- " + spec.get("note", "Check the platform's current specs before upload.")]
    if kind == "press":
        L += ["", "FOR THE PRINTER",
              "- Press PDFs: PDF/X-4 where the file says so; fonts embedded or outlined; trim and bleed boxes set "
              "(bleed as the printer asks, commonly 3 mm); output intent = the printer's profile.",
              "- Ask for a contract proof and sign it before the run; the converter's dieline governs structure."]
    L += ["", "CHECKING THE FILES",
          f"- {SUMS} lists a SHA-256 for every file. Check with: sha256sum -c {SUMS}  (macOS: shasum -a 256 -c {SUMS};",
          "  Windows PowerShell: Get-FileHash <file> -Algorithm SHA256)."]
    if H.get("support"): L += ["", "SUPPORT", "- " + H["support"]]
    for n in H.get("notes", []) + t.get("notes", []): L.append("- " + n)
    return "\n".join(L).rstrip() + "\n"


# ---------------------------------------------------------------- plan / apply
def _walk(folder):
    out = {}
    if os.path.isdir(folder):
        for dp, dn, fn in os.walk(folder):
            for f in fn:
                p = os.path.join(dp, f); out[os.path.relpath(p, folder).replace(os.sep, "/")] = p
    return out


def plan_target(m, base, tname, entries, ctx, release_root):
    """Everything the target folder should hold, as {rel: {kind, src|data, sha, size, facts}}; plus warnings/errors."""
    t = m["targets"][tname]; warn, err = [], []
    naming = t.get("naming", "human" if t.get("kind", tname) == "client" else "safe")
    max_name, max_rel = int(t.get("max_name", 120)), int(t.get("max_rel", 200))
    folder = sanitize(render(t.get("folder", "{slug}_" + tname.upper() + "_{stamp}"), ctx), "safe" if naming == "safe" else "human")
    spec = PLATFORMS.get(t.get("platform", ""), {})
    plan, by_rel = {}, {}
    for e in entries:
        parts = [sanitize(p, naming, max_name) for p in e["name"].replace("\\", "/").split("/") if p.strip()]
        parts[-1] = sanitize(parts[-1] + e["ext"], naming, max_name)
        rel = "/".join(parts)
        if rel.lower() in {r.lower() for r in plan}:
            other = next(r for r in plan if r.lower() == rel.lower())
            err.append(f"{tname}: two sources map to {rel!r}: {plan[other].get('src')} and {e['src']} "
                       f"(names must differ beyond case: Windows and macOS ignore case)"); continue
        size = os.path.getsize(e["src"]); facts = image_facts(e["src"]) if e["ext"] in IMG_EXT else None
        plan[rel] = {"kind": "copy", "src": e["src"], "size": size, "facts": facts,
                     "pdfx": pdf_facts(e["src"]) if e["ext"] == ".pdf" else None}
        by_rel[rel] = e
        w_, e_ = platform_checks(rel, size, e["ext"], facts, spec); warn += w_; err += e_
        if t.get("kind", tname) == "press" and e["ext"] == ".pdf" and not str(plan[rel]["pdfx"]).startswith("PDF/X"):
            warn.append(f"{rel}: not a PDF/X file; ask the printer if they accept it (PDF/X-4 is the safe default)")
    cov = t.get("cover")
    if cov:
        src = os.path.join(base if not cov.get("from_source_root", True) else m["_src_root"], render(cov["src"], ctx))
        if not os.path.isfile(src): err.append(f"{tname}: missing cover source {src}")
        elif spec.get("cover_no_gif") and src.lower().endswith(".gif"): err.append(f"{tname}: a GIF cannot be a cover")
        else:
            sizes = [tuple(s) for s in cov.get("sizes", spec.get("covers", []))]
            names = cov.get("names", [])
            for k, (w, h) in enumerate(sizes):
                fmt = cov.get("format", "auto"); fmt = ("png" if k == 0 else "jpg") if fmt == "auto" else fmt
                facts = image_facts(src)
                if facts and facts[:2] == (w, h) and src.lower().endswith("." + fmt):
                    with open(src, "rb") as f: data, up = f.read(), False        # already the exact size: ship the bytes as made
                else: data, up = make_cover(src, w, h, fmt)
                tpl = names[k] if k < len(names) else cov.get("name", "00_COVER_{w}x{h}")
                rel = sanitize(render(tpl, dict(ctx, w=w, h=h)) + "." + fmt, "safe")
                plan[rel] = {"kind": "bytes", "data": data, "size": len(data), "facts": image_facts(data)}
                if up: warn.append(f"{rel}: cover source is smaller than {w}x{h}; it was upscaled")
                if spec.get("cover_min") and (w < spec["cover_min"][0] or h < spec["cover_min"][1]):
                    warn.append(f"{rel}: below the platform minimum cover {spec['cover_min'][0]}x{spec['cover_min'][1]}")
    for rel in plan:
        full = os.path.join(release_root, folder, rel)
        if len(folder) + 1 + len(rel) > max_rel:
            err.append(f"{tname}: path {folder}/{rel} is {len(folder) + 1 + len(rel)} characters; limit {max_rel} "
                       f"(shorten the label or folder so it unzips anywhere)")
        elif len(os.path.abspath(full)) > 259:
            warn.append(f"{tname}: {rel} lands at {len(os.path.abspath(full))} characters here; Windows without long paths stops at 260")
    if any(os.path.splitext(r)[1].lower() in FONT_EXT for r in plan) and not any(f.get("files_included") for f in m.get("handover", {}).get("fonts", [])):
        warn.append(f"{tname}: font files are in the delivery but no font in handover.fonts says files_included; check the licence")
    if t.get("readme", True):
        txt = readme_text(m, tname, t, folder, plan, by_rel, ctx).encode("utf-8")
        plan[README] = {"kind": "bytes", "data": txt, "size": len(txt)}
    for rel, p in plan.items(): p["sha"] = p.get("sha") or (sha256_bytes(p["data"]) if p["kind"] == "bytes" else sha256_file(p["src"]))
    if t.get("checksums", True):
        sums = "".join(f"{plan[r]['sha']}  {r}\n" for r in sorted(plan)).encode("utf-8")
        plan[SUMS] = {"kind": "bytes", "data": sums, "size": len(sums), "sha": sha256_bytes(sums)}
    return folder, plan, by_rel, warn, err


def _park(path, park_dir, rel):
    dst = os.path.join(park_dir, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(path, dst); return dst


def _zip_bytes_entries(folder_name, plan, d):
    """Deterministic zip into a temp file; returns its path. Names sorted, fixed date, media stored."""
    y, mo, da = (int(x) for x in d.split("-")); fd, tmp = tempfile.mkstemp(suffix=".zip"); os.close(fd)
    with zipfile.ZipFile(tmp, "w") as z:
        for rel in sorted(plan):
            p = plan[rel]; zi = zipfile.ZipInfo(f"{folder_name}/{rel}", date_time=(y, mo, da, 12, 0, 0))
            zi.external_attr = 0o644 << 16; zi.create_system = 3
            zi.compress_type = zipfile.ZIP_STORED if os.path.splitext(rel)[1].lower() in STORED else zipfile.ZIP_DEFLATED
            if p["kind"] == "bytes": z.writestr(zi, p["data"])
            else:
                with open(p["src"], "rb") as f, z.open(zi, "w") as w: shutil.copyfileobj(f, w, 1 << 20)
    return tmp


def _crc(p):
    import zlib
    if p["kind"] == "bytes": return zlib.crc32(p["data"])
    c = 0
    with open(p["src"], "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): c = zlib.crc32(chunk, c)
    return c


def zip_matches(zpath, folder, plan):
    """True when an existing zip already holds exactly this tree with the same contents (names + CRC-32)."""
    if not os.path.isfile(zpath): return False
    try:
        with zipfile.ZipFile(zpath) as z:
            have = {i.filename: i.CRC for i in z.infolist() if not i.filename.endswith("/")}
    except zipfile.BadZipFile: return False
    want = {f"{folder}/{r}": p for r, p in plan.items()}
    return set(have) == set(want) and all(have[n] == _crc(p) for n, p in want.items())


def build(manifest, dry_run=False, targets=None, allow_stale=False, zip_=True, source_root=None, release_root=None,
          quiet=False, stamp_now=None):
    """Plan every target, fail on any problem, then (unless dry_run) apply: park, copy, write, zip. Returns a report."""
    m, base = load_manifest(manifest); m = dict(m)
    src_root = os.path.abspath(source_root or os.path.join(base, m.get("source_root", ".")))
    rel_root = os.path.abspath(release_root or os.path.join(base, m.get("release_root", "release")))
    m["_src_root"] = src_root; ctx = base_context(m)
    only = set(targets) if targets else None
    if only and only - set(m["targets"]): raise HandoverError([f"unknown target(s): {', '.join(sorted(only - set(m['targets'])))}"])
    entries, probs, skipped = expand(m, src_root, only)
    marker = os.path.join(base, m["build_marker"]) if m.get("build_marker") else None
    stale = staleness(entries, src_root, marker)
    warnings = list(skipped)
    if stale and (allow_stale or m.get("stale") == "warn"): warnings += stale
    else: probs += stale
    report = {"stamp": ctx["stamp"], "release_root": rel_root, "dry_run": dry_run, "targets": {}, "warnings": warnings}
    plans = {}
    for tname in m["targets"]:
        if only and tname not in only: continue
        folder, plan, by_rel, w, e = plan_target(m, base, tname, [x for x in entries if x["target"] == tname], ctx, rel_root)
        probs += e; warnings += w; plans[tname] = (folder, plan, by_rel)
    if probs: raise HandoverError(probs)
    ts = stamp_now or datetime.now().strftime("%Y-%m-%d_%H%M%S")
    park_base = os.path.join(rel_root, "_parked", ts); k = 2
    while not dry_run and os.path.exists(park_base): park_base = os.path.join(rel_root, "_parked", f"{ts}_{k}"); k += 1
    for tname, (folder, plan, by_rel) in plans.items():
        t = m["targets"][tname]; fpath = os.path.join(rel_root, folder); have = _walk(fpath)
        added = sorted(r for r in plan if r not in have)
        changed = sorted(r for r in plan if r in have and sha256_file(have[r]) != plan[r]["sha"])
        parked = sorted(r for r in have if r not in plan)
        same = len(plan) - len(added) - len(changed)
        r = {"folder": folder, "path": fpath, "added": added, "changed": changed, "parked": parked, "same": same,
             "files": len(plan), "bytes": sum(p["size"] for p in plan.values()), "kind": t.get("kind", tname),
             "largest": sorted(((p["size"], x) for x, p in plan.items()), reverse=True)[:3], "zip": None}
        if r["kind"] == "portfolio":
            r["reupload"] = sorted({panel_no(x) for x in added + changed if x not in (README, SUMS) and panel_no(x)})
        zpath = os.path.join(rel_root, folder + ".zip"); want_zip = zip_ and t.get("zip", True)
        if not dry_run:
            pdir = os.path.join(park_base, folder)
            for x in changed + parked: _park(have[x], pdir, x)
            for x in added + changed:
                dst = os.path.join(fpath, x); os.makedirs(os.path.dirname(dst), exist_ok=True)
                if plan[x]["kind"] == "bytes":
                    with open(dst, "wb") as f: f.write(plan[x]["data"])
                else: shutil.copy2(plan[x]["src"], dst)
            for dp, dn, fn in sorted(os.walk(fpath, topdown=False)):   # empty sub-folders left by parking (folders only)
                if dp != fpath and not os.listdir(dp): os.rmdir(dp)
            if want_zip:
                if zip_matches(zpath, folder, plan): zstate = "unchanged (same contents)"
                else:
                    tmp = _zip_bytes_entries(folder, plan, ctx["date"])
                    if os.path.exists(zpath): _park(zpath, park_base, folder + ".zip")
                    shutil.move(tmp, zpath); zstate = "written"
                r["zip"] = {"path": zpath, "bytes": os.path.getsize(zpath), "state": zstate}
        elif want_zip:
            same_zip = not (added or changed or parked) and zip_matches(zpath, folder, plan)
            r["zip"] = {"path": zpath, "bytes": os.path.getsize(zpath) if same_zip else None,
                        "state": "unchanged (same contents)" if same_zip else
                                 ("would rebuild (old zip parked)" if os.path.exists(zpath) else "would write")}
        r["parked_to"] = os.path.join(park_base, folder) if (r["changed"] or r["parked"]) else None
        report["targets"][tname] = r
    if not quiet: print_report(report)
    return report


def print_report(rep):
    head = "DRY RUN (nothing written)" if rep["dry_run"] else "BUILT"
    print(f"{head}  {rep['stamp']}  ->  {rep['release_root']}")
    for tname, r in rep["targets"].items():
        print(f"\n{tname.upper()}  {r['folder']}  ({r['files']} files, {human_size(r['bytes'])})")
        for sym, key, verb in (("+", "added", "add" if rep["dry_run"] else "added"),
                               ("~", "changed", "change" if rep["dry_run"] else "changed"),
                               (">", "parked", "park" if rep["dry_run"] else "parked")):
            if r[key]:
                print(f"  {sym} {verb} {len(r[key])}:"); [print(f"      {x}") for x in r[key][:40]]
                if len(r[key]) > 40: print(f"      ... and {len(r[key]) - 40} more")
        print(f"  = same {r['same']}")
        if r.get("parked_to") and not rep["dry_run"]: print(f"  parked into {r['parked_to']} (nothing deleted)")
        if r.get("reupload"): print(f"  re-upload panels: {', '.join(r['reupload'])}")
        if r["zip"]:
            z = r["zip"]; print(f"  zip: {os.path.basename(z['path'])}  {z['state']}" + (f", {human_size(z['bytes'])}" if z["bytes"] else ""))
        print("  largest: " + "; ".join(f"{x} {human_size(s)}" for s, x in r["largest"]))
    if rep["warnings"]:
        print("\nWARNINGS"); groups = {}
        for w in rep["warnings"]:                 # one line for many files with the same problem
            head, _, tail = w.partition(": ")
            groups.setdefault(re.sub(r"\d+(\.\d+)? (B|KB|MB|GB)", "#", tail) if tail else w, []).append((head, w))
        for ws in groups.values():
            if len(ws) > 3: print(f"  - {len(ws)} files ({ws[0][0]} ... {ws[-1][0]}): {ws[0][1].partition(': ')[2]}")
            else:
                for _, w in ws: print("  - " + w)


def mark(manifest):
    """Touch the build marker. Call at the START of a render run: anything older afterwards was not re-rendered."""
    m, base = load_manifest(manifest)
    if not m.get("build_marker"): raise HandoverError(["manifest has no build_marker"])
    p = os.path.join(base, m["build_marker"]); os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(datetime.now().isoformat(timespec="seconds") + "\n")
    return p


# ---------------------------------------------------------------- release diff
def _sums(path):
    """{rel: sha} from a release folder (its SHA256SUMS.txt, else hashing), a zip, or a SHA256SUMS file."""
    if os.path.isdir(path):
        s = os.path.join(path, SUMS)
        if os.path.isfile(s): return _sums(s)
        return {r: sha256_file(p) for r, p in _walk(path).items()}
    if path.lower().endswith(".zip"):
        out = {}
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if n.endswith("/"): continue
                rel = n.split("/", 1)[1] if "/" in n else n
                if rel == SUMS: continue
                out[rel] = hashlib.sha256(z.read(n)).hexdigest()
        return out
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip(): h, rel = line.rstrip("\n").split(None, 1); out[rel.lstrip("*")] = h
    return out


def release_diff(old, new, quiet=False):
    """What changed between two releases, by content: added, removed, changed, renamed, and the numbers to re-upload."""
    a, b = _sums(old), _sums(new); a.pop(SUMS, None); b.pop(SUMS, None)
    changed = sorted(r for r in a.keys() & b.keys() if a[r] != b[r] and r != README)
    added = sorted(b.keys() - a.keys()); removed = sorted(a.keys() - b.keys())
    by_hash = {h: r for r, h in a.items()}
    renamed = sorted((by_hash[b[r]], r) for r in added if b[r] in by_hash and by_hash[b[r]] in removed)
    for o, n in renamed: added.remove(n); removed.remove(o)
    nums = sorted({panel_no(r) for r in changed + added if panel_no(r)})
    rep = {"added": added, "removed": removed, "changed": changed, "renamed": renamed, "panels": nums,
           "readme_changed": README in a and README in b and a[README] != b[README]}
    if not quiet:
        print(f"{os.path.basename(os.path.normpath(old))}  ->  {os.path.basename(os.path.normpath(new))}")
        for k in ("added", "removed", "changed"):
            if rep[k]: print(f"  {k} {len(rep[k])}: " + ", ".join(rep[k]))
        for o, n in renamed: print(f"  renamed: {o} -> {n}")
        print("  re-upload: " + (", ".join(nums) if nums else "nothing"))
    return rep


# ---------------------------------------------------------------- self-test
def selftest():
    """Synthetic sources in a temp dir; asserts naming, failures, staleness, parking, checksums, zip, dry run, diff."""
    from PIL import Image
    import time
    tmp = tempfile.mkdtemp(prefix="handover_"); S = os.path.join(tmp, "src"); R = os.path.join(tmp, "release")
    ok = []

    def png(rel, col, size=(400, 500)):
        p = os.path.join(S, rel); os.makedirs(os.path.dirname(p), exist_ok=True); Image.new("RGB", size, col).save(p); return p

    def snapshot(root):
        out = {}
        for dp, dn, fn in os.walk(root):
            for f in fn:
                p = os.path.join(dp, f); st = os.stat(p); out[os.path.relpath(p, root)] = (st.st_size, st.st_mtime_ns, sha256_file(p))
        return out

    def check(cond, what):
        if not cond: raise AssertionError(what)
        ok.append(what)

    try:
        for line, col in (("mango", "#E8A317"), ("kiwi", "#6A8F2B")):
            png(f"{line}_front.png", col); png(f"{line}_back.png", col)
        for i in range(1, 4): png(f"behance/panel_{i:02d}.png", (40 * i, 80, 120), (1400, 788))
        png("cover.png", "#334455", (2000, 1500)); png("scene_plate.jpg", "#999999")
        os.makedirs(os.path.join(S, "art"), exist_ok=True)
        with open(os.path.join(S, "art", "mango.svg"), "w") as f: f.write("<svg/>")
        with open(os.path.join(S, "film.mp4"), "wb") as f: f.write(b"\x00\x00\x00\x18ftypmp42" + b"0" * 2000)
        with open(os.path.join(S, "press_mango.pdf"), "wb") as f: f.write(b"%PDF-1.6\n/GTS_PDFXVersion (PDF/X-4)\n%%EOF")
        old = time.time() - 3600
        for f in ("art/mango.svg",): os.utime(os.path.join(S, f), (old, old))
        man = {
            "project": "Example Co", "slug": "EXCO", "version": 1, "date": "2026-11-21",
            "source_root": S, "release_root": R,
            "groups": {"title": {"number": "00", "label": "Overview"}, "pouch": {"number": "02", "label": "Fruit pouch 100 g"},
                       "odd": {"number": "03", "label": 'Mix: "A/B" <x>? |*'}, "film": {"number": "09", "label": "Films"}},
            "targets": {"client": {"kind": "client", "folder": "CLIENT_{slug}_{stamp}"},
                        "portfolio": {"kind": "portfolio", "platform": "behance", "folder": "BEHANCE_{slug}_{stamp}",
                                      "cover": {"src": "cover.png"}},
                        "press": {"kind": "press", "folder": "PRESS_{slug}_{stamp}", "zip": False, "status": "press-ready"}},
            "handover": {"studio": "Example Studio", "fonts": [{"name": "Space Grotesk", "licence": "SIL OFL 1.1", "holder": "the foundry"}],
                         "ai": {"tools": "an image model (plates only)"}},
            "items": [
                {"target": "client", "group": "pouch", "src": "{line}_{view}.png", "name": "{group} {label} - {line|cap} {view}",
                 "for": {"line": ["mango", "kiwi"], "view": ["front", "back"]}, "inputs": ["art/{line}.svg"], "status": "concept"},
                {"target": "client", "group": "odd", "src": "mango_front.png", "name": "{group} {label} - Café été ."},
                {"target": "client", "group": "odd", "src": "kiwi_front.png", "name": "CON"},
                {"target": "client", "group": "odd", "src": "kiwi_back.png", "name": "{group} " + "very long label " * 20},
                {"target": "client", "group": "film", "src": "scene_plate.jpg", "name": "{group} Range in a scene", "ai": True, "static": True},
                {"target": "client", "group": "film", "src": "film.mp4", "name": "{group} Flavour film"},
                {"target": "portfolio", "src": "behance/panel_*.png", "name": "{slug}_behance_{nn}"},
                {"target": "press", "src": "press_mango.pdf", "name": "mango/Mango pouch press {v}"},
            ]}
        mp = os.path.join(tmp, "manifest.json")

        def save(mm):
            with open(mp, "w", encoding="utf-8") as f: json.dump(mm, f, indent=1)

        # sanitiser unit checks
        for bad in ('a<b>c:d"e/f\\g|h?i*j', "CON", "nul.txt", "COM¹", "trail. ", "x" * 300 + ".png"):
            s = sanitize(bad); check(not any(c in s for c in RESERVED_CHARS) and len(s) <= 120 and not s.endswith((".", " "))
                                     and s.split(".")[0].upper() not in RESERVED_NAMES, f"sanitize {bad[:20]!r} -> {s[:30]!r}")
        check(sanitize("Fruit pouch 100 g - Mango.png", "safe") == "Fruit_pouch_100_g_-_Mango.png", "safe naming")
        check(render("{line|words|title}", {"line": "exam-night"}) == "Exam Night", "template filters")

        # 1. first build: names rendered and sanitised, under the limits
        save(man); rep = build(mp, quiet=True)
        cf = os.path.join(R, "CLIENT_EXCO_v01_2026-11-21"); names = sorted(os.listdir(cf))
        check("02 Fruit pouch 100 g - Mango front.png" in names and "02 Fruit pouch 100 g - Kiwi back.png" in names, "names rendered")
        check(all(not any(c in n for c in RESERVED_CHARS) and not n.rstrip(".png").endswith((" ", ".")) for n in names), "no illegal characters")
        check("_CON.png" in names, "device name guarded")
        check(any(n.startswith("03 Mix -") and "Café" in n for n in names), "reserved characters replaced, accents kept (NFC)")
        check(all(len("CLIENT_EXCO_v01_2026-11-21/" + n) <= 200 and len(n) <= 120 for n in names), "under the name and path limits")
        bf = os.path.join(R, "BEHANCE_EXCO_v01_2026-11-21")
        from PIL import Image as _I
        check(_I.open(os.path.join(bf, "00_COVER_1616x1264.png")).size == (1616, 1264)
              and _I.open(os.path.join(bf, "00_COVER_808x632.jpg")).size == (808, 632), "covers at platform sizes")
        check(os.path.isfile(os.path.join(R, "PRESS_EXCO_v01_2026-11-21", "mango", "Mango_pouch_press_v01.pdf")), "sub-folders in names")
        rd = open(os.path.join(cf, README), encoding="utf-8").read()
        check("AI DISCLOSURE" in rd and "[AI plate]" in rd and "Space Grotesk: SIL OFL 1.1" in rd and "concept" in rd, "README content")
        check("PDF/X-4" in open(os.path.join(R, "PRESS_EXCO_v01_2026-11-21", README), encoding="utf-8").read(), "PDF/X detected")

        # 2. checksum file correct
        sums = _sums(os.path.join(cf, SUMS)); files = _walk(cf)
        check(set(sums) == set(files) - {SUMS} and all(sha256_file(files[r]) == h for r, h in sums.items()), "checksums correct")

        # 3. zip contains the exact tree, UTF-8 flag on non-ASCII names
        with zipfile.ZipFile(cf + ".zip") as z:
            check(sorted(z.namelist()) == sorted("CLIENT_EXCO_v01_2026-11-21/" + r for r in files), "zip holds the exact tree")
            check(all(i.flag_bits & 0x800 for i in z.infolist() if not i.filename.isascii()), "zip UTF-8 name flag")
            check(z.testzip() is None, "zip CRCs")
        check(not os.path.exists(os.path.join(R, "PRESS_EXCO_v01_2026-11-21.zip")), "zip off per target")

        # 4. rerun unchanged: nothing moves, zip untouched
        rep = build(mp, quiet=True)
        check(all(not (r["added"] or r["changed"] or r["parked"]) for r in rep["targets"].values())
              and rep["targets"]["client"]["zip"]["state"].startswith("unchanged"), "idempotent rerun")

        # 5. missing source fails loudly and writes nothing
        bad = json.loads(json.dumps(man)); bad["items"].append({"target": "client", "src": "nope_*.png", "name": "x"})
        bad["release_root"] = os.path.join(tmp, "release_bad"); save(bad)
        try: build(mp, quiet=True); check(False, "missing source must fail")
        except HandoverError as e: check("missing source nope_*.png" in str(e) and not os.path.exists(bad["release_root"]), "missing source fails, nothing written")

        # 6. stale source flagged (input newer than render), and by the build marker
        now = time.time(); os.utime(os.path.join(S, "art", "mango.svg"), (now + 5, now + 5)); save(man)
        try: build(mp, quiet=True); check(False, "stale must fail")
        except HandoverError as e: check("stale: mango_front.png is older than its input art" in str(e).replace("\\", "/"), "stale input flagged")
        check(build(mp, quiet=True, allow_stale=True, dry_run=True)["warnings"], "allow-stale downgrades to a warning")
        os.utime(os.path.join(S, "art", "mango.svg"), (old, old))
        mk = dict(man, build_marker="marker.txt"); save(mk); mark(mp)
        os.utime(os.path.join(tmp, "marker.txt"), (now + 10, now + 10))
        try: build(mp, quiet=True); check(False, "marker stale must fail")
        except HandoverError as e: check("predates the build marker" in str(e) and "scene_plate" not in str(e), "build marker flags un-rendered files (static exempt)")
        save(man)

        # 7. dry run changes nothing on disk, but reports the diff
        png("behance/panel_02.png", "#FF0000", (1400, 788)); before = snapshot(tmp)
        rep = build(mp, dry_run=True, quiet=True); after = snapshot(tmp)
        check(before == after, "dry run touches nothing")
        check([x for x in rep["targets"]["portfolio"]["changed"] if x not in (README, SUMS)] == ["EXCO_behance_02.png"]
              and rep["targets"]["portfolio"]["reupload"] == ["02"], "dry run lists the panel to re-upload")

        # 8. rerun parks removed and changed files; nothing deleted
        hashes_before = {v[2] for k, v in snapshot(R).items()}; count_before = len(snapshot(R))
        m2 = json.loads(json.dumps(man)); m2["items"][0]["for"]["line"] = ["mango"]; save(m2)
        rep = build(mp, quiet=True, stamp_now="2026-11-21_120000"); snap = snapshot(R)
        check(len(rep["targets"]["client"]["parked"]) == 2 and "EXCO_behance_02.png" in rep["targets"]["portfolio"]["changed"], "removed and changed files listed")
        pk = os.path.join(R, "_parked", "2026-11-21_120000")
        check(os.path.isfile(os.path.join(pk, "CLIENT_EXCO_v01_2026-11-21", "02 Fruit pouch 100 g - Kiwi front.png"))
              and os.path.isfile(os.path.join(pk, "BEHANCE_EXCO_v01_2026-11-21", "EXCO_behance_02.png")), "parked into _parked/<timestamp>/")
        check(hashes_before <= {v[2] for v in snap.values()} and len(snap) >= count_before, f"nothing deleted ({count_before} -> {len(snap)} files)")
        check(not os.path.exists(os.path.join(cf, "02 Fruit pouch 100 g - Kiwi front.png")), "removed file gone from the delivery")

        # 9. release diff between v01 and v02 lists changed panel numbers
        m3 = json.loads(json.dumps(m2)); m3["version"] = 2; save(m3); build(mp, quiet=True)
        png("behance/panel_03.png", "#00FF00", (1400, 788)); png("behance/panel_04.png", "#0000FF", (1400, 788))
        m3["version"] = 3; save(m3); build(mp, quiet=True)
        d = release_diff(os.path.join(R, "BEHANCE_EXCO_v02_2026-11-21"), os.path.join(R, "BEHANCE_EXCO_v03_2026-11-21.zip"), quiet=True)
        check(d["changed"] == ["EXCO_behance_03.png"] and d["added"] == ["EXCO_behance_04.png"] and d["panels"] == ["03", "04"], "release diff lists panels")

        # 10. duplicate names fail
        m4 = json.loads(json.dumps(man)); m4["items"].append({"target": "client", "group": "pouch", "src": "kiwi_front.png", "name": "02 fruit POUCH 100 g - mango FRONT"})
        m4["release_root"] = os.path.join(tmp, "release_dup"); save(m4)
        try: build(mp, quiet=True, dry_run=True); check(False, "duplicate must fail")
        except HandoverError as e: check("two sources map to" in str(e), "case-insensitive duplicate names fail")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for w in ok: print("PASS", w)
    print(f"selftest: {len(ok)} checks passed")
    return len(ok)


# ---------------------------------------------------------------- CLI
def main(argv=None):
    if argv is None: argv = sys.argv[1:]
    for stream in (sys.stdout, sys.stderr):                      # non-ASCII file names on a legacy Windows console
        try: stream.reconfigure(errors="replace")
        except (AttributeError, ValueError): pass
    if argv and argv[0] == "--selftest":
        selftest(); return 0
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="plan and build the delivery folders")
    b.add_argument("manifest"); b.add_argument("--dry-run", action="store_true", help="print the diff, write nothing")
    b.add_argument("--target", action="append", help="only this target (repeatable)")
    b.add_argument("--allow-stale", action="store_true"); b.add_argument("--no-zip", action="store_true")
    b.add_argument("--source-root"); b.add_argument("--release-root")
    b.add_argument("--json", help="also write the report as JSON here")
    k = sub.add_parser("mark", help="touch the build marker (start of a render run)"); k.add_argument("manifest")
    d = sub.add_parser("diff", help="compare two releases"); d.add_argument("old"); d.add_argument("new")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "build":
            rep = build(a.manifest, a.dry_run, a.target, a.allow_stale, not a.no_zip, a.source_root, a.release_root)
            if a.json:
                with open(a.json, "w", encoding="utf-8") as f: json.dump(rep, f, indent=1, default=str)
        elif a.cmd == "mark": print("marker:", mark(a.manifest))
        else: release_diff(a.old, a.new)
    except HandoverError as e:
        print(f"HANDOVER FAILED ({len(e.problems)} problem(s)); nothing was written:", file=sys.stderr)
        for p in e.problems: print("  - " + p, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
