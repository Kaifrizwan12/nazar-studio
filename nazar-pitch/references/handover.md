# Handover and close

## Handover pack
- Final files in the agreed structure (each kit's deliverables section), with a **README** saying what to use where
- Source files (if included in scope)
- Brand guidelines (PDF) and any quick guides
- A licence list: fonts, images, music, with who holds each licence
- The trademark first-pass record, with the recommendation for legal clearance
- Contacts for future work, and a support window if agreed (e.g. 30 days for small fixes)

## Close the project
- Final invoice, sent once the files are ready (and files released on payment, per the agreement)
- A short close call: what worked, what to improve, what's next (packaging, social, web, a retainer)
- Ask for a testimonial and permission to publish
- Archive the project: final files, `SPEC.md`, research, correspondence

## Case study / Behance write-up
Short paragraphs, in this order: the client and the problem → the insight from research → the idea (one sentence) → the mark and system → the applications → the outcome (real results if available) → credits (team, photographers, typefaces, archives used).
Images: the strongest single image first, then the system, then applications in use (real photos where possible), then details. Label concept or fictional work honestly. Respect confidentiality and the launch timing.

## Client deck and Behance: what works (owner-tested)
- **Visual-first, one short title per page.** Kicker + a title under ~30 characters; the pack fills the page. Paragraphs belong in the call, not on the slide.
- **A width guard on every text line:** measure each line against its box, shrink to a floor, two lines for narrow columns, and **fail the build** if anything still overflows. Look at a contact sheet of every page before sending.
- **Never crop the product at a page edge** by accident (slice crops cut pack tops). Fit packs whole; crop only on purpose (a macro cover).
- **Cover: one pack, very close** (frost, product, the name filling the frame) reads modern. A flood colour plus a row of packs reads like a catalogue.
- **Close on the best range photo under a tinted gradient with a thank-you** in the brand's voice.
- **Behance = the same pages in case-study order,** no folios, no client to-do page. Keep the PDF light (render pages to JPEG; vector-embedded photos blew one deck past 100 MB).
- **Client folder:** a root folder with only the PDF, pack images, film and one range photo, friendly file names, no tech files.
- **End the client deck with "How far are we":** Done / Next / Need from you, short bullets.


## Review wall (comments that reach Claude)
- Publish every deck page as a numbered 16:9 sheet on one private claude.ai Artifact. Declare `comments` with `composer_only: true`, so the page asks for no consent.
- Put a **Comment** button under each sheet that calls `openComposer({element: sheet})`. Mark each sheet `data-comment-target`, so a click anywhere on it anchors to it.
- The reviewer writes the note and presses *Send to Claude*. The note lands in the session that published the page. Ask for one note per change.
- The page is private until the owner shares it from the Share menu; say so when you hand over the link.
