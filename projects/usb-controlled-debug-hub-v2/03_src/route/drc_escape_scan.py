#!/usr/bin/env python3
"""Scan legal off-pad via locations using the project's real KiCad DRC.

This is a diagnostic aid for dense fanout.  It never edits the input board:
each candidate is added to a temporary copy, checked with the matching project
and DRU sidecars, and discarded unless requested by the caller.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pcbnew


def frange(start: float, stop: float, step: float):
    value = start
    while value <= stop + step / 10:
        yield round(value, 6)
        value += step


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("board", type=Path)
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--dru", type=Path, required=True)
    ap.add_argument("--net", required=True)
    ap.add_argument("--start", nargs=2, type=float, required=True,
                    metavar=("X", "Y"))
    ap.add_argument("--x", nargs=3, type=float, required=True,
                    metavar=("START", "STOP", "STEP"))
    ap.add_argument("--y", nargs=3, type=float, required=True,
                    metavar=("START", "STOP", "STEP"))
    ap.add_argument("--width", type=float, default=0.18)
    ap.add_argument("--via-size", type=float, default=0.41)
    ap.add_argument("--via-drill", type=float, default=0.15)
    args = ap.parse_args()

    source = pcbnew.LoadBoard(str(args.board))
    net = source.FindNet(args.net)
    if net is None:
        raise SystemExit(f"unknown net: {args.net}")

    clean = []
    best = None
    with tempfile.TemporaryDirectory(prefix="drc-escape-") as raw_tmp:
        tmp = Path(raw_tmp)
        for x in frange(*args.x):
            for y in frange(*args.y):
                board = pcbnew.LoadBoard(str(args.board))
                track = pcbnew.PCB_TRACK(board)
                track.SetNetCode(net.GetNetCode())
                track.SetLayer(pcbnew.F_Cu)
                track.SetWidth(pcbnew.FromMM(args.width))
                track.SetStart(pcbnew.VECTOR2I_MM(*args.start))
                track.SetEnd(pcbnew.VECTOR2I_MM(x, y))
                board.Add(track)

                via = pcbnew.PCB_VIA(board)
                via.SetNetCode(net.GetNetCode())
                via.SetPosition(pcbnew.VECTOR2I_MM(x, y))
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
                data = json.loads(report.read_text())
                errors = [v for v in data.get("violations", [])
                          if v.get("severity") == "error"]
                if best is None or len(errors) < best[0]:
                    best = (len(errors), x, y, [
                        {"type": v.get("type"),
                         "description": v.get("description")}
                        for v in errors
                    ])
                if not errors:
                    clean.append([x, y])
                    print(f"CLEAN {x:.3f} {y:.3f}", flush=True)

    print(json.dumps({"net": args.net, "clean": clean, "best": best},
                     indent=2))
    return 0 if clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
