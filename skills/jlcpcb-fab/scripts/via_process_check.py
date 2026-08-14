#!/usr/bin/env python3
"""Grade selective IPC-4761 via intent against the exact KiCad board.

    /usr/bin/python3 via_process_check.py BOARD.kicad_pcb
        [--assembly 03_src/rules/assembly.yaml] [--json OUT]

KiCad can store capping/filling per via, but a Gerber order does not carry
those native item attributes.  A selective process therefore needs a
fabricator-visible selector.  This gate uses the drill family declared in
``assembly.yaml`` and proves both directions:

* every protected drill is Type VII filled+capped at the declared geometry;
* every ordinary drill is unprotected and belongs to the declared ordinary
  family.

The order remark is also graded because it is the instruction the fabricator
actually receives.  DRC cannot establish any of these manufacturing facts.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pcbnew

try:
    import yaml
except ImportError:
    sys.exit("V-PROCESS: PyYAML is required")


TOL_MM = 0.0015


def find_assembly(board_path: Path, explicit: str | None = None):
    if explicit:
        path = Path(explicit).resolve()
        return path
    board_path = board_path.resolve()
    for anc in [board_path.parent, *board_path.parents]:
        candidate = anc / "03_src" / "rules" / "assembly.yaml"
        if candidate.is_file():
            return candidate
    return None


def load_assembly(board_path: Path, explicit: str | None = None):
    path = find_assembly(board_path, explicit)
    if path is None or not path.is_file():
        return {}, path
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a mapping")
    return data, path


def via_order_note(data: dict, source: Path | None = None) -> str | None:
    process = data.get("via_process")
    if not isinstance(process, dict):
        return None
    remark = str(process.get("order_remark") or "").strip()
    if not remark:
        return None
    origin = source.as_posix() if source else "assembly.yaml"
    confirm = bool(process.get("uploader_confirmation_required"))
    return (
        "JLCPCB VIA PROCESS — GENERATED; DO NOT RE-TYPE\n"
        f"Source: {origin}\n"
        f"Order remark: {remark}\n"
        "Uploader confirmation required: " + ("YES" if confirm else "NO")
        + "\n"
    )


def close(a, b):
    return abs(float(a) - float(b)) <= TOL_MM


def via_in_pad_hits(board):
    """Map via UUIDs to exact undrilled component lands containing them.

    Same-net via/pad overlap is intentionally DRC-clean, but an open barrel
    beneath an SMT paste aperture is not assembly-neutral.  Use KiCad's exact
    pad hit-test rather than a rectangular approximation and require every
    such barrel to belong to the declared filled/capped process.
    """
    copper_layers = [layer for layer in board.GetEnabledLayers().Seq()
                     if pcbnew.IsCopperLayer(layer)]
    pads = []
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if (pad.GetDrillSize().x > 0
                    or not any(pad.IsOnLayer(layer)
                               for layer in copper_layers)):
                continue
            pads.append((footprint.GetReference(), pad,
                         pad.GetBoundingBox()))
    out = {}
    for via in board.GetTracks():
        if via.GetClass() != "PCB_VIA":
            continue
        pos = via.GetPosition()
        hits = [f"{ref}.{pad.GetNumber()}"
                for ref, pad, bbox in pads
                if bbox.Contains(pos) and pad.HitTest(pos)]
        if hits:
            out[via.m_Uuid.AsString()] = hits
    return out


def _mm(value, path, fails):
    try:
        value = float(value)
    except (TypeError, ValueError):
        fails.append(f"V-SCHEMA {path}: expected a number, got {value!r}")
        return None
    if value <= 0:
        fails.append(f"V-SCHEMA {path}: must be positive, got {value}")
        return None
    return value


def check(board_path: Path, assembly: str | None = None):
    data, apath = load_assembly(board_path, assembly)
    board = pcbnew.LoadBoard(str(board_path))
    vip_hits = via_in_pad_hits(board)
    protected_without_contract = [
        item for item in board.GetTracks()
        if item.GetClass() == "PCB_VIA"
        and (item.GetCappingMode() == pcbnew.CAPPING_MODE_CAPPED
             or item.GetFillingMode() == pcbnew.FILLING_MODE_FILLED)
    ]
    out = {
        "board": str(board_path), "assembly": str(apath) if apath else None,
        "fails": [], "oks": [], "coverage": {}, "na": None, "census": {},
    }
    vp = data.get("via_process")
    if vp is None:
        if vip_hits or protected_without_contract:
            out["fails"].append(
                "V-SCHEMA assembly.yaml declares no via_process although "
                f"the board has {len(vip_hits)} via-in-pad site(s) and "
                f"{len(protected_without_contract)} via(s) carrying native "
                "fill/cap flags")
        else:
            out["na"] = "V-PROCESS N-A: assembly.yaml declares no via_process"
        return out
    if not isinstance(vp, dict):
        out["fails"].append("V-SCHEMA via_process: expected a mapping")
        return out

    geom = vp.get("protected_geometry")
    selector = vp.get("fabricator_selector")
    if not isinstance(geom, dict):
        out["fails"].append(
            "V-SCHEMA via_process.protected_geometry: expected a mapping")
        geom = {}
    if not isinstance(selector, dict):
        out["fails"].append(
            "V-SCHEMA via_process.fabricator_selector: expected a mapping")
        selector = {}

    size = _mm(geom.get("via_diameter_mm"),
               "via_process.protected_geometry.via_diameter_mm", out["fails"])
    drill = _mm(geom.get("drill_mm"),
                "via_process.protected_geometry.drill_mm", out["fails"])
    kind = selector.get("kind")
    if kind != "drill_family":
        out["fails"].append(
            "V-SCHEMA via_process.fabricator_selector.kind: must be "
            "'drill_family' because Gerber order remarks cannot select native "
            "KiCad per-via flags")
    protected_drill = _mm(
        selector.get("protected_drill_mm"),
        "via_process.fabricator_selector.protected_drill_mm", out["fails"])
    ordinary = selector.get("ordinary_drill_mm")
    if not isinstance(ordinary, list) or not ordinary:
        out["fails"].append(
            "V-SCHEMA via_process.fabricator_selector.ordinary_drill_mm: "
            "expected a non-empty list")
        ordinary_drills = []
    else:
        ordinary_drills = [
            value for i, raw in enumerate(ordinary)
            if (value := _mm(
                raw,
                f"via_process.fabricator_selector.ordinary_drill_mm[{i}]",
                out["fails"])) is not None
        ]
    if drill is not None and protected_drill is not None and not close(
            drill, protected_drill):
        out["fails"].append(
            f"V-SCHEMA protected geometry drill {drill:g}mm disagrees with "
            f"fabricator selector {protected_drill:g}mm")
    if protected_drill is not None and any(
            close(protected_drill, value) for value in ordinary_drills):
        out["fails"].append(
            "V-SCHEMA protected and ordinary drill families overlap")

    remark = str(vp.get("order_remark") or "").strip()
    if not remark:
        out["fails"].append("V-ORDER via_process.order_remark is missing")
    else:
        low = remark.lower()
        for word in ("fill", "cap"):
            if word not in low:
                out["fails"].append(
                    f"V-ORDER order_remark does not name {word!r}")
        if protected_drill is not None and f"{protected_drill:.2f}" not in remark:
            out["fails"].append(
                f"V-ORDER order_remark does not name protected "
                f"{protected_drill:.2f} mm drill family")
        for value in ordinary_drills:
            if f"{value:.2f}" not in remark:
                out["fails"].append(
                    f"V-ORDER order_remark does not name ordinary "
                    f"{value:.2f} mm drill family")
    if vp.get("uploader_confirmation_required") is not True:
        out["fails"].append(
            "V-ORDER uploader_confirmation_required must be true for a "
            "selective via process")

    protected = ordinary_count = partial = 0
    census = {}
    for item in board.GetTracks():
        if item.GetClass() != "PCB_VIA":
            continue
        diameter = pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu))
        hole = pcbnew.ToMM(item.GetDrill())
        capped = item.GetCappingMode() == pcbnew.CAPPING_MODE_CAPPED
        filled = item.GetFillingMode() == pcbnew.FILLING_MODE_FILLED
        key = f"{diameter:.3f}/{hole:.3f};cap={int(capped)};fill={int(filled)}"
        census[key] = census.get(key, 0) + 1
        pos = item.GetPosition()
        where = (f"{item.GetNetname() or '(no net)'} at "
                 f"({pcbnew.ToMM(pos.x):.3f},{pcbnew.ToMM(pos.y):.3f})")
        pads = vip_hits.get(item.m_Uuid.AsString(), [])
        if pads and not (capped and filled):
            out["fails"].append(
                f"V-VIP {where}: ordinary/unprotected via is centred in "
                f"SMT land(s) {', '.join(pads)}; declare and realize a "
                "filled+capped process or move the via")
        if capped != filled:
            partial += 1
            out["fails"].append(
                f"V-FLAGS {where}: partial Type-VII state "
                f"cap={int(capped)} fill={int(filled)}")
            continue
        if capped and filled:
            protected += 1
            if size is not None and drill is not None and not (
                    close(diameter, size) and close(hole, drill)):
                out["fails"].append(
                    f"V-GEOM {where}: protected via is "
                    f"{diameter:.3f}/{hole:.3f}mm, expected "
                    f"{size:.3f}/{drill:.3f}mm")
            if protected_drill is not None and not close(hole, protected_drill):
                out["fails"].append(
                    f"V-SELECT {where}: protected via is outside the "
                    f"{protected_drill:.3f}mm drill family")
        else:
            ordinary_count += 1
            if protected_drill is not None and close(hole, protected_drill):
                out["fails"].append(
                    f"V-SELECT {where}: ordinary via shares protected "
                    f"{protected_drill:.3f}mm drill family")
            elif ordinary_drills and not any(close(hole, x) for x in ordinary_drills):
                out["fails"].append(
                    f"V-SELECT {where}: ordinary {hole:.3f}mm drill is not in "
                    f"declared families {ordinary_drills}")

    total = protected + ordinary_count + partial
    out["census"] = census
    out["coverage"] = {
        "V-FLAGS": f"{total}/{total} vias graded",
        "V-SELECT": f"{total}/{total} vias compared with drill families",
        "V-VIP": f"{len(vip_hits)}/{len(vip_hits)} via-in-pad sites graded",
    }
    if total == 0:
        out["fails"].append(
            "V-COVER: via_process is declared but the exact board has 0 vias")
    if protected == 0:
        out["fails"].append(
            "V-COVER: via_process is declared but 0 protected vias were found")
    if not out["fails"]:
        out["oks"].append(
            f"V-PROCESS {protected} protected / {ordinary_count} ordinary / "
            f"{partial} partial; process families are drill-disjoint")
        out["oks"].append("V-ORDER exact generated order remark is complete")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("--assembly")
    ap.add_argument("--json")
    args = ap.parse_args(argv)
    result = check(Path(args.board), args.assembly)
    if args.json:
        json_path = Path(args.json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result, indent=2) + "\n")
    if result.get("na"):
        print(result["na"])
        return 0
    for name, value in result["coverage"].items():
        print(f"  coverage {name}: {value}")
    for key, count in sorted(result["census"].items()):
        print(f"  census {count:3d} x {key}")
    for value in result["oks"]:
        print(f"  ok   {value}")
    for value in result["fails"]:
        print(f"  FAIL {value}")
    if result["fails"]:
        print(f"V-PROCESS FAIL: {len(result['fails'])} finding(s)")
        return 1
    print("V-PROCESS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
