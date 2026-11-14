"""Demo: "Pencil meets cursor". The hand starts the line; the machine cleans it up.

    python examples/pencil_cursor.py      # → exports/illustration/pencil_cursor(.svg/.png/_riso.png)

Concept lock
  idea   : one continuous line, wobbly graphite from a pencil on the left, clean vector with nodes toward a cursor on the right
  focal  : the one selected node (accent) with its handles out, where hand becomes vector
  light  : upper left (pencil's lit edge, cast shadow down-right)
  budget : paper, ink, graphite grey, pencil black + cedar, one accent (orange); weights 1.5 / 0.6 / 0.25
  says   : Nazar's rule: hands first, the machine helps
"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engine"))
from ink import Sheet, ellipse_pts

PAPER, INK, GRAPHITE, PENCIL, CEDAR, LIT, GRID, ACCENT = (
    "#F2EEE6", "#1C1B19", "#57534E", "#2A2826", "#D7B489", "#77726B", "#C9C4BA", "#E4572E")
s = Sheet(240, 110, paper=PAPER, seed=9, hand=1.0)

# the digital side: a faint dot grid fading in from the middle
for gx in range(102, 238, 6):
    for gy in range(8, 106, 6):
        a = max(0.0, min(1, (gx - 100) / 50)) ** 1.6
        s._add(GRID, f'<circle cx="{gx}" cy="{gy}" r="0.32" fill="{GRID}" fill-opacity="{a:.2f}"/>')

# the line's key points (one curve, shared by both halves)
K = [(44, 66), (64, 57), (86, 67), (107, 58), (128, 62), (150, 52), (172, 59), (194, 49)]

# --- hand half: graphite, pressure, a second lighter pass like a real sketch
s.stroke(K[:5], width=1.7, taper=0.06, taper_end=0.0, pressure=[1.0, 0.8, 0.95, 0.75, 0.6], colour=INK)
s.stroke([(x + 0.6, y - 0.7) for x, y in K[:4]] + [(124, 61.5)], width=0.55, taper=0.3, colour=GRAPHITE, wobble=0.008)
for i in range(14):                                                     # graphite dust near the tip
    x, y = 40 + i * 1.7 + s.rng.uniform(-1, 1), 70 + s.rng.uniform(-2, 3)
    s._add(GRAPHITE, f'<ellipse cx="{x:.2f}" cy="{y:.2f}" rx="{s.rng.uniform(0.15, 0.4):.2f}" ry="0.2" fill="{GRAPHITE}" fill-opacity="0.45"/>')

# --- vector half: the same curve, mechanical (no hand), thin, even
s.hand = 0.0
s.stroke(K[4:], width=0.6, taper=0.0, pressure="even", colour=INK, wobble=0.0)
for (x, y) in (K[4], K[6], K[7]):                                       # anchor nodes
    sq = [(x - 1.3, y - 1.3), (x + 1.3, y - 1.3), (x + 1.3, y + 1.3), (x - 1.3, y + 1.3)]
    s.flat(sq, "#FFFFFF", smooth=False); s.stroke(sq, width=0.35, closed=True, corners=True, pressure="even", taper=0)
# the selected node: accent, handles out along the tangent
nx, ny = K[5]
tx, ty = K[6][0] - K[4][0], K[6][1] - K[4][1]
L = math.hypot(tx, ty); tx, ty = tx / L, ty / L
for sgn in (-1, 1):
    hx, hy = nx + sgn * tx * 11, ny + sgn * ty * 11
    s.stroke([(nx, ny), (hx, hy)], width=0.3, pressure="even", taper=0, colour=ACCENT)
    s.flat(ellipse_pts(hx, hy, 1.0, 1.0, n=8), "#FFFFFF"); s.stroke(ellipse_pts(hx, hy, 1.0, 1.0, n=8), width=0.35, closed=True, colour=ACCENT)
sq = [(nx - 1.6, ny - 1.6), (nx + 1.6, ny - 1.6), (nx + 1.6, ny + 1.6), (nx - 1.6, ny + 1.6)]
s.flat(sq, ACCENT, smooth=False); s.stroke(sq, width=0.35, closed=True, corners=True, pressure="even", taper=0)

# --- the cursor (classic pointer), resting at the end of the line
cx, cy, k = 197, 46.5, 0.85
arrow = [(0, 0), (0, 15), (3.6, 11.4), (6.2, 17.2), (8.6, 16.1), (6.0, 10.4), (10.8, 10.4)]
pts = [(cx + x * k, cy + y * k) for x, y in arrow]
s.flat([(x + 0.9, y + 0.9) for x, y in pts], "#DDD8CF", smooth=False)                 # tiny drop shadow, flat
s.flat(pts, "#FFFFFF", smooth=False); s.stroke(pts, width=0.55, closed=True, corners=True, pressure="even", taper=0)

# --- the pencil (drawn by hand again), tip on the start of the line
s.hand = 1.0
tip = (43.2, 66.8); ax, ay = -0.72, -0.69                                  # axis toward the upper left
L_ = math.hypot(ax, ay); ax, ay = ax / L_, ay / L_
nxp, nyp = -ay, ax                                                         # normal
P = lambda d, w: (tip[0] + ax * d + nxp * w, tip[1] + ay * d + nyp * w)
graphite = [P(0, 0), P(3, -0.9), P(3, 0.9)]
cone = [P(3, -0.9), P(13, -3.1), P(13, 3.1), P(3, 0.9)]
body = [P(13, -3.1), P(66, -3.1), P(66, 3.1), P(13, 3.1)]
s.flat([(x + 2.2, y + 2.6) for x, y in body + cone], "#E2DCD0", smooth=False)   # cast shadow down-right
s.flat(cone, CEDAR, smooth=False)
s.hatch(cone[:2] + [P(13, 0), P(3, 0)], angle=math.degrees(math.atan2(ay, ax)) + 90, gap=0.7, width=0.18, tone=1, colour="#9C7A52")
s.flat(graphite, PENCIL, smooth=False)
s.flat(body, PENCIL, smooth=False)
s.stroke([P(14, -1.6), P(65, -1.6)], width=0.45, colour=LIT, pressure="even", taper=0.1)   # hexagon facet, lit
s.stroke([P(14, 1.1), P(65, 1.1)], width=0.3, colour="#45423E", pressure="even", taper=0.1)
s.stroke(body, width=0.8, closed=True, corners=True)
s.stroke(cone + [cone[0]], width=0.6, corners=True)
s.stroke([P(13, -3.4), P(12.0, -1.4), P(13.6, 0.4), P(12.2, 2.2), P(13, 3.4)], width=0.45)  # scalloped paint edge

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exports", "illustration", "pencil_cursor")
s.save(out)
s.save(out + "_riso", riso=True)
print("✓", os.path.relpath(out), s.stats)
