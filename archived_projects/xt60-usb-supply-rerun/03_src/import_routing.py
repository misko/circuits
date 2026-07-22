#!/usr/bin/env python3
"""Import the final KRT routing chain file (06_build/route/routed_final.kicad_pcb)
into the freshly generated board, refill zones, save. Runs inside
rebuild_all.sh step 5 only when the artifact exists.

The chain file is COMMITTED-adjacent build state: rebuilding from a clean
clone without it leaves a placement-only board (documented in
03_src/contracts.md pipeline notes). Routing regeneration procedure lives
in 03_src/route_board.sh."""
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
BOARD = PROJ / "04_kicad" / "xt60-usb-supply.kicad_pcb"
KRT_OUT = PROJ / "03_src" / "route" / "routed_final.kicad_pcb"
SKILLS = PROJ.parent.parent / "skills" / "kicad-pcb" / "scripts"

r = subprocess.run([sys.executable, str(SKILLS / "import_krt.py"),
                    str(KRT_OUT), str(BOARD), str(BOARD)],
                   text=True, capture_output=True)
sys.stdout.write(r.stdout)
sys.stderr.write(r.stderr)
if r.returncode != 0:
    raise SystemExit("ERROR: routing import failed")
print("ROUTING: imported", KRT_OUT.name)
