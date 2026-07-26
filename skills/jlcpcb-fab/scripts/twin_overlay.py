#!/usr/bin/env python3
"""twin_overlay.py — draw every footprint's COURTYARD onto a twin render, so a
model-vs-footprint disagreement is visible instead of merely tabulated.

    twin_overlay.py BOARD.kicad_pcb TWIN.png [--out DIR] [--twin-report CSV]
                    [--crop-flagged] [--report MD]

WHY THIS EXISTS. `jlc_twin` ALREADY computes the thing this draws — it emits
MODEL-REG ("body center 3.5mm off courtyard, area ratio 0.70") and MODEL-SELF
("JLC model bbox center off JLC's OWN pads by (+2.20,-2.87)mm"). Those numbers
are correct and they were correct on crow-recorder-central-v2 v1.5 for exactly
the two connectors a human later squinted at and called wrong.

The failure was not detection. It was that the NUMBER and the PICTURE lived in
different files, so the render — which is the artifact a human actually looks at
— showed two connectors apparently retracted from the board edge with nothing on
it to say "this is a known model-registration offset, the land is fine".

A reviewer given only the render will either miss a real defect or, as happened
here, invent an explanation for a real anomaly and move on. Both of those are
worse than a picture with a box drawn on it.

WHAT IT PROVES AND WHAT IT DOES NOT. The red box is the FOOTPRINT COURTYARD,
which is what gets fabricated: gerbers and CPL derive from pads, never from the
3D model. So a body sitting outside its red box is a MODEL defect, not a board
defect — the land is still right. That distinction is the whole point, and it is
the one a reviewer cannot make from an un-annotated render.

CALIBRATION IS MEASURED, NOT ASSUMED. The mm->px transform is derived from the
board's own green extent in the image and cross-checked for anisotropy. A twin
render is orthographic and straight-on; if x and y scales disagree by more than
`--aniso-tol` the projection is NOT valid and this tool REFUSES rather than
drawing boxes in the wrong places. A misleading overlay would be worse than
none — see the I-HW geodesic, which encoded the wrong physics rather than none
and was believed because it produced a number.
"""
import argparse
import csv
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("twin_overlay: needs Pillow (PIL)")

RED = (255, 0, 0)
BLUE = (0, 160, 255)
AMBER = (255, 170, 0)


def board_extent_px(im):
    """(minx, miny, maxx, maxy) of the green board region, by sampling."""
    W, H = im.size
    px = im.load()
    minx, miny, maxx, maxy = W, H, 0, 0
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            r, g, b = px[x, y][:3]
            if g > r + 8 and g > b + 8 and g > 25:
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
    if maxx <= minx or maxy <= miny:
        return None
    return minx, miny, maxx, maxy


def load_board(path):
    import pcbnew
    return pcbnew.LoadBoard(str(path))


def collect(board):
    """[(ref, (x0,y0,x1,y1) courtyard mm, has_model)] plus board edge bbox mm."""
    import pcbnew
    bb = board.GetBoardEdgesBoundingBox()
    edge = (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
            bb.GetRight() / 1e6, bb.GetBottom() / 1e6)
    out = []
    for fp in board.GetFootprints():
        cy = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
        if cy.GetWidth() == 0 and cy.GetHeight() == 0:
            cy = fp.GetCourtyard(pcbnew.B_CrtYd).BBox()
        if cy.GetWidth() == 0 and cy.GetHeight() == 0:
            out.append((fp.GetReference(), None, len(list(fp.Models())) > 0))
            continue
        out.append((fp.GetReference(),
                    (cy.GetLeft() / 1e6, cy.GetTop() / 1e6,
                     cy.GetRight() / 1e6, cy.GetBottom() / 1e6),
                    len(list(fp.Models())) > 0))
    return out, edge


