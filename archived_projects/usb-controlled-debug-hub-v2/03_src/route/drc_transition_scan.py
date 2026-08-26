#!/usr/bin/env python3
"""Move one F/B transition through a grid and grade every candidate by DRC."""

from __future__ import annotations

import argparse
import gc
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pcbnew


# A routing checkpoint is intentionally incomplete.  Grade only geometry that
# a later wave cannot repair; dangling copper, library-context notices and
# unrelated opens are deferred exactly as route_and_stitch_generic does.
HARD_TYPES = {
    "annular_width", "board_edge", "clearance", "copper_edge_clearance",
    "diff_pair_uncoupled_length_too_long", "drill_out_of_range",
    "hole_clearance", "hole_to_hole", "shorting_items", "track_width",
    "through_hole_pad_without_hole", "tracks_crossing", "via_diameter",
    "via_in_pad",
}


def mm(point):
    return (round(pcbnew.ToMM(point.x), 6),
            round(pcbnew.ToMM(point.y), 6))


def values(start, stop, step):
    value = start
    while value <= stop + step / 10:
        yield round(value, 6)
        value += step


def add_track(board, net_code, layer, width, start, end):
    track = pcbnew.PCB_TRACK(board)
    track.SetNetCode(net_code)
    track.SetLayer(layer)
    track.SetWidth(pcbnew.FromMM(width))
    track.SetStart(pcbnew.VECTOR2I_MM(*start))
    track.SetEnd(pcbnew.VECTOR2I_MM(*end))
    board.Add(track)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board", type=Path)
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--dru", type=Path, required=True)
    ap.add_argument("--net", required=True)
    ap.add_argument("--junction", nargs=2, type=float, required=True)
    ap.add_argument("--x", nargs=3, type=float, required=True)
    ap.add_argument("--y", nargs=3, type=float, required=True)
    ap.add_argument("--width", type=float, default=.18)
    ap.add_argument("--via-size", type=float, default=.46)
    ap.add_argument("--via-drill", type=float, default=.20)
    args = ap.parse_args()

    original = pcbnew.LoadBoard(str(args.board))
    matches = [item for item in original.GetTracks()
               if item.GetNetname() == args.net]
    if not matches:
        raise SystemExit(f"unknown net: {args.net}")
    net_code = matches[0].GetNetCode()
    # Keep the source board alive while candidate boards are loaded.  KiCad
    # 10's SWIG ownership can invalidate a subsequent LoadBoard result when
    # the first board is explicitly collected in the same process.
    del matches
    junction = tuple(args.junction)
    clean = []
    best = None
    with tempfile.TemporaryDirectory(prefix="drc-transition-") as raw:
        tmp = Path(raw)
        for x in values(*args.x):
            for y in values(*args.y):
                board = pcbnew.LoadBoard(str(args.board))
                removed = False
                for item in list(board.GetTracks()):
                    if (item.GetNetname() == args.net
                            and isinstance(item, pcbnew.PCB_VIA)
                            and mm(item.GetPosition()) == junction):
                        board.Remove(item)
                        removed = True
                if not removed:
                    raise SystemExit(f"no {args.net} via at {junction}")
                candidate = (x, y)
                add_track(board, net_code, pcbnew.F_Cu, args.width,
                          junction, candidate)
                add_track(board, net_code, pcbnew.B_Cu, args.width,
                          junction, candidate)
                via = pcbnew.PCB_VIA(board)
                via.SetNetCode(net_code)
                via.SetPosition(pcbnew.VECTOR2I_MM(*candidate))
                via.SetWidth(pcbnew.FromMM(args.via_size))
                via.SetDrill(pcbnew.FromMM(args.via_drill))
                via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                board.Add(via)
                stem = f"candidate_{x:.3f}_{y:.3f}"
                pcb = tmp / f"{stem}.kicad_pcb"
                report = tmp / f"{stem}.json"
                pcbnew.SaveBoard(str(pcb), board)
                shutil.copy2(args.project, pcb.with_suffix(".kicad_pro"))
                shutil.copy2(args.dru, pcb.with_suffix(".kicad_dru"))
                subprocess.run(
                    ["kicad-cli", "pcb", "drc", "--format", "json",
                     "--output", str(report), str(pcb)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    check=False,
                )
                errors = [v for v in json.loads(report.read_text())
                          .get("violations", [])
                          if v.get("type") in HARD_TYPES]
                if best is None or len(errors) < best[0]:
                    best = [len(errors), x, y,
                            [[v.get("type"), v.get("description")]
                             for v in errors]]
                if not errors:
                    clean.append([x, y])
                    print(f"CLEAN {x:.3f} {y:.3f}", flush=True)
    print(json.dumps({"net": args.net, "clean": clean, "best": best},
                     indent=2))
    return 0 if clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
