# Models and prompt translation

> **Dated file: capabilities as checked on 2026-11-14.** Models change fast. Re-check the official docs before a job and update this table. The rules in SKILL.md barely change between models.

## Google, current line-up (as of 2026-11-14)
- **Imagen is shut down in the Gemini API.** Use the Nano Banana family (aistudio.google.com/docs/imagen).
- **Veo 3.1 Preview models were shut down in the Gemini API on 22 Oct 2026.** Use **Gemini Omni Flash** (`gemini-omni-1.2-flash`) or the GA Veo models on Vertex (aistudio.google.com/docs/video).
- In **Flow**, Veo 3.1 Fast and Quality retire on 5 Dec 2026, and Extend was retired on 5 Nov 2026 (support.google.com/flow/answer/16352836).

### Images: Nano Banana family (aistudio.google.com/docs/image-generation)
| Model | ID | Use |
|---|---|---|
| Nano Banana 2.1 | `gemini-nano-banana-2.1` | Default |
| Nano Banana Pro | `gemini-3-pro-image` | Professional assets, text |
| Nano Banana 2 / 2 Lite / original | `gemini-3.1-flash-image` / `-lite-image` / `gemini-2.5-flash-image` | Older or cheaper |

- **References:** up to 14 per request. On 2.1 / 3.1 Flash: 10 objects + 4 characters. On Pro: 6 objects + 5 characters + 3 style references.
- **Sizes:** 1K / 2K / 4K (uppercase K).
- **Aspect ratios:** 1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3, 4:5, 5:4, 8:1, 9:16, 16:9, 21:9.
- **SynthID** on every output. No official seed: plan for non-determinism and log every run.

Rules from Google's guide:
- describe the scene, don't list keywords;
- be specific; state the purpose;
- iterate conversationally, breaking complex scenes into steps;
- phrase positively;
- use camera terms;
- edits keep the input's aspect ratio (with several inputs, the **last** image's), so state the ratio explicitly;
- to fix drift, open a new chat with a detailed character description;
- describe the critical features that must stay unchanged.

Text in images: give the exact text, font style and design, and use Pro. Better still, generate the text first. Treat AI text as placeholder until it's proofread at 100%.

Templates (fill in the brackets):
- **Photoreal:** "A photorealistic [shot] of [subject], [action], set in [environment]. Lit by [lighting], creating a [mood] atmosphere. Captured with a [camera/lens], emphasising [textures]. [Ratio]."
- **Product:** "A high-resolution, studio-lit product photograph of [product] on [surface], [lighting setup], [angle], sharp focus on [detail]. [Ratio]."
- **Edit:** "Using the provided image of [subject], [add/remove/modify] [element]; keep everything else exactly the same: style, lighting, composition."
- **Compose:** "Combine: take [element from image 1] and place it with/on [element from image 2]; match lighting and shadows."

### Google's own prompting guides (checked 2026-11-22)
- *7 tips to get the most out of Nano Banana Pro* (blog.google, 2025-11-20) and *The ultimate Nano Banana prompting guide* (Google Cloud, 2026-03-06). Nano Banana Pro = Gemini 3 Pro Image; Nano Banana 2 = Gemini 3.1 Flash Image. Re-check IDs in the docs; the guides give none.
- Structures: text-to-image = [Subject] + [Action] + [Location/context] + [Composition] + [Style]; with references = [Reference images] + [Relationship instruction] + [New scenario].
- **Give every reference a role** in words ("Use image A for the pose, image B for the style, image C for the background"). Up to 14 references, the number varies by surface.
- Name the light setup ("three-point softbox setup", "chiaroscuro with harsh, high contrast"), the lens and aperture ("shallow depth of field (f/1.8)", "macro lens"), the camera or film stock; define the canvas ("a 9:16 vertical poster").
- Edits: say what changes and "keep everything else the same". Google warns that blending and **lighting changes can produce unnatural artifacts**: for new light, generate a new plate (`../../nazar-shoot/references/gemini_routes.md`).
- Text: put words in quotes, name the type style and placement; small text and spelling "may not work perfectly", so final type is always set in post.
- Every output carries SynthID and C2PA credentials. Knowledge cutoff of both models: January 2025.
- For the shot itself (camera, lights, glare, reflections) write the prompt from `../../nazar-shoot/engine/shotplan.py`'s plan, not from adjectives.

