# Designing on the dieline (MVPs, drafts, and how pros think in 3D)

`nazar-packaging` decides **what the pack says** (idea, hierarchy, range system). This file is about **putting it on the structure**: which panel does what, how art behaves across folds, seals and windows, and how to make fast, honest MVP drafts with the engine.

## 1. Think in the object, not the flat
The flat dieline is a lie your eye believes. Shoppers never see it.
- **Fold a paper sample first** and draw on it with a marker: brand, name, variant, the opening. Ten minutes of paper saves a day of rework.
- **Know which face the shopper sees.** Tube cartons stand (the front faces out) or lie (the top or a side becomes the face). Pouches show the front and the gusset base. Chips packets stand, hang or lie in a bin. Mailers are seen lid-first, at the door. Ask: "on shelf, in hand, at home, on the doorstep: which panel?"
- **Panel jobs (a default map):**

| Panel | Job |
|---|---|
| Front / principal display panel (PDP) | Brand block → product name → variant → one benefit → net quantity (US: bottom 30% of the PDP, in lines parallel to the base; small-PDP exemption) [SRC: FDA] |
| Sides | Second brand hit (cartons are often shelved side-out), variant colour, a story line, how-to-use icons |
| Back | Story in the brand voice, mandatory copy, barcode, recycling, contacts |
| Top / lid | Brand from above (low shelves, freezers, doorstep), opening cue |
| Bottom | Codes, batch, small marks; sometimes a reward ("you found it") |
| Inside / turn-ins / under the flap | The second moment: a line, a pattern, a thank-you. Costs a second print pass (decide early) |
| Tuck / dust flaps | Usually unseen: plain colour, or a wink for the opener |

## 2. Art that survives folds, drift and seals
Print, cut and fold each drift. Design so ±1 mm (cartons) or about ±4 mm (form-fill-seal flexibles) doesn't show [SRC].
- **Backgrounds run through every fold, past every cut, into bleed.** Never stop a colour at a crease.
- **No thin borders or keylines along a fold or edge.** Any drift makes them visibly uneven. Use a wide band or none.
- **Wrap with intent.** A band or stripe that continues around a corner is strong, provided it's wide enough to forgive drift. Line up wraps on the folded paper sample, not on the flat.
- **Split elements** (a word or face across two panels) only when the split is the idea. Otherwise keep type within one panel.
- **Type: 3–5 mm off folds and cuts; more on flexibles** (seals distort, keep about 6 mm clear) [SRC].
- **Seals print, but distort.** Let colour run through them; keep logos, small type and barcodes out [SRC].
- **Glue areas: no ink, no varnish.** The engine knocks them out.
- **Curved creases (pillow packs) and tapered labels bend straight lines.** Design on the curve's guides (radial lines and arcs on cone labels).

## 3. The shelf is a wall, not a pack
- **Billboard / blocking:** several facings side by side can form one larger image or pattern. Design the repeat on the actual display pattern so packs line up and reinforce each other [SRC]. Research suggests billboarding helps, with less benefit when the billboarded image is text rather than objects [SRC].
- **But keep variant findability:** brand blocking must be balanced against finding your variant fast [SRC]. One variant cue (colour, number, icon) that never breaks the brand block (`../nazar-packaging/references/system.md`).
- **Test as a wall:** the engine's contact sheet plus a 6-up line-up of the range, in greyscale, at 2–3 m.

## 4. Transparency, windows and metallics (the explicit playbook)
| Scenario | Structure | How the art works | Engine |
|---|---|---|---|
| **Fully clear pouch** with a printed label area | Clear laminate, reverse printed | Unprinted = see-through. **White underlay** wherever colours must look opaque; no white where the product should show | `pouch` + `"bg": "clear"`, `"substrate": "clear"` → `_white.png` plate |
| **Partly transparent pouch** (window in a printed pouch) | Clear laminate, printed all over except the window | Window = no ink and no white. Frame the product: it's the hero | `"type": "window"` block, `"show_through": "<product colour>"` |
| **Kraft / paper pouch with a window** | Paper laminated to a clear film, window die-cut in the paper | Like a carton window: a cut in the paper, film behind | Use `"substrate": "board"` logic; ask the converter |
| **Metallised pouch or chips packet** | Metallised film (the light barrier) | No window unless the laminate has a non-metallised area (registered metallisation or a clear-film window): costs more, and adds light. Colours with no white under them shimmer metallic (a design tool) | `flowwrap` / `pouch` + `"substrate": "metallised"` |
| **Carton with a window** | Die-cut hole + film patch glued inside | Window at least ~10–15 mm from creases and cuts so the patch has glue room and the board doesn't break [SRC]; frame what matters; the inside of the carton shows through too | `"type": "window"` on a carton → a real CUT hole + patch outline |
| **Die-cut shape, no film** (a peek, a handle, a reveal) | Open cut-out | Only if the product can't fall out or get dirty; ≥ ~10 mm from creases [SRC] | `"type": "window"` (note: open) |
| **Clear plastic box / blister** | Thermoformed or folded clear | Print on an inner card; or reverse-print with white | Outside the engine: name it and get the converter's drawing |

