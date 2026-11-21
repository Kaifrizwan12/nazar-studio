# Review wall (beta, for the designer): live comments that reach Claude

A private studio page that shows every design as a numbered sheet, made for the designer reviewing work in progress (the client still gets the finished PDF). The designer comments on any sheet and presses **Send to Claude**. The note arrives in the working chat, Claude fixes the design and republishes, and the page updates for everyone who has it open.

## Fire it up (three steps)
1. **Build:**
   ```bash
   python nazar-core/engine/review_wall.py <images folder> <out folder> --title "<Brand> review" \
       --titles titles.json --accent "#F4B91E,#E43D55,#8CC43C"
   ```
   `titles.json` is `[["Title", "section"], ...]` in file order. It's optional: titles fall back to the file names.
2. **Publish:** call the Artifact tool once with the arguments in `<out>/publish.json`:
   - `file_path` and `root`;
   - the `files` map of `img/NN.jpg`;
   - `capabilities: {"comments": {"composer_only": true}}`;
   - `icon` and `description`.
   Before writing a page by hand, load the `artifact-capabilities` skill. The generator already follows it.
3. **Listen:** the publish result arms a live subscription. Once it's connected, every comment sent with *Send to Claude* starts a turn in this chat.
   - Answer it in the thread.
   - Make the fix in the engine, not in the image.
   - Rebuild, then republish the **same file path** so the URL stays the same.
   - Plain comments (not sent to Claude) don't notify; read them with the `ArtifactComments` tool, action `read`, when asked.

## Resolved state and rounds
State lives in `<out>/wall.json`, next to the page: the round number and, for each sheet (keyed by its source file name), the source hash, the resolved flag and the previous image. Rebuild into the same `<out>` every time.
- **Resolved** means every comment on that sheet in this round has had a reply *after* its republish. It is not client approval: the signed approval still comes from the proof or PDF.
  ```bash
  python nazar-core/engine/review_wall.py <images> <out> --title "<Brand> review" --resolve 03,07   # numbers or source file names
  python nazar-core/engine/review_wall.py <images> <out> --title "<Brand> review" --unresolve 07
  python nazar-core/engine/review_wall.py <images> <out> --title "<Brand> review" --new-round        # client round 2: all open again
  ```
- The page shows an **Open** or **Resolved** badge on each sheet, a "Round N · x of y resolved" count, and filters for All, Open, Resolved and Updated.
- **A sheet whose design changes goes back to Open.** This is the proofing rule: changed artwork goes back for sign-off. To fix and close a sheet in one go, pass `--resolve` in that same rebuild once the thread reply is ready.
- Keep the same `--title`, `--titles` and `--accent` on every rebuild. The flags change state only; they don't reset the rest.

## Before/after on republished sheets
- When a sheet's source image has changed since the last build, its last built image is kept as `img/prev/NN.jpg` and added to the `publish.json` files map automatically.
- That sheet gets an overlay slider: before on the left, after on the right, labelled, starting at 50 %. The "Before · R1" tag shows the round the before image came from. A **Show before / Show after** button flips the whole sheet at once, which is the quickest way to catch a small shift.
- The before image stays until the sheet changes again; then the image you just replaced becomes the new before. Renumbering (a sheet inserted earlier) carries the before image along with its sheet.
- Use the **Updated** filter to show only the sheets that changed, and reply in each thread with what moved.
- Self-check after editing the engine: `python nazar-core/engine/test_review_wall.py` (Windows: set `PYTHONUTF8=1` first).
- Research behind these choices: `references/research_review.md`.

## Rules that held up
- **One sheet per design, in story order,** with the same numbers as the deck, so "07" means the same thing in chat, deck and page.
- **Composer-only comments:** no consent prompt. The shell renders the threads; the page never builds its own list.
- **A Comment button per sheet,** plus `data-comment-target` on the sheet, so a click anywhere on the design anchors to it.
- **Ask for one note per change.** A thread with five asks gets four forgotten.
- **Each fix:** rebuild, run QA, republish, then reply in the thread with what changed. Never mark a note done before the republish.
- **The page is private.** Only the owner, and whoever they share it with from the Share menu, can open it. Say so when handing over the link.
- **Size:** keep images at most 1600 px, JPEG q82, about 150 KB each. One publish carries up to 64 MB, so publish more in batches to the same URL.
