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

## Rules that held up
- **One sheet per design, in story order,** with the same numbers as the deck, so "07" means the same thing in chat, deck and page.
- **Composer-only comments:** no consent prompt. The shell renders the threads; the page never builds its own list.
- **A Comment button per sheet,** plus `data-comment-target` on the sheet, so a click anywhere on the design anchors to it.
- **Ask for one note per change.** A thread with five asks gets four forgotten.
- **Each fix:** rebuild, run QA, republish, then reply in the thread with what changed. Never mark a note done before the republish.
- **The page is private.** Only the owner, and whoever they share it with from the Share menu, can open it. Say so when handing over the link.
- **Size:** keep images at most 1600 px, JPEG q82, about 150 KB each. One publish carries up to 64 MB, so publish more in batches to the same URL.
