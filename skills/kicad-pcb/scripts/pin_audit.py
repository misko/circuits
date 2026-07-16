#!/usr/bin/env python3
"""Pin-audit dossier extractor: everything a FRESH-CONTEXT reviewer needs to
verify one part's pins against the datasheet and electrical intent - and
nothing of the authors' conclusions.

Per part it emits <ref>.md containing:
  - the pad table straight from the BOARD: pad number, footprint-local
    position (rotation-0 frame), side, size, and the NET actually connected
  - the computed pin-1 corner and winding direction (CW/CCW, top view)
  - the pin-function map from 02_parts/<MPN>/part.yaml (datasheet-sourced)
  - the datasheet path, so the reviewer can check the pinout figure directly
  - join gaps: pads missing from the yaml pin map and vice versa

It deliberately draws NO conclusions: the reviewer must independently derive
the expected winding from the datasheet package drawing and judge whether
each pin's net makes electrical sense. (A mirror-numbered footprint shipped
twice because every automated gate compared our artifacts against each other
- they were consistently wrong together. Fresh eyes break that loop.)

usage: pin_audit.py BOARD BOM_JLC_CSV PARTS_DIR OUTDIR [--refs U1,U2,...]
Default ref set: every part with more than 3 pads (ICs, FETs, connectors).

Run with the KiCad-bundled python (/usr/bin/python3).
"""
import argparse
import csv
import math
import sys
from pathlib import Path

import pcbnew

try:
    import yaml
except ImportError:
    yaml = None


def local_pads(fp):
    """Pads in the footprint's own frame (board rotation undone)."""
    rot = fp.GetOrientationDegrees()
    fp.SetOrientationDegrees(0)
    ox, oy = fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6
    out = []
    for p in fp.Pads():
        n = str(p.GetNumber())
        out.append({
            "num": n,
            "x": round(p.GetPosition().x / 1e6 - ox, 3),
            "y": round(p.GetPosition().y / 1e6 - oy, 3),
            "w": round(p.GetSize(pcbnew.F_Cu).x / 1e6, 2),
            "h": round(p.GetSize(pcbnew.F_Cu).y / 1e6, 2),
            "net": p.GetNetname() or "(no net)",
            "tht": p.GetDrillSize().x > 0,
        })
    fp.SetOrientationDegrees(rot)
    return out


def side_of(p, pads):
    xs = [q["x"] for q in pads]
    ys = [q["y"] for q in pads]
    mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    dx, dy = p["x"] - mx, p["y"] - my
    if abs(dx) < 0.3 and abs(dy) < 0.3:
        return "center"
    # KiCad frame: +y is DOWN on the top view
    return ("E" if dx > 0 else "W") if abs(dx) > abs(dy) else ("S" if dy > 0 else "N")


def winding(pads):
    """CW/CCW of numeric pin sequence around the centroid, TOP view.
    KiCad's +y-down means a mathematically-positive angle sweep is CW on
    screen; report in top-view screen terms (what a datasheet figure shows)."""
    seq = sorted((p for p in pads if p["num"].isdigit() and p["side"] != "center"),
                 key=lambda p: int(p["num"]))
    if len(seq) < 3:
        return "n/a (too few perimeter pins)"
    xs = [p["x"] for p in seq]
    ys = [p["y"] for p in seq]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    total = 0.0
    for a, b in zip(seq, seq[1:]):
        a1 = math.atan2(a["y"] - cy, a["x"] - cx)
        a2 = math.atan2(b["y"] - cy, b["x"] - cx)
        d = a2 - a1
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        total += d
    # +y down: positive accumulated angle = clockwise as drawn/viewed from top
    return "CW (top view)" if total > 0 else "CCW (top view)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("bom")
    ap.add_argument("parts_dir")
    ap.add_argument("outdir")
    ap.add_argument("--refs", default="")
    args = ap.parse_args()

    board = pcbnew.LoadBoard(args.board)
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    parts = Path(args.parts_dir)

    ref_mpn = {}
    for row in csv.DictReader(open(args.bom)):
        for ref in row["Designator"].split(","):
            ref_mpn[ref.strip()] = row.get("MPN", "")

    want = [r.strip() for r in args.refs.split(",") if r.strip()]
    made = []
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        pads = local_pads(fp)
        numbered = [p for p in pads if p["num"]]
        if want:
            if ref not in want:
                continue
        elif len(numbered) <= 3:
            continue
        for p in pads:
            p["side"] = side_of(p, numbered)
        mpn = ref_mpn.get(ref, "")
        ymap, ds, verified = {}, "(none)", ""
        ypath = parts / mpn / "part.yaml"
        if mpn and ypath.exists() and yaml:
            y = yaml.safe_load(open(ypath))
            ymap = {str(k): v for k, v in (y.get("pins") or {}).items()}
            d = y.get("datasheet") or {}
            pdfs = list((parts / mpn).glob("*.pdf"))
            ds = str(pdfs[0]) if pdfs else d.get("url", "(none)")
            verified = y.get("verified", "")
        lines = [
            f"# pin dossier: {ref}  ({mpn or 'MPN unknown'})",
            "",
            f"- footprint: {fp.GetFPID().GetUniStringLibId()}",
            f"- board position: ({fp.GetPosition().x/1e6:.1f}, {fp.GetPosition().y/1e6:.1f}) rot {fp.GetOrientationDegrees():.0f}",
            f"- computed winding of pins 1..N: **{winding(numbered)}**",
            f"- datasheet: {ds}",
            f"- part.yaml verification note: {verified or '(none)'}",
            "",
            "Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN",
            "(so this table reads like the top view of the part on the board).",
            "",
            "| pad | local (x,y) | side | size | function (part.yaml) | NET on board |",
            "|---|---|---|---|---|---|",
        ]
        seen = set()
        for p in sorted(numbered, key=lambda q: (len(q["num"]), q["num"])):
            fn = ymap.get(p["num"], "(not in yaml)")
            if isinstance(fn, dict):
                fn = fn.get("name", str(fn))
            seen.add(p["num"])
            lines.append(f"| {p['num']} | ({p['x']:+.2f},{p['y']:+.2f}) | {p['side']} "
                         f"| {p['w']}x{p['h']}{' THT' if p['tht'] else ''} | {fn} | {p['net']} |")
        missing = [k for k in ymap if k not in seen]
        if missing:
            lines += ["", f"part.yaml pins with NO pad on the footprint: {missing}"]
        anon = sum(1 for p in pads if not p["num"])
        if anon:
            lines += ["", f"({anon} unnumbered paste/mechanical pads not shown)"]
        (out / f"{ref}.md").write_text("\n".join(lines) + "\n")
        made.append(ref)
    print(f"dossiers: {len(made)} -> {out}  ({', '.join(made)})")


if __name__ == "__main__":
    main()
