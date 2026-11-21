"""Six-page demo of deck.py, built only from nazar-core's sample assets (the example mark and device SVGs).

    python nazar-pitch/engine/example_deck.py            -> out_example/Example_Co.pdf + contact sheet
    BEHANCE=1 python nazar-pitch/engine/example_deck.py  -> out_example/behance/ panels + covers

The 'cards' below are sample stand-ins rendered from the mark (a front in a colour, a back on paper), so the
compose helpers have something to overlap. On a real job you place the client's exact pack renders instead.
"""
import os, sys
import cairosvg
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from deck import Deck, CORE, couple, fan, toss, bleed, ar

OUT = os.path.join(HERE, "out_example")
TOKENS = {"name": "Example Co.", "folio": "Example Co. · deck engine demo · Nazar Studio",
          "colours": {"paper": "#EFE9DF", "ink": "#1B1A17", "mute": "#6B655B", "accent": "#E8572A", "dark": "#26211E"}}
d = Deck(TOKENS, OUT)
MARK = os.path.join(CORE, "example", "logo", "mark.svg"); DEV = os.path.join(CORE, "example", "logo", "device.svg")
TINTS = [("Signal", "#E8572A"), ("Moss", "#5E7A4A"), ("Indigo", "#3A4A7A"), ("Ochre", "#C9962E"), ("Plum", "#7A3A5E")]


def card(name, tint, back=False):
    """A 600 x 900 sample card: front = tint + device + name; back = paper + facts block. Transparent corners."""
    p = os.path.join(d.cache, f"card_{name.lower()}_{'back' if back else 'front'}.png")
    if os.path.exists(p): return p
    w, h = 600, 900; ink = "#FFF" if not back else d.INK
    b = f'<rect width="{w}" height="{h}" rx="36" fill="{d.PAPER if back else tint}"/>'
    if back:
        b += d.rect(48, 60, w - 96, 14, tint) + d.tx("FACTS", 48, 150, 22, "label", fill=d.MUTE, track=0.14)
        for i, ln in enumerate(["Net 100 g", "One ingredient", "Batch 0011", "Made by hand"]):
            b += d.tx(ln, 48, 230 + i * 70, 30, "text", fill=d.INK) + d.rect(48, 250 + i * 70, w - 96, 2, d.MUTE, op=0.3)
        b += d.svg_file(DEV, 48, h - 200, 140, 140, fill=tint)
    else:
        b += d.svg_file(DEV, 60, 70, 220, 220, fill="#FFF") + d.fit(name.upper(), 60, h - 120, 96, w - 120, fill=ink)
        b += d.tx("EXAMPLE CO.", 60, h - 60, 18, "label", fill=ink, track=0.16)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{b}</svg>'
    cairosvg.svg2png(bytestring=svg.encode(), write_to=p, output_width=w * 2); return p


FR = [card(n, t) for n, t in TINTS]; BK = [card(n, t, True) for n, t in TINTS]

# 01 hero: one card huge and turned, bleeding off the right edge; name top-left
b = d.img(bleed(FR[0], d.cache, 1100, 1080, 1250, 560, 560, angle=-8), d.W - 1100, 0, 1100, 1080, bg=d.DARK)
b += d.tx("EXAMPLE CO.", 80, 120, 40, fill="#FFF") + d.tx("DECK ENGINE · DEMO", 80, 162, 14, "label", fill="#CFC6BB", track=0.16)
b += d.para("Every page one idea, one device, nothing stacked.", 80, 860, 30, 620, "text", fill="#FFF")[0]
d.page(b, "hero bleed", bg=d.DARK, folio=False)

# 02 the idea: big line left, the exact mark right
b = d.top("The idea", "One mark, five colours.", maxw=900)
b += d.para("The sample mark from nazar-core, placed as the file it is. Each colour gets a name of its own.", 80, 420, 24, 760, "text", fill=d.MUTE, maxh=200)[0]
b += d.svg_file(MARK, 1100, 200, 700, 700)
d.page(b, "split: line left, mark right")

# 03 range: five fronts as a hand of cards
b = d.top("The range", "Pick any colour.") + d.img(fan(FR, d.cache), 60, 260, d.W - 120, 720)
b += d.label("  ·  ".join(n for n, _ in TINTS), d.W / 2, 1010)
d.page(b, "fan of fronts")

# 04 turn over: front leading, its own back behind, three couples on a colour field
b = d.top("Turn it over", "Front sells, back tells.", ink="#FFF")
cw = (d.W - 120) / 3
for j, i in enumerate((1, 2, 4)):
    x = 60 + j * cw
    b += d.img(couple(FR[i], BK[i], d.cache), x + 10, 280, cw - 20, 680, bg=TINTS[3][1]) + d.label(TINTS[i][0], x + cw / 2, 1010, fill="#FFF")
d.page(b, "front-back couples", bg=TINTS[3][1], ink="#FFF")

# 05 scale: the backs tossed on paper, small text block left
b = d.top("Every back", "Same card, same order.", maxw=620)
b += d.para("Facts sit in the same place on every colour, so a shopper learns it once.", 80, 440, 22, 560, "text", fill=d.MUTE)[0]
b += d.img(toss(BK, d.cache), 720, 60, 1140, 960)
d.page(b, "toss of backs")

# 06 contact: dark panel with the mark, contact list right (the studio page before thank-you)
b = d.rect(0, 0, 760, d.H, d.INK) + d.svg_file(DEV, 80, 200, 300, 300, fill="#FFF")
b += d.fit("Nazar Studio", 80, 640, 64, 620, fill="#FFF") + d.para("Sample contact page. Ask the owner for real details; never invent them.", 80, 720, 22, 600, "text", fill="#CFC6BB")[0]
b += d.tx("SAY HELLO", 880, 88, 16, "label", track=0.14) + d.fit("Let's talk.", 880, 200, 72, 960)
for i, (k, v) in enumerate([("Email", "studio@example.com"), ("Phone", "+00 000 0000000"), ("Web", "example.com")]):
    y = 380 + i * 140
    b += d.rect(880, y - 58, 8, 72, TINTS[i][1]) + d.label(k, 912, y - 40, anchor="start", size=14) + d.fit(v, 912, y + 12, 34, 920, "bold")
d.page(b, "studio contact split")

d.build()
