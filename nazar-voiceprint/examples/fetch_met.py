"""Fetch CC0 photographs from The Met (Open Access, public domain) for a blind
grading test. Keeps an object only if isPublicDomain is true AND its own
`medium` field names the process, so the label is the answer key.

    python -I fetch_met.py out_dir
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
PROCESSES = {  # search query -> (word that must appear in the medium, how many)
    "cyanotype": ("cyanotype", 10),
    "albumen silver print": ("albumen", 6),
    "salted paper print": ("salted paper", 6),
    "autochrome": ("autochrome", 3),
}
# a public design repo: no nudes, no portraits of identifiable people, no album covers
SKIP_TAGS = {"nudes", "portraits", "men", "women", "boys", "girls", "children", "babies", "self-portraits"}
SKIP_WORDS = ("nude", "portrait", "album", "cover", "self-portrait")
# excluded after looking at every image: nude studies whose titles don't say so,
# and a book cover rather than a photograph
EXCLUDE_IDS = {271890, 271868, 291498}


def get(url, tries=4):
    """Polite: pace every call and back off on 403/429 (the Met rate-limits bursts)."""
    for k in range(tries):
        time.sleep(0.35)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and k < tries - 1:
                time.sleep(15 * (k + 1))
                continue
            raise


def main(out):
    os.makedirs(out, exist_ok=True)
    manifest = []
    for q, (must, PER) in PROCESSES.items():
        ids = json.loads(get(f"{API}.1/search?q={urllib.parse.quote(q)}&hasImages=true&departmentId=19&limit=150&offset=0"))["objectIDs"] or []
        kept = 0
        for oid in ids:
            if kept >= PER:
                break
            try:
                o = json.loads(get(f"{API}/objects/{oid}"))
            except Exception:
                continue
            med = (o.get("medium") or "").lower()
            img = o.get("primaryImageSmall")
            if not (o.get("isPublicDomain") and img and must in med):
                continue
            tags = {t.get("term", "").lower() for t in (o.get("tags") or [])}
            text = " ".join([o.get("title", ""), o.get("objectName", "")]).lower()
            if oid in EXCLUDE_IDS or tags & SKIP_TAGS or any(w_ in text for w_ in SKIP_WORDS):
                continue
            name = f"{must.replace(' ', '_')}_{oid}.jpg"
            try:
                data = get(img)
            except Exception:
                continue
            open(os.path.join(out, name), "wb").write(data)
            manifest.append({"file": name, "process": must, "objectID": oid, "title": o.get("title", "")[:80],
                             "artist": (o.get("artistDisplayName") or "Unknown")[:60], "date": o.get("objectDate", ""),
                             "medium": o.get("medium", ""), "page": o.get("objectURL", ""), "licence": "CC0 (The Met Open Access)"})
            kept += 1
        print(f"{must:15} kept {kept}")
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    print("total", len(manifest))


if __name__ == "__main__":
    main(sys.argv[1])
