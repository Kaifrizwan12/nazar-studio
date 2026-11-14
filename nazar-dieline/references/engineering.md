# Engineering: board, allowances, grain, creases, locks, dies

Numbers here are **starting rules** gathered from converter guides, standards and research, and sources disagree on several of them. Each one is marked with how sure it is. The converter's figures win, every time.

## 1. Measure and clear
- Measure three samples with calipers; take the largest in each axis. Add the cap, pump, label thickness and any bulge.
- **Clearance (inside dimension minus product):** commonly about 1–2 mm per axis for rigid products in cartons, more for soft or variable products, and less where the product must not rattle (use an insert instead) [KNOWN]. Automatic lines often specify their own.
- Write inside dimensions as L × W × D (ECMA) and keep a "product → inside → panel (crease to crease) → outside" table in the spec.

## 2. Board
### Folding carton board
| Grade | What | Feel and use |
|---|---|---|
| SBS / GZ / SBB | Solid bleached board | Brightest white, best print, premium |
| FBB / GC | Folding boxboard (virgin fibre, mechanical middle) | Stiff for its weight; the European workhorse |
| WLC / GD / GT | White-lined chipboard (recycled) | Cheapest; greyer back, lower fold strength |
| SUS / CUK | Kraft-backed / unbleached | Strength, wet and freezer uses, a natural look |

Typical caliper is about 0.35–0.7 mm (14–28 pt) [SRC]. Specify by **caliper and stiffness**, not grammage alone, since two boards of the same gsm can fold very differently.

### Corrugated
| Flute | Approx. caliper | Use |
|---|---|---|
| F | ≈ 0.8 mm | Retail packs printed like cartons |
| E | ≈ 1.6 mm | Mailers, retail-ready, good print surface |
| B | ≈ 3.2 mm | Shippers, displays, die-cut fitments |
| C | ≈ 4.0 mm | Standard shipping cases |
| A | ≈ 4.8 mm | Cushioning, heavy stacking |
| BC / EB | ≈ 7 / 4.8 mm | Double wall: heavy goods, export |

Caliper figures vary by mill and source (the table follows the US standard table; others quote E as 1.0–1.8 mm) [SRC]. Get the converter's real caliper: the engine takes it as `caliper` or `flute`.

## 3. Allowances: where caliper goes
Every fold wraps board around board, so panels grow outward. The rules below are the defaults the engine uses; converters each have their own tables per board.

| Where | Starting rule | Confidence |
|---|---|---|
| Tube carton panels (crease to crease) | inside + 1 × caliper | Engine default; converters vary |
| Depth with closures | inside + 1 × caliper per closure | Engine default |
| Tuck clearance (tongue narrower than opening) | ≈ 1–1.5 × caliper per side; sources quote 1.5× and 2× [SRC] | Rule of thumb |
| Dust flap shoulder | bevel ≈ 15° so it clears the closure [SRC] | Rule of thumb |
| Dust flap height | ≤ half the length (or they collide); ≈ 0.5–0.8 × W | Geometry |
| Glue flap | ≈ 12–22 mm wide, tapered 7–15° at the ends; no varnish, no laminate, no ink where glue lands [SRC] | Converter decides |
| Corrugated RSC flaps | half the width (+ allowance), so the outer flaps meet in the middle [SRC: FBA] | Standard |
| RSC manufacturer's joint | often ≈ 30–40 mm | Unconfirmed by standard: ask |
| RSC slot | ≈ 2 × caliper or the converter's slot tool | Converter |

