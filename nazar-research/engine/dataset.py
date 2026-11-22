"""Research tree + reference dataset builder for nazar-research (every nazar kit's research goes through here).

  python dataset.py plan <research_dir> "<brief>" --kit packaging[,logo,social...]
      writes the research tree for those kits' profiles: 00_seed.md, one file per angle, sources.md, gaps.md,
      summary.md, codes.md, dataset/ (manifest with targets per kit). Re-running adds what's missing, never overwrites.
  python dataset.py add <research_dir> <urls.tsv|urls.json>
      downloads images: verified with Pillow, size/type capped, deduplicated by sha1, appended to manifest.json
      urls.tsv columns: url <tab> page <tab> source <tab> kind <tab> tags(comma) <tab> rights
  python dataset.py harvest <research_dir> <page_url> <kind> [source] [rights] [--max N]
      reads a web page and pulls its real images (og:image, <img src/srcset>, <a href> to image files, largest srcset
      candidate), then downloads them like `add`. Use on product, retailer, award, archive and press pages.
  python dataset.py sheets <research_dir>     contact sheets per kind in dataset/sheets/
  python dataset.py report <research_dir>     counts per kind, source, rights; thin flag per kit target
  python dataset.py kits                      lists the kit profiles
  python dataset.py --selftest

Downloads are untrusted data: only images are kept (opened and verified), nothing is executed, files are named by hash.
No personal details go into requests: a generic User-Agent is used.
"""
import hashlib, io, json, os, sys, time, urllib.request, urllib.parse
from PIL import Image, ImageDraw

UA = "Mozilla/5.0 (compatible; nazar-research/1.0; reference dataset)"
MAX_BYTES = 25 * 1024 * 1024
MIN_SIDE = 240
ANGLES = {1: "brand", 2: "history-people", 3: "place", 4: "product", 5: "category", 6: "competitors-shelf",
          7: "leaders-awards", 8: "customers", 9: "culture-language", 10: "channels-formats", 11: "rules", 12: "papers"}
# kit -> (angles, dataset kinds, target size); mirrors references/kit_profiles.md
KITS = {
    "strategy":      ([1, 2, 5, 6, 8, 9, 12], ["competitor", "ad"], 80),
    "logo":          ([1, 2, 3, 5, 6, 7], ["mark", "lettering", "competitor", "leader"], 150),
    "brand-book":    ([1, 3, 5, 6, 7, 10], ["manual", "competitor", "place"], 120),
    "packaging":     ([4, 5, 6, 7, 10, 11], ["competitor", "leader", "award", "heritage", "shelf", "app-tile"], 250),
    "dieline":       ([4, 6, 7, 10], ["structure", "dieline"], 100),
    "shoot":         ([3, 4, 7, 10], ["photo", "in-use", "lighting", "place"], 150),
    "art-direction": ([3, 4, 7, 10], ["photo", "in-use", "lighting", "place"], 150),
    "study":         ([7], ["best"], 30),
    "social":        ([1, 6, 8, 9, 10], ["feed", "competitor", "leader", "format"], 200),
    "backdrops":     ([1, 10], ["feed", "spec"], 40),
    "ooh":           ([3, 6, 7, 9, 10], ["street", "award", "lettering"], 150),
    "motion":        ([7, 10], ["ident", "title", "spec"], 80),
    "web":           ([6, 7, 8, 10], ["site", "pattern"], 80),
    "type":          ([3, 5, 7], ["lettering", "specimen", "in-use"], 120),
    "colour":        ([3, 4, 5], ["surface", "product", "pigment", "competitor"], 120),
    "illustration":  ([3, 5, 7], ["craft", "plate", "illustrator"], 120),
    "prompts":       ([7, 10], ["photo"], 40),
    "voiceprint":    ([1, 8, 9], ["own-work"], 0),
    "story":         ([1, 6, 7, 8], ["case-study"], 60),
    "pitch":         ([1, 6, 7, 8], ["case-study"], 60),
}
ALL_KINDS = sorted({k for _, ks, _ in KITS.values() for k in ks} | {"brand", "material", "other"})


