#!/bin/zsh
# Download OpenStreetMap street geometry for one place into osm/<name>.json
# usage: ./fetch_map.sh <name> <lat> <lon> [half-height-deg=0.014] [half-width-deg=0.022]
# Credit "© OpenStreetMap contributors" once, on the sources page.
cd "$(dirname "$0")"; mkdir -p osm
NAME=$1 LAT=$2 LON=$3 DH=${4:-0.014} DW=${5:-0.022}
S=$(python3 -c "print(round($LAT-$DH,4))") N=$(python3 -c "print(round($LAT+$DH,4))")
W=$(python3 -c "print(round($LON-$DW,4))") E=$(python3 -c "print(round($LON+$DW,4))")
Q="[out:json][timeout:120];(way[\"highway\"]($S,$W,$N,$E););out geom;"
for i in 1 2 3 4; do
  curl -s -m 180 -A "nazar-brand-book/1.0" --data-urlencode "data=$Q" https://overpass-api.de/api/interpreter -o osm/$NAME.json
  head -c 1 osm/$NAME.json | grep -q '{' && { echo "$NAME ok $(wc -c < osm/$NAME.json) bytes"; exit 0; }
  sleep 15
done; echo "$NAME FAILED (Overpass busy, try again later)"; exit 1
