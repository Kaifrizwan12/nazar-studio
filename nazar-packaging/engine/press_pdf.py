"""Press-style PDFs, a colour spec and a readiness report from layered SVG pack masters (generic, brand-free).

    python engine/press_pdf.py --in "<folder>/**/*-art.svg" --out <folder>/print --prefix BRAND

Input: SVG masters in mm (1 viewBox unit = 1 mm), top-level <g id="..."> layers. Ink plates and technical layers
are matched by id (edit PLATES / TECH / SKIP below to your naming). Each <name>_PRINT.pdf holds:
  page 1  composite (ink plates only, never notes or dielines)
  then    one page per ink plate, drawn in black (a separation preview)
  last    the technical layers (cut, crease, glue, dieline) in magenta, labelled "never prints"
Boxes: BleedBox = the art incl. bleed, TrimBox = art minus bleed, MediaBox = art + a slug strip with the label.
If a flat panel has no bleed (viewBox starts at 0), its background rect is extended 3 mm at export and the
report says so (photos that touch a trim edge must be extended by hand).
Also writes COLOUR_SPEC.md (hex, RGB, a CMYK *screen estimate*, an empty Pantone column) and press_readiness.md.
These are concept press files: the converter's CAD dieline and the printer's profile govern the final separations.
Guide: references/press_files.md. Needs: cairosvg, pypdf.
"""
import os, re, io, glob, copy, argparse
import xml.etree.ElementTree as ET
import cairosvg
from pypdf import PdfWriter, PdfReader
from pypdf.generic import RectangleObject

NS = "http://www.w3.org/2000/svg"; ET.register_namespace("", NS); ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
PLATES = ["TINT", "WHITE_INK", "DARK_INK", "MATTE_VARNISH", "ART"]
TECH = ["DIELINE", "CUT", "CREASE", "GLUE", "GLUE_NO_INK", "BLEED", "PERF"]
SKIP = ["LABELS", "NOTES", "PLACEHOLDER"]            # notes for humans, never print
SLUG, MM, TECH_COL = 14.0, 72 / 25.4, "#E6007E"


def parts(path):
    t = ET.parse(path); r = t.getroot()
    return r, [float(v) for v in r.get("viewBox").split()], {c.get("id"): c for c in list(r) if c.get("id")}


def recolor(el, col):
    for e in el.iter():
        for a in ("fill", "stroke"):
            if e.get(a) and e.get(a) != "none": e.set(a, col)
        if e.get("style"): e.set("style", re.sub(r"(fill|stroke):\s*(?!none)[^;]+", lambda m: f"{m.group(1)}:{col}", e.get("style")))
    return el


def page_svg(r, vb, keep, col, label):
    x, y, w, h = vb
    root = ET.Element(f"{{{NS}}}svg", {"width": f"{w}mm", "height": f"{h + SLUG}mm", "viewBox": f"{x} {y} {w} {h + SLUG}"})
    ET.SubElement(root, f"{{{NS}}}rect", {"x": str(x), "y": str(y), "width": str(w), "height": str(h + SLUG), "fill": "#FFFFFF"})
    for c in list(r):
        if c.get("id") in keep: root.append(recolor(copy.deepcopy(c), col) if col else copy.deepcopy(c))
    ET.SubElement(root, f"{{{NS}}}text", {"x": str(x + 4), "y": str(y + h + SLUG * 0.62), "font-family": "Arial", "font-size": "3.2"}).text = label
    return ET.tostring(root, encoding="unicode")


