# Plan the shot before the prompt

A pro product photographer has decided the camera, the lens, every light, where each reflection will land and where the shadow falls before the first frame. A generator does none of this; it averages. So we plan first, in numbers, and the prompt is written *from* the plan. Engine: `engine/shotplan.py`. Research: `research_realism.md`.

## The order (never skip a step; each one feeds the next)
| # | Decide | How | Why it matters |
|---|---|---|---|
| 1 | **The story line** | `scenes.md`: who, where, when, what just happened, why the product is there | The light, surface and props all come from the place and the hour |
| 2 | **The target look** | 6-20 references through `../../nazar-study/` (`look.py set`, recipe cards) | Numbers to brief and check against: black point, contrast, saturation, falloff, empty space, grain |
| 3 | **The product's real size and finish** | Measure the pack (mm) and name its finish: matte, satin, frosted, gloss, foil, glass | Size sets the lens and distance; finish decides which lights will glare |
| 4 | **Camera** | Height, distance, focal length, aperture. Eye level to the pack's middle for a front render; straight down for a flat-lay; 3/4 only with a 3/4 render | Our render has one camera; the plate must match it |
| 5 | **Lights** | One motivated key (side, height, size, distance, colour), fill or negative fill, rim if the finish or story needs it | Shadow direction, length and edge, and the gradient on the pack, all follow |
| 6 | **Reflections** | The family of angles on the pack face; the floor's finish and the camera height (Fresnel) | Glare that eats the print is decided here, not fixed in post |
| 7 | **Run the plan** | `python engine/shotplan.py plan spec.json -o plan/` | Plan, diagram, warnings, plate prompt, composite args |
| 8 | **Fix every warning or accept it in writing** | Move the light the planner suggests; stop down; step back | A plan with open warnings is not a plan |
| 9 | **Brief the plate** | Start from `plan/plate_prompt.txt`, add the texture words from the recipe cards, translate per model (`gemini_routes.md`, `../../nazar-prompts/references/models.md`) | The prompt carries geometry, not mood words |
| 10 | **Generate, then read the plate's real light** | `look.py card plate.jpg` and the eight clues (`../../nazar-study/references/reading_light.md`). If its shadows disagree with the plan by more than about 20 degrees, reject it or re-plan to match it | Models ignore briefs; the composite must follow the plate as it is, not the plan |
| 11 | **Seat the product** | `composite.py` with the plan's `--light` and `--persp`, or `proxy.py` for the proxy route | Physics-matched shadow, perspective and grade |
| 12 | **Check** | `composite.py` QA list (`camera_pass.md`), `look.py compare final.jpg target/set.json`, then your own eyes at 100% and at phone size | Inside the target range, no physics miss, print sharp |

## The spec (fields `shotplan.py` reads)
```json
{
  "scene": "one real place, one moment",
  "frame": {"aspect": "4:5", "px": [1080, 1350]},
  "camera": {"sensor": "ff", "focal_mm": 85, "distance_m": 1.4, "height_m": 0.42, "f_number": 8, "coc_mm": 0.03},
  "subject": {"name": "stand-up pouch", "w_m": 0.16, "h_m": 0.23, "d_m": 0.06, "finish": "satin",
              "face_tilt_deg": 4, "bend_deg": 12, "base_height_m": 0.30},
  "surface": {"material": "real material words", "finish": "matte|satin|gloss"},
  "lights": [{"role": "key", "kind": "strip", "az": -55, "el": 38, "distance_m": 1.1, "size_m": 0.6, "cct_k": 5000, "power": 1.0}],
  "never": ["no product, no text, no logos, no faces"],
  "grade": "shot on 35 mm film, natural grain, no HDR"
}
```
Angles: `az` 0 = beside the camera, -90 = camera-left, +90 = camera-right, 180 = behind the product; `el` = degrees above the horizon. `face_tilt_deg` = how far the face leans back; `bend_deg` = how far a filled pouch's face curves away at the sides. `python engine/shotplan.py example` prints a full spec.

## What the planner tells you, and what to do with it
| Output | Read it as | Typical fix |
|---|---|---|
| `product_frame_fill` | Share of frame height the product fills | Under 18%: print won't read; over 85%: no air |
| `dof_depth_mm` vs product depth | Front-to-back zone of focus | Stop down, step back, or accept a soft back edge on purpose |
| `persp` | Signed keystone (+ top narrower: low camera or pack leaning back; - top wider: camera above an upright pack) | Passed to `composite.py --persp` |
| Light `quality` and `penumbra_at_tip_mm` | Hard / medium / soft, and how wide the shadow edge is | Bigger or closer source = softer |
| `shadow_dir`, `shadow_len_x_product_h` | Where the shadow goes and how long | Passed to `composite.py --light`; must match the plate |
| `falloff_across_product_stops` | How much one side of the pack is darker from distance alone | A close light gives a strong gradient; move it back for even light |
| `ratio_to_key_stops` | Fill and rim strength | 1-2 stops is typical product; 3+ is dramatic |
| `mired_vs_key` | Colour clash between sources | Over 30: visible; keep only if motivated |
| `glare_frac`, `where` | Share of the pack face where a light mirrors into the lens | Move to the suggested position; or a large soft source on purpose over an unprinted area |
| Floor `mirror_reflection_strength` | How strong the product's reflection is on the surface | Gloss + low camera = a big reflection to build; matte = none |

## Rules
1. **One key.** If two lights are within a stop from opposite sides, the planner warns: two shadows are an amateur and AI tell.
2. **Glare is decided before the prompt.** If the key mirrors over the print, move it; never "fix" it by letting a model repaint the pack.
3. **The plate is the truth after it exists.** Read its real shadow direction and re-run the composite with what you measured; the plan was the brief, not the result.
4. **Numbers in the prompt, adjectives out.** "Soft strip from camera-left, 55 degrees off axis, 38 degrees up, shadows 1.3 times as long as the object is tall" beats "beautiful soft cinematic lighting".
5. **Same plan for every SKU in a set** (all-or-none). Change the plan once, re-run every SKU.
