# Improving the kit from your own work

The kits are a starting point. They get better when the person using them says what broke, and when the work shows where a rule was wrong, missing or too loose. Any Claude running a `nazar-*` kit does this as part of the job.

## When to look for an improvement
- A rule was followed and the result was still wrong (the check passed, a human saw the fault).
- An engine gave a number or verdict the user overruled.
- The user corrected the same thing twice.
- A step was skipped because it didn't fit this kind of job.
- A real asset exposed a limit the docs don't mention (a resolution, a script, a file type).

## What to do, in order
1. **Say it in one line** at the end of the job: "This rule failed here because X."
2. **Log it** in `LESSONS.md` in the kit's folder (create it if missing), one entry each:
   `date · kit · what happened · what the evidence was · proposed change`.
   Keep the evidence in the entry: the measurement, the check, the user's words. A hunch without evidence goes in as a hunch.
3. **Propose the patch.** Name the exact file and the exact line or rule to change. Don't edit a shipped `SKILL.md`, reference or engine silently.
4. **Patch only with the user's okay**, then test on the asset that exposed the problem and on one other, so the fix doesn't just fit one case.
5. **If an engine was wrong, fix the engine and add the failing case as a test** rather than adding a note that says "be careful".

## Rules for good lessons
- One lesson, one cause. Don't bundle.
- Prefer a measurable rule to adjectives ("accent below 3:1 on the background" beats "low contrast").
- A lesson from one client's taste goes in that user's own PATTERN or brand file, not in the kit. The kit holds what is true for most jobs.
- Don't loosen a safety rule (client logos, AI imagery approval, licences, nudity, privacy) because a job was inconvenient.
- Remove or correct a lesson that later turns out wrong. Don't leave stale ones.
- Cite the source when a lesson rests on research, the same way the references do.

## What never goes in a lesson or a patch
Client names, brand names under NDA, contact details, unreleased copy, private archives or anyone's voiceprint content. Describe the case generically ("a bilingual snack pack with a 90 mm tall label").

## If the user shares the kit
Ask whether `LESSONS.md` entries are theirs alone or worth sending back to the kit's author. Never send them without a yes.
