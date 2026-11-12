# nazar-studio 👁️👁️

> A whole design studio, in folders. It asks before it draws, reads old archives instead of scrolling trends, and won't let a widow sneak into a headline.

**nazar-studio** is a set of [Claude Code](https://claude.com/claude-code) skills from Nazar, a creative studio run by Kaif Nathani. Drop it in, describe a brand, and Claude works the way a fussy, archive-obsessed, slightly cheeky studio would:

1. **Asks first.** Questions come up front, each with options and a recommended pick.
2. **Researches properly.** It goes to old manuals, crate labels, street lettering and real maps. Trend blogs come last.
3. **Thinks in ideas.** Every route gets one sentence of meaning before any pixels.
4. **Builds, then nitpicks.** About 90 QA checks catch the gap under the heading before you do.

No AI slop, no stock photos, no cartoon mockups, and no "elevate your journey".

## What's in the box
| Kit | Does |
|---|---|
| `nazar-core` | The brain everything shares: the profile, research path, ideation, masters' practices, QA, the renderer |
| `nazar-strategy` | Positioning, names, taglines that actually have an edge |
| `nazar-logo` | Marks, from 100 thumbnails to the blur test to every export file |
| `nazar-brand-book` | The identity system and the book (with hidden things to find) |
| `nazar-packaging` | Packs that win the shelf in 2 seconds and print without drama |
| `nazar-social` | Feed-native systems, reels, launch grids, the slop test |
| `nazar-ooh` | Billboards, walls, vehicles and screens that read in one breath |
| `nazar-motion` | Logos that move like they mean it |
| `nazar-web` | Brand sites that are fast, accessible and a little bit extra |
| `nazar-art-direction` | Photo briefs, illustration guides, icon grids |
| `nazar-pitch` | Proposals, pricing, contracts, feedback (and how to survive it) |

## Install (30 seconds, 0 drama)
```bash
git clone https://github.com/Kaifrizwan12/nazar-studio.git
cp -R nazar-studio/nazar-* ~/.claude/skills/
```
Keep the kits side by side, since they all read `nazar-core`. For a single project, copy them into `.claude/skills/` in that repo instead, and drop `CLAUDE.md` in the root.

## Use
Open your project in Claude and say what you need, or paste a ready-made prompt from [`PROMPTS.md`](PROMPTS.md):
> *"Brand book for a neighbourhood coffee roaster. Bilingual. Make it sober, but let it wink."*

Then answer the questions. It'll take it from there, and it'll show its homework.

## House rules
- Meaning before looks. If the logo needs explaining, it isn't finished.
- The client's logo is sacred. Nobody "cleans it up".
- Loud colour, calm grid.
- Lock the tagline before the build. Changing it on page 60 costs everyone a weekend.

## Credits
Method and taste by **Kaif Nathani** / Nazar. Standing on the shoulders of Vignelli, Rand, Rams, Müller-Brockmann, Aicher, Crouwel, Games, Gill, Bass, Albers and a lot of very patient archivists. Fonts in `nazar-core/engine/fonts` are SIL OFL (licences included).

Made with two eyes open. 👁️👁️