def read_twin_findings(path):
    """ref -> [(status, detail)] for the statuses that mean 'the body may not
    sit where the land is'. These are the rows whose meaning is VISUAL."""
    interesting = {"MODEL-REG", "MODEL-SELF", "PAD-GEOM", "PAD-MISMATCH",
                   "MIRRORED", "POLARITY-CHECK", "POLARITY-FIT-BLIND",
                   "PAD-MULTIPLICITY", "NO-BODY", "FETCH-FAILED"}
    found = {}
    if not path or not Path(path).is_file():
        return found
    for row in csv.DictReader(open(path)):
        st = (row.get("Status") or "").strip()
        if st in interesting:
            found.setdefault((row.get("Ref") or "").strip(), []).append(
                (st, (row.get("Detail") or "").strip()))
    return found


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("twin_png")
    ap.add_argument("--out", default=None, help="directory for overlay + crops")
    ap.add_argument("--twin-report", default=None, help="twin_report.csv")
    ap.add_argument("--crop-flagged", action="store_true")
    ap.add_argument("--report", default=None, help="write a markdown report here")
    ap.add_argument("--aniso-tol", type=float, default=0.02)
    a = ap.parse_args(argv)

    im = Image.open(a.twin_png).convert("RGB")
    ext = board_extent_px(im)
    if ext is None:
        print("OVERLAY ERROR: no green board region found — is this a twin render?",
              file=sys.stderr)
        return 2
    minx, miny, maxx, maxy = ext

    board = load_board(a.board)
    parts, edge = collect(board)
    ex0, ey0, ex1, ey1 = edge
    bw, bh = ex1 - ex0, ey1 - ey0

    sx = (maxx - minx + 1) / bw
    sy = (maxy - miny + 1) / bh
    aniso = sx / sy
    if abs(aniso - 1.0) > a.aniso_tol:
        # REFUSE. A projection this tool cannot trust must not be drawn — an
        # overlay in the wrong place is believed exactly as readily as one in
        # the right place.
        print(f"OVERLAY REFUSED: anisotropy {aniso:.4f} exceeds tol "
              f"{a.aniso_tol} (x {sx:.4f} px/mm, y {sy:.4f} px/mm). The render "
              f"is not orthographic/straight-on, so courtyard projection would "
              f"be wrong. No image written.", file=sys.stderr)
        return 2

    def X(mm): return minx + (mm - ex0) * sx
    def Y(mm): return miny + (mm - ey0) * sy

    findings = read_twin_findings(a.twin_report)
    outdir = Path(a.out) if a.out else Path(a.twin_png).parent
    outdir.mkdir(parents=True, exist_ok=True)

    d = ImageDraw.Draw(im)
    d.rectangle([X(ex0), Y(ey0), X(ex1), Y(ey1)], outline=BLUE, width=2)
    drawn = no_courtyard = 0
    for ref, cy, has_model in parts:
        if cy is None:
            no_courtyard += 1
            continue
        col = AMBER if ref in findings else RED
        w = 3 if ref in findings else 1
        d.rectangle([X(cy[0]), Y(cy[1]), X(cy[2]), Y(cy[3])], outline=col, width=w)
        drawn += 1

    ov = outdir / (Path(a.twin_png).stem + "_courtyard_overlay.png")
    im.save(ov)

    crops = []
    if a.crop_flagged and findings:
        base = Image.open(a.twin_png).convert("RGB")
        for ref, cy, _ in parts:
            if cy is None or ref not in findings:
                continue
            pad = 40
            box = (max(0, int(X(cy[0])) - pad), max(0, int(Y(cy[1])) - pad),
                   min(im.size[0], int(X(cy[2])) + pad),
                   min(im.size[1], int(Y(cy[3])) + pad))
            c = base.crop(box)
            dd = ImageDraw.Draw(c)
            dd.rectangle([X(cy[0]) - box[0], Y(cy[1]) - box[1],
                          X(cy[2]) - box[0], Y(cy[3]) - box[1]],
                         outline=RED, width=2)
            dd.rectangle([X(ex0) - box[0], Y(ey0) - box[1],
                          X(ex1) - box[0], Y(ey1) - box[1]],
                         outline=BLUE, width=2)
            c = c.resize((c.width * 5, c.height * 5), Image.LANCZOS)
            p = outdir / f"overlay_{ref}.png"
            c.save(p)
            crops.append((ref, p))

    lines = []
    lines.append(f"# Twin courtyard overlay — {Path(a.twin_png).name}\n")
    lines.append(f"- calibration: **{sx:.4f} px/mm** x, **{sy:.4f} px/mm** y, "
                 f"anisotropy **{aniso:.4f}** (tol {a.aniso_tol}) — orthographic, projection valid")
    lines.append(f"- board edge: {ex0:.3f}..{ex1:.3f} x, {ey0:.3f}..{ey1:.3f} y mm")
    lines.append(f"- courtyards drawn: **{drawn}**; footprints with no courtyard: {no_courtyard}")
    lines.append(f"- overlay: `{ov.name}`\n")
    lines.append("**Red** = footprint courtyard (what gets fabricated). "
                 "**Amber** = courtyard of a ref jlc_twin flagged. "
                 "**Blue** = board edge.\n")
    lines.append("A body drawn OUTSIDE its box is a **3D-model** defect, not a board "
                 "defect: gerbers and CPL derive from pads, never from the model. "
                 "That distinction is what a reviewer cannot make from an "
                 "un-annotated render.\n")
    if findings:
        lines.append(f"## {len(findings)} ref(s) flagged by jlc_twin — check these boxes first\n")
        lines.append("| ref | status | what the render will look like |")
        lines.append("|---|---|---|")
        for ref, fl in sorted(findings.items()):
            for st, detail in fl:
                lines.append(f"| `{ref}` | **{st}** | {detail[:190]} |")
        lines.append("")
    if crops:
        lines.append("## Per-ref crops\n")
        for ref, p in crops:
            lines.append(f"- `{ref}` -> `{p.name}`")
        lines.append("")
    txt = "\n".join(lines) + "\n"
    if a.report:
        Path(a.report).write_text(txt)
    print(txt)
    print(f"OVERLAY OK: {drawn} courtyards, {len(findings)} flagged, "
          f"{len(crops)} crops -> {ov}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
