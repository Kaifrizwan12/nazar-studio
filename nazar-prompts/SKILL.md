---
name: nazar-prompts
description: Nazar Studio's AI image and video prompting kit. Use when a client has approved AI-generated imagery or video in writing, or when a concept is too complex to draw in code and a ready prompt should be handed over. Writes model-agnostic master prompts and translates them for Gemini image models (Nano Banana family), Gemini Omni / Veo video, Google Flow (frames, ingredients, scene builder), Midjourney, OpenAI image, Runway and Kling, with asset-attachment checklists, an iteration log, brand-consistency and anti-AI-look rules, and disclosure, licensing and ethics checks.
---

# Nazar prompts

Read `../nazar-core/SKILL.md` first. **The user's prompt leads; use what the job needs.**

## When this kit applies
- **The client approved AI imagery or video in writing.** Log who approved it and when, the model, and the date.
- **A concept is too complex for code drawing** (`../nazar-illustration/`). Claude hands over a ready prompt as the advanced route, alongside the honest code-drawn version.
- Never for logos or final type. Logos, legal copy, prices and Urdu/Hindi text are added **in post** with the real assets.

## Rules
1. **Write one master description in natural language**, then translate it per model (`references/models.md`). Describe the scene; don't list keywords.
2. **Purpose and placement first:** what it's for, the aspect ratio, and the copy-safe zone ("top 20% clear for the headline, added in post").
3. **Art-direction vocabulary:**
   - shot (ECU…EWS), angle, lens (24/50/85/100 mm macro), depth of field;
   - one motivated light source (key, fill, rim, softbox, golden hour, practicals);
   - materials and surfaces; film stock and grain.
4. **Phrase positively** ("an empty street"); use a negative field only where the model has one.
5. **Brand consistency:** describe colours in words **and** hex, and above all attach a palette or style reference image. Keep product and logo references as "preserve exactly", then swap in the vector logo in post anyway.
6. **Anti-AI-look:**
   - real texture (pores, weave, dust);
   - one motivated light, not "cinematic lighting";
   - an off-centre subject;
   - a restrained, film-like grade;
   - no "ultra-detailed, 8K, masterpiece, trending";
   - no unmotivated glow or bloom (Kaif's rejections).
7. **Attach the right assets** (`references/assets.md`): plain-background product references, character sheets, location plates, style frames, start and end frames, all in the output aspect ratio, at least 1920 px on the long side.
8. **Iterate in small steps; restart a fresh session when it drifts.** Log every run (`templates` in `references/assets.md`): date, tool, model ID, settings, full prompt, attached files, output, keep/kill and why.
9. **Ethics and legal:**
   - never name living artists; describe the qualities of a style instead;
   - no third-party logos or real people without releases;
   - disclose AI use and keep SynthID / C2PA metadata;
   - outputs aren't exclusive (Gemini API terms);
   - do substantial human post-production and keep the layered files (US copyright guidance);
   - check local disclosure rules (EU AI Act Art. 50; India's IT Rules amendment 2026).

## Files
- `references/models.md`: dated capabilities and per-model prompt translation (Nano Banana, Omni/Veo, Flow, Midjourney, OpenAI, Runway, Kling), structures and examples
- `references/assets.md`: asset checklists per job (pack hero, reel, product video, OOH), the iteration log template, the disclosure note
- `references/product_texture_prompts.md`: product-texture photos and empty plates for pack composites (anti-slop lesson, model notes, a template)
