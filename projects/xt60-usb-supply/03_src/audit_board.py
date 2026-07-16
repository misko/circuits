#!/usr/bin/env python3
"""Placement/pad invariant gate (I1-I7) — wraps the skills audit template
with this project's config, adds project-specific checks:
  - no tracks on In1.Cu (solid GND plane contract, ARCHITECTURE.md)
  - proximity gates (decouplers/FB near their ICs, ESD near ports)
Prints AUDIT: PASS on success; exits nonzero otherwise."""
import json
import math
import subprocess
import sys
from pathlib import Path

import pcbnew

PROJ = Path(__file__).resolve().parent.parent
BOARD = PROJ / "04_kicad" / "xt60-usb-supply.kicad_pcb"
SKILLS = PROJ.parent.parent / "skills"
AUDIT = SKILLS / "kicad-pcb" / "scripts" / "audit_template.py"
CFG = PROJ / "03_src" / "rules" / "audit.json"

# (satellite, anchor, budget_mm) — placement-and-proximity.md
PROXIMITY = [
    ("CIN_A1", "U1", 6.0), ("CIN_A2", "U1", 6.0),
    ("CIN_C1", "U2", 6.0), ("CIN_C2", "U2", 6.0),
    ("CVCC_A", "U1", 5.0), ("CVCC_C", "U2", 5.0),
    ("CBS_A", "U1", 6.0), ("CBS_C", "U2", 6.0),
    ("RFA1", "U1", 10.0), ("RFA2", "U1", 10.0),
    ("RFC1", "U2", 10.0), ("RFC2", "U2", 10.0),
    ("U3", "J2", 12.0), ("U4", "J3", 12.0), ("U5", "J4", 12.0),
    ("U6", "J5", 12.0), ("R3", "J5", 15.0), ("R4", "J5", 15.0),
    ("D1", "Q1", 20.0), ("CB1", "Q1", 25.0), ("CB2", "Q1", 25.0),
]


def main():
    fails = []

    # I1-I7 via template
    r = subprocess.run([sys.executable, str(AUDIT), str(BOARD),
                        "--config", str(CFG)],
                       capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        fails.append("audit_template (I1-I7)")

    board = pcbnew.LoadBoard(str(BOARD))

    # no tracks on In1
    in1 = board.GetLayerID("In1.Cu")
    bad = [t for t in board.GetTracks() if t.GetLayer() == in1
           and t.GetClass() != "PCB_VIA"]
    if bad:
        fails.append(f"{len(bad)} tracks on In1.Cu (must stay a solid plane)")
    else:
        print("IN1_CLEAN: PASS")

    # proximity
    pos = {fp.GetReference(): fp.GetPosition() for fp in board.GetFootprints()}
    for sat, anchor, budget in PROXIMITY:
        if sat not in pos or anchor not in pos:
            fails.append(f"proximity: missing {sat}/{anchor}")
            continue
        d = math.hypot((pos[sat].x - pos[anchor].x) / 1e6,
                       (pos[sat].y - pos[anchor].y) / 1e6)
        if d > budget:
            fails.append(f"proximity: {sat} is {d:.1f}mm from {anchor} (budget {budget})")
    if not any(f.startswith("proximity") for f in fails):
        print(f"PROXIMITY: PASS ({len(PROXIMITY)} pairs)")

    if fails:
        print("AUDIT: FAIL")
        for f in fails:
            print(" -", f)
        sys.exit(1)
    print("AUDIT: PASS")


if __name__ == "__main__":
    main()
