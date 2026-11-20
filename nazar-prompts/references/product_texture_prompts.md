# Product-texture photos and plates (for pack composites)

Used by the hybrid pack-render workflow (`../../nazar-dieline/references/frosted_film_render.md`): AI makes only the set and the product texture, never the pack. Client's written OK first.

## The anti-slop lesson
- **Floating or spiral "exploding" product on a flat chroma background reads as AI slop.** Pieces hang in the air, light comes from nowhere, every piece is perfect. Nobody believes it.
- **What worked: a grounded overhead food-styling shot.**
  - a small, casual cluster (not a heap, not a pattern) plus one fresh element (half a fresh fruit, a cracked shell);
  - one hard sun from the top-left, with real short shadows;
  - 100 mm macro, f/11 (everything sharp, nothing dreamy);
  - real texture words: fibres, caramelised spots, sugar crystals, uneven hand-cut edges, a few crumbs;
  - off-centre, with empty paper around it;
  - shot on matte paper in the **exact pack colour, with hex**, so it drops into the pack or layout without a cut-out halo.
- For a fill texture (the pile inside a pouch), ask for the pile to **fill the frame edge to edge**, top-down, same light.

## Which model (checked 2026-11-20)
- **Figma MCP `generate_image`:** `gpt-image-2.5-sunburst` gave a more natural, casual styling. `gemini-3.1-flash-image` arranged the pieces too neatly (a grid feel). Try both; keep the casual one.
- **Canva `generate-image` ignores `user_intent`** and follows only the literal prompt. Poor for controlled plates. Put everything in the prompt, or use another tool.
- Never ask any model for the pack itself: frosted film comes out opaque or glassy, and label text breaks.

## Template
> Overhead food-styling photograph, shot straight down. A small casual cluster of [product, e.g. dried apricot halves], [5–9] pieces, loosely touching, off-centre toward the [lower left], with half a fresh [fruit] beside them. Real texture: [fibres, caramelised spots, uneven hand-cut edges, a few crumbs]. One hard sun from the top-left casting short crisp shadows to the bottom-right. 100 mm macro lens at f/11, everything in focus. Background: plain matte paper in exactly [colour name] [#hex], evenly lit, no gradient, no props. Natural colour, restrained grade, fine film grain. [Ratio, e.g. 4:5]. No floating pieces, no splash, no text.

Variants:
- **Fill texture:** replace the cluster with "a dense pile filling the whole frame edge to edge, no background visible".
- **Empty plate:** "an empty [surface: linen, limestone, painted plaster] tabletop, shot straight down, one hard sun from the top-left, [a few loose pieces scattered at the left and bottom edges], centre left empty for products added in post".