### Video: Gemini Omni Flash, Veo, Flow
- **Formula** (Google Cloud Veo 3.1 guide): **[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]**.
- **Audio:** dialogue in quotes (`A woman says, "…"`), `SFX: …`, `Ambient noise: …`. Keep dialogue within the clip length.
- **Timestamps** for multi-shot clips: `[00:00-00:02] … [00:02-00:04] …`, one camera move per segment.
- **Omni:**
  - Output: 3–15 s (10 by default), 16:9 or 9:16, 720p (1080p and 4K are upscaled).
  - Inputs: up to 6 subject images (≤ 3 per character, ≤ 2 characters) and up to 3 reference clips of 3 s or less.
  - Write **"In a single continuous shot. No scene cuts."** to stop it cutting between shots.
  - Write sound as "Sound design: … No dialogue.".
  - No negative-prompt field, so write "Do not …" in the prompt.
  - Don't use deprecated control tags; describe each input's role in plain words.
  - Extension sees only the **last 10 s**: describe again anything that appeared earlier.
- **Veo on Vertex:** up to 3 asset references (JPEG/PNG); with subject images the output is 8 s only; 720p/1080p, 16:9 or 9:16, 4/6/8 s.
- **Flow** (labs.google/flow):
  - Three modes: **Text**, **Frames** (start and/or end) and **Ingredients** (a style, or up to 3 subjects, locations or objects; type `@` to pull assets in).
  - Use plain or segmented backgrounds for subjects; keep location and style references free of extra subjects.
  - Keep a consistent look across ingredients, and make the prompt refer to every supplied ingredient.
  - Scene Builder sequences, trims and downloads clips; repeat key details across shots.
- **Recommended workflows:**
  - Frames → video: make start and end frames in Nano Banana, then describe the transition.
  - Dialogue: one reference per character plus the set, one prompt per shot, and the reverse shot made by changing only the framing.

## Other models: key differences
- **Midjourney:** short phrases plus parameters (`--ar`, `--stylize` 0–1000, `--chaos`, `--seed`, `--raw`, `--no`), and `--sref` for style. Keyword-friendly, with a usable seed. (V7 Omni Reference may be replaced in V8 [UNVERIFIED].)
- **OpenAI image:** state the result first (subject, use, composition, ratio); labelled sections are fine. Put text in quotes with its position and type, spell brand names letter by letter, and ask for no extra text. For edits, "change only X" plus what to preserve. Number your references; make one change per turn.
- **Runway image-to-video:** describe **motion only** (subject, environment, camera, timing); don't re-describe what the image shows.
- **Kling** [UNVERIFIED]: Subject + Movement + Scene + (Camera + Lighting + Atmosphere), plus a separate negative field (morphing, warped limbs, flicker).

**Portability:** keep one master description, then translate it:
- Midjourney: compress it to phrases plus parameters.
- Runway and Kling: keep the motion only.
- Veo and Omni: add the audio lines and "single continuous shot".
- OpenAI: add labelled sections and quoted text.

## Worked structures
**Packaging hero (Nano Banana Pro, image 1 = the real pack):**
```
Purpose: e-commerce hero, 4:5, top third clear for the headline (added in post).
Using the provided image 1 of the [product] pack, keep the pack's shape, label artwork, colours and logo exactly unchanged.
Place it on [surface: material, colour in words + #hex], slightly right of centre, 3/4 angle, camera at pack height, 100 mm
macro look, f/8 sharp across the label. Single large softbox key from camera-left, white bounce right, soft contact shadow.
Props: [2 props, materials]. Muted natural grade, real surface texture, no extra text or logos. 4:5, 2K.
```
**Social reel (Omni, 9:16):**
```
In a single continuous shot. No scene cuts.
Slow push-in, medium close-up, subtle handheld, 35 mm. The woman from reference 1 (same face, hair, outfit), the product from
reference 2. She unscrews the jar, looks up and half-smiles. Small sunlit kitchen, morning, steam from a cup behind.
Naturalistic warm window light from the left, light film grain, muted palette.
Sound design: kettle ticking, spoon on ceramic. She says softly: "[line under 8 s]".
```

## Sources
aistudio.google.com/docs (image-generation, imagen, video, omni, terms) · developers.googleblog.com (prompting Gemini 2.5 Flash Image) · cloud.google.com/blog (ultimate prompting guide for Veo 3.1) · docs.cloud.google.com/vertex-ai (video prompt guide; reference images) · support.google.com/flow (16352836, 16353334) · labs.google/fx/tools/flow/faq · blog.google (Flow tips; SynthID verification) · docs.midjourney.com · developers.openai.com (image prompting) · help.runwayml.com · policies.google.com/terms/generative-ai/use-policy · copyright.gov/ai (Part 2) · artificialintelligenceact.eu (Art. 50)
