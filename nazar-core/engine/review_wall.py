"""Review wall: a folder of designs -> a private live page (beta, for the designer) to comment on each design in progress,
and every note sent with "Send to Claude" lands in the working chat. Generic, brand-free.

    python review_wall.py <images folder> <out folder> --title "Brand review" [--titles titles.json] [--accent "#hex,#hex"]

Writes <out>/review.html, <out>/img/NN.jpg (max 1600 px, 16:9 or as-is) and <out>/publish.json: the exact
Artifact publish arguments (file_path, root, files map, capabilities). Claude then publishes it in one call.
titles.json (optional): [["Title", "section"], ...] in file order; otherwise titles come from the file names.

State lives in <out>/wall.json (per sheet, keyed by source file name): source hash, resolved flag, previous version.
    --resolve 03,07      mark sheets resolved (every comment of this round on them answered): badge + filter on the page
                         (a sheet whose design changes later goes back to open until resolved again)
    --unresolve 07       mark open again
    --new-round          start a new client round: clear every resolved flag, round number +1
Rebuilding into the same <out> after a design changed keeps its last image as img/prev/NN.jpg, and the page shows a
before/after slider and toggle on that sheet until the next change replaces it. Self-check: python test_review_wall.py
Guide: references/review_wall.md.
"""
import os, sys, json, argparse, html, hashlib
from PIL import Image

EXT = (".png", ".jpg", ".jpeg", ".webp")

