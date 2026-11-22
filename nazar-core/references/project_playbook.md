# Project playbook: from an empty folder to a released brand

For anyone who clones the skills into an empty project and a brand walks in. Nothing here is fixed to one brand or one kind of job: the task decides the folders and the order of work. Read the task, pick its recipe (section 2), scaffold only what it needs, and grow the project as new tasks arrive.

## 0. Start (5 minutes)
```
your-project/
  .claude/skills/        the cloned nazar skills (this repo)
```
1. Name the task (section 2), then `python .claude/skills/nazar-core/engine/scaffold.py init "<Brand or working name>" --task <task>[,<task>]` (tasks: identity packaging rebrand social campaign web motion shoot piece; add `--new-brand` when the brand has no identity yet; `scaffold.py tasks` lists the recipes).
   It creates **only the folders that task needs**, plus a hub `README.md`, `SPEC.md`, `STATUS.md`, a filled-in `CLAUDE.md`, `.gitignore` and `_archive/MANIFEST.md`. It also installs the `nazar-researcher` subagent and lays out `01_research/` for the task's research profiles. It never overwrites an existing file. When a new task arrives, run it again: it adds what's missing.
2. `git init`. Keep the repo private: it is client work.
3. Put the client's files in `00_brief/` exactly as received (brief, logo, photos, old packs). Never edit originals.
4. **Ask once about contributing** (open-source users): `python .claude/skills/nazar-core/engine/contribute.py ask` prints the question; record the answer with `contribute.py set yes|no|later`. See section 5.

