"""Hero illustration: "Helping Hands". The machine does the cranking; Nazar does the choosing.

    python examples/helping_hands.py        # → exports/illustration/helping_hands(.svg/.png, _riso.png)

Concept lock (one sentence): white gloves (the AI) feed and crank a chrome press; the person's own hand picks the one card
worth keeping. The head stays human and calm.
Composition: gallery-still, 3/4 seated figure in the left third, lit from the left, big quiet wall. The press sits right of
centre; the crank glove makes the high diagonal; cards fan from the press toward the figure's hand (eye path: gloves →
press → cards → hand → face). Focal: the hand lifting the single accent card.
Clothes: black turtleneck; camel overcoat draped over the shoulders: padded shoulder, notch lapels, the near EMPTY sleeve
hangs loose (the tell of a draped coat); the reaching arm comes from under the coat front.
Budget: line ink + wall, table, camel, turtleneck, chrome, glove white, skin + ONE accent. 3 weights: 1.25 / 0.75 / 0.22.
Light: upper left; every shadow (hatch) falls right and down.

Review: code drawing reached "reads clearly" but not "art-level" for a multi-figure scene. The advanced route (with the
client's written approval) is this image prompt, e.g. for Gemini / Nano Banana Pro:
  Purpose: hero illustration for a design studio's website, 3:2, quiet wall space top-right for a headline added later.
  An editorial illustration in a hand-inked style with flat risograph colours and slight misregistration, visible paper
  grain. A calm man in a black turtleneck sits three-quarters to the right at a plain table, a camel overcoat draped over
  his shoulders with the near empty sleeve hanging loose. His eyes are lowered; his own hand picks up a single bright
  vermilion card from a fan of pale cards. Right of centre stands a chrome hand-crank press (a pasta machine crossed with a
  letterpress: rounded side plates, two rollers, a funnel hopper, a crank). Two disembodied white cartoon gloves operate
  it: one turns the crank, the other drops papers, a code bracket, a tiny chart and a meme square into the hopper. Pale
  grey-blue wall, warm off-white table, one soft light from the upper left. Palette: grey-blue, cream, camel, near-black,
  chrome grey, one vermilion accent. Gallery-still, silent, no text, no glow, no gradients.
"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engine"))
from ink import Sheet, ellipse_pts, arc_pts

WALL, TABLE, CAMEL, TURTLE, CHROME, CHROME_D, GLOVE, SKIN, HAIR, ACCENT, CARD = (
    "#D3DCE0", "#ECE5D8", "#B98656", "#262523", "#C9CED1", "#878F95", "#FBFAF6", "#C99C78", "#2A2522", "#E4572E", "#F6F2E8")
LIT, GREY = "#6C6862", "#9AA0A4"
C, D, Hh = 1.25, 0.75, 0.22
s = Sheet(240, 160, paper=WALL, seed=21, hand=1.0)

def rot(cx, cy, a):
    r = math.radians(a)
    return lambda x, y: (cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r))

# ================================================================ figure (behind the table)
# turtleneck torso, 3/4 (far side narrower)
torso = [(53, 54), (66, 51.5), (79, 54), (87, 110), (47, 110)]
s.flat(torso, TURTLE)
s.stroke([(55.5, 58), (51.5, 84), (50, 108)], width=0.5, colour=LIT, taper=0.3)

# far coat panel (right of the turtleneck), lapel
coat_far = [(73, 52.5), (82, 53.5), (89, 60), (91, 110), (81, 110), (80.5, 82), (76, 64)]
s.flat(coat_far, CAMEL, offset=(0.6, -0.4))
s.hatch(s.shape(coat_far), angle=66, gap=1.2, width=Hh, tone=2)
s.stroke(coat_far, width=C, closed=True)
s.stroke([(74.5, 53.5), (79.5, 64), (80.5, 76)], width=D)                               # far lapel roll


# near coat body + padded shoulder
coat_near = [(62, 51.5), (52, 51), (42, 54), (36.5, 61), (35, 85), (36, 110), (56, 110), (55, 86), (57, 68), (61, 57)]
s.flat(coat_near, CAMEL, offset=(0.6, -0.4))
s.hatch(s.shape([(37, 90), (48, 88), (55, 96), (55.5, 109), (37, 109)]), angle=66, gap=1.5, width=Hh, tone=1)
s.stroke(coat_near, width=C, closed=True)
s.stroke([(60.5, 52.5), (56, 61), (58.5, 63.5), (55.5, 74)], width=D, corners=True)     # notch lapel
s.stroke([(43, 55), (49, 53.3), (56, 53.2)], width=0.5, colour=LIT, taper=0.3)          # shoulder pad edge, lit

# the EMPTY near sleeve hanging loose from the shoulder (in front of the coat)
sleeve = [(37.5, 58), (45.5, 59.5), (46, 74), (44.5, 99), (35.5, 99.5), (35, 80)]
s.flat(sleeve, CAMEL, offset=(0.6, -0.4))
s.stroke(sleeve, width=C, closed=True)
s.stroke([(35.6, 96.2), (44.6, 95.7)], width=D)                                          # cuff
s.stroke([(41, 63), (42.2, 78), (40.5, 92)], width=0.45, taper=0.35)                     # sleeve fold
s.stroke([(38.5, 99.8), (39.5, 101.5)], width=0.4)                                       # hollow cuff opening
s.hatch(s.shape([(41.5, 62), (45.4, 61), (45.6, 75), (44.3, 98), (41, 98)]), angle=70, gap=1.1, width=Hh, tone=2)

# turtleneck collar + neck
collar = [(59.5, 44.5), (71.5, 44.5), (72.5, 53), (58.5, 53)]
s.flat(collar, TURTLE, smooth=False)
s.stroke([(59.5, 44.5), (58.5, 53), (65.5, 54.5), (72.5, 53), (71.5, 44.5)], width=C)
for y in (47.3, 50.3):
    s.stroke([(59.8, y), (65.5, y + 0.9), (71.3, y)], width=0.33, colour=LIT)

# head: 3/4, facing right and slightly down toward the cards. Calm, eyes lowered.
head = [(60.5, 24), (69, 21.5), (76, 26), (77.3, 33), (75.8, 36.5), (76.6, 38.2), (74.5, 40), (72, 44.5), (65, 45.5), (60.5, 41.5), (58.5, 33)]
s.flat(head, SKIN, offset=(0.4, -0.3))
s.hatch(s.shape([(59, 33), (62, 31), (63.5, 41), (65.5, 45), (61, 42)]), angle=60, gap=0.9, width=0.18, tone=1)   # far cheek shade
s.stroke(head, width=C, closed=True)
hair = [(58.6, 33.5), (58.8, 26), (64, 20.6), (71.5, 20.2), (76.8, 24.8), (76.2, 27.6), (70, 26.2), (64.5, 28.5), (62.5, 34.5), (60.4, 37)]
s.flat(hair, HAIR)
s.stroke(hair, width=0.9, closed=True)
s.stroke(arc_pts(71.5, 31.2, 2.0, 15, 165, 5), width=0.55)                               # lowered eyelid
s.stroke([(70.2, 29.4), (73.2, 28.9)], width=0.5)                                        # brow
s.stroke([(76.8, 34.2), (77.6, 37.4), (75.9, 37.9)], width=0.55, corners=True)           # nose
s.stroke([(73.2, 40.9), (75.0, 40.6)], width=0.45)                                       # mouth, quiet
s.stroke(ellipse_pts(62.4, 35.2, 1.6, 2.4, n=7), width=0.6, closed=True)                 # ear

# ================================================================ table
s.flat([(-6, 108), (246, 108), (246, 166), (-6, 166)], TABLE, smooth=False)
s.stroke([(0, 108.4), (90, 108), (170, 108.5), (240, 108.2)], width=C, taper=0.02, pressure="even")

# reaching arm: out from under the far coat front, over the table edge (drawn after the table)
arm = [(79.5, 76), (85, 74.5), (108, 104), (103, 110), (80.5, 88)]
s.flat(arm, TURTLE)
s.stroke([(81, 75.5), (85.5, 74.5), (107.5, 104)], width=0.5, colour=LIT, taper=0.3)
s.stroke([(85, 74.5), (108, 104), (103, 110), (80.5, 88)], width=C)
flap = [(80.2, 70), (88.8, 71), (90, 80), (81, 90.5)]                                       # coat front falls over the arm's root
s.flat(flap, CAMEL, smooth=False, offset=(0.6, -0.4))
s.hatch(s.shape(flap, smooth=False), angle=66, gap=1.2, width=Hh, tone=2)
s.stroke([(88.8, 71), (90, 80), (81, 90.5)], width=C)

# figure's hand on the table, lifting the accent card (focal)
s.hatch([(100, 113), (120, 116), (118, 119), (98, 116)], angle=-15, gap=0.8, width=Hh, tone=1)   # hand + card shadow
pick = rot(115, 112, -14)
card_pts = [pick(-7, -5), pick(7, -5), pick(7, 5), pick(-7, 5)]
s.flat(card_pts, ACCENT, smooth=False, offset=(0.4, -0.3))
s.stroke(card_pts, width=D, closed=True, corners=True)
s.stroke([pick(-4.5, -1.8), pick(3.5, -1.8)], width=0.9, colour=CARD, pressure="even", taper=0.05)
hand = [(102, 105), (108.5, 103.2), (113.5, 106), (114.5, 109.5), (111.5, 112), (104.5, 111.5)]
s.flat(hand, SKIN, offset=(0.4, -0.3))
s.stroke(hand, width=D, closed=True)
s.stroke([(110.5, 107.2), (114.6, 108.3)], width=0.4)                                    # pinch: index over the card
s.stroke([(106.5, 109.8), (111, 110.6)], width=0.35)                                     # thumb crease

# ================================================================ the press (pasta machine × letterpress), right of centre
base = [(126, 99), (186, 99), (186, 113), (126, 113)]
s.flat(base, CHROME_D, smooth=False)
s.flat([(126, 99), (186, 99), (186, 102.5), (126, 102.5)], CHROME, smooth=False)        # top bevel catches light
s.stroke(base, width=C, closed=True, corners=True)
s.stroke([(126.5, 102.5), (185.5, 102.5)], width=D, pressure="even", taper=0.05)
slot = [(140, 106.2), (172, 106.2), (172, 108.6), (140, 108.6)]                          # output slot
s.flat(slot, TURTLE, smooth=False); s.stroke(slot, width=D, closed=True, corners=True)
s.hatch([(176, 103), (185.5, 103), (185.5, 112.5), (176, 112.5)], angle=90, gap=0.8, width=0.2, tone=2)

for x0 in (131, 171):                                                                    # side plates, rounded tops
    plate = [(x0, 99), (x0, 64)] + arc_pts(x0 + 5, 64, 5, 180, 360, 8)[1:-1] + [(x0 + 10, 64), (x0 + 10, 99)]
    s.flat(plate, CHROME, smooth=False)
    s.hatch([(x0 + 6.8, 63), (x0 + 9.6, 63), (x0 + 9.6, 98.6), (x0 + 6.8, 98.6)], angle=90, gap=0.7, width=0.18, tone=2)
    s.stroke(plate, width=C, closed=True, corners=True)
    s.stroke([(x0 + 2.2, 66), (x0 + 2.4, 95)], width=0.8, colour="#FFFFFF", pressure="even", taper=0.12)   # chrome highlight
for y0 in (70, 80):                                                                      # two rollers between the plates
    roller = [(141, y0), (171, y0), (171, y0 + 7.5), (141, y0 + 7.5)]
    s.flat(roller, CHROME, smooth=False)
    s.flat([(141, y0 + 4.8), (171, y0 + 4.8), (171, y0 + 7.5), (141, y0 + 7.5)], CHROME_D, smooth=False)
    s.stroke([(141.5, y0 + 1.6), (170.5, y0 + 1.6)], width=0.7, colour="#FFFFFF", pressure="even", taper=0.08)
    s.stroke([(141, y0), (171, y0)], width=D, pressure="even", taper=0.03)
    s.stroke([(141, y0 + 7.5), (171, y0 + 7.5)], width=D, pressure="even", taper=0.03)
s.stroke([(141.5, 88.5), (156, 89.6), (170.5, 88.5)], width=0.4, colour=GREY)           # paper path between rollers
hopper = [(137, 44), (175, 44), (165, 64), (147, 64)]
s.flat(hopper, CHROME, smooth=False)
s.hatch([(160, 45), (174, 45), (165, 63.5), (158, 63.5)], angle=72, gap=0.85, width=0.19, tone=2)
s.stroke(hopper, width=C, closed=True, corners=True)
s.stroke(ellipse_pts(156, 44, 19, 2.6, n=12), width=D, closed=True)
# crank: hub on the right plate, arm, turned handle
s.flat(ellipse_pts(176, 73, 3.4, 3.4, n=8), CHROME_D)
s.stroke(ellipse_pts(176, 73, 3.4, 3.4, n=8), width=D, closed=True)
s.stroke([(176, 73), (186, 67.5), (194, 62.5)], width=2.0, pressure="even", taper=0.04)
s.stroke([(194, 62.5), (196, 56.5)], width=2.4, pressure="even", taper=0.05)             # handle grip

# ================================================================ the gloves (the AI): white, disembodied, busy
def glove(cx, cy, a, open_hand=False):
    """Cartoon white glove: palm, four rounded fingers, thumb, three stitch lines, flared cuff."""
    g = rot(cx, cy, a)
    P = lambda pts: [g(x, y) for x, y in pts]
    if open_hand:      # fingers spread downward, letting things drop
        fingers = [(-4.6, 4, -6.2, 11.5, 13), (-1.6, 4.6, -2.0, 13.2, 6), (1.6, 4.6, 2.0, 13.0, -4), (4.4, 4, 5.4, 11.2, -12)]
    else:              # curled round the handle: short knuckle bumps
        fingers = [(-4.5, 4, -4.8, 7.6, 0), (-1.5, 4.3, -1.5, 8.1, 0), (1.5, 4.3, 1.5, 8.0, 0), (4.4, 4, 4.5, 7.4, 0)]
    for (x0, y0, x1, y1, tilt) in fingers:
        L = math.dist((x0, y0), (x1, y1)); f = rot(0, 0, 0)
        w = 1.55
        dx, dy = (x1 - x0) / L, (y1 - y0) / L; nx, ny = -dy, dx
        pts = [(x0 + nx * w, y0 + ny * w), (x1 + nx * w, y1 + ny * w)] + [(x1 + dx * w * math.sin(t) + nx * w * math.cos(t), y1 + dy * w * math.sin(t) + ny * w * math.cos(t)) for t in [k * math.pi / 6 for k in range(1, 6)]] + [(x1 - nx * w, y1 - ny * w), (x0 - nx * w, y0 - ny * w)]
        s.flat(P(pts), GLOVE, smooth=False); s.stroke(P(pts), width=0.6, closed=True, corners=True)
    thumb = [(-5.8, -1.5), (-9.5, 1.5), (-10.2, 4.8), (-8.4, 5.6), (-5.4, 3)] if open_hand else [(-5.6, -1), (-8.6, 2.2), (-7.8, 5.2), (-5.2, 4.2)]
    palm = [(-6, -4), (6, -4.4), (6.4, 4.6), (-6.2, 4.8)]
    s.flat(P(palm), GLOVE, offset=(0.3, -0.2)); s.stroke(P(palm), width=D, closed=True)
    s.flat(P(thumb), GLOVE); s.stroke(P(thumb), width=0.6, closed=True)
    for k in (-2.2, 0, 2.2): s.stroke([g(k, -2.6), g(k * 1.08, 2.2)], width=0.3)            # stitch lines on the back
    cuff = [(-6.6, -4.2), (6.3, -4.6), (8, -8.6), (-8.3, -8.2)]
    s.flat(P(cuff), GLOVE, offset=(0.3, -0.2)); s.stroke(P(cuff), width=D, closed=True)
    s.stroke([g(-6, -6.3), g(6.4, -6.7)], width=0.32, colour=GREY)
    s.hatch(P([(2.5, -3.6), (6, -4), (6.2, 4.4), (2.8, 4.5)]), angle=a + 80, gap=0.7, width=0.16, tone=1)
    for i_ in (-1, 0, 1):                                                                    # motion ticks off the cuff
        s.stroke([g(-2 + i_ * 3.4, -10.6), g(-2.4 + i_ * 3.6, -13.4)], width=0.32, colour=GREY, taper=0.4)
glove(199.5, 59.2, 96)                      # cranking: comes in from the right, fingers wrap the grip
glove(156, 22, 182, open_hand=True)         # feeding the hopper

# raw inputs falling from the open glove into the hopper
def page(cx, cy, a, lines=4):
    g = rot(cx, cy, a); pts = [g(-3.8, -4.8), g(3.8, -4.8), g(3.8, 4.8), g(-3.8, 4.8)]
    s.flat(pts, CARD, smooth=False); s.stroke(pts, width=0.55, closed=True, corners=True)
    for k in range(lines): s.stroke([g(-2.4, -2.6 + k * 1.8), g(2.4, -2.6 + k * 1.8)], width=0.28, pressure="even", taper=0.1)
page(147, 37, -24)                                                       # spec page
s.stroke([(162.5, 33), (160.5, 35.5), (162.5, 38)], width=0.6); s.stroke([(167.5, 33), (169.5, 35.5), (167.5, 38)], width=0.6)
s.stroke([(165.8, 32.6), (164.2, 38.4)], width=0.5)                      # </>
meme = [(150.5, 27.5), (157, 27), (157.4, 33), (151, 33.4)]
s.flat(meme, CARD, smooth=False); s.stroke(meme, width=0.5, closed=True, corners=True)
s.stroke(arc_pts(153.9, 30.4, 1.6, 20, 160, 5), width=0.38)
for i, h in enumerate((2.5, 4.2, 1.8, 5)):                               # a little chart
    s.stroke([(170 + i * 1.7, 31.5), (170 + i * 1.7, 31.5 - h)], width=1.0, pressure="even", taper=0.02)

# ================================================================ finished cards fanning out of the press toward the hand
fan = [(146, 121, 8, CARD), (133, 124, -6, CARD), (122, 126, 4, CARD)]
for cx, cy, a, col in fan:
    g = rot(cx, cy, a); pts = [g(-7, -5), g(7, -5), g(7, 5), g(-7, 5)]
    s.hatch([g(-6, 5.2), g(8, 5.2), g(8.5, 6.6), g(-5.5, 6.6)], angle=a - 4, gap=0.7, width=0.18, tone=1)
    s.flat(pts, col, smooth=False, offset=(0.4, -0.3))
    s.stroke(pts, width=D, closed=True, corners=True)
    s.stroke([g(-4.5, -2), g(3, -2)], width=0.75, pressure="even", taper=0.05)
    s.stroke([g(-4.5, 0.8), g(4.5, 0.8)], width=0.3, pressure="even", taper=0.1)
s.hatch([(127, 113.5), (188, 113.5), (184, 118), (124, 117.5)], angle=-6, gap=0.85, width=Hh, tone=2)   # press shadow

# the black paper rose (idle prop), near the figure
for k, rr in enumerate((4.6, 3.3, 2.1, 1.0)):
    s.flat(ellipse_pts(22, 121, rr, rr * 0.8, rot=k * 27, n=7), TURTLE if k % 2 == 0 else "#45423E")
s.stroke([(22, 124.5), (23.5, 132), (26.5, 137)], width=0.7)
s.flat([(23.8, 130.5), (29.5, 128), (26.4, 132.6)], TURTLE)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exports", "illustration", "helping_hands")
s.save(out)
s.save(out + "_riso", riso=True, misregister=0.3)
print("✓", os.path.relpath(out), s.stats)
