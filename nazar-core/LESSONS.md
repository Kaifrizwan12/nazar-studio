# Lessons from real work (nazar-core)
Format: date, what happened, evidence, change made. Generic on purpose: no client names or private data.

- 2026-11-21 · Reading slide text needed macOS · On Windows the tesseract installer often isn't on PATH. · `engine/read_text.py` now finds tesseract (TESSERACT_CMD, PATH, C:\Program Files\Tesseract-OCR), then pytesseract, prepares the slide per tessdoc (invert dark, upscale, border, psm 11, TSV boxes) and says what to install if neither; `references/research_ocr.md`, `engine/test_read_text.py`.
- 2026-11-21 · Brand files arrived late or wrong · Square backdrops got resampled to 4:5 and dark logos got boxed on dark slides. · `tags.py` asks up front for native 4:5 light and dark backdrops and a light-on-dark logo, checks ratio and transparency, and lists what is still missing in the profile; the social and backdrops intakes and the pattern template ask the same; `engine/test_profile_files.py`.