def _kits(arg):
    ks = [k.strip().replace("nazar-", "") for k in arg.split(",") if k.strip()]
    bad = [k for k in ks if k not in KITS]
    if bad:
        raise SystemExit(f"unknown kit(s) {bad}; known: {', '.join(KITS)}")
    return ks


def plan(rd, brief, kits=("packaging",)):
    os.makedirs(os.path.join(rd, "dataset", "sheets"), exist_ok=True); os.makedirs(os.path.join(rd, "papers"), exist_ok=True)
    def w(name, text):
        p = os.path.join(rd, name)
        if not os.path.exists(p):
            open(p, "w", encoding="utf-8").write(text)
    angles = sorted({a for k in kits for a in KITS[k][0]})
    w("00_seed.md", f"# Seed\n\nBrief: {brief}\n\n## Questions (the plan)\n- \n\n## Perspectives to ask from\n- buyer\n- shopkeeper\n- competitor's designer\n- historian\n- printer / maker\n")
    for a in angles:
        w(f"{a:02d}_{ANGLES[a]}.md", f"# {ANGLES[a].replace('-', ' ').title()}\n\nQueries run:\n- \n\n## Findings (tag, fact, link, date seen)\n- \n\n"
                                    "## Still missing (next round's queries)\n- \n\nRounds: 0 · new findings per round: \n")
    w("codes.md", "# Category codes (residual / dominant / emergent), each with 3 dataset files\n\n## Residual\n\n## Dominant (the cliche)\n\n## Emergent\n")
    w("sources.md", "# Sources\n\n"); w("gaps.md", "# Gaps: what we could not find, and where it might be\n\n")
    w("summary.md", "# Summary (one page)\n\n## 5 findings that matter\n\n## Cliche to avoid\n\n## Forgotten thing to revive\n\n"
                    "## Empty spot on the shelf / feed / street\n\n## 3 concept seeds\n\n## What the dataset shows\n")
    mp = os.path.join(rd, "dataset", "manifest.json")
    man = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {"kits": {}, "items": []}
    for k in kits:
        man["kits"][k] = {"kinds": KITS[k][1], "target": KITS[k][2], "angles": KITS[k][0]}
    json.dump(man, open(mp, "w", encoding="utf-8"), indent=1)
    print(f"{rd}: kits {list(man['kits'])}, angles {angles}")
    return rd


def _rows(path):
    if path.endswith(".json"):
        return json.load(open(path, encoding="utf-8"))
    out = []
    for ln in open(path, encoding="utf-8"):
        if not ln.strip() or ln.startswith("#"):
            continue
        c = (ln.rstrip("\n").split("\t") + [""] * 6)[:6]
        out.append(dict(url=c[0], page=c[1], source=c[2], kind=c[3] or "other",
                        tags=[t.strip() for t in c[4].split(",") if t.strip()], rights=c[5] or "unknown"))
    return out


def _fetch(url):
    if urllib.parse.urlparse(url).scheme not in ("http", "https"):
        raise ValueError("not http(s)")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("too large")
    return data


def page_images(html, base):
    """Image URLs on a page, best first: og/twitter image, then <img> (largest srcset), then links to image files."""
    from html.parser import HTMLParser
    found = []
    class P(HTMLParser):
        def handle_starttag(self, tag, at):
            a = dict(at)
            if tag == "meta" and (a.get("property") or a.get("name") or "").lower() in ("og:image", "og:image:url", "twitter:image") and a.get("content"):
                found.append((0, a["content"]))
            elif tag in ("img", "source"):
                ss = a.get("srcset") or a.get("data-srcset")
                if ss:
                    best = max((c.strip().split() for c in ss.split(",") if c.strip()),
                               key=lambda c: float(c[1][:-1]) if len(c) > 1 and c[1][:-1].replace(".", "").isdigit() else 0)
                    found.append((1, best[0]))
                for k in ("data-src", "data-original", "src"):
                    if a.get(k) and not a[k].startswith("data:"):
                        found.append((2, a[k])); break
            elif tag == "a" and (a.get("href") or "").lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")):
                found.append((1, a["href"]))
    P().feed(html)
    out, seen = [], set()
    for _, u in sorted(found, key=lambda x: x[0]):
        u = urllib.parse.urljoin(base, u.strip())
        if u not in seen and urllib.parse.urlparse(u).scheme in ("http", "https") and not u.lower().split("?")[0].endswith((".svg", ".gif")):
            seen.add(u); out.append(u)
    return out


