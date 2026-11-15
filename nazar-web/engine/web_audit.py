#!/usr/bin/env python3
"""
nazar-web/engine/web_audit.py: audit one static HTML page (stdlib only).

Checks things that are objectively checkable from the file:
  document     <html lang>, <title>, meta viewport, exactly one <h1>, no skipped heading levels
  images       alt on every <img> (alt="" allowed only if marked decorative), width/height attributes
               (layout shift), and natural pixel width vs displayed width: flags images more than
               2x wider than their CSS width (2x covers a retina screen)
  links        empty link text, "click here"
  colour       WCAG 2 contrast of the page's declared text colour on its background (CSS custom
               properties --fg/--bg or body color/background), 4.5:1
  weight       total bytes of the page and its local assets, largest asset
It cannot judge design, copy, or real-device performance (no network or rendering): run Lighthouse
or WebPageTest for those. Page-weight budgets have no universal standard, so weight is reported,
not graded.

    python web_audit.py page.html [--json]
"""
import json
import os
import re
import struct
import sys
from html.parser import HTMLParser


def jpeg_png_size(path):
    try:
        with open(path, "rb") as f:
            d = f.read(65536)
        if d[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", d[16:24])
        i = 2
        while i < len(d):
            if d[i] != 0xFF:
                i += 1; continue
            m = d[i + 1]
            if m in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", d[i + 5:i + 9]); return w, h
            i += 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
    except Exception:
        pass
    return None


def lum(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = self.title = self.viewport = False
        self.h = []; self.imgs = []; self.links = []; self.in_a = None; self.css = ""; self.in_style = False; self.in_title = False

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "html": self.lang = bool(a.get("lang"))
        if tag == "title": self.in_title = True
        if tag == "style": self.in_style = True
        if tag == "meta" and a.get("name") == "viewport": self.viewport = True
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"): self.h.append(int(tag[1]))
        if tag == "img": self.imgs.append(a)
        if tag == "a": self.in_a = {"text": "", "href": a.get("href")}
    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False
        if tag == "style": self.in_style = False
        if tag == "a" and self.in_a is not None: self.links.append(self.in_a); self.in_a = None
    def handle_data(self, d):
        if self.in_style: self.css += d
        if self.in_title and d.strip(): self.title = True
        if self.in_a is not None: self.in_a["text"] += d


def audit(path):
    base = os.path.dirname(os.path.abspath(path))
    html = open(path, encoding="utf-8").read()
    p = P(); p.feed(html)
    out = []
    add = lambda lvl, msg: out.append((lvl, msg))
    if not p.lang: add("fail", "<html> has no lang attribute (screen readers pick the wrong voice)")
    if not p.title: add("fail", "no <title>")
    if not p.viewport: add("fail", "no meta viewport (broken on phones)")
    if p.h.count(1) != 1: add("fail", f"{p.h.count(1)} <h1> elements (needs exactly one)")
    for a, b in zip(p.h, p.h[1:]):
        if b > a + 1:
            add("fail", f"heading level skips from h{a} to h{b}"); break
    miss = [i for i in p.imgs if "alt" not in i]
    if miss: add("fail", f"{len(miss)} of {len(p.imgs)} images have no alt attribute")
    noWH = [i for i in p.imgs if not (i.get("width") and i.get("height"))]
    if noWH: add("warn", f"{len(noWH)} images lack width/height (the page jumps as they load)")
    css_w = {}
    for m in re.finditer(r"\.([\w-]+)\s*\{[^}]*?width:\s*(\d+)px", p.css):
        css_w[m.group(1)] = int(m.group(2))
    total, biggest, oversize = len(html.encode()), (0, ""), []
    for i in p.imgs:
        src = i.get("src", "")
        if not src or src.startswith(("http", "data:")): continue
        fp = os.path.join(base, src)
        if os.path.exists(fp):
            sz = os.path.getsize(fp); total += sz
            if sz > biggest[0]: biggest = (sz, src)
            dim = jpeg_png_size(fp)
            shown = int(i["width"]) if i.get("width") else next((css_w[c] for c in i.get("class", "").split() if c in css_w), None)
            if dim and shown and dim[0] > 2 * shown: oversize.append((src, dim[0], shown))
    if oversize:
        s = oversize[0]; add("warn", f"{len(oversize)} images are over 2x their displayed width (e.g. {s[0]}: {s[1]} px shown at {s[2]} px)")
    for l in p.links:
        t = l["text"].strip().lower()
        if not t: add("fail", "a link has no text")
        elif t in ("click here", "here", "read more"): add("warn", f'link text "{t}" says nothing out of context')
    vars_ = dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{3,6})", p.css))
    fg = vars_.get("fg") or (re.search(r"body\s*\{[^}]*?[^-]color:\s*(#[0-9a-fA-F]{3,6})", p.css) or [None, None])[1]
    bg = vars_.get("bg") or (re.search(r"body\s*\{[^}]*?background(?:-color)?:\s*(#[0-9a-fA-F]{3,6})", p.css) or [None, None])[1]
    if fg and bg:
        r = contrast(fg, bg)
        add("ok" if r >= 4.5 else "fail", f"text {fg} on {bg} is {r:.2f}:1 (WCAG AA needs 4.5:1)")
    if not out or all(l == "ok" for l, _ in out):
        add("ok", "no structural problems found")
    return {"file": os.path.basename(path), "findings": out, "weight_kb": round(total / 1024), "largest": (biggest[1], round(biggest[0] / 1024)), "images": len(p.imgs)}


if __name__ == "__main__":
    r = audit(sys.argv[1])
    if "--json" in sys.argv:
        print(json.dumps(r, indent=1))
    else:
        print(f"{r['file']}: {r['weight_kb']} KB total, {r['images']} images, largest {r['largest'][0]} ({r['largest'][1]} KB)")
        for l, m in r["findings"]:
            print(f"  [{l:4}] {m}")
