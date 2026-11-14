"""Dieline + draft art → a step-by-step build plan for claude-talk-to-figma-mcp (community MCP, runs locally).

    python engine/dieline.py templates/dieline.json --figma       # writes <name>_figma.json next to the other files

The plan is a list of MCP tool calls in order. Claude runs them one by one after `join_channel`:
  - "$PAGE"  → the current page id (from get_pages / get_document_info)
  - "$FRAME" → the id returned by step 1 (the job frame)
  - "$LAST"  → the id returned by the previous step (used for follow-ups like set_font_name)
Units: 1 mm = 72/25.4 px, so a Figma PDF export comes out at true size.

What lands in Figma (bottom → top):
  Background (bg colour, bleed, pattern)   one vector
  Panels that read upright                 editable rectangles, text (with font set), logo / barcode / windows as vectors
  Panels that are rotated (tucks, lids…)   one vector group each (talk-to-figma has no rotate tool); edit in the source JSON
  DIELINE · do not edit                    cut / crease / perf / glue / safe as vectors, named layers
See ../FIGMA.md for setup and the run protocol.
"""
import json, math, os
from dieline import COL, path_d, esc
import art as A

K = 72 / 25.4      # px per mm

def rgb(hexv, a=None):
    h = hexv.lstrip("#")
    c = {"r": round(int(h[0:2], 16) / 255, 4), "g": round(int(h[2:4], 16) / 255, 4), "b": round(int(h[4:6], 16) / 255, 4)}
    if a is not None: c["a"] = a
    return c

FONT_FAMILY = {"display": ("Anton", "Regular"), "text": ("Space Grotesk", "Regular"), "medium": ("Space Grotesk", "Medium"),
               "light": ("Space Grotesk", "Light"), "label": ("Space Mono", "Regular"), "mono": ("Space Mono", "Regular")}

def font_for(key, art):
    fonts = art.get("figma_fonts", {})          # override per job: {"display": ["Family", "Style"], ...}
    if key in fonts: return tuple(fonts[key])
    return FONT_FAMILY.get(key, FONT_FAMILY["text"])

def svg_doc(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * K:.2f}" height="{h * K:.2f}" viewBox="0 0 {w:.3f} {h:.3f}">'
            f'{("<defs>" + defs + "</defs>") if defs else ""}{body}</svg>')


