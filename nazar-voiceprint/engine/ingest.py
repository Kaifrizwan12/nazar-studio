#!/usr/bin/env python3
"""
nazar-voiceprint/engine/ingest.py: drop a whole archive, get a clean corpus.

Walks a folder (any mess: old .docx from an office job, scripts, notes, a
portfolio) and sorts it into what each layer of the skill can read:
  - words:   .docx .txt .md .rtf .fountain .fdx (Final Draft) .pdf (if pypdf
             is installed) -> plain-text files in <out>/text/
  - visuals: .png .jpg .jpeg .webp .tif -> listed for visual.py
  - everything else: listed as skipped, never silently dropped

The pre-AI check: for each document it reads the best date it can find
(.docx core.xml created/modified, PDF metadata, else file mtime) and flags
anything dated on or after 30 Nov 2022 (ChatGPT's public release) as
"possibly AI-touched". Those are kept out of the voice corpus by default,
because the whole point is the person's pattern, not a model's. Dates can be
wrong (copied files, re-saves), so the manifest shows them and the person
decides.

Needs only the standard library (pypdf optional).

    python ingest.py path/to/archive --out corpus/ [--include-post-ai]
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import zipfile
from xml.etree import ElementTree as ET

AI_ERA = dt.datetime(2022, 11, 30)
TEXT_EXT = {".docx", ".txt", ".md", ".rtf", ".fountain", ".fdx", ".pdf"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_text_and_date(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
        paras = []
        for p in root.iter(W + "p"):
            t = "".join(n.text or "" for n in p.iter(W + "t"))
            if t.strip():
                paras.append(t)
        date = None
        if "docProps/core.xml" in z.namelist():
            core = z.read("docProps/core.xml").decode("utf-8", "ignore")
            m = re.search(r"<dcterms:created[^>]*>([^<]+)<", core) or re.search(r"<dcterms:modified[^>]*>([^<]+)<", core)
            if m:
                try:
                    date = dt.datetime.fromisoformat(m.group(1).replace("Z", "")[:19])
                except ValueError:
                    pass
    return "\n\n".join(paras), date, "docx core.xml" if date else None


def fdx_text(path):
    root = ET.parse(path).getroot()
    out = []
    for p in root.iter("Paragraph"):
        kind = p.get("Type", "")
        t = "".join(x.text or "" for x in p.iter("Text")).strip()
        if not t:
            continue
        out.append(t.upper() if kind in ("Scene Heading", "Character") else t)
    return "\n".join(out)


def rtf_text(raw):
    raw = re.sub(r"\\par[d]?", "\n", raw)
    raw = re.sub(r"\{\\\*[^{}]*\}|\\[a-zA-Z]+-?\d* ?|[{}]", "", raw)
    return raw


def pdf_text_and_date(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return None, None, None
    r = PdfReader(path)
    text = "\n".join((pg.extract_text() or "") for pg in r.pages)
    date = None
    meta = r.metadata or {}
    d = meta.get("/CreationDate") or meta.get("/ModDate")
    m = re.match(r"D:(\d{4})(\d{2})(\d{2})", str(d or ""))
    if m:
        date = dt.datetime(int(m[1]), int(m[2]), int(m[3]))
    return text, date, "pdf metadata" if date else None


def extract(path):
    ext = os.path.splitext(path)[1].lower()
    date, src = None, None
    if ext == ".docx":
        text, date, src = docx_text_and_date(path)
    elif ext == ".fdx":
        text = fdx_text(path)
    elif ext == ".pdf":
        text, date, src = pdf_text_and_date(path)
        if text is None:
            return None, None, "pdf (install pypdf to read)"
    else:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if ext == ".rtf":
            text = rtf_text(text)
    if date is None:
        date, src = dt.datetime.fromtimestamp(os.path.getmtime(path)), "file mtime (weak)"
    return text, date, src


def ingest(folder, out, include_post_ai=False):
    os.makedirs(os.path.join(out, "text"), exist_ok=True)
    manifest = {"words": [], "visuals": [], "held_back_post_ai": [], "skipped": []}
    for dirpath, _, files in os.walk(folder):
        for f in sorted(files):
            if f.startswith(".") or f.startswith("~$"):
                continue
            p = os.path.join(dirpath, f)
            ext = os.path.splitext(f)[1].lower()
            rel = os.path.relpath(p, folder)
            if ext in IMG_EXT:
                manifest["visuals"].append(rel)
                continue
            if ext not in TEXT_EXT:
                manifest["skipped"].append(rel)
                continue
            try:
                text, date, src = extract(p)
            except Exception as e:  # a corrupt file shouldn't kill a 400-file archive
                manifest["skipped"].append(f"{rel} (unreadable: {e.__class__.__name__})")
                continue
            if text is None:
                manifest["skipped"].append(f"{rel} ({src})")
                continue
            words = len(re.findall(r"\w+", text))
            entry = {"file": rel, "words": words, "date": date.date().isoformat() if date else None, "date_source": src}
            if date and date >= AI_ERA and not include_post_ai:
                manifest["held_back_post_ai"].append(entry)
                continue
            safe = re.sub(r"[^\w.-]+", "_", rel)[:120] + ".txt"
            with open(os.path.join(out, "text", safe), "w", encoding="utf-8") as fh:
                fh.write(text)
            entry["corpus_file"] = f"text/{safe}"
            manifest["words"].append(entry)
    manifest["totals"] = {
        "documents_in_corpus": len(manifest["words"]),
        "words_in_corpus": sum(e["words"] for e in manifest["words"]),
        "held_back_post_ai": len(manifest["held_back_post_ai"]),
        "images_for_visual_layer": len(manifest["visuals"]),
    }
    with open(os.path.join(out, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--out", default="voiceprint_corpus")
    ap.add_argument("--include-post-ai", action="store_true", help="keep files dated after 30 Nov 2022 in the corpus")
    a = ap.parse_args()
    m = ingest(a.folder, a.out, a.include_post_ai)
    t = m["totals"]
    print(f"corpus: {t['documents_in_corpus']} documents, {t['words_in_corpus']:,} words -> {a.out}/text/")
    print(f"held back as possibly AI-touched (dated on/after 30 Nov 2022): {t['held_back_post_ai']}")
    print(f"images for the visual layer: {t['images_for_visual_layer']}")
    if m["skipped"]:
        print(f"skipped: {len(m['skipped'])} (see manifest.json)")
    words = t["words_in_corpus"]
    if words < 5000:
        print("note: under ~5,000 words the frequency-based features get noisy; more samples will sharpen the pattern.")
