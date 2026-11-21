# The sequence: beats, devices, flatplan

## Beats (in order; each is one page unless noted)
| # | Beat | What the page does | Typical device |
|---|---|---|---|
| 1 | **Hook** | The opening image. The hero product, very close or on its own colour, with no paragraph | full-bleed crop, hero bleed |
| 2 | **Brief / tension** | What was asked, in one line, plus up to four words of constraint | statement + colour tiles |
| 3 | **Insight** | The one thing the research found, as a sentence (the gap, the rival, the habit) | three-column finding, one quote |
| 4 | **Idea** | The idea in one line, beside the image that proves it | split: line left, image bleeding right |
| 5 | **System** (2–3 pages) | The rules that make the family: structure measured, colour, the rulebook | measured flats grid, colour columns, rule list beside one clean pack |
| 6 | **Applications** (one page per format) | Each format once, front and back, each with a new composition | see the device list below |
| 7 | **Payoff** | Everything together, then the motion or the real-world moment | family sheet, film strip, the one owner-picked scene |
| 8 | **Credits / contact** | The studio page: mark, one line, contact list (owner-supplied facts only) | dark panel + contact list |
| 9 | **Thank-you** | The final image, mirroring the hook | full-bleed close |

## The application rhythm
hero > range > turn over > scale > detail > split > standing > dark
- **hero**: one product, front and back, with its colour as the page edge
- **range**: every variant fronts together (a fan, a row, a hand of cards)
- **turn over**: every back, in one composed group
- **scale**: one product huge and bleeding, the rest small (till-side row)
- **detail**: a macro of a finish, seal or texture
- **split**: a text column and a gutter system, with products top-aligned to the headline
- **standing**: products as they sit (3/4 view, gusset on show)
- **dark**: a dark page; the recipe, facts or night use leads

Repeat the cycle for long ranges, but never reuse the same device. Change the scale, the colour or the crop.

## Device names (declare one per page in `d.page(..., device=...)`)
hero bleed · full-bleed crop · statement tiles · three-column finding · split line/image · measured flats grid · colour columns · rule list + pack · front-back pair · hand of cards · toss · specimen grid · couples row · scale contrast · macro detail · standing row · dark split · flats strip · before/after · arrow sequence (1 arrives, 2 opens) · family sheet · film strip · studio contact split · final image
Composer devices (each `engine/composers.py` result carries one in `.device`; pass it as `d.page(..., device=c.device)`): hand of cards · front-back pair · overlap row · standing row · scale lineup · cascade · stack · hero bleed · specimen grid · scatter · toss · extended plate

## Composing product groups (2026-11-21, `references/research_composers.md`)
- Overlapping, tucked or bleeding groups go through `engine/composers.py` as ONE RGBA, so deck.py's overlap and off-page guards still pass.
- One `Light` per deck: every shadow falls the same way (default from above-left, down-right). Never mix composites made with different lights on one page.
- Every product gets a soft shadow plus a tight contact shadow from its own silhouette. No floating cut-outs and no single blurry blob.
- Scale truth: when sizes sit side by side, use `true_scale=True` with real mm. A small pack is never shown as big as a large one, because misleading size is regulated in the EU, UK, US, India and Pakistan.
- One product leads each group (front, nearest, largest). Groups of 3 or 5 read calmer than 4 or 6 (advisory).
- Put the line top-left, where F and Z scanning both start. Put the group opposite or lower right, and bleed off the right or bottom edge so the cut points on into the scroll.
- Extend a plate only over an even surface (`extend_canvas`). Never continue an object cut by the edge.
- Run `DeviceLog().report()` (or read the build's warnings) before showing. A repeat is a fail.

## Flatplan check (before building and again on the contact sheet)
- [ ] Every product's front AND back appears exactly once (tick a list of SKU × side)
- [ ] No device name repeats (the build warns)
- [ ] No two dense pages side by side; big visual moments spaced out
- [ ] Ground colour changes at least every 3 pages; never 3 cream pages in a row
- [ ] Scale changes: at least one bleed, one macro, one "all together"
- [ ] The final image mirrors the hook
- [ ] The measured flats page exists (grams + mm for every structure)
- [ ] The studio contact page sits directly before thank-you