## 1. Folder map (numbered by the order the work happens; only the task's folders exist)
```
00_brief/            what the client gave, untouched + brief-summary.md
01_research/         nazar-research output: angles, sources, gaps, codes, summary, dataset/ (reference only)
02_strategy/         positioning, naming, tagline, messaging (locked lines go to SPEC.md)
03_identity/         logo, colour, type, illustration, photo style, brand book
04_packaging/        _architecture (formats, SKU list), core-reference/ (01_versions, 02_dielines, 03_mockups), print-production/
05_social-media/     profile kit, templates, pillars, first posts
06_marketplace/      store and listing assets (only if the brand sells online)
07_collateral/       stationery, kiosk, merch
08_photo-video/      shot plans, plates, composites, films
09_meetings/         agendas and notes (YYYY-MM_topic.md)
10_deliverables/     client PDFs per version
CLIENT_<BRAND>_v01_<date>/     the release the client receives (root, one per sent version)
BEHANCE_<BRAND>_v01_<date>/    the portfolio release (root)
_archive/            superseded things, moved never deleted, listed in MANIFEST.md
```
Folders for jobs not in scope are not created. Add them when the job arrives (`scaffold.py init` again with the new job: it adds only what's missing).

## 2. Order of work: pick the recipe that fits the task
Read the prompt and the brief first. Name the task in one line ("a pack range for a new snack brand", "a rebrand", "a launch campaign", "30 posts for an existing brand"). Then take the recipe below that fits, drop the steps the brief already covers (an existing brand keeps its logo; a posts job skips strategy), and tell the user the plan in one short block. Every recipe starts with research (`nazar-research`, the subagent in the background while intake runs) and ends with QA and a release.

| Task | Steps in order (kits) | Folders created |
|---|---|---|
| **New brand, full identity** | brief → research → strategy (position, name, tagline: lock) → logo → colour + type → brand book → applications → story → release | 00 01 02 03 09 10 |
| **Packaging** (new or existing brand) | brief → research (category, competitors, the shelf, a dataset of real packs) → core pack on a real dieline (one pack approved) → range and family rules → support pieces (box, mailer, display) → shoot → story → release | 00 01 04 08 10 (+02 03 if the brand is new) |
| **Rebrand / refresh** | brief → research (current assets: fame and uniqueness) → keep / change / drop list → strategy if positioning moves → mark refresh → system → rollout list → release | 00 01 02 03 10 |
| **Social system or content** | brief → research (the feeds, competitors, culture) → pillars → backdrops → templates → first posts → playbook | 00 01 05 |
| **Campaign / OOH** | brief → research (the place, street media, culture) → idea and routes → key visual → adaptations per site → mockups in place → release | 00 01 07 08 10 |
| **Website / landing page** | brief → research (competitor and leader sites, customers) → structure → design → build → audit | 00 01 03 (+ web/) |
| **Motion / film** | brief → research (idents in the category, specs) → storyboard → stills for review → render → platform exports | 00 01 08 |
| **Shoot / product imagery** | brief → research (the best photography of the category) → shot plan → plates → composites → realism gates | 00 01 08 |
| **Single piece** (one post, one label, one deck) | brief → a short research pass → make → QA | only where the piece lives |

**When tasks stack** (a brand grows from packaging into social, then a campaign), run `scaffold.py init --jobs <new job>` again: it adds the new folders and the new research profile, and keeps everything that exists. The research folder grows; it is never restarted.

**Adjust by relevance.** The table is a default, not a rule. A brand that already has a strong identity starts at its task; a brief with a deadline drops the deeper research rounds and says so; a job the table doesn't name borrows the closest recipe. The user's prompt always leads.

## 3. Practices (learnt the hard way on real work)
- **Show before you build big, and before every commit.** Preview stills or a contact sheet first; render films and full decks only after a yes. Commit and push only on a clear yes.
- **Lock before production.** Name, tagline and idea go into `SPEC.md`. A change after the lock costs a rebuild: say what it touches, once, then do it everywhere (every pack, film, deck page, mockup) and re-run QA.
- **Versions.** Work happens in `01_versions/vNN_<label>/`. A version that was **sent** is frozen: never rebuild into it. Bump the version string in the build and publish scripts for the next round.
- **Never delete; archive.** Superseded versions, release folders, zips, scratch plates go to `_archive/` with a line in `MANIFEST.md` (what, from where, why, date). Ask before removing anything.
- **Release folders are copies of `out/`.** If they are hard links (to save disk), detach before rebuilding, or a rebuild rewrites the frozen release. An unsent version may be rebuilt in place.
- **One build command, one QA gate.** A `qa_all.py`-style script rebuilds everything and fails on overflow, overlaps, missing files and contrast. Nothing ships on FAIL.
- **One family.** Change one SKU, change all. Rules in `FAMILY_RULES.md`.
- **Real over generated.** The pack is always our render; AI makes only empty plates and textures, labelled, with the client's written yes.
- **Presentation rules.** Photos woven into the story, not tacked on at the end; no image carries its own background; structures shown beside their flat dielines; best work forward, no repeated hero; no running footer.
- **Privacy.** Client names and files never go into the public skills repo. Lessons are written generically.
- **Disk.** Films and decks are big. Check free space before a full render; render JPG panels when short.
- **Log what you learn.** A failure becomes a line in the kit's `LESSONS.md`; a decision becomes a line in `SPEC.md` or `STATUS.md`.

## 4. Moving files: when and where
| Moment | Move |
|---|---|
| Client sends something | `00_brief/` (originals), note in `brief-summary.md` |
| A reference is useful | `01_research/dataset/` via `dataset.py harvest/add` (with source and rights) |
| A route is rejected | `_archive/` with a manifest line (keep the reasoning) |
| A version is sent | `scaffold.py release <out_dir> <BRAND> vNN [--kind CLIENT|BEHANCE]` copies the deliverables to the root as real copies (a rebuild can never rewrite them) and archives the previous release; the version is frozen |
| The next round starts | the previous release folders go to `_archive/` (`scaffold.py archive <path> "<why>"`); only the latest release stays at the root |
| Final print files approved | `04_packaging/print-production/` only |

## 5. Giving back (opt-in, open-source users)
The skills improve from real work. People who clone them are asked **once per project** whether they want to share what their project taught the kits. The default is no, and nothing leaves the machine without a yes to the exact text.
1. **Ask once** at the start: `contribute.py ask`, then record the answer with `contribute.py set yes|no|later`. A no is never asked again for that project; later is asked again at the next release.
2. **Keep learning locally either way.** Lessons go into each kit's `LESSONS.md` as usual, written generically (`references/improve.md`).
3. **At a release, if yes:** `contribute.py preview` gathers the new lessons and the project's pathway (the task recipe, the steps as they happened, where it left the recipe). It scrubs brand and client names (from SPEC, README, the brief and `.claude/private_terms.txt`), emails, links, phone numbers, paths, prices and handles, then writes `.claude/contribution_preview.md`.
4. **The user reads every line**, edits anything still too specific, and says yes again for that text.
5. `contribute.py send` refuses if any private term is still there. Otherwise it prints the `gh issue create` command for the skills repo (run from the user's own account, after confirming) or the link to paste it by hand.
What is shared: lessons (what failed, the evidence, the fix) and the order of steps. Never shared: files, images, copy, names, numbers or anyone's voice.