**Rules that save launches**
- **Light kills fats.** Chips, nuts, oils and some colours and vitamins degrade under light. Metallised film exists largely as a light barrier: without one, chips can turn rancid fast; metallised film plus nitrogen gave the best results in shelf-life research [SRC]. A window is a shelf-life decision, not a design flourish. Set `"light_sensitive": true` and the engine flags it.
- **Products settle and break.** Granola, coffee and chips settle in transit: a high window shows headspace and crumbs. Put the window where the product sits after shipping, and test with a shaken sample.
- **Condensation and fog:** fresh and chilled products fog clear film (ask for anti-fog film).
- **Design with the product's colour.** Behind a window, the product is a colour in your palette. Choose the surrounding colours against it (`"show_through"` previews it). Never fake it with an illustration inside the window.
- **Reverse print order:** on clear film the image is mirrored and printed inside, then the white goes on behind the colours. The converter handles the order; you supply the white as its own spot layer (`WHITE`) built to the design, and the engine's white plate shows your intent.
- **Seals and windows don't mix.** Keep windows out of seal and zipper zones (the engine flags it).

## 5. Chips packets and flow wraps (specifics)
- The web runs: fin | back (half) | (gusset) | **front** | (gusset) | back (half) | fin. **The back's art is split** across the two edges and meets at the fin seal down the back's centre. The engine renders a single "Back" design into both halves correctly and warns when type sits under the folded fin.
- **End seals are crimped and serrated:** colour runs through them; nothing readable there. The **eye mark** sits in a non-image area per the converter.
- **Print direction:** art can run parallel to the fin or to the end seals [SRC], and the wrapper and the converter decide. Ask before designing.
- **Facing on shelf:** bags slump and wrinkle, so the brand block sits in the **upper middle** of the front where the bag stays flat; avoid detail near the crimps.
- **Pillow vs gusseted:** gussets let the bag stand (a better shelf face) and add a side panel for variant colour.

## 6. MVP drafts with the engine
1. Get the structure right first (`styles.md`). Then write an `"art"` block in the job (see `templates/dieline.json`: `rte_carton_mvp`, `mailer_mvp`, `window_carton_mvp`, `clear_pouch_mvp`, `chips_flowwrap_mvp`).
2. Tokens come from `../nazar-core/engine/brand.json` (`base`, `light`, `accent`, `secondary`), and type is outlined from the brand's fonts. Never type a hex the brand book doesn't have.
3. Logos: `{"type": "logo", "src": "path/to/client_logo.svg"}`, the client's exact file. A missing file is flagged P1, and a placeholder is drawn instead. **Never redraw a mark.**
4. Mandatory copy: use `placeholder` blocks sized for the real text, and replace them with the client's copy before anything goes to a converter.
5. Run → read `<name>_art_qa.md` → fix every P1 → look at `<name>_art.png`, `<name>_box.png` (the folded view) and, for film, `<name>_white.png`.
6. Show MVPs as **routes**: three structures or three art directions on the same structure, with the folded view next to each flat. State what's placeholder.

Block types: `text`, `para`, `band`, `rect`, `circle`, `rule`, `logo`, `placeholder`, `barcode` (GS1 EAN-13 at true size: 37.29 × 25.93 mm at 100%, 80% minimum) [SRC], `window`. Art-level keys: `bg` (token, hex or `clear`), `ink`, `pattern` (`stripes`/`dots`, runs across folds), `substrate` (`board` `clear` `metallised` `white` `kraft`), `show_through`, `light_sensitive`, `patch_margin`.

## 7. What the engine checks, and what it can't
Automatic: type size (pt), contrast against the actual fill behind the text, safe-area crossings, paragraph overflow, barcode size and fit, net quantity in the PDP's bottom 30%, missing logo files, art aimed at glue, a missing brand block, windows near creases or in seals, windows on opaque film, metallised and light-sensitive warnings, product settling.
Human (always): the folded paper proof, the shelf line-up, the AI-tell test (`../nazar-core/references/ai_tells.md`), legal copy from the client, the converter's dieline.
