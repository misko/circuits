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
import hashlib
import math
import re
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


def datasheet_path(part_dir, declared):
    """Resolve the vendored PDF by its declared digest, never directory order.

    A dossier once selected the older non-automotive PDF merely because it
    sorted first beside the exact Q-grade authority. Fresh review must see
    the bytes whose digest part.yaml actually asserts. A URL, a sole PDF, or
    an adjacent family document is not review evidence: fail before dossiers
    are commissioned if the authority is absent or its bytes do not match.
    """
    want = str((declared or {}).get("sha256") or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", want):
        raise RuntimeError(
            f"P-AUTH {part_dir}: datasheet.sha256 is missing or malformed; "
            "fresh pin review requires a digest-selected local PDF")
    pdfs = sorted(part_dir.glob("*.pdf"))
    for pdf in pdfs:
        if hashlib.sha256(pdf.read_bytes()).hexdigest().lower() == want:
            return str(pdf)
    raise RuntimeError(
        f"P-AUTH {part_dir}: no local PDF matches declared SHA-256 {want}; "
        f"found {len(pdfs)} PDF(s)")


def part_authority(parts_dir, exact_mpn):
    """Return ``(part_dir, parsed_part_yaml)`` for one exact BOM MPN.

    An exact orderable MPN can contain characters that cannot safely be used
    as one directory component (for example ``MCP2221A-I/SL``), so directory
    spelling is not identity.  Resolve through the dossier's authoritative
    ``mpn:`` field, never through punctuation stripping or another fuzzy
    normalization.  The directory name remains the compatibility fallback
    only for older dossiers that omit ``mpn:``.

    Duplicate exact identities are an ambiguity and therefore a hard
    P-AUTH failure.  This deliberately scans the small dossier tree instead
    of guessing which filesystem-safe spelling an author intended.
    """
    parts_dir = Path(parts_dir)
    if yaml is None:
        raise RuntimeError("P-AUTH: PyYAML is required to resolve exact MPN dossiers")
    matches = []
    for ypath in sorted(parts_dir.glob("*/part.yaml")):
        try:
            data = yaml.safe_load(ypath.read_text(encoding="utf-8-sig")) or {}
        except Exception as exc:  # noqa: BLE001 - surface the exact bad authority
            raise RuntimeError(f"P-AUTH {ypath}: cannot parse part.yaml: {exc}") from exc
        if not isinstance(data, dict):
            raise RuntimeError(f"P-AUTH {ypath}: part.yaml must contain a mapping")
        declared_mpn = str(data.get("mpn") or ypath.parent.name).strip()
        if declared_mpn == exact_mpn:
            matches.append((ypath.parent, data))
    if not matches:
        raise RuntimeError(
            f"P-AUTH {parts_dir}: exact BOM MPN {exact_mpn!r} resolves to no "
            "part.yaml `mpn:` identity")
    if len(matches) != 1:
        paths = ", ".join(str(part_dir / "part.yaml") for part_dir, _ in matches)
        raise RuntimeError(
            f"P-AUTH {parts_dir}: exact BOM MPN {exact_mpn!r} is ambiguous "
            f"across {len(matches)} dossiers: {paths}")
    return matches[0]


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
    for row in csv.DictReader(open(args.bom, encoding="utf-8-sig")):
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
        ymap, aliases, ds, verified = {}, {}, "(none)", ""
        if mpn:
            part_dir, y = part_authority(parts, mpn)
            ymap = {str(k): v for k, v in (y.get("pins") or {}).items()}
            aliases = {str(k): v for k, v in (y.get("pin_aliases") or {}).items()}
            d = y.get("datasheet") or {}
            ds = datasheet_path(part_dir, d)
            verified = y.get("verified", "")
        physical_map = dict(ymap)
        semantic_seen = set()
        alias_targets = set()
        for semantic, spec in aliases.items():
            if not isinstance(spec, dict) or not spec.get("footprint"):
                continue
            target = str(spec["footprint"])
            alias_targets.add(target)
            if semantic in ymap:
                physical_map[target] = ymap[semantic]
        winding_pads = [p for p in numbered
                        if p["num"] in physical_map and p["num"] not in alias_targets]
        lines = [
            f"# pin dossier: {ref}  ({mpn or 'MPN unknown'})",
            "",
            f"- footprint: {fp.GetFPID().GetUniStringLibId()}",
            f"- board position: ({fp.GetPosition().x/1e6:.1f}, {fp.GetPosition().y/1e6:.1f}) rot {fp.GetOrientationDegrees():.0f}",
            f"- computed winding of pins 1..N: **{winding(winding_pads)}**",
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
            fn = physical_map.get(p["num"], "(not in yaml)")
            if isinstance(fn, dict):
                fn = fn.get("name", str(fn))
            seen.add(p["num"])
            for semantic, spec in aliases.items():
                if isinstance(spec, dict) and str(spec.get("footprint", "")) == p["num"]:
                    semantic_seen.add(semantic)
            lines.append(f"| {p['num']} | ({p['x']:+.2f},{p['y']:+.2f}) | {p['side']} "
                         f"| {p['w']}x{p['h']}{' THT' if p['tht'] else ''} | {fn} | {p['net']} |")
        if aliases:
            lines += ["", "Declared pin aliases (review these against the manufacturer drawing):"]
            for semantic, spec in sorted(aliases.items()):
                if isinstance(spec, dict):
                    lines.append(
                        f"- `{semantic}`: schematic `{spec.get('schematic', '')}`, "
                        f"footprint `{spec.get('footprint', '')}`, "
                        f"fused: `{str(bool(spec.get('fused', False))).lower()}`; "
                        f"why: {spec.get('why', '(none)')}; evidence: {spec.get('evidence', '(none)')}"
                    )
        missing = [k for k in ymap if k not in seen and k not in semantic_seen]
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
