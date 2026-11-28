"""Generate class-diagram SVG and Mermaid from authored OntoUML JSON models."""
from __future__ import annotations

import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
MODELS = ROOT.parent / "ontouml-to-gufo-check" / "models"

CASES = [
    ("01-endurant-types", "1. Endurant types"),
    ("02-objects-and-parts", "2. Objects and their parts"),
    ("03-qualities", "3. Qualities and quality values"),
    ("04-relators", "4. Relators and extrinsic aspects"),
    ("05-events", "5. Events"),
    ("06-situations", "6. Situations"),
    ("07-higher-order-types", "7. Higher-order types"),
    ("invalid-01-endurant-types", "1, invalid variant"),
    ("invalid-07-higher-order-types", "7, invalid variant"),
]

INK = "#18362f"
MUTED = "#53675f"
LINE = "#d6ded5"
PALE = "#edf1e9"
PAPER = "#fbfaf6"
ACCENT = "#b94d30"

BOX_H = 52
BOX_PAD_X = 16
MIN_W = 120
MAX_W = 220
LAYER_GAP_Y = 92
BOX_GAP_X = 28
MARGIN = 28


def label_of(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("en") or next(iter(value.values()), "") or ""
    return str(value)


def mermaid_id(name: str, fallback: str) -> str:
    raw = name or fallback
    out = []
    for ch in raw:
        if ch.isalnum() or ch == "_":
            out.append(ch)
        elif ch in " -":
            out.append("_")
    ident = "".join(out) or fallback.replace(":", "_")
    if ident[0].isdigit():
        ident = "C_" + ident
    return ident


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse(model: dict):
    elements = {e["id"]: e for e in model.get("elements") or [] if "id" in e}
    classes = [e for e in elements.values() if e.get("type") == "Class"]
    gens = [e for e in elements.values() if e.get("type") == "Generalization"]
    gsets = [e for e in elements.values() if e.get("type") == "GeneralizationSet"]
    rels = []
    for e in elements.values():
        if e.get("type") != "BinaryRelation":
            continue
        ends = []
        for pid in e.get("properties") or []:
            p = elements.get(pid)
            if not p:
                continue
            ends.append(
                {
                    "id": p.get("id"),
                    "name": label_of(p.get("name")),
                    "type": p.get("propertyType"),
                    "card": p.get("cardinality"),
                    "agg": (p.get("aggregationKind") or "NONE"),
                }
            )
        if len(ends) == 2 and ends[0]["type"] and ends[1]["type"]:
            rels.append(
                {
                    "id": e["id"],
                    "name": label_of(e.get("name")),
                    "stereotype": e.get("stereotype") or "",
                    "ends": ends,
                }
            )
    return classes, gens, gsets, rels


def layers_for(classes, gens):
    ids = [c["id"] for c in classes]
    parents = {i: [] for i in ids}
    children = {i: [] for i in ids}
    for g in gens:
        gen, spec = g.get("general"), g.get("specific")
        if gen in parents and spec in parents:
            parents[spec].append(gen)
            children[gen].append(spec)

    depth = {}

    def walk(cid, seen):
        if cid in depth:
            return depth[cid]
        if cid in seen:
            return 0
        seen = seen | {cid}
        if not parents[cid]:
            depth[cid] = 0
        else:
            depth[cid] = 1 + max(walk(p, seen) for p in parents[cid])
        return depth[cid]

    for cid in ids:
        walk(cid, set())

    by = {}
    for cid, d in depth.items():
        by.setdefault(d, []).append(cid)
    # stable order: keep model order
    order = {c["id"]: i for i, c in enumerate(classes)}
    for d in by:
        by[d].sort(key=lambda i: order[i])
    return by, parents, children, depth


def text_width(text: str, size: float, bold: bool = False) -> float:
    # approximate glyph width for the page's sans/serif mix
    unit = 0.62 if bold else 0.56
    return len(text) * size * unit


def box_size(name: str, stereo: str) -> tuple[float, float]:
    w = max(MIN_W, text_width(name, 14, True) + BOX_PAD_X * 2, text_width(f"«{stereo}»", 11) + BOX_PAD_X * 2 if stereo else 0)
    w = min(MAX_W, w)
    return w, BOX_H


def pack_rows(ids, sizes, max_row_w):
    rows, current, width = [], [], 0
    for cid in ids:
        w = sizes[cid][0]
        need = w if not current else width + BOX_GAP_X + w
        if current and need > max_row_w:
            rows.append(current)
            current, width = [cid], w
        else:
            current.append(cid)
            width = need
    if current:
        rows.append(current)
    return rows


def layout(classes, gens, rels):
    by, parents, children, depth = layers_for(classes, gens)
    sizes = {c["id"]: box_size(label_of(c.get("name")) or c["id"], c.get("stereotype") or "") for c in classes}
    max_row_w = 980
    depth_of = {cid: d for d, ids in by.items() for cid in ids}
    same_layer_rels = 0
    for rel in rels:
        ends = [rel["ends"][0]["type"], rel["ends"][1]["type"]]
        if all(e in depth_of for e in ends) and depth_of[ends[0]] == depth_of[ends[1]]:
            same_layer_rels += 1
    row_gap = LAYER_GAP_Y + (28 if same_layer_rels >= 4 else 0)

    staged = []
    y = MARGIN + 10
    max_w = 720
    depths = sorted(by)
    for d in depths:
        rows = pack_rows(by[d], sizes, max_row_w)
        for r_i, row in enumerate(rows):
            widths = [sizes[i][0] for i in row]
            layer_w = sum(widths) + BOX_GAP_X * (len(row) - 1)
            max_w = max(max_w, layer_w + MARGIN * 2)
            staged.append((layer_w, row, y))
            last_sub = r_i == len(rows) - 1
            last_layer = d == depths[-1]
            if not (last_sub and last_layer):
                y += BOX_H + row_gap
            else:
                y += BOX_H
    canvas_w = max_w
    canvas_h = y + MARGIN + 12
    positions = {}
    for layer_w, row, ry in staged:
        x = (canvas_w - layer_w) / 2
        for cid in row:
            w, h = sizes[cid]
            positions[cid] = (x, ry, w, h)
            x += w + BOX_GAP_X
    return positions, canvas_w, canvas_h


def xml(s: str) -> str:
    return escape(s, {"'": "&apos;", '"': "&quot;"})


def box_points(pos):
    x, y, w, h = pos
    return {
        "cx": x + w / 2,
        "cy": y + h / 2,
        "top": (x + w / 2, y),
        "bottom": (x + w / 2, y + h),
        "left": (x, y + h / 2),
        "right": (x + w, y + h / 2),
        "x": x,
        "y": y,
        "w": w,
        "h": h,
    }


def anchors(a, b):
    """Choose sides of boxes a, b for a line from a to b."""
    pa, pb = box_points(a), box_points(b)
    # if b is clearly above a, generalization-style: top of a to bottom of b
    if pb["cy"] + 8 < pa["y"]:
        return pa["top"], pb["bottom"]
    if pa["cy"] + 8 < pb["y"]:
        return pa["bottom"], pb["top"]
    if pb["cx"] >= pa["cx"]:
        return pa["right"], pb["left"]
    return pa["left"], pb["right"]


def svg_for(title: str, model: dict, invalid: bool = False, slug: str = "d") -> str:
    classes, gens, gsets, rels = parse(model)
    positions, width, height = layout(classes, gens, rels)
    # extra space if many relations
    height += 8
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" width="{width:.0f}" height="{height:.0f}" role="img">',
        f"<title>{xml(title)}</title>",
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        f'<defs><marker id="gen-{slug}" markerWidth="12" markerHeight="10" refX="12" refY="5" orient="auto"><path d="M0,0 L12,5 L0,10 Z" fill="{PAPER}" stroke="{INK}" stroke-width="1.2"/></marker>',
        f'<marker id="agg-{slug}" markerWidth="12" markerHeight="10" refX="0" refY="5" orient="auto"><path d="M0,5 L6,0 L12,5 L6,10 Z" fill="{PAPER}" stroke="{INK}" stroke-width="1.2"/></marker>',
        f'<marker id="comp-{slug}" markerWidth="12" markerHeight="10" refX="0" refY="5" orient="auto"><path d="M0,5 L6,0 L12,5 L6,10 Z" fill="{INK}" stroke="{INK}" stroke-width="1.2"/></marker></defs>',
    ]
    if invalid:
        parts.append(
            f'<text x="{MARGIN}" y="18" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="{ACCENT}">Invalid variant — drawn from the authored OntoUML JSON</text>'
        )
        # nudge? title already in caption; keep a small banner only if there's margin
    # relations first (under boxes)
    for rel in rels:
        e0, e1 = rel["ends"]
        if e0["type"] not in positions or e1["type"] not in positions:
            continue
        (x1, y1), (x2, y2) = anchors(positions[e0["type"]], positions[e1["type"]])
        # diamond at the COMPOSITE/SHARED whole end
        start_marker = end_marker = ""
        def mark(end, at_start):
            if end["agg"] == "COMPOSITE":
                return 'marker-start="url(#comp-{slug})"' if at_start else 'marker-end="url(#comp-{slug})"'
            if end["agg"] == "SHARED":
                return 'marker-start="url(#agg-{slug})"' if at_start else 'marker-end="url(#agg-{slug})"'
            return ""
        # aggregation is on the whole; marker should sit on that end.
        # If end 1 is the whole, marker at x2,y2 (end). Our markers have refX=0 so they attach at the start of the marker direction — use start/end carefully.
        # Simpler: no markers if it gets messy; use a filled/unfilled diamond via a small path at the whole end.
        whole = None
        part = None
        if e0["agg"] in ("COMPOSITE", "SHARED"):
            whole, part, filled = e0, e1, e0["agg"] == "COMPOSITE"
        elif e1["agg"] in ("COMPOSITE", "SHARED"):
            whole, part, filled = e1, e0, e1["agg"] == "COMPOSITE"
        else:
            filled = None
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{INK}" stroke-width="1.1"/>'
        )
        if filled is not None:
            # diamond at whole end
            wx, wy = (x1, y1) if whole["type"] == e0["type"] else (x2, y2)
            ox, oy = (x2, y2) if whole["type"] == e0["type"] else (x1, y1)
            dx, dy = ox - wx, oy - wy
            length = math.hypot(dx, dy) or 1
            ux, uy = dx / length, dy / length
            px, py = -uy, ux
            s = 6
            p1 = (wx + ux * 2 * s, wy + uy * 2 * s)
            p2 = (wx + ux * s + px * s * 0.7, wy + uy * s + py * s * 0.7)
            p3 = (wx + ux * s - px * s * 0.7, wy + uy * s - py * s * 0.7)
            fill = INK if filled else PAPER
            parts.append(
                f'<polygon points="{wx:.1f},{wy:.1f} {p2[0]:.1f},{p2[1]:.1f} {p1[0]:.1f},{p1[1]:.1f} {p3[0]:.1f},{p3[1]:.1f}" fill="{fill}" stroke="{INK}" stroke-width="1.1"/>'
            )
        label = rel["stereotype"] or rel["name"]
        if not label:
            # unnamed ordinary relation — omit or use a mid dot? skip label
            mid = ((x1 + x2) / 2, (y1 + y2) / 2)
        else:
            if rel["stereotype"] and rel["name"] and rel["name"].lower() != rel["stereotype"].lower():
                label = f"«{rel['stereotype']}» {rel['name']}"
            elif rel["stereotype"]:
                label = f"«{rel['stereotype']}»"
            mid = ((x1 + x2) / 2, (y1 + y2) / 2)
            # offset label a little along the normal
            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy) or 1
            nx, ny = -dy / length * 8, dx / length * 8
            parts.append(
                f'<text x="{mid[0]+nx:.1f}" y="{mid[1]+ny:.1f}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10" fill="{MUTED}">{xml(label)}</text>'
            )
        # cardinalities
        def card_at(end, px, py, otherx, othery):
            if not end["card"]:
                return
            dx, dy = otherx - px, othery - py
            length = math.hypot(dx, dy) or 1
            tx, ty = px + dx / length * 16, py + dy / length * 16
            parts.append(
                f'<text x="{tx:.1f}" y="{ty-4:.1f}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="9" fill="{MUTED}">{xml(str(end["card"]))}</text>'
            )
        card_at(e0, x1, y1, x2, y2)
        card_at(e1, x2, y2, x1, y1)

    # generalizations
    for g in gens:
        if g.get("specific") not in positions or g.get("general") not in positions:
            continue
        (x1, y1), (x2, y2) = anchors(positions[g["specific"]], positions[g["general"]])
        # shorten the end so the hollow triangle sits on the general box
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy) or 1
        x2s, y2s = x2 - dx / length * 2, y2 - dy / length * 2
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2s:.1f}" y2="{y2s:.1f}" stroke="{INK}" stroke-width="1.2" marker-end="url(#gen-{slug})"/>'
        )

    # class boxes
    for c in classes:
        x, y, w, h = positions[c["id"]]
        name = label_of(c.get("name")) or c["id"]
        stereo = c.get("stereotype") or ""
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="5" fill="{PALE}" stroke="{INK}" stroke-width="1.2"/>'
        )
        if stereo:
            parts.append(
                f'<text x="{x+w/2:.1f}" y="{y+20:.1f}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="{MUTED}">«{xml(stereo)}»</text>'
            )
            parts.append(
                f'<text x="{x+w/2:.1f}" y="{y+38:.1f}" text-anchor="middle" font-family="Georgia, serif" font-size="14" fill="{INK}">{xml(name)}</text>'
            )
        else:
            parts.append(
                f'<text x="{x+w/2:.1f}" y="{y+32:.1f}" text-anchor="middle" font-family="Georgia, serif" font-size="14" fill="{INK}">{xml(name)}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def mermaid_for(model: dict) -> str:
    classes, gens, gsets, rels = parse(model)
    names = {c["id"]: label_of(c.get("name")) or c["id"] for c in classes}
    ids = {cid: mermaid_id(name, cid) for cid, name in names.items()}
    used = {}
    # ensure unique mermaid ids
    for cid, ident in list(ids.items()):
        if ident in used:
            ids[cid] = ident + "_" + cid.split(":")[-1].replace("-", "_")
        used[ids[cid]] = cid
    lines = ["classDiagram"]
    for c in classes:
        ident = ids[c["id"]]
        stereo = c.get("stereotype") or ""
        lines.append(f"  class {ident} {{")
        if stereo:
            lines.append(f"    <<{stereo}>>")
        lines.append("  }")
        # also a label if mermaid id differs
        pretty = names[c["id"]]
        if pretty and pretty != ident:
            lines.append(f'  {ident} : {pretty}' if False else f'  class {ident}["{pretty}"]')
    # The class ident["label"] may duplicate class blocks; use alias form only
    # Rewrite more cleanly:
    lines = ["classDiagram"]
    for c in classes:
        ident = ids[c["id"]]
        pretty = names[c["id"]].replace('"', "'")
        stereo = c.get("stereotype") or ""
        lines.append(f'  class {ident}["{pretty}"]')
        if stereo:
            lines.append(f"  {ident} : <<{stereo}>>")
    for g in gens:
        if g.get("specific") in ids and g.get("general") in ids:
            lines.append(f'  {ids[g["specific"]]} --|> {ids[g["general"]]}')
    for rel in rels:
        e0, e1 = rel["ends"]
        if e0["type"] not in ids or e1["type"] not in ids:
            continue
        a, b = ids[e0["type"]], ids[e1["type"]]
        label = rel["stereotype"] or rel["name"] or ""
        label = label.replace('"', "'")
        card0 = f' "{e0["card"]}"' if e0["card"] else ""
        card1 = f' "{e1["card"]}"' if e1["card"] else ""
        whole_on = None
        if e0["agg"] in ("COMPOSITE", "SHARED"):
            whole_on = 0
        elif e1["agg"] in ("COMPOSITE", "SHARED"):
            whole_on = 1
        if whole_on == 1:
            arrow = "*--" if e1["agg"] == "COMPOSITE" else "o--"
            core = f"  {a}{card0} {arrow}{card1} {b}"
        elif whole_on == 0:
            arrow = "*--" if e0["agg"] == "COMPOSITE" else "o--"
            core = f"  {b}{card1} {arrow}{card0} {a}"
        else:
            core = f"  {a}{card0} --{card1} {b}"
        if label:
            core += f" : {label}"
        lines.append(core)
    return "\n".join(lines) + "\n"


def main():
    written = []
    for slug, title in CASES:
        src = MODELS / slug / "model.json"
        model = load(src)
        invalid = slug.startswith("invalid-")
        svg = svg_for(title, model, invalid=invalid, slug=slug)
        mmd = mermaid_for(model)
        (ROOT / f"{slug}.svg").write_text(svg, encoding="utf-8", newline="\n")
        (ROOT / f"{slug}.mmd").write_text(mmd, encoding="utf-8", newline="\n")
        written.append((slug, src.stat().st_size, len(svg), len(mmd)))
        print(f"wrote {slug}.svg ({len(svg)} bytes) and {slug}.mmd from {src.relative_to(ROOT.parent)}")
    return written


if __name__ == "__main__":
    main()
