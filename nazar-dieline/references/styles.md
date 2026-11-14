# Styles and codes

Two code books let you name a structure without a drawing. Ask converters in these terms.

## ECMA: folding cartons
The ECMA Code of Folding Carton Design Styles (European Carton Makers Association), first published in 1967 and digital since 2009, groups styles into families. A full code adds pairs of digits for variants (for example A20.20.01.03) [SRC]. Codes differ in the details between editions and converters, so check the converter's library rather than trusting a secondary site's drawing.

| Family (letter) | What it is | Typical uses |
|---|---|---|
| A1x / A2x: tube cartons | A glued tube closed by tucks, locks or glue at both ends | Cosmetics, tea, pharma, toys, small electronics |
| A20.20-type | **Reverse tuck end (RTE)**: top tuck hinged on one face, bottom on the opposite face | The cheapest, fastest everyday carton |
| A20.20-type (straight) | **Straight tuck end (STE)**: both tucks on the same face, so the front prints clean | When the front panel must have no flap crease |
| A2x with lock bottoms | **1-2-3 snap-lock bottom**: hand-assembled lock; **crash-lock (auto-bottom)**: pre-glued, pops open | Heavier products; crash-lock for fast hand-filling |
| A3x / A4x: sleeves and wraps | Open tubes, wraparounds, sleeves over trays | Multipacks, food sleeves, drawer outers |
| A5x–A6x: trays | Erected trays: glued corners, locked corners, Beers / Brightwood-type, lift-top trays | Food, gift, display, drawer inners |
| A7x+: special and combination | Hinged lids, display cartons, folders, multi-part | Display, gift, specialist |

Treat the family groupings above as a working map. The authority is the ECMA book and the converter's CAD library (most CAD systems ship ECMA and FEFCO libraries as parametric standards).

## FEFCO / ESBO: corrugated (the International Fibreboard Case Code)
Adopted by the International Corrugated Case Association. **Layouts are drawn as seen from the inside of the case** [SRC: FEFCO Code]. Four-digit codes; the first two digits give the family.

| Code | Family | Common styles |
|---|---|---|
| 00xx | Commercial rolls and sheets | Flat sheets |
| 02xx | Slotted cases | **0201 RSC** (all flaps one length, outers meet at the middle), 0200 half-slotted, 0203 full overlap, 0204/0205 centre-special |
| 03xx | Telescope (lid + base) | 0300 series lids, 0310 trays with lids |
| 04xx | Folders and trays | **0427** mailer (roll-end tuck front, no tape), 0421/0426 variants, 0401 wraparound |
| 05xx | Slide types | Sleeves with drawers |
| 06xx | Rigid types (bliss) | Bliss boxes, heavy shippers |
| 07xx | Ready-glued cases | Crash-lock bottoms |
| 09xx | Interior fittings | Partitions, pads, liners, dividers |

## Which style for which job
| Job | Start with | Why |
|---|---|---|
| Light product, retail shelf, hand or machine fill | RTE | Cheapest die and fastest glue line |
| Front panel must be uninterrupted | STE | The tucks stay off the front |
| Product heavier than ~0.5 kg, or a fast hand line | Crash-lock bottom + tuck top | Pops open and won't fall through |
| Food tray, gift inner, display | Glued-corner or locked-corner tray | Rigid walls, ships flat |
| A range with one shared outer | Sleeve over a tray or carton | One die, many sleeves |
| E-commerce, ships as is | FEFCO 0427 mailer in E or B flute | Tape-free, strong, an unboxing canvas |
| Shipping case | FEFCO 0201 | The universal shipper |
| Premium gift | Rigid set-up box (`rigid.md`) | Weight, edges, unboxing |
| Small, soft, light goods | Pillow pack | One die, no glue on the ends, a soft shape |
| Granular, liquid, snack | Stand-up pouch (`flexibles_labels.md`) | Light, cheap freight, big face |
| Chips, crisps, extruded snacks, bars | Flow-wrap pillow bag, metallised (`flexibles_labels.md`) | Fast lines, light and oxygen barrier, nitrogen flush |

## What the engine draws
| Engine style | Code family | Notes |
|---|---|---|
| `rte` / `ste` | ECMA A20.20-type | Dust flaps with shoulders, friction steps at the tuck crease, tapered glue flap |
| `sleeve` | ECMA A3x-type | Optional thumb notches |
| `tray` | ECMA A6x-type, glued corners | Corner flaps glue inside the end walls |
| `rsc` / `hsc` | FEFCO 0201 / 0200 | Manufacturer's joint, slots, flap = half width; McKee estimate from ECT |
| `mailer` | FEFCO 0427-type | Double side walls with locking tabs, ears, lid dust flaps, tuck |
| `pillow` | Pillow pack | Curved creases and cuts from a sagitta |
| `rigid` | Set-up box | Greyboard blank + wrap with turn-ins and corner tabs |
| `cone_label` / `wrap_label` | Labels | Frustum maths; overlap; guides |
| `pouch` | Stand-up pouch | Seals, gusset fold, zipper band, notch, hang hole, eye mark |
| `flowwrap` | Flow-wrap / VFFS pillow bag (chips, snacks, bars) | Fin seal, serrated crimp end seals, split back, optional side gussets, eye mark |
| `sleeve_grid` | Shrink sleeve | Shrink % by height from a container profile, pre-stretch ellipses |

Not drawn (ask the converter for their parametric standard): snap-lock and crash-lock bottoms, Beers/Brightwood trays, hinged-lid cigarette-style cartons, display headers, partitions, 0201 variants with special joints. Drawing them approximately would mislead, so we name the code and get the real file.
