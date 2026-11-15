"""Fetch CC0 line art from The Met whose MEDIUM gives a known answer for line quality:
  woodcut (Duerer)     blunt, even cut line
  etching (Rembrandt)  fine, scratchy needle line
  brush (Hokusai)      tapered, pressure-sensitive line
Used to test strokes.py against ground truth. Only an APPROVED ALLOWLIST (accession
or object ID reviewed by eye) is saved; candidates go to a contact sheet first.

    python -I fetch_line_masters.py out_dir            # saves candidates, for review
    python -I fetch_line_masters.py out_dir --approved # saves only APPROVED ids (use this)
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
# name used in the artist field -> (search query, medium word that must appear, how many candidates)
MASTERS = {"durer": ("Dürer woodcut", "woodcut", "rer", 14), "rembrandt": ("Rembrandt etching", "etching", "Rembrandt", 14),
           }
# Approved after looking at every candidate by eye. Left out: both Four Horsemen and Saint John
# in the cauldron (partial nudity in the Apocalypse plates), Samson (ambiguous), and one
# almost-black Entombment (unusable). An allowlist, so nothing unreviewed can be saved.
APPROVED = {
    "durer": {360117, 388793, 396910, 752394, 759726, 760025, 760028, 760029, 760032},
    "rembrandt": {343138, 343139, 354629, 354638, 359805, 359970, 364151, 364153, 364154, 369807, 370641, 371734, 373068},
}


def get(url, tries=4):
    for k in range(tries):
        time.sleep(0.35)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and k < tries - 1:
                time.sleep(15 * (k + 1)); continue
            raise


def main(out, approved_only=False):
    os.makedirs(out, exist_ok=True)
    manifest = []
    for key, (q, medium, artist_bit, per) in MASTERS.items():
        ids = json.loads(get(f"{API}.1/search?q={urllib.parse.quote(q)}&hasImages=true&departmentId=9&limit=80&offset=0"))["objectIDs"] or []
        kept = 0
        for oid in ids:
            if kept >= per:
                break
            if approved_only and oid not in APPROVED.get(key, set()):
                continue
            try:
                o = json.loads(get(f"{API}/objects/{oid}"))
            except Exception:
                continue
            if not (o.get("isPublicDomain") and o.get("primaryImageSmall") and artist_bit.lower() in (o.get("artistDisplayName") or "").lower()
                    and medium in (o.get("medium") or "").lower()):
                continue
            fn = f"{key}_{oid}.jpg"
            open(os.path.join(out, fn), "wb").write(get(o["primaryImageSmall"]))
            manifest.append({"file": fn, "master": key, "objectID": oid, "title": (o.get("title") or "")[:80], "date": o.get("objectDate", ""),
                             "medium": o.get("medium", ""), "page": o.get("objectURL", ""), "licence": "CC0 (The Met Open Access)"})
            kept += 1
        print(f"{key:10} {kept}", flush=True)
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], "--approved" in sys.argv)
