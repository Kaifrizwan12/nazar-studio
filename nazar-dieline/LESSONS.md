# Lessons (nazar-dieline)

## 2026-11-20 · Windows run
- **What failed:** `dieline.py` crashed on Windows twice. (1) `print("✓ ...")` raised UnicodeEncodeError on the cp1252 console. (2) `art.py` `write_qa` calls `open(path, "w")` with no encoding, and the "≥" in the QA text crashed it. Spec files also came out garbled (× and ² as `?`).
- **Workaround used:** run with `PYTHONUTF8=1`.
- **Patched 2026-11-20 (owner okayed):** add `encoding="utf-8"` to every `open(..., "w")` in `dieline.py` and `art.py`, and `sys.stdout.reconfigure(encoding="utf-8")` at startup.
- **Also:** CairoSVG needs `libcairo-2.dll` on Windows. `requirements.txt` doesn't say so, and selftest doesn't test the dieline engine. Any GTK runtime works, and so does the Tesseract-OCR install folder (it ships libcairo-2.dll) on PATH. Proposed: add a dieline render to `selftest.py` and a Windows note to the README.
- **QA gap:** a placeholder zone overlapping a pouch's rounded corner seal was not flagged (seen only by eye). Proposed: include the corner-seal arcs in `check_box` zones.

## 2026-11-20: flat-bottom pouch and display header added
- **Added `box_pouch`** (flat-bottom box pouch print layout: front | gusset | back | gusset + separate bottom, edge seals, zip, base fold-unders). It was needed for a kitchen range; it's drawn as one strip for planning, and the converter's template sets the real web split.
- **`tray` now draws `header`** (mm): the note had mentioned the option but it wasn't implemented.
- **QA gap confirmed again:** pouch rounded corner seals are not checked. On a small doypack (110 wide) a batch box at the back's bottom-right sat on the arc with no flag. Proposed: add the corner arcs to the zone check in `art.py`.
