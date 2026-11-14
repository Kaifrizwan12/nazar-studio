"""Simple cartoon demo: a kulhad (clay chai cup) mascot waving hello. Bold outline, flat colours, one highlight.

    python examples/kulhad.py        # → exports/illustration/kulhad(.svg/.png/_riso.png)

Concept: a warm hello. Shapes: a rounded trapezoid body (friendly, stable), big eyes low on the face (young),
rubber-hose arms with white gloves, one wave. Light from the upper left: shade on the right side of the cup.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engine"))
from ink import Sheet, ellipse_pts, arc_pts

PAPER, CLAY, CLAY_D, RIM, CHAI, INK, BLUSH, STEAM = (
    "#F3EBDD", "#C8673C", "#9E4A2A", "#E59466", "#8A5A2B", "#1E1B18", "#E98A73", "#B8A88F")
s = Sheet(160, 160, paper=PAPER, seed=5, hand=0.6)

s.flat(ellipse_pts(80, 136, 34, 5, n=10), "#D9CDB8")                                    # ground shadow

body = [(50, 63), (110, 63), (104, 132), (56, 132)]                                     # the cup (top hides under the rim)
s.flat(body, CLAY, smooth=False)
s.flat([(97, 65), (109.5, 65), (103.5, 131), (93, 131)], CLAY_D, smooth=False)           # shade side
s.stroke([(50, 63), (56, 132), (104, 132), (110, 63)], width=2.2, corners=True, taper=0.04)   # sides + base only
s.stroke([(55, 72), (56.5, 100)], width=1.6, colour="#F2B48C", pressure="even", taper=0.2)   # highlight

s.flat(ellipse_pts(80, 62, 31, 7, n=12), RIM, offset=(0, 0))                                           # rim + chai
s.flat(ellipse_pts(80, 62.6, 26, 4.6, n=12), CHAI)
s.stroke(ellipse_pts(80, 62, 31, 7, n=12), width=2.0, closed=True)

for x in (68, 92):                                                                      # eyes
    s.flat(ellipse_pts(x, 92, 5.2, 6.4, n=10), "#FFFFFF")
    s.stroke(ellipse_pts(x, 92, 5.2, 6.4, n=10), width=1.3, closed=True)
    s.flat(ellipse_pts(x + 1.2, 93.2, 2.6, 3.2, n=8), INK)
    s.flat(ellipse_pts(x + 2.0, 91.6, 0.9, 0.9, n=6), "#FFFFFF")
s.stroke(arc_pts(80, 101, 8, 25, 155, 8), width=1.8)                                    # smile
for x in (59, 101):
    s.flat(ellipse_pts(x, 104, 4, 2.2, n=8), BLUSH)                                     # cheeks

s.stroke([(55, 100), (44, 98), (38, 88), (36, 79)], width=2.2, pressure="even", taper=0.05)   # waving arm
s.stroke([(105, 104), (115, 110), (119.5, 117)], width=2.2, pressure="even", taper=0.05)      # resting arm
for cx, cy, r in ((35.5, 74.5, 5.2), (121, 121, 4.6)):                                  # glove hands
    s.flat(ellipse_pts(cx, cy, r, r * 1.05, n=8), "#FFFFFF")
    s.stroke(ellipse_pts(cx, cy, r, r * 1.05, n=8), width=1.4, closed=True)
for r, a0, a1 in ((11, -140, -95), (15, -135, -100)):                                   # wave lines
    s.stroke(arc_pts(35.5, 74.5, r, a0, a1, 5), width=1.0, taper=0.3)

for x0, h in ((72, 0), (84, 4), (95, 1)):                                               # steam curls
    s.stroke([(x0, 52), (x0 - 3, 45 - h), (x0 + 2, 38 - h), (x0 - 2, 31 - h)], width=1.4, colour=STEAM, taper=0.35)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exports", "illustration", "kulhad")
s.save(out)
s.save(out + "_riso", riso=True)
print("✓", os.path.relpath(out))
