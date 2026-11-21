# Research: review states, proofing rounds, before/after comparison

Collected on 2026-11-21 for the review wall (`engine/review_wall.py`, guide `references/review_wall.md`). This file records patterns only. Most sources are vendor help pages, community threads or component docs, so treat them as common practice, not measured research.

## 1. Resolved states in design and code review tools
**Findings**
- Resolving is a per-thread state, kept rather than deleted. Resolved items are collapsed or filtered out of the default view and can be reopened. One code-review platform collapses resolved threads by default so reviewers can focus on open ones, and offers a Reopen action.
- A Resolved filter is standard, and users complain when it is hard to find or switches on by itself. Designers want "open only" by default and "resolved" on demand.
- **Main pain point:** once the design changes, a resolved note loses its context. Threads point at areas that no longer exist, and reviewers can't see what the note was about. Tying threads and states to a specific version or commit is the usual remedy.

**Sources (accessed 2026-11-21)**
- Community thread, resolved-comment filter behaviour in a layout app's review panel: https://community.adobe.com/t5/indesign-discussions/indesign-review-panel-automatically-filters-to-resolved-comments-when-editing-text/td-p/14619901/page/2
- Community answer, finding resolved comments in a shared design review link: https://community.adobe.com/t5/adobe-xd-discussions/how-to-find-resolved-comment-in-xd-s-design-review-link/m-p/11125400
- Forum thread (2022), "couple comments with file history": https://forum.figma.com/archive-21/couple-comments-with-file-history-34865 (403 on fetch; read from the search summary)
- Article, resolvable comments in code review: https://community.atlassian.com/t5/Bitbucket-articles/Simplify-code-review-in-Bitbucket-with-resolvable-comments/ba-p/2331486
- Changelog, marking design feedback resolved: https://mockflow.com/changelog/now-mark-completed-design-feedback-as-resolved.md

## 2. Proofing practice in print and packaging
**Findings**
- Approval comes in gates: concept, artwork, pre-press, then the proof before the run. Each round is tracked with a full approval history, which works as an audit trail.
- **Printer proof tags use three outcomes:** OK as is (release to print), OK with corrections (fix, with or without a new proof), and new proof required. Forms disagree on whether "OK with corrections" needs another proof, so agree on it up front.
- When artwork changes mid-cycle, it goes back through the approval stages it had already passed.
- Approval by committee means nobody is accountable. Name one signer.
- Mark corrections directly on the proof, never on loose notes that can get separated from it. When a revised proof comes back, check that each correction was made and that nothing else changed.

**Sources (accessed 2026-11-21)**
- Packaging design workflow, brief to production: https://www.goproof.net/blog/packaging-design-workflow-brief-to-production
- Packaging design process: https://www.ziflow.com/blog/packaging-design-process
- Artwork management and approval history: https://www.loftware.com/why-artwork-management
- State proof approval form ("approved as is", corrections without a new proof): https://forms.in.gov/download.aspx?id=11941
- University print approval and release (a new proof after changes): https://csprocedures.rutgers.edu/node/10
- How to check a proof (mark-up rules, the tag, a second revised proof): https://des.wa.gov/services/print-mail/resource-center/how-check-proof
- Proofing and approval cycles, practical guide: https://www.fespa.com/en/news-media/features/proofing-and-approval-cycles-a-practical-guide (403 on fetch; read from the search summary)
- Community thread, "approved with changes" vs "changes required": https://experienceleaguecommunities.adobe.com/adobe-workfront-general-23/how-do-you-use-approved-with-changes-and-reject-for-proofs-126085

## 3. Before/after comparison UX
**Findings**
- **Slider (swipe):** best when the change sits in the same frame and the reviewer gains from scrubbing across details. Visual-diff guides rank it the most useful mode for catching small element shifts. Label both sides clearly. Don't use one when a static image says it just as well.
- **Toggle (blink, flip):** flips the whole frame at once. It's the usual mobile fallback for a slider, and good for spotting any change at all.
- **Side by side:** for seeing both states at once on wide screens. It breaks down on phones, where both images shrink, and it can miss 1 px shifts at thumbnail size.
- **Onion skin:** opacity overlay for sub-pixel drift. Text gets hard to read when the layers overlap, so keep it as a specialist mode.
- **Pixel diff:** highlights changed areas, usually in red, to confirm what the other views showed.
- Use a native range input (keyboard and touch friendly), give it large touch targets, and start at 50 %.

**Sources (accessed 2026-11-21)**
- City design system, before and after slider usage: https://summit.calgary.ca/components/media-overview/before-and-after-slider.html (404 on fetch; read from the search summary)
- Before/after layouts on mobile: https://studio.swiperjs.com/for/before-after
- Compare slider component (orientation, touch targets): https://diceui.com/docs/components/base/compare-slider
- Image view modes (2-up, swipe, onion skin): https://github.blog/news-insights/the-library/behold-image-view-modes/
- Screenshot regression comparison modes: https://support.smartbear.com/crossbrowsertesting/docs/visual-testing/screenshot-regression-testing.html
- Visual regression diff panel, which mode for what: https://camoa.github.io/dev-guides/testing/visual-regression/html-report/pw-report-vr-diff-panel/

## Applied to the review wall
| Finding | What the wall does |
|---|---|
| Resolved is kept, filterable and reopenable | `--resolve` / `--unresolve`, Open/Resolved badge, All / Open / Resolved filters, "x of y resolved" count |
| Context is lost after a change; tie it to a version | State keyed by source file and hash in `wall.json`; the before image is kept per sheet; the Before tag names its round ("Before · R1") |
| Changed artwork goes back for approval | A sheet whose design changes reopens automatically; re-resolve it after the reply |
| Rounds are tracked | `--new-round` bumps the round shown on the page and clears every resolved flag |
| Resolved is not approval | Wording is "Resolved", never "Approved"; signed approval stays on the proof or PDF (see nazar-pitch handover) |
| Slider for same-frame changes, toggle for a whole flip, side by side is weak on phones | Labelled overlay slider (native range, 50 % start) plus a Show before / Show after toggle; no side-by-side mode |
| Check that nothing else changed | The Updated filter shows only the changed sheets, for a quick pass over each round |
