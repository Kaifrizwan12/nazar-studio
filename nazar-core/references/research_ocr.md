# Research: reading slide text without macOS (2026-11-21)

Backs `engine/read_text.py`. Tags: [SRC] read for this note, [KNOWN] background.

## Findings
- **Tesseract's own advice** (tessdoc, "Improving the quality of the output"). [SRC] https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html
  - It works best at about 300 dpi or more, so small images should be scaled up.
  - Tesseract 4 and later expect **dark text on a light ground**; invert light-on-dark images first (3.05 and older coped either way).
  - Text cropped with no margin causes errors, so add a small border (about 10 px). A huge border around one word can return an empty page.
  - It binarises with Otsu inside; 5.0 added adaptive Otsu and Sauvola for uneven grounds.
  - Page segmentation: 3 = automatic page (the default), 6 = one uniform block, 11 = **sparse text, as much as possible in no particular order**, 7/8/10 = one line / word / character.
  - Retraining rarely helps unless the font or language is unusual.
- **PSM in practice.** Forcing a mode that doesn't match the layout can scramble the reading order. Sparse mode suits text scattered around a page. [SRC] https://pyimagesearch.com/2021/11/15/tesseract-page-segmentation-modes-psms-explained-how-to-improve-your-ocr-accuracy/ ; tesseract-ocr mailing list threads on --psm
- **Windows.** The project ships no Windows binary itself; the UB Mannheim build is the usual installer. It installs to `C:\Program Files\Tesseract-OCR\tesseract.exe` and has not always added itself to PATH, so tools should look there and let the user set the path. pytesseract needs the tesseract program too (its `tesseract_cmd`). [SRC] https://github.com/UB-Mannheim/tesseract/wiki ; pytesseract usage notes

## What we took from it
1. Order: macOS Vision, then the tesseract program (`TESSERACT_CMD`, the PATH, then the Windows default folders), then pytesseract; with none of them, stop with a message that says what to install.
2. Prepare every slide: greyscale, invert a dark ground, scale the long side to 1600 px or more, add a 10 px white border.
3. Use `--psm 11` (sparse text) for slides, since headlines, labels and handles sit apart. On our rendered test slide, modes 3, 6 and 11 all read both lines; 11 is the mode that suits scattered slide text.
4. Ask tesseract for TSV, so every line comes back with a confidence and a box, the same as the macOS reader.
5. OCR stays a first draft of `copy.json`: stylised display type, Roman Urdu and small text still need checking by eye.

## Measured here
- Tesseract 5.4.0 on Windows 11 (`engine/test_read_text.py`): both lines of a rendered 1080 x 1350 slide read correctly, dark-on-light and light-on-dark, with boxes in the right place. The clean dark slide also read without inversion (5.x copes better than the 4.x note suggests); inversion stays because it costs nothing and helps on busy dark grounds, per the docs.
