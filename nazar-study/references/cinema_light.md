# Cinematic light, translated to product work

Film lighting is product lighting with a story attached: every source has a reason to be there. Tags: [SRC] checked (link), [KNOWN] widely documented film history (verify before quoting in client copy). Studied 2026-11-22. Cite the film and scene as a reference; never put stills in a deliverable.

## Cinematographers
| Who | What they're known for | The practice we take for a product scene |
|---|---|---|
| **Roger Deakins** | Lights so each source traces to something plausible in the set; uses large soft sources for naturalism (ASC on *The Village*, 2004); diagrams all the lighting with the gaffer and grip before the shoot [SRC] | **Motivate every light.** Name the window, lamp or sky that justifies the key before writing the plate prompt; draw the diagram first (`shotplan.py`). Restraint: "just enough" light |
| **Subrata Mitra** (Satyajit Ray's films) | Credited with developing bounce lighting, reflecting light off cloth to imitate soft daylight indoors [KNOWN] | **Bounce, don't blast.** The desi interior look (soft, shadowless-but-directional) comes from a large bounced source; brief "light bounced off a white sheet from the courtyard side" |
| **V. K. Murthy** (*Kaagaz Ke Phool*, 1959) | The famous beam of light through a studio's high window [KNOWN] | **One shaft, with dust,** as the single event in a frame. Use it once per campaign, motivated by a high window |
| **Gordon Willis** (*The Godfather*) | Top light and deep underexposure; eyes left in shadow [KNOWN] | **Let parts of the frame go black.** A low-key product frame needs the shadow side to really fall off; lifted shadows read as video |
| **Néstor Almendros** (*Days of Heaven*) | Shot much of the film at magic hour, the minutes after sunset [KNOWN] | **Name the minute, not "golden hour".** After-sunset light is soft, shadowless and cool-warm split; before sunset it is hard and orange. Different shadows, different plate |
| **John Alcott** (*Barry Lyndon*) | Candlelit interiors shot with very fast lenses [KNOWN] | **A practical can be the key.** If a lamp or candle is in frame, its light must fall off fast (inverse square) and be warm; `shotplan.py` warns on the mired gap |
| **Vittorio Storaro** | Treats colour as meaning; wrote *Writing with Light* [KNOWN] | **Colour of light as a brand decision:** one controlled colour cast per line, motivated and repeated across every SKU |
| **Christopher Doyle** (Wong Kar-wai's films) | Saturated practicals, frames within frames, step-printed motion [KNOWN] | **Frame within a frame** (a doorway, a shelf gap, a rickshaw window) and coloured practicals for night scenes |
| **Emmanuel Lubezki** | Natural and available light, long takes [KNOWN] | **Shoot (or brief) at the hour the light is right** instead of adding light; the plate's time of day is the lighting design |

## Painters' light (the vocabulary film borrowed)
| Name | What it is | Product use |
|---|---|---|
| **Tenebrism** (Caravaggio) | Figures pulled out of near-black by one hard source [KNOWN] | A hero pack in a dark scene: one hard key, black flag on the far side, no fill |
| **Window light** (Vermeer) | Soft daylight from a high side window, gradual falloff across the room [KNOWN] | The default "real kitchen" key: large, soft, from one side, falling off across the table |
| **Rembrandt lighting** | Key about 45 degrees to the side and above, a small triangle of light on the shadow cheek [KNOWN] | For packs: a key 35-60 degrees off axis and above gives modelling on the gusset and a readable face |
| **Chiaroscuro** | The modelling of form by light and shade in general [KNOWN] | Every pack face needs a gradient; a flat-lit pack reads as a scan |

## Working vocabulary (use these words in plate briefs; they mean something to a gaffer)
- **Key, fill, rim/back, kicker, practical** (a lamp in the shot), **motivated** (the light has a source in the story).
- **Negative fill:** a black card or flag on the shadow side to deepen it, the reverse of a bounce.
- **Book light:** a source bounced into a diffuser, a very soft key.
- **Flag, cutter, scrim, silk:** block, shape, reduce or soften a light.
- **Ratio in stops:** key to fill, 1 stop = half.
- **Hard / soft:** set by the source's size relative to its distance, not its brightness.
- **Contrast of temperature:** a warm key against a cool fill is a decision; say why.

## Translation table: from a film reference to a plate brief
| If the reference is... | Brief the plate as... | `shotplan.py` spec |
|---|---|---|
| A dark interior with one lamp | "one warm practical lamp camera-left, just outside frame, falling off fast; black shadows; no fill" | key bare, size 0.2 m, dist 0.8 m, cct 2800; no fill |
| A sunlit courtyard | "hard noon sun high from camera-right; short crisp shadows; sky fill cool" | key sun (size tiny, far), el 65; fill bounce cct 7000 |
| A shop at night | "overhead tube light, flat and slightly green; shelf lip shadows straight down" | key strip overhead el 80, cct 4500 |
| An after-sunset rooftop | "no direct sun; the whole sky as a soft cool source; warm city glow low behind" | key huge soft el 30, cct 7500; rim cct 3000 low |
