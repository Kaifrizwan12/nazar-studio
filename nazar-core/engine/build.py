"""Render the brand book: one PNG per page, a contact sheet, a bound PDF.

usage: build.py [page-id-prefix ...]   (no args = whole book; run twice so contents pick up page numbers)
"""
import io, os, sys, base64, json
import cairosvg
from PIL import Image
from lib import W, H, M, BRAND, HERE, ACCENT, circle, _path

OUT = _path(BRAND["exports"])
SVGDIR = os.path.join(HERE, "out")

def all_pages():
    pages = []
    for mod in BRAND["page_modules"]:
        pages += __import__(mod).PAGES
    return pages

def main(filters):
    os.makedirs(f"{OUT}/pages", exist_ok=True); os.makedirs(SVGDIR, exist_ok=True)
    fns = all_pages()
    if not filters:                                   # full build: clear stale pages from older numbering
        for d in (f"{OUT}/pages", SVGDIR):
            for f_ in os.listdir(d):
                if f_[:2].isdigit(): os.remove(os.path.join(d, f_))
    built, numbers, devices = [], {}, {}
    for n, fn in enumerate(fns, 1):
        p = fn()
        numbers[p.pid] = n
        if filters and not any(p.pid.startswith(f) for f in filters): continue
        name = f"{n:02d}_{p.pid}"
        svg = p.svg(n)
        open(f"{SVGDIR}/{name}.svg", "w").write(svg)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{OUT}/pages/{name}.png", output_width=W)
        devices[name] = p.dev_pos
        built.append(name); print("✓", name, flush=True)
    json.dump(numbers, open(f"{SVGDIR}/pages.json", "w"))
    if not filters:
        if BRAND.get("reveal_pid"): reveal(fns, built, devices)
        bind(built)
    sheet(built)

def reveal(fns, built, devices):
    """Second pass: the reveal page shows every page as a thumbnail with its hidden device circled."""
    i = next((i for i, nm in enumerate(built) if nm.endswith(BRAND["reveal_pid"])), None)
    if i is None: return
    p = fns[i]()
    cols, gap = 10, 10
    tw = (W - 2 * M - (cols - 1) * gap) / cols; th = tw * H / W
    for j, nm in enumerate(built):
        x = M + (j % cols) * (tw + gap); y = 330 + (j // cols) * (th + gap + 4)
        im = Image.open(f"{OUT}/pages/{nm}.png").convert("RGB").resize((int(tw * 2), int(th * 2)), Image.LANCZOS)
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=82)
        p.add(f'<image x="{x:.1f}" y="{y:.1f}" width="{tw:.1f}" height="{th:.1f}" href="data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"/>',
              f'<rect x="{x:.1f}" y="{y:.1f}" width="{tw:.1f}" height="{th:.1f}" fill="none" stroke="{p.t["ink"]}" stroke-opacity="0.15"/>')
        if devices.get(nm):
            dx, dy, ds = devices[nm]; k = tw / W
            p.add(circle(x + (dx + ds / 2) * k, y + (dy + ds / 2) * k, 7, stroke=ACCENT, sw=1.5))
    svg = p.svg(i + 1)
    open(f"{SVGDIR}/{built[i]}.svg", "w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{OUT}/pages/{built[i]}.png", output_width=W)
    print("✓ reveal page", flush=True)

def bind(built):
    from pypdf import PdfWriter, PdfReader
    w = PdfWriter()
    for nm in built:
        w.append(PdfReader(io.BytesIO(cairosvg.svg2pdf(url=f"{SVGDIR}/{nm}.svg"))))
    name = f'{BRAND["name"].replace(" ", "_")}_Brand_Book_{BRAND["year"]}.pdf'
    with open(f"{OUT}/{name}", "wb") as f: w.write(f)
    print("✓ PDF", name, flush=True)

def sheet(names, cols=4, tw=480):
    """Contact sheet: what Kaif reviews."""
    th = tw * H // W
    rows = (len(names) + cols - 1) // cols
    im = Image.new("RGB", (cols * (tw + 12) + 12, rows * (th + 12) + 12), "#777")
    for i, nm in enumerate(names):
        t = Image.open(f"{OUT}/pages/{nm}.png").convert("RGB").resize((tw, th), Image.LANCZOS)
        im.paste(t, (12 + (i % cols) * (tw + 12), 12 + (i // cols) * (th + 12)))
    im.save(f"{OUT}/sheet.png")

if __name__ == "__main__":
    main(sys.argv[1:])
