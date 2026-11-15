"""Fetch CC0 prints by named designers from the Cleveland Museum of Art Open
Access API, for the 'how a person designs' test. Prints only (no sculpture,
bound volumes or drawings). Files are named <designer>_<accession>.jpg, which is
what designer_test.py expects.

Review every image by eye before use (a contact sheet makes that quick) and
add only approved accessions to KEEP.

    python -I fetch_cma_designers.py out_dir
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://openaccess-api.clevelandart.org/api/artworks/"
UA = {"User-Agent": "voiceprint-research/0.1 (style-analysis test)"}
DESIGNERS = {"steinlen": ("Steinlen", 14), "lautrec": ("Toulouse", 14), "cheret": ("Chéret", 12), "mucha": ("Mucha", 7)}
# An ALLOWLIST, not an exclusion list: only the accession numbers below were looked at
# and approved (an exclusion list let the quota refill with unreviewed images).
# Left out after review: the Elles series' bedroom and bathing scenes (partial nudity),
# a faint ghostly dancer sketch (ambiguous), and near-duplicates of a kept print
# (a second impression, crops of one poster, a repeat colourway), which would leak
# between train and test.
KEEP = {
    "steinlen": {"2016.247", "2012.271", "1926.287", "1921.380", "1921.378", "1946.196", "1923.138", "1969.283",
                 "1924.985", "2016.245", "1921.379", "1924.227", "2014.282"},
    "lautrec": {"1952.10", "1967.234", "1925.1202", "1925.1204", "1925.1204.2", "2023.145", "1950.586"},
    "cheret": {"1976.1072", "1978.1054", "1972.1126", "1987.1064", "2009.555", "1987.1063", "1987.1065", "1981.1025", "2009.544"},
    "mucha": {"1969.236", "1973.1018", "1969.238", "1969.239", "1992.35", "1977.1018"},
}


def get(url, tries=4):
    for k in range(tries):
        time.sleep(0.3)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and k < tries - 1:
                time.sleep(10 * (k + 1)); continue
            raise


def main(out):
    os.makedirs(out, exist_ok=True)
    manifest = []
    for key, (query, per) in DESIGNERS.items():
        q = urllib.parse.urlencode({"artists": query, "cc0": 1, "has_image": 1, "type": "Print", "limit": 100,
                                    "fields": "id,accession_number,title,creators,creation_date,technique,url,images"})
        rows = json.loads(get(f"{API}?{q}"))["data"]
        kept = 0
        for r in rows:
            if kept >= per:
                break
            acc = r["accession_number"]
            web = ((r.get("images") or {}).get("web") or {}).get("url")
            names = " ".join(c.get("description", "") for c in (r.get("creators") or []))
            if not web or acc not in KEEP[key] or query.split()[0].lower().replace("é", "e") not in names.lower().replace("é", "e"):
                continue
            fn = f"{key}_{acc.replace('.', '-')}.jpg"
            open(os.path.join(out, fn), "wb").write(get(web))
            manifest.append({"file": fn, "designer": key, "accession": acc, "title": (r.get("title") or "")[:80],
                             "date": r.get("creation_date", ""), "technique": (r.get("technique") or "")[:60],
                             "page": r.get("url", ""), "licence": "CC0 (Cleveland Museum of Art Open Access)"})
            kept += 1
        print(f"{key:9} fetched {kept}", flush=True)
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1, ensure_ascii=False)
    print("total", len(manifest), flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