**Friction lock:** a small step at the tuck crease (the engine draws one caliper's width) catches the dust flaps, so the tuck can't spring open. Other locks: slit locks (a short cut at each end of the tuck crease), thumb-notch releases, and hidden tab locks for display lids.

Tucks are humidity-sensitive: one that is too tight won't go in on a humid day, and one that is too loose falls open on a dry one [SRC]. Test samples in the climate of the market.

## 4. Grain (machine direction)
Board is stiffer along the grain (MD) and folds more cleanly when the crease runs **with** the grain [SRC]. The two goals pull against each other, so the converter decides. The engine's default is the common one:
- **Tube cartons:** grain **around the tube** (horizontal on the layout, across the main vertical creases), so the panels resist bulging and the carton stands square. Board makers link grain to bulge control [SRC: Iggesund].
- **Trays:** grain along L, so the long walls stay straight.
- **Corrugated:** flutes vertical on shippers, for stacking strength.
- **Rigid wraps and labels:** the paper grain parallel to the spine or wrap direction, to stop curl and lifting.
Mark the grain on every concept, and get it confirmed on the converter's drawing.

## 5. Creases
- A good crease leaves a clean groove on the print side and a **symmetric bead** on the inside [SRC: research]. Cracking on the fold means the crease is too deep, the board too dry, or it is folded against the grain.
- Heavier board needs a wider crease channel [SRC]; the die-maker sets rule height and channel width per board.
- **Reverse creases** (folding the other way) are marked separately, since the die has the rule on the other side.
- Ink, varnish and lamination crack on creases: avoid heavy solids across the main folds on uncoated or recycled board, and ask for a crease test on the printed board.
- Perforations: specify cut/tie (for example 3 mm cut, 1 mm tie) and whether a tear strip has a pull tab.

## 6. Tolerances
- Die-cutting accuracy is typically quoted around **±0.5 mm**; print-to-cut registration varies with the process (tighter on offset sheets than on corrugated) [SRC].
- So: keep type and logos **3–5 mm** from cuts and folds, never run a thin border along a crease (any drift shows), and let backgrounds run past folds.
- Flap alignment: ±0.5 mm per flap is a common target [SRC].

## 7. Die-making basics (so the drawing respects the tool)
- **Flatbed steel-rule dies:** cutting rule (often 2 pt) and creasing rule set into a laser-cut plywood base; rubber ejection strips push the sheet off the knives. **Rotary dies** are faster and cost more, and are used for long runs and corrugated.
- **Nicks (ties):** small gaps ground into the cutting rule that hold blanks in the sheet through the press; they are torn out at stripping. Place them on edges where a small burr won't show (not on the front panel's visible edge). Very thick board may need none [SRC].
- **Minimum features:** tight inside corners, slivers and tiny holes are hard to cut and strip. Give windows a radius (≈ 1–3 mm) and keep bridges between cut-outs wider than about 2–3 × caliper.
- **Stripping and blanking:** waste between blanks must come out cleanly. Shared cut lines between blanks ("common cuts") save board and rule.
- Die cost scales with rule length: the engine reports cut and crease length so you can compare routes.

## 8. Nesting
- Lay blanks on the converter's sheet size with gripper margin and gutters. The engine's rough count uses a simple grid in both orientations; interlocked and tumbled nests (rotating alternate blanks 180°) often fit more.
- **Board area per blank × run length = most of the material cost.** A slightly smaller glue flap or tuck can add a blank per sheet, so check before finalising.

## 9. Compression and stacking (corrugated)
- **Simplified McKee:** BCT ≈ 5.87 × ECT × √(caliper × perimeter), in lbf, lb/in and inches, for an RSC [SRC]. It is the least accurate method: it ignores die-cuts, hand holes, humidity and handling.
- Then apply safety factors for real conditions. Humidity, storage time, pallet overhang and misaligned stacking each cut strength a lot, so the total factor is often 3–5 or more [KNOWN]; the converter and the test lab set it.
- Required BCT ≈ (load from the boxes above) × safety factor. If it fails: a higher ECT grade, double wall, a different flute, a smaller footprint relative to height, or internal fitments.

## 10. Prototyping
1. **Paper mock-up** at 1:1 from the engine's PDF: checks proportions and the opening.
2. **Plotter sample** cut on a CAD table (most converters have one) in the real board: checks fit and folds.
3. **White sample** from the converter, unprinted, on production board: fill it, close it, drop it, stack it, ship it.
4. **Printed prototype** (digital) for client sign-off and photography.