PAGE = """<title>{title}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap">
<style>
/* Layout: a contact-sheet wall, one numbered sheet per design, in the order given; brand colours run as a strip under the header. */
:root{{--bg:#EEEAE4;--paper:#FAF8F5;--ink:#1D1B19;--mute:#6C655F;--line:#D8D1C8;--focus:#1D1B19;--ok:#2F6B45;--okink:#FFFFFF;
  --display:"Space Grotesk",system-ui,sans-serif;--body:"Inter",system-ui,-apple-system,sans-serif}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#161412;--paper:#201D1B;--ink:#F2EEE8;--mute:#A49B92;--line:#38322D;--focus:#F2EEE8;--ok:#8FD3A6;--okink:#10251A;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#161412;--paper:#201D1B;--ink:#F2EEE8;--mute:#A49B92;--line:#38322D;--focus:#F2EEE8;--ok:#8FD3A6;--okink:#10251A;color-scheme:dark}}
body{{background:var(--bg);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.5}}
.wrap{{max-width:1280px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:40px 64px}}
header{{display:grid;gap:12px;padding-block-end:18px}}
.kicker{{font:700 12px var(--display);letter-spacing:.16em;text-transform:uppercase;color:var(--mute)}}
h1{{font-family:var(--display);font-weight:700;font-size:clamp(40px,7vw,80px);line-height:.95;margin:0;text-wrap:balance}}
.how{{max-width:62ch;color:var(--mute);margin:0}} .how b{{color:var(--ink);font-weight:600}}
.strip{{display:grid;grid-auto-flow:column;height:8px;margin-block:8px 20px}}
.bar{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-block:0 24px}}
.bar .lbl{{font:500 12px var(--body);color:var(--mute);letter-spacing:.05em;text-transform:uppercase;margin-inline-end:4px}}
.bar button,.cmp button{{font:600 13px var(--body);color:var(--ink);background:transparent;border:1px solid var(--line);border-radius:999px;padding:5px 12px;cursor:pointer}}
.bar button[aria-pressed="true"],.cmp button[aria-pressed="true"]{{background:var(--ink);color:var(--paper);border-color:var(--ink)}}
.bar button:focus-visible,.cmp button:focus-visible,.cmp input:focus-visible{{outline:3px solid var(--focus);outline-offset:2px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,480px),1fr));gap:28px 24px}}
figure{{margin:0;display:grid;gap:10px;min-width:0}} figure[hidden]{{display:none}}
.sheet{{position:relative;background:var(--paper);border:1px solid var(--line);max-width:100%;overflow:hidden}}
.sheet img{{display:block;width:100%;height:auto}}
.sheet .before{{position:absolute;inset:0 auto 0 0;width:50%;overflow:hidden;border-right:2px solid var(--paper)}}
.sheet .before img{{max-width:none;height:100%}}
.tag{{position:absolute;top:8px;font:600 11px var(--body);letter-spacing:.06em;text-transform:uppercase;background:var(--ink);color:var(--paper);padding:2px 8px}}
.tag.b{{left:8px}} .tag.a{{right:8px}}
.cmp{{display:flex;align-items:center;gap:10px;min-width:0}} .cmp input{{flex:1;min-width:0;accent-color:var(--ink)}} .cmp button{{flex:none;font-size:12px;padding:4px 11px}}
figcaption{{display:flex;align-items:baseline;gap:12px;min-width:0}}
.no{{font:700 13px var(--display);color:var(--mute);font-variant-numeric:tabular-nums;flex:none}}
.t{{font:700 17px/1.25 var(--display);flex:1;min-width:0}} .sec{{font:500 12px var(--body);color:var(--mute);letter-spacing:.05em;text-transform:uppercase}}
.badge{{flex:none;font:600 11px var(--body);letter-spacing:.06em;text-transform:uppercase;border-radius:999px;padding:3px 9px;border:1px solid var(--line);color:var(--mute)}}
.badge.res{{background:var(--ok);border-color:var(--ok);color:var(--okink)}}
button.c{{flex:none;font:600 13px var(--body);color:var(--ink);background:transparent;border:1.5px solid var(--ink);border-radius:999px;padding:6px 14px;cursor:pointer}}
button.c:hover{{background:var(--ink);color:var(--paper)}} button.c:focus-visible{{outline:3px solid var(--focus);outline-offset:2px}}
footer{{margin-top:48px;color:var(--mute);font-size:13px}}
</style>
<div class="wrap">
<header><span class="kicker">{kicker}</span><h1>{h1}</h1>
<p class="how">Every design, numbered. <b>Press Comment under a design</b> (or turn on comment mode and click any sheet), write one note per change, and choose <b>Send to Claude</b>: it reaches the working session, which fixes it and republishes this page. Sheets marked <b>Resolved</b> have every note of this round answered; a changed sheet shows a <b>Before/After</b> slider.</p></header>
<div class="strip" aria-hidden="true">{strip}</div>
<div class="bar" role="group" aria-label="Filter sheets"><span class="lbl">Round {round} · <span id="cnt"></span></span>
<button type="button" data-f="all" aria-pressed="true">All</button><button type="button" data-f="open" aria-pressed="false">Open</button><button type="button" data-f="res" aria-pressed="false">Resolved</button><button type="button" data-f="upd" aria-pressed="false">Updated</button></div>
<main class="grid" id="grid"></main>
<footer>{footer}</footer>
</div>
<script>
const PAGES = {pages};
const grid = document.getElementById("grid");
PAGES.forEach(([f, t, s, res, prev, pr], i) => {{
  const n = String(i + 1).padStart(2, "0"), el = document.createElement("figure");
  el.id = "p" + n; el.setAttribute("data-comment-target", ""); el.dataset.res = res ? "1" : "0"; el.dataset.upd = prev ? "1" : "0";
  el.innerHTML = `<div class="sheet"><img src="img/${{f}}" alt="" loading="${{i < 4 ? "eager" : "lazy"}}"></div><figcaption><span class="no">${{n}}</span><span class="t"><span class="tt"></span> <span class="sec"></span></span><span class="badge${{res ? " res" : ""}}">${{res ? "Resolved" : "Open"}}</span><button class="c" type="button" id="c${{n}}" hidden>Comment</button></figcaption>`;
  el.querySelector("img").alt = n + ": " + t; el.querySelector(".tt").textContent = t; el.querySelector(".sec").textContent = s ? "· " + s : "";
  if (prev) {{
    const sh = el.querySelector(".sheet"), b = document.createElement("div"); b.className = "before";
    b.innerHTML = `<img src="img/${{prev}}" alt="${{n}} before"><span class="tag b">Before${{pr ? " · R" + pr : ""}}</span>`;
    sh.appendChild(b); sh.insertAdjacentHTML("beforeend", `<span class="tag a">After</span>`);
    const bi = b.querySelector("img"), fit = () => {{ bi.style.width = sh.clientWidth + "px"; }};
    if (window.ResizeObserver) new ResizeObserver(fit).observe(sh); fit();
    const c = document.createElement("div"); c.className = "cmp";
    c.innerHTML = `<button type="button" aria-pressed="false">Show before</button><input type="range" min="0" max="100" value="50" aria-label="${{n}} before/after split">`;
    const btn = c.querySelector("button"), rg = c.querySelector("input");
    const set = v => {{ b.style.width = v + "%"; rg.value = v; btn.setAttribute("aria-pressed", v >= 100 ? "true" : "false"); btn.textContent = v >= 100 ? "Show after" : "Show before"; }};
    rg.addEventListener("input", () => set(+rg.value));
    btn.addEventListener("click", () => set(btn.getAttribute("aria-pressed") === "true" ? 0 : 100));
    el.insertBefore(c, el.querySelector("figcaption")); set(50);
  }}
  grid.appendChild(el);
}});
const figs = [...grid.children];
document.getElementById("cnt").textContent = figs.filter(x => x.dataset.res === "1").length + " of " + figs.length + " resolved";
document.querySelectorAll(".bar button").forEach(b => b.addEventListener("click", () => {{
  document.querySelectorAll(".bar button").forEach(x => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
  const f = b.dataset.f;
  figs.forEach(x => {{ x.hidden = !(f === "all" || (f === "res" && x.dataset.res === "1") || (f === "open" && x.dataset.res === "0") || (f === "upd" && x.dataset.upd === "1")); }});
}}));
(async () => {{
  let cm = null; try {{ cm = await claude.use("comments"); }} catch (e) {{}}
  if (!cm) return;
  document.querySelectorAll("button.c").forEach(b => {{ b.hidden = false; b.addEventListener("click", async () => {{
    try {{ await cm.openComposer({{ element: b.closest("figure") }}); }}
    catch (e) {{ if (e && e.code === "unavailable") document.querySelectorAll("button.c").forEach(x => x.hidden = true); }}
  }}); }});
}})();
</script>
"""


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()


