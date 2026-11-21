"""Review wall: a folder of designs -> a private live page (beta, for the designer) to comment on each design in progress,
and every note sent with "Send to Claude" lands in the working chat. Generic, brand-free.

    python review_wall.py <images folder> <out folder> --title "Brand review" [--titles titles.json] [--accent "#hex,#hex"]

Writes <out>/review.html, <out>/img/NN.jpg (max 1600 px, 16:9 or as-is) and <out>/publish.json: the exact
Artifact publish arguments (file_path, root, files map, capabilities). Claude then publishes it in one call.
titles.json (optional): [["Title", "section"], ...] in file order; otherwise titles come from the file names.
Guide: references/review_wall.md.
"""
import os, sys, json, argparse, html
from PIL import Image

EXT = (".png", ".jpg", ".jpeg", ".webp")

PAGE = """<title>{title}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap">
<style>
/* Layout: a contact-sheet wall, one numbered sheet per design, in the order given; brand colours run as a strip under the header. */
:root{{--bg:#EEEAE4;--paper:#FAF8F5;--ink:#1D1B19;--mute:#6C655F;--line:#D8D1C8;--focus:#1D1B19;
  --display:"Space Grotesk",system-ui,sans-serif;--body:"Inter",system-ui,-apple-system,sans-serif}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#161412;--paper:#201D1B;--ink:#F2EEE8;--mute:#A49B92;--line:#38322D;--focus:#F2EEE8;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#161412;--paper:#201D1B;--ink:#F2EEE8;--mute:#A49B92;--line:#38322D;--focus:#F2EEE8;color-scheme:dark}}
body{{background:var(--bg);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.5}}
.wrap{{max-width:1280px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:40px 64px}}
header{{display:grid;gap:12px;padding-block-end:18px}}
.kicker{{font:700 12px var(--display);letter-spacing:.16em;text-transform:uppercase;color:var(--mute)}}
h1{{font-family:var(--display);font-weight:700;font-size:clamp(40px,7vw,80px);line-height:.95;margin:0;text-wrap:balance}}
.how{{max-width:62ch;color:var(--mute);margin:0}} .how b{{color:var(--ink);font-weight:600}}
.strip{{display:grid;grid-auto-flow:column;height:8px;margin-block:8px 28px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,480px),1fr));gap:28px 24px}}
figure{{margin:0;display:grid;gap:10px;min-width:0}}
.sheet{{background:var(--paper);border:1px solid var(--line);max-width:100%;overflow:hidden}}
.sheet img{{display:block;width:100%;height:auto}}
figcaption{{display:flex;align-items:baseline;gap:12px;min-width:0}}
.no{{font:700 13px var(--display);color:var(--mute);font-variant-numeric:tabular-nums;flex:none}}
.t{{font:700 17px/1.25 var(--display);flex:1;min-width:0}} .sec{{font:500 12px var(--body);color:var(--mute);letter-spacing:.05em;text-transform:uppercase}}
button.c{{flex:none;font:600 13px var(--body);color:var(--ink);background:transparent;border:1.5px solid var(--ink);border-radius:999px;padding:6px 14px;cursor:pointer}}
button.c:hover{{background:var(--ink);color:var(--paper)}} button.c:focus-visible{{outline:3px solid var(--focus);outline-offset:2px}}
footer{{margin-top:48px;color:var(--mute);font-size:13px}}
</style>
<div class="wrap">
<header><span class="kicker">{kicker}</span><h1>{h1}</h1>
<p class="how">Every design, numbered. <b>Press Comment under a design</b> (or turn on comment mode and click any sheet), write one note per change, and choose <b>Send to Claude</b>: it reaches the working session, which fixes it and republishes this page.</p></header>
<div class="strip" aria-hidden="true">{strip}</div>
<main class="grid" id="grid"></main>
<footer>{footer}</footer>
</div>
<script>
const PAGES = {pages};
const grid = document.getElementById("grid");
PAGES.forEach(([f, t, s], i) => {{
  const n = String(i + 1).padStart(2, "0"), el = document.createElement("figure");
  el.id = "p" + n; el.setAttribute("data-comment-target", "");
  el.innerHTML = `<div class="sheet"><img src="img/${{f}}" alt="" loading="${{i < 4 ? "eager" : "lazy"}}"></div><figcaption><span class="no">${{n}}</span><span class="t"><span class="tt"></span> <span class="sec"></span></span><button class="c" type="button" id="c${{n}}" hidden>Comment</button></figcaption>`;
  el.querySelector("img").alt = n + ": " + t; el.querySelector(".tt").textContent = t; el.querySelector(".sec").textContent = s ? "· " + s : "";
  grid.appendChild(el);
}});
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


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--title", default="Review wall"); ap.add_argument("--titles"); ap.add_argument("--accent", default="")
    ap.add_argument("--kicker", default="Designer review · beta"); ap.add_argument("--footer", default="Private review page. Comments stay with this page.")
    a = ap.parse_args()
    files = sorted(f for f in os.listdir(a.src) if f.lower().endswith(EXT))
    if not files: sys.exit("no images in " + a.src)
    names = json.load(open(a.titles, encoding="utf-8")) if a.titles else None
    os.makedirs(os.path.join(a.out, "img"), exist_ok=True)
    pages, fmap, total = [], {}, 0
    for i, f in enumerate(files):
        dst = f"{i + 1:02d}.jpg"; p = os.path.join(a.out, "img", dst)
        im = Image.open(os.path.join(a.src, f)).convert("RGB"); im.thumbnail((1600, 1600), Image.LANCZOS); im.save(p, quality=82, optimize=True)
        total += os.path.getsize(p)
        t, s = (names[i] + [""])[:2] if names and i < len(names) else (os.path.splitext(f)[0].replace("_", " ").replace("-", " "), "")
        pages.append([dst, t, s]); fmap["img/" + dst] = "img/" + dst
    cols = [c.strip() for c in a.accent.split(",") if c.strip()] or ["#1D1B19"]
    strip = "".join(f'<i style="background:{html.escape(c)}"></i>' for c in cols)
    page = PAGE.format(title=html.escape(a.title), kicker=html.escape(a.kicker), h1=html.escape(a.title), strip=strip,
                       footer=html.escape(a.footer), pages=json.dumps(pages, ensure_ascii=False).replace("</", "<\\/"))
    hp = os.path.join(a.out, "review.html"); open(hp, "w", encoding="utf-8").write(page)
    pub = {"file_path": os.path.abspath(hp), "root": os.path.abspath(a.out), "files": fmap,
           "capabilities": {"comments": {"composer_only": True}}, "icon": "review",
           "description": f"{len(files)} designs to review; comment on any one and send the note to Claude."}
    json.dump(pub, open(os.path.join(a.out, "publish.json"), "w", encoding="utf-8"), indent=1)
    print(f"{len(files)} designs, {total / 1e6:.1f} MB -> {hp}\nPublish with the Artifact tool using {os.path.join(a.out, 'publish.json')}")
    if total > 60e6: print("WARNING: over 60 MB; publish in two batches to the same url (64 MB per publish)")


if __name__ == "__main__":
    main()
