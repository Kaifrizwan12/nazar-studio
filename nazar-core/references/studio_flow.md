# Studio flow: how every Kaif job runs

The same seven phases apply to a logo, a pack or a billboard. Each kit adds its own detail on top.

| # | Phase | Goal | Gate (what must be true before moving on) |
|---|---|---|---|
| 1 | **Brief** | Understand the job, the business and the constraints | Intake round 1 answered, and the facts asked in plain text. Scope and price agreed (`nazar-pitch`). |
| 2 | **Research** | Earn the right to an opinion | `research/summary.md` exists: 5 key findings, the cliché to avoid, the forgotten thing to revive, the empty spot on the competitor map, 3 concept seeds. |
| 3 | **Direction** | Agree the idea before the look | 2–3 routes shown with rationale. One chosen. The idea written in one sentence and confirmed ("yes"). |
| 4 | **Design** | Make it real | Work built in the agreed system, shown section by section as contact sheets. |
| 5 | **Test** | Prove it works in the world | The kit's stress tests passed (blur, size, shelf, feed, distance, print). Issues fixed. |
| 6 | **QA** | Catch what Kaif would catch | `qa_design.md` run on everything, plus the kit's QA list. P1 and P2 issues fixed and reported. |
| 7 | **Handover** | Make it usable without us | Files named and organised, a README, licences listed, the spec updated, a case-study write-up. |

## Files every job keeps (in the client repo)
```
SPEC.md            the locked decisions (idea, name, tagline, palette, type, scope, open questions)
research/          inventory, research passes, summary, sources, moodboard (with rights noted)
engine/            copied from nazar-core/engine when rendering locally
exports/           what gets shown and delivered
assets/            the final asset pack
```

## Rhythm with Kaif
- Show contact sheets, not single images. He reviews by page or number.
- Each review is fixed in one pass, and then the same class of issue is hunted everywhere.
- After every locked decision, update `SPEC.md` the same day.
- If he changes a locked decision, state the cost (pages or files affected) once, then do it.