def plan(d, out):
    art = d.p.get("art") or {}
    x0, y0, x1, y1 = d.bbox()
    bleed = float(d.p.get("bleed", 3))
    m = bleed + 2
    W, H = (x1 - x0) + 2 * m, (y1 - y0) + 2 * m
    ox, oy = m - x0, m - y0                         # job mm → frame mm
    P = lambda x, y: (round((x + ox) * K, 2), round((y + oy) * K, 2))
    steps = [{"tool": "create_frame", "args": {"name": f"{d.name} · {d.style}", "x": 0, "y": 0, "width": round(W * K, 2), "height": round(H * K, 2),
                                               "parentId": "$PAGE", "fillColor": rgb("#FFFFFF")}, "save_as": "$FRAME"}]
    def svg_step(name, body, defs=""):
        steps.append({"tool": "set_svg", "args": {"svgString": svg_doc(W, H, f'<g transform="translate({ox:.3f},{oy:.3f})">{body}</g>', defs),
                                                  "x": 0, "y": 0, "name": name, "parentId": "$FRAME"}})
    # 1. background
    if art:
        bg = A.token(art.get("bg"), "#FFFFFF") if art.get("bg") != "clear" else None
        body = ""
        if bg:
            body += "".join(f'<path d="{path_d(o)}" fill="{bg}" stroke="{bg}" stroke-width="{2 * bleed:.3f}" stroke-linejoin="miter"/>' for o in d.outlines)
        pat = A.global_pattern(d, art)
        clip = "".join(f'<path d="{path_d(o)}"/>' for o in d.outlines)
        if pat: body += f'<g clip-path="url(#die)">{pat}</g>'
        if body: svg_step("Background (colour + bleed + pattern)", body, f'<clipPath id="die">{clip}</clipPath>' if pat else "")
    # 2. panels
    pcfg = art.get("panels", {}) if art else {}
    base_dir = d.p.get("_base_dir", os.getcwd())
    for n, poly, sf, *up in d.panels:
        if n.startswith("Back-half"): continue
        cfg = A.match_panel(n, pcfg) or (art.get("default") if art else None)
        if not cfg: continue
        up = up[0] if up else (0, -1)
        o, lx, ly, pw, ph = A.frame_axes(poly, up)
        pa = A.PanelArt(n, pw, ph, sf if sf is not None else float(d.p.get("safe", 3)), cfg, art, base_dir, [])
        upright = abs(lx[0] - 1) < 1e-6 and abs(ly[1] - 1) < 1e-6
        if not upright:
            tr, _, _ = A.panel_frame(poly, up)
            svg_step(f"Panel · {n} (rotated: vector)", f'<g transform="{tr}">{pa.svg()}</g>')
            continue
        if cfg.get("bg"):
            gx, gy = P(o[0], o[1])
            steps.append({"tool": "create_rectangle", "args": {"name": f"{n} · bg", "x": gx, "y": gy, "width": round(pw * K, 2), "height": round(ph * K, 2),
                                                               "parentId": "$FRAME", "fillColor": rgb(pa.bg)}})
        for b in cfg.get("blocks", []):
            t = b.get("type", "text")
            if t in ("band", "rect"):
                if t == "band" and b.get("full", True):
                    bx, bw, by, bh = 0, pw, float(b.get("y", 0)) * ph, float(b.get("h", 0.1)) * ph
                elif t == "band":
                    bx, bw, by, bh = pa.X(b.get("x", 0)), float(b.get("w", 1)) * pa.sw, pa.Y(b.get("y", 0)), float(b.get("h", 0.1)) * pa.sh
                else:
                    bx, by, bw, bh = pa.X(b.get("x", 0)), pa.Y(b.get("y", 0)), float(b.get("w", 0.2)) * pa.sw, float(b.get("h", 0.2)) * pa.sh
                gx, gy = P(o[0] + bx, o[1] + by)
                steps.append({"tool": "create_rectangle", "args": {"name": f"{n} · {t}", "x": gx, "y": gy, "width": round(bw * K, 2), "height": round(bh * K, 2),
                                                                   "parentId": "$FRAME", "fillColor": rgb(pa.colour(b, "fill", A.token("accent")))}})
            elif t in ("text", "para"):
                size, fk = float(b.get("size", 4 if t == "text" else 2.4)), b.get("font", "text")
                if t == "text":
                    w = A.tw(b["text"], size, fk, float(b.get("track", 0)))
                    anc = b.get("anchor", "start")
                    lx_ = pa.X(b.get("x", 0)) - (w if anc == "end" else w / 2 if anc == "middle" else 0)
                    ly_ = pa.Y(b.get("y", 0)) - size * 0.95
                    content = b["text"]
                else:
                    lx_, ly_ = pa.X(b.get("x", 0)), pa.Y(b.get("y", 0)) - size * 0.95
                    content = "\n".join(A.wrap(b["text"], size, float(b.get("w", 1)) * pa.sw, fk))
                gx, gy = P(o[0] + lx_, o[1] + ly_)
                fam, style = font_for(fk, art)
                steps.append({"tool": "create_text", "args": {"name": f"{n} · {content[:24]}", "x": gx, "y": gy, "text": content,
                                                              "fontSize": round(size * K, 2), "fontColor": rgb(pa.colour(b)), "parentId": "$FRAME"}})
                steps.append({"tool": "set_font_name", "args": {"nodeId": "$LAST", "family": fam, "style": style}, "optional": True,
                              "note": "if the font isn't installed in Figma, skip; the text stays editable"})
            else:                                     # logo, barcode, placeholder, circle, rule → vectors in panel space
                one = A.PanelArt(n, pw, ph, pa.s, {"blocks": [b]}, art, base_dir, [])
                frag = one.svg(background=False)
                if frag:
                    label = {"logo": "logo (client file)", "barcode": "barcode placeholder", "placeholder": f"placeholder · {b.get('label', '')[:24]}"}.get(t, t)
                    svg_step(f"{n} · {label}", f'<g transform="translate({o[0]:.3f},{o[1]:.3f})">{frag}</g>')
    # split flow-wrap back
    sb = getattr(d, "split_back", None)
    if sb and A.match_panel("Back", pcfg):
        pa = A.PanelArt("Back", sb["W"], sb["h"], float(d.p.get("safe", 3)), A.match_panel("Back", pcfg), art, base_dir, [])
        body, defs = "", ""
        for x0_, shift in ((sb["BR"], 0), (sb["BL"], sb["W"] / 2)):
            cid = f"sb{int(x0_ * 10)}"
            defs += f'<clipPath id="{cid}"><rect x="{x0_:.3f}" y="{sb["y0"]:.3f}" width="{sb["W"] / 2:.3f}" height="{sb["h"]:.3f}"/></clipPath>'
            body += f'<g clip-path="url(#{cid})"><g transform="translate({x0_ - shift:.3f},{sb["y0"]:.3f})">{pa.svg()}</g></g>'
        svg_step("Back (split across the web: vector)", body, defs)
    # windows
    if getattr(d, "windows", None):
        svg_step("WINDOWS (no ink / die-cut)", A.windows_svg(d, art).replace("url(#chk)", "#D9D9D9"))
    # 3. dieline on top
    die = ("".join(f'<path d="{path_d(g)}" fill="#ffffff" fill-opacity="0.9" stroke="{COL["GLUE"]}" stroke-width="0.2"/>' for g in d.glue)
           + "".join(f'<path d="{path_d(l, False)}" fill="none" stroke="{COL["CREASE"]}" stroke-width="0.3" stroke-dasharray="3 1.5"/>' for l in d.lines["CREASE"])
           + "".join(f'<path d="{path_d(l, False)}" fill="none" stroke="{COL["PERF"]}" stroke-width="0.3" stroke-dasharray="1 1"/>' for l in d.lines["PERF"])
           + "".join(f'<path d="{path_d(o)}" fill="none" stroke="{COL["CUT"]}" stroke-width="0.35"/>' for o in d.outlines + d.holes))
    svg_step("DIELINE · do not edit (cut / crease / perf / glue)", die)
    doc = {"job": d.name, "style": d.style, "frame_mm": [round(W, 2), round(H, 2)], "px_per_mm": round(K, 5),
           "protocol": ["join_channel(<code from the Figma plugin>)", "get_document_info or get_pages → $PAGE",
                        "run steps in order; store ids: save_as names and $LAST", "optional steps may be skipped on error",
                        "finish: get_node_info($FRAME) and export_node_as_image to check against <name>_art.png"],
           "steps": steps}
    path = os.path.join(out, d.name + "_figma.json")
    json.dump(doc, open(path, "w"), indent=1)
    return path, len(steps)
