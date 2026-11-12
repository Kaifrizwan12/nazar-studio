"""Example pages: one of each page type. Copy, rename (pages_a.py, pages_b.py ...) and replace per brand.

Every page function returns a Page. Register it in PAGES, in book order.
"""
from lib import *

SEC = dict(BRAND["sections"])
def sec(n): return f"{n} · {SEC[n].upper()}"

def cover():
    p = Page("00.1", "Cover", "", DARK); p.furniture = False; p.grain = True
    p.add(logo_centered("mark", W / 2, H / 2 - 40, 360))
    p.add(text(BRAND["name"].upper(), W / 2, H / 2 + 230, 15, "label", LIGHT_, 0.8, 0.3, "middle"))
    return p

def dictionary():
    """Front-matter device: the name as a dictionary entry."""
    p = Page("00.2", "Definition", sec("00"), LIGHT)
    x = col_x(2)
    p.add(text("SIGN — SIGNAL", W - M, 152, 13, "label", SEC_D, track=0.08, anchor="end"))
    p.add(text("signal", x, 460, 72, "text-l", BASE))
    p.add(text("/sig-nəl/   n.", x, 510, 19, "label", SEC_D))
    body, _ = para("a sign that carries one meaning across a distance, and arrives intact.",
                   x, 580, 28, COL * 7 + GUTTER * 6, "text", BASE)
    p.add(body).device(W - M - 18, 880)
    return p

def contents():
    p = Page("00.3", "Contents", sec("00"), LIGHT)
    p.heading("Contents", "Why, then the idea, then how it looks.")
    nums = page_numbers()
    first = {"00": "00.1", "01": "01.0", "02": "02.1", "03": "03.1", "04": "04.1", "09": "09.1"}
    y = 380
    for n, name in BRAND["sections"]:
        pg = nums.get(first.get(n), "")
        p.add(text(n, col_x(2), y, 19, "label", SEC_D), text(name, col_x(3), y, 28, "text", BASE),
              hair(col_x(3) + width("text", name, 28) + 24, y - 6, col_x(10) - 24, y - 6, BASE, 0.25, 1, "1 4"),
              text(f"{pg:02d}" if pg else "", col_x(10), y, 19, "label", ACCENT))
        y += 64
    return p.device(W - M - 18, H - M - 40)

def divider():
    p = Page("01.0", "Divider", sec("01"), DARK); p.grain = True
    p.add(text("01", M, 300, 160, "text-l", LIGHT_))
    p.add(text(SEC["01"], M, H - M - 20, 48, "text", LIGHT_))
    p.add(logo("mark", W - M - 520, 220, 520, op=0.9))
    return p.device(M + 300, H - M - 120)

def statement():
    p = Page("01.1", "The idea", sec("01"), DARK)
    y = p.heading("The idea", "One idea, carried everywhere.", "Nine pages, one signal.")
    for i in range(9):   # the graphic does the talking: nine suns, the ninth is the accent
        cx = col_x(1) + i * 180
        p.add(circle(cx, 640, 54, ACCENT if i == 8 else LIGHT_, 1 if i == 8 else 0.12))
        p.add(text(f"PAGE {i + 1}", cx, 740, 12, "label", SEC, track=0.08, anchor="middle"))
    return p.device(W - M - 18, 900)

def logo_primary():
    p = Page("02.1", "Primary mark", sec("02"), LIGHT)
    p.heading("The mark", "Use this wherever possible.", "Exact artwork only. Never redrawn.")
    p.add(logo("mark", M, 330, 560))
    x = col_x(7)
    for i, (k, v) in enumerate([("EXACT ARTWORK", "Use the supplied SVG or PNG."), ("MINIMUM 24 PX", "Below that, use the device."),
                                ("CLEAR SPACE", "One mark-height on every side.")]):
        y = 420 + i * 130
        p.add(text(k, x, y, 13, "label", ACCENT, track=0.08), text(v, x, y + 40, 28, "text", BASE), hair(x, y + 70, W - M, y + 70, BASE, 0.12))
    return p.device(W - M - 18, H - M - 40)

def palette():
    p = Page("03.1", "Palette", sec("03"), LIGHT)
    p.heading("Colour", "Four colours, by share.")
    keys = [k for k, v in BRAND["colours"].items() if v.get("share")]
    total = sum(BRAND["colours"][k]["share"] for k in keys)
    x, span = M, W - 2 * M
    lw = (span - (len(keys) - 1) * GUTTER) / len(keys)          # labels sit in equal columns: small shares never collide
    for i, k in enumerate(keys):
        c = BRAND["colours"][k]; w = span * c["share"] / total
        lx = M + i * (lw + GUTTER)
        p.add(rect(x, 340, w - 8, 420, c["hex"], stroke=BASE, sw=1, sop=0.1))
        p.add(rect(lx, 818, 22, 22, c["hex"], stroke=BASE, sw=1, sop=0.15))
        p.add(text(c["name"], lx + 38, 840, 28, "text", BASE), text(c["meaning"], lx + 38, 874, 19, "text", SEC_D),
              text(f'{c["hex"].upper()} · {c["share"]}%', lx + 38, 910, 13, "label", SEC_D, track=0.05))
        x += w
    return p.device(W - M - 18, 160)

def pairings():
    p = Page("03.2", "Pairings", sec("03"), DARK)
    p.heading("Pairings", "What sits on what.", "Contrast ratios are measured, not guessed.")
    pairs = [(BASE, LIGHT_), (LIGHT_, BASE), (BASE, ACCENT), (LIGHT_, SEC_D)]
    tw = (W - 2 * M - 3 * GUTTER) / 4
    for i, (bg, fg) in enumerate(pairs):
        x = M + i * (tw + GUTTER)
        p.add(rect(x, 360, tw, 360, bg, stroke=LIGHT_, sw=1, sop=0.15), text("Aa", x + 40, 520, 96, "text", fg))
        p.add(text(f"{contrast(bg, fg):.1f} : 1", x + 40, 680, 13, "label", fg, track=0.08))
    return p.device(W - M - 18, H - M - 40)

def type_scale():
    p = Page("04.1", "Type", sec("04"), DARK)
    p.heading("Type", "Three roles. Never bold for lines.")
    rows = [("display", "EXAMPLE", 120, "DISPLAY · ANTON · LOGO, POSTERS"), ("text", "One idea per page.", 48, "TEXT · SPACE GROTESK REGULAR"),
            ("label", "PAGE 07 · SECTION 04 · 2026", 19, "LABEL · SPACE MONO")]
    y = 470
    for key, s, size, note in rows:
        p.add(text(s, M, y, size, key, LIGHT_), text(note, W - M, y, 12, "label", SEC, track=0.08, anchor="end"),
              hair(M, y + 30, W - M, y + 30, LIGHT_, 0.1))
        y += size + 110
    return p.device(W - M - 18, 160)

def reveal():
    p = Page("09.1", "Reveal", sec("09"), DARK)
    p.heading("The hidden device", "Where it was hiding.", "One on every page. Did you find it?")
    return p                      # build.py fills the thumbnails on its second pass

PAGES = [cover, dictionary, contents, divider, statement, logo_primary, palette, pairings, type_scale, reveal]