def harvest(rd, page, kind, source="", rights="unknown", max_n=40, fetch_page=None, fetch=None):
    if fetch_page is None:
        req = urllib.request.Request(page, headers={"User-Agent": UA, "Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read(8 * 1024 * 1024).decode("utf-8", "replace")
    else:
        html = fetch_page(page)
    urls = page_images(html, page)[:max_n]
    src = source or urllib.parse.urlparse(page).netloc
    print(f"{page}: {len(urls)} candidate images")
    rows = [dict(url=u, page=page, source=src, kind=kind, tags=[], rights=rights) for u in urls]
    return add(rd, rows, **({"fetch": fetch, "delay": 0} if fetch else {}))


def _verify(data):
    im = Image.open(io.BytesIO(data)); im.verify()
    im = Image.open(io.BytesIO(data)); im.load()
    if min(im.size) < MIN_SIDE:
        raise ValueError(f"too small {im.size}")
    return im


def add(rd, src, fetch=_fetch, delay=0.6):
    mp = os.path.join(rd, "dataset", "manifest.json"); man = json.load(open(mp, encoding="utf-8"))
    seen = {it["sha1"] for it in man["items"]}; urls = {it["url"] for it in man["items"]}
    ok = dup = bad = 0
    for row in (_rows(src) if isinstance(src, str) else src):
        if row["url"] in urls:
            dup += 1; continue
        try:
            data = fetch(row["url"]); im = _verify(data); h = hashlib.sha1(data).hexdigest()
            if h in seen:
                dup += 1; continue
            kind = row.get("kind") if row.get("kind") in ALL_KINDS else "other"
            os.makedirs(os.path.join(rd, "dataset", kind), exist_ok=True)
            fn = f"{kind}/{h[:16]}.jpg"
            im.convert("RGB").save(os.path.join(rd, "dataset", fn), quality=90)
            man["items"].append(dict(file=fn, url=row["url"], page=row.get("page", ""), source=row.get("source", ""), kind=kind,
                                     tags=row.get("tags", []), rights=row.get("rights", "unknown"), sha1=h, w=im.width, h=im.height,
                                     seen=time.strftime("%Y-%m-%d")))
            seen.add(h); urls.add(row["url"]); ok += 1
        except Exception as e:
            bad += 1; print("skip", str(row.get("url", ""))[:90], "-", e)
        time.sleep(delay)
    json.dump(man, open(mp, "w", encoding="utf-8"), indent=1)
    print(f"added {ok}, duplicates {dup}, failed {bad}, total {len(man['items'])}")
    return ok, dup, bad


def sheets(rd, cell=220, cols=8):
    man = json.load(open(os.path.join(rd, "dataset", "manifest.json"), encoding="utf-8")); out = []
    for kind in ALL_KINDS:
        items = [it for it in man["items"] if it["kind"] == kind]
        if not items:
            continue
        rows = (len(items) + cols - 1) // cols
        sh = Image.new("RGB", (cols * cell, rows * (cell + 18) + 30), "#F3EEE5"); d = ImageDraw.Draw(sh)
        d.text((8, 6), f"{kind}  ({len(items)})", fill="#1E1A17")
        for i, it in enumerate(items):
            im = Image.open(os.path.join(rd, "dataset", it["file"])); im.thumbnail((cell - 8, cell - 8))
            x, y = (i % cols) * cell, 30 + (i // cols) * (cell + 18)
            sh.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2))
            d.text((x + 4, y + cell), (it.get("source") or "")[:30], fill="#7A7068")
        p = os.path.join(rd, "dataset", "sheets", f"{kind}.jpg"); sh.save(p, quality=86); out.append(p)
    print("\n".join(out)); return out


def report(rd):
    man = json.load(open(os.path.join(rd, "dataset", "manifest.json"), encoding="utf-8")); it = man["items"]
    def count(key):
        c = {}
        for x in it:
            v = x.get(key) or "?"; c[v] = c.get(v, 0) + 1
        return dict(sorted(c.items(), key=lambda kv: -kv[1]))
    per_kit = {k: dict(have=(n := sum(1 for x in it if x["kind"] in cfg["kinds"])), target=cfg["target"], thin=n < cfg["target"])
               for k, cfg in man.get("kits", {}).items()}
    r = dict(total=len(it), kits=per_kit, kind=count("kind"), source=count("source"), rights=count("rights"))
    print(json.dumps(r, indent=1)); return r


def selftest():
    import tempfile
    rd = tempfile.mkdtemp(prefix="nazar_ds_")
    plan(rd, "test brief", ["packaging", "logo"])
    assert os.path.exists(os.path.join(rd, "06_competitors-shelf.md")) and os.path.exists(os.path.join(rd, "02_history-people.md"))
    open(os.path.join(rd, "summary.md"), "a").write("kept"); plan(rd, "again", ["social"])           # re-plan never overwrites
    assert open(os.path.join(rd, "summary.md")).read().endswith("kept") and os.path.exists(os.path.join(rd, "09_culture-language.md"))
    def img(c, s=(400, 300)):
        b = io.BytesIO(); Image.new("RGB", s, c).save(b, "PNG"); return b.getvalue()
    fake = {"http://a/1.png": img("red"), "http://a/2.png": img("red"), "http://a/3.png": img("blue", (100, 100)),
            "http://a/4.png": b"<html>no</html>", "http://a/5.png": img("green")}
    rows = [dict(url=u, page="p", source="test", kind="competitor", tags=["t"], rights="unknown") for u in fake]
    assert add(rd, rows, fetch=lambda u: fake[u], delay=0) == (2, 1, 2)       # content duplicate, too small, not an image
    assert add(rd, rows[:1], fetch=lambda u: fake[u], delay=0) == (0, 1, 0)   # same url twice
    r = report(rd); assert r["total"] == 2 and r["kits"]["packaging"]["thin"] and sheets(rd)
    html = ('<meta property="og:image" content="/og.png"><img src="data:x"><img srcset="s.png 300w, big.png 1200w" src="s.png">'
            '<a href="pack.jpg?x=1">p</a><img src="icon.svg">')
    assert page_images(html, "http://a/p/") == ["http://a/og.png", "http://a/p/big.png", "http://a/p/pack.jpg?x=1", "http://a/p/s.png"]
    hf = {"http://a/og.png": img("navy"), "http://a/p/big.png": img("teal"), "http://a/p/pack.jpg?x=1": img("navy"), "http://a/p/s.png": img("teal", (50, 50))}
    assert harvest(rd, "http://a/p/", "leader", fetch_page=lambda u: html, fetch=lambda u: hf[u]) == (2, 1, 1)
    try:
        _fetch("file:///etc/passwd"); raise AssertionError("file url accepted")
    except ValueError:
        pass
    print("SELFTEST PASS")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
    elif a[0] == "--selftest":
        selftest()
    elif a[0] == "kits":
        for k, (ang, kinds, t) in KITS.items():
            print(f"{k:14s} angles {ang}  kinds {kinds}  target {t}")
    elif a[0] == "plan":
        plan(a[1], a[2], _kits(a[a.index("--kit") + 1] if "--kit" in a else "packaging"))
    elif a[0] == "add":
        add(a[1], a[2])
    elif a[0] == "harvest":
        mx = int(a[a.index("--max") + 1]) if "--max" in a else 40
        pos = [x for i, x in enumerate(a) if x != "--max" and (i == 0 or a[i - 1] != "--max")]
        harvest(pos[1], pos[2], pos[3], pos[4] if len(pos) > 4 else "", pos[5] if len(pos) > 5 else "unknown", mx)
    elif a[0] == "sheets":
        sheets(a[1])
    elif a[0] == "report":
        report(a[1])
