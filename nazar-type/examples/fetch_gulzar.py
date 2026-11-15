"""Fetch the real Gulzar font (Google Fonts, SIL OFL 1.1) and its licence file, for the
type-QA demo. The font isn't committed to the repo: fetch it, keep the OFL text with it.

    python -I fetch_gulzar.py out_dir
"""
import os
import sys
import urllib.request

BASE = "https://github.com/googlefonts/gulzar/raw/main/"
FILES = {"Gulzar.ttf": "fonts/ttf/Gulzar-Regular.ttf", "OFL_gulzar.txt": "OFL.txt"}

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
for name, path in FILES.items():
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "nazar-type-demo/0.1"})
    data = urllib.request.urlopen(req, timeout=60).read()
    open(os.path.join(out, name), "wb").write(data)
    print(f"{name}: {len(data):,} bytes")
