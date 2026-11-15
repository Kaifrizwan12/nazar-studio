"""Fetch public-domain (CC0) posters by named designers from The Met, for a
'how a person designs' test. Keeps an object only if it's public domain, the
artist field names the designer, it's a poster, and nothing in its tags or
title suggests nudity. Every image is still reviewed by eye before use.

    python -I fetch_met_designers.py out_dir [--count]
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://collectionapi.metmuseum.org/public/collection/v1"
UA = {"User-Agent": "voiceprint-research/0.1 (style-analysis test)"}
DESIGNERS = {"Edward Penfield": 8, "Will Bradley": 8, "Jules Chéret": 8, "Théophile-Alexandre Steinlen": 8}
SKIP_TAGS = {"nudes", "female nudes", "male nudes", "erotica"}
SKIP_WORDS = ("nude", "nu ", "bather")
EXCLUDE_IDS = set()   # filled after review if anything slips through


def get(url, tries=4):
    for k in range(tries):
        time.sleep(0.35)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and k < tries - 1:
                time.sleep(15 * (k + 1)); continue
            raise


def main(out, count_only=False):
    os.makedirs(out, exist_ok=True)
    manifest = []
    for name, per in DESIGNERS.items():
        ids = json.loads(get(f"{API}.1/search?q={urllib.parse.quote(name + ' poster')}&hasImages=true&departmentId=9&limit=120&offset=0"))["objectIDs"] or []
        kept, seen = 0, 0
        for oid in ids:
            if kept >= per:
                break
            try:
                o = json.loads(get(f"{API}/objects/{oid}"))
            except Exception:
                continue
            seen += 1
            artist = (o.get("artistDisplayName") or "")
            last = name.split()[-1].lower()
            tags = {t.get("term", "").lower() for t in (o.get("tags") or [])}
            text = f"{o.get('title', '')} {o.get('objectName', '')}".lower()
            if not (o.get("isPublicDomain") and o.get("primaryImageSmall") and last in artist.lower() and "poster" in text):
                continue
            if oid in EXCLUDE_IDS or tags & SKIP_TAGS or any(w in text for w in SKIP_WORDS):
                continue
            kept += 1
            if count_only:
                continue
            fn = f"{last.replace('é', 'e')}_{oid}.jpg"
            open(os.path.join(out, fn), "wb").write(get(o["primaryImageSmall"]))
            manifest.append({"file": fn, "designer": name, "objectID": oid, "title": o.get("title", "")[:80],
                             "date": o.get("objectDate", ""), "page": o.get("objectURL", ""), "licence": "CC0 (The Met Open Access)"})
        print(f"{name:32} search hits {len(ids):4}  kept {kept}")
    if not count_only:
        json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], "--count" in sys.argv)