def load_state(out):
    """<out>/wall.json: {"round": n, "sheets": {source file: {hash, img, resolved, prev?}}}; empty on a first build."""
    p = os.path.join(out, "wall.json")
    st = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    st.setdefault("round", 1); st.setdefault("sheets", {})
    return st


def pick(spec, files):
    """'03,07' (sheet numbers) or source file names -> source file names."""
    out = []
    for tok in (x.strip() for x in (spec or "").split(",")):
        if not tok:
            continue
        if tok.isdigit() and 1 <= int(tok) <= len(files): out.append(files[int(tok) - 1])
        elif tok in files: out.append(tok)
        else: sys.exit(f"--resolve/--unresolve: no sheet '{tok}'")
    return out


def build(src, out, title="Review wall", titles=None, accent="", kicker="Designer review · beta",
          footer="Private review page. Comments stay with this page.", resolve="", unresolve="", new_round=False, quiet=False):
    files = sorted(f for f in os.listdir(src) if f.lower().endswith(EXT))
    if not files: sys.exit("no images in " + src)
    names = json.load(open(titles, encoding="utf-8")) if titles else None
    img = os.path.join(out, "img"); os.makedirs(os.path.join(img, "prev"), exist_ok=True)
    st = load_state(out)
    if new_round:
        st["round"] += 1
        for v in st["sheets"].values(): v["resolved"] = False
    old = st["sheets"]

    def read(rel):
        p = os.path.join(img, rel) if rel else ""
        return open(p, "rb").read() if rel and os.path.exists(p) else None

    # Hold every earlier image in memory first, so renumbered sheets can't overwrite each other's files.
    cur_bytes = {f: read(r.get("img")) for f, r in old.items()}
    prev_bytes = {f: read(r.get("prev")) for f, r in old.items()}
    sheets, pages, fmap, total = {}, [], {}, 0
    for i, f in enumerate(files):
        dst = f"{i + 1:02d}.jpg"; p = os.path.join(img, dst); sp = os.path.join(src, f)
        h = sha(sp); rec = dict(old.get(f, {})); before = prev_bytes.get(f)
        changed = bool(rec.get("hash")) and rec["hash"] != h
        if changed and cur_bytes.get(f):
            before = cur_bytes[f]; rec["prev_round"] = rec.get("round", st["round"])  # last published image becomes the "before"
        if changed:
            rec["resolved"] = False  # proofing practice: changed artwork goes back for sign-off; re-resolve after the reply
        if rec.get("hash") == h and cur_bytes.get(f):
            open(p, "wb").write(cur_bytes[f])  # unchanged: keep the exact bytes (also covers a renumber)
        else:
            im = Image.open(sp).convert("RGB"); im.thumbnail((1600, 1600), Image.LANCZOS); im.save(p, quality=82, optimize=True)
            rec["round"] = st["round"]
        pv = os.path.join(img, "prev", dst)
        if before:
            open(pv, "wb").write(before); rec["prev"] = "prev/" + dst
            fmap["img/prev/" + dst] = "img/prev/" + dst; total += len(before)
        else:
            rec.pop("prev", None); rec.pop("prev_round", None)
            if os.path.exists(pv): os.remove(pv)
        rec.update(hash=h, img=dst); rec.setdefault("resolved", False); rec.setdefault("round", st["round"])
        sheets[f] = rec
        total += os.path.getsize(p)
        t, s = (names[i] + [""])[:2] if names and i < len(names) else (os.path.splitext(f)[0].replace("_", " ").replace("-", " "), "")
        pages.append([dst, t, s]); fmap["img/" + dst] = "img/" + dst
    for f in pick(resolve, files): sheets[f]["resolved"] = True
    for f in pick(unresolve, files): sheets[f]["resolved"] = False
    for i, f in enumerate(files):
        pages[i] += [bool(sheets[f]["resolved"]), sheets[f].get("prev"), sheets[f].get("prev_round")]
    st["sheets"] = sheets
    json.dump(st, open(os.path.join(out, "wall.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    cols = [c.strip() for c in accent.split(",") if c.strip()] or ["#1D1B19"]
    strip = "".join(f'<i style="background:{html.escape(c)}"></i>' for c in cols)
    page = PAGE.format(title=html.escape(title), kicker=html.escape(kicker), h1=html.escape(title), strip=strip, round=st["round"],
                       footer=html.escape(footer), pages=json.dumps(pages, ensure_ascii=False).replace("</", "<\\/"))
    hp = os.path.join(out, "review.html"); open(hp, "w", encoding="utf-8").write(page)
    pub = {"file_path": os.path.abspath(hp), "root": os.path.abspath(out), "files": fmap,
           "capabilities": {"comments": {"composer_only": True}}, "icon": "review",
           "description": f"{len(files)} designs to review; comment on any one and send the note to Claude."}
    json.dump(pub, open(os.path.join(out, "publish.json"), "w", encoding="utf-8"), indent=1)
    if not quiet:
        nres = sum(1 for x in pages if x[3]); nprev = sum(1 for x in pages if x[4])
        print(f"{len(files)} designs (round {st['round']}: {nres} resolved, {nprev} with before/after), {total / 1e6:.1f} MB -> {hp}"
              f"\nPublish with the Artifact tool using {os.path.join(out, 'publish.json')}")
        if total > 60e6: print("WARNING: over 60 MB; publish in two batches to the same url (64 MB per publish)")
    return st, pages, pub


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--title", default="Review wall"); ap.add_argument("--titles"); ap.add_argument("--accent", default="")
    ap.add_argument("--kicker", default="Designer review · beta"); ap.add_argument("--footer", default="Private review page. Comments stay with this page.")
    ap.add_argument("--resolve", default="", help="sheets to mark resolved: numbers or source file names, comma separated")
    ap.add_argument("--unresolve", default="", help="sheets to mark open again")
    ap.add_argument("--new-round", action="store_true", help="new client round: clear every resolved flag, round +1")
    a = ap.parse_args()
    build(a.src, a.out, a.title, a.titles, a.accent, a.kicker, a.footer, a.resolve, a.unresolve, a.new_round)


if __name__ == "__main__":
    main()
