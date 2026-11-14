# Shelf-ready, display and shipping structures

## Shelf-ready packaging (SRP / RRP)
A case that goes straight onto the shelf. The retailer test is the **five easies**: easy to **identify**, **open**, **shelve**, **shop** and **dispose** [SRC]. They were developed at Walmart and adopted widely (ECR's "Blue Book"; ECR Australasia guidelines; IGD's longer list of eleven) [SRC].
- **Identify:** brand and variant readable from the aisle on the case front; case codes where staff look.
- **Open:** a perforated tear-away front or lid that opens without a knife (knives cut products). Tear lines need tested cut/tie values and a clear "push here" cue.
- **Shelve:** fits the retailer's shelf depth and height; the right number of facings.
- **Shop:** the shopper can see and take a product without wrecking the tray: a low front lip, a window, fingers' room.
- **Dispose:** mono-material and flattens easily.
Retailer rules are specific and change: ask for the current SRP spec of every retailer on the list.

## Counter and floor displays (CDU, FSDU)
- **Counter display unit (CDU):** a tray with a raised header, often E or B flute. The header carries the message; the tray holds 6–24 units. The engine's `tray` is a starting point.
- **Floor-standing display unit (FSDU):** shelves, a header, side panels and a base plinth, usually shipped flat, sometimes pre-filled [SRC].
- **Load-test it.** One common practice is to load each shelf with the real product weight plus about 20% for 48–72 hours and check for bowing [SRC: single source, verify]. The usual failure is shelf bowing; humidity in stores weakens corrugated over weeks [SRC].
- Design for assembly by a store worker with no instructions: few parts, numbered, with locks that click.
- Big printed headers are seen from 5–10 m: apply the legibility logic in `../nazar-ooh/references/legibility.md`.
- Transit protection for pre-filled units (an outer shipper, corner posts) is tested separately (ISTA).

## E-commerce: ships in own container
- **Amazon** certifies packaging through the ISTA 6-Amazon.com protocols. Tiers include Frustration-Free Packaging (Tier 1), Ships in Own Container / SIOC (Tier 2) and Prep-Free Packaging (Tier 3), and programme names have changed over time (FFP → SIOC → SIPP) [SRC]. Test types depend on weight and size. **Read Amazon's current packaging certification guidelines and use an ISTA-certified lab;** don't design to a remembered rule.
- **Other platforms and couriers** have their own drop and size rules; ISTA 3A is the general parcel-delivery simulation, and Amazon adopted it early on before moving to ISTA 6 [SRC].
- The **FEFCO 0427 mailer** (engine `mailer`) is the default DTC box: no tape, strong in E or B flute. The lid's inside is free media; a tear strip makes opening and returns easier.
- **Right-size:** dimensional-weight pricing punishes air, so fit the product + protection, not a stock size.
- **Protection:** suspension, corrugated fitments, moulded pulp, paper void fill. Avoid loose plastic fill when the brand claims plastic-free.

## Transit testing (shippers and anything that travels)
- **ISTA** procedures simulate drops, vibration, compression and climate (1-series basic, 2-series partial, 3-series general simulation, 6-series member-specific such as Amazon).
- **Compression:** see the McKee estimate in `engineering.md` §9, then lab BCT tests on real samples, then a safety factor for humidity, time and stacking pattern.
- **Pallet pattern:** column stacking keeps box corners aligned (strongest); interlocking adds stability but costs compression. Overhang off the pallet edge is a big strength loss.
- Run the test with the **real filled product**. An empty box proves nothing.