def build(path, dst, prefix, ver):
    r, vb, g = parts(path); x, y, w, h = vb
    src = open(path, encoding="utf-8").read(); issues = []
    wm = re.search(r'<svg[^>]*\swidth="([\d.]+)mm"', src)
    if wm and abs(float(wm.group(1)) - w) > 0.5: issues.append(f"SVG width {wm.group(1)} mm != viewBox span {w:g} mm (file scales on export)")
    bleed = max(0.0, -x)
    if bleed <= 0 and not any(k in g for k in TECH) and "TINT" in g:
        bg = next((e for e in g["TINT"].iter() if e.tag.endswith("rect") and e.get("fill")), None)
        if bg is not None:
            g["TINT"].insert(0, ET.Element(f"{{{NS}}}rect", {"x": str(x - 3), "y": str(y - 3), "width": str(w + 6), "height": str(h + 6), "fill": bg.get("fill")}))
            vb = [x - 3, y - 3, w + 6, h + 6]; x, y, w, h = vb; bleed = 3.0
            if "<image" in src: issues.append("bleed added as flat tint: extend any photo touching a trim edge by 3 mm")
    if bleed <= 0: issues.append("no bleed beyond trim (add 3 mm)")
    name = os.path.basename(path).rsplit(".", 1)[0]
    trim = f"{w - 2 * bleed:.1f} x {h - 2 * bleed:.1f} mm"
    tag = f"{prefix} {name} {ver}"
    pages = [("COMPOSITE", page_svg(r, vb, [k for k in g if k in PLATES], None, f"{tag} | COMPOSITE | trim {trim} | bleed {bleed:g} mm | concept"))]
    pages += [(p, page_svg(r, vb, [p], "#000000", f"{tag} | PLATE {p} (separation preview) | trim {trim}")) for p in PLATES if p in g]
    tech = [k for k in g if k in TECH]
    if tech: pages.append(("TECH", page_svg(r, vb, tech, TECH_COL, f"{tag} | TECHNICAL: {', '.join(tech)} (never prints)")))
    wr = PdfWriter()
    for _, s in pages:
        pg = PdfReader(io.BytesIO(cairosvg.svg2pdf(bytestring=s.encode("utf-8"), unsafe=True))).pages[0]
        top = float(pg.mediabox.height); ah = h * MM
        pg.bleedbox = RectangleObject([0, top - ah, w * MM, top])
        pg.trimbox = RectangleObject([bleed * MM, top - ah + bleed * MM, (w - bleed) * MM, top - bleed * MM])
        wr.add_page(pg)
    out = os.path.join(dst, f"{prefix}_{name}_{ver}_PRINT.pdf")
    with open(out, "wb") as f: wr.write(f)
    miss = [p for p in ("TINT", "WHITE_INK", "DARK_INK") if p not in g]
    if miss: issues.append("missing plates: " + ", ".join(miss))
    if not tech: issues.append("no cut/crease layer (structure comes from the converter dieline)")
    if "<image" in src: issues.append("raster image: check >= 300 ppi at size, convert to printer CMYK")
    if re.search(r"barcode", src, re.I): issues.append("check barcode is a real GS1 number, not a placeholder")
    return out, [p for p, _ in pages], trim, bleed, issues, g


def cmyk_est(hx):
    r, gg, b = (int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5)); k = 1 - max(r, gg, b)
    if k >= 1: return (0, 0, 0, 100)
    return tuple(round(v * 100) for v in [(1 - v - k) / (1 - k) for v in (r, gg, b)] + [k])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--in", dest="src", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", default="PACK"); ap.add_argument("--ver", default="v01"); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = [build(p, a.out, a.prefix, a.ver) for p in sorted(glob.glob(a.src, recursive=True))]
    cols = {}
    for out, *_, g in rows:
        for e in (g.get("TINT").iter() if g.get("TINT") is not None else []):
            v = (e.get("fill") or "").upper()
            if re.fullmatch(r"#[0-9A-F]{6}", v): cols.setdefault(v, set()).add(os.path.basename(out))
    with open(os.path.join(a.out, "COLOUR_SPEC.md"), "w", encoding="utf-8") as f:
        f.write(f"# {a.prefix} colour spec {a.ver} (concept)\n\nCMYK values are **screen estimates only**; final CMYK comes from the printer's profile. "
                "Spot inks are picked on a **physical** guide under D50 light against the approved swatch.\n\n| HEX | RGB | CMYK estimate | Spot (pick on guide) | Files |\n|---|---|---|---|---|\n")
        for hx in sorted(cols):
            c = cmyk_est(hx); f.write(f"| {hx} | {int(hx[1:3],16)} {int(hx[3:5],16)} {int(hx[5:7],16)} | C{c[0]} M{c[1]} Y{c[2]} K{c[3]} |  | {len(cols[hx])} |\n")
        f.write("\n**Ask the printer:** process (gravure / flexo / digital), film and laminate, profile and total ink limit, stations and white, "
                "minimum type and line, trap, bleed and dieline conventions, PDF/X version and preflight profile, proof on the real substrate.\n")
    with open(os.path.join(a.out, "press_readiness.md"), "w", encoding="utf-8") as f:
        f.write("# Press readiness\n\n## Blocked on others (every file)\n- printer profile + CMYK/spot conversion (files are RGB)\n- converter CAD dieline\n"
                "- barcodes, lab values, licence lines\n- physical proof + press check\n\n## Per file\n| File | Pages | Trim | Bleed | Our fixes |\n|---|---|---|---|---|\n")
        for out, pages, trim, bleed, issues, _ in rows: f.write(f"| {os.path.basename(out)} | {' / '.join(pages)} | {trim} | {bleed:g} mm | {'; '.join(issues) or 'ok'} |\n")
    print(f"{len(rows)} PRINT pdfs -> {a.out} | {sum(1 for r_ in rows if r_[4])} with our own fixes listed in press_readiness.md")
