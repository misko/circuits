#!/usr/bin/env python3
"""Create a route-input project in 06_build/route/ (canon R1: rules ride
INTO the router).

History: this project's original route inputs (r0..r6) were made by ad-hoc
pcbnew saves, which write a bare default .kicad_pro — so KRT routed against
Default 0.2mm only and the width floors were enforced post-route by the DRC
gate (R-RULES FAIL, waived adopted-forward for the v1.1 release; see
03_src/rules/policy_waivers.yaml). ANY future route input must be produced
by THIS script instead.

What it does:
  1. copies the (track-free) board to 06_build/route/<name>.kicad_pcb;
  2. writes <name>.kicad_pro carrying the FULL net_settings (netclasses +
     patterns) and design-rule floors from 04_kicad/usb_power_3s.kicad_pro
     (which generate_rules.py maintains from 03_src/rules/nets.yaml);
  3. refuses a board that already has tracks or filled zones (KRT routes
     straight through existing copper — kicad-pcb golden rule 2).

Run: /usr/bin/python3 03_src/route_prep.py [name]   (default: r0)
"""
import json
import shutil
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
K = HERE.parent / "04_kicad"
OUT = HERE.parent / "06_build" / "route"
BOARD = K / "usb_power_3s.kicad_pcb"
PRO = K / "usb_power_3s.kicad_pro"

name = sys.argv[1] if len(sys.argv) > 1 else "r0"
OUT.mkdir(parents=True, exist_ok=True)

b = pcbnew.LoadBoard(str(BOARD))
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
if tracks:
    sys.exit(f"route_prep: board has {len(tracks)} tracks — KRT input must be "
             "track-free (regenerate the board without importing a route first)")
filled = [z.GetZoneName() or z.GetNetname() for z in b.Zones() if z.IsFilled()]
if filled:
    sys.exit(f"route_prep: board has FILLED zones {filled[:4]} — unfill before "
             "routing (KRT routes through existing copper)")

shutil.copy(BOARD, OUT / f"{name}.kicad_pcb")

pro = json.loads(PRO.read_text())
ns = pro.get("net_settings", {})
classes = [c.get("name") for c in ns.get("classes", [])]
if len(classes) <= 1:
    sys.exit(f"route_prep: 04_kicad project has only {classes} — run "
             "generate_rules.py first (canon R1: no routing without classes)")
route_pro = {
    "board": {"design_settings": pro.get("board", {}).get("design_settings", {})},
    "meta": {"filename": f"{name}.kicad_pro", "version": 3},
    "net_settings": ns,
}
(OUT / f"{name}.kicad_pro").write_text(json.dumps(route_pro, indent=2))
print(f"route_prep: wrote 06_build/route/{name}.kicad_pcb + .kicad_pro "
      f"(classes={classes})")
