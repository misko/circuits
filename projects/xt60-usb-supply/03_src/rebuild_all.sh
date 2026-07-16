#!/bin/bash
# THE entry point: regenerate everything from 03_src and gate it.
# Fresh-agent contract: final two lines of a green run are
#   violations: 0 {}
#   unconnected: 0
set -euo pipefail
cd "$(dirname "$0")/.."   # project root

PY=/usr/bin/python3       # KiCad-bundled (imports pcbnew)
B=04_kicad/xt60-usb-supply.kicad_pcb

mkdir -p 06_build/netlists 06_build/drc

echo "=== 1. schematic ==="
$PY 03_src/generate_schematic.py

echo "=== 2. netlist export ==="
kicad-cli sch export netlist -o 06_build/netlists/xt60-usb-supply.net \
  04_kicad/xt60-usb-supply.kicad_sch

echo "=== 3. netlist parity ==="
$PY 03_src/check_parity.py

echo "=== 4. board (placement + zones) ==="
$PY 03_src/generate_board.py

echo "=== 5. routing import + stitch + fill ==="
if [ -f 06_build/route/routed_final.kicad_pcb ]; then
  $PY 03_src/import_routing.py
else
  echo "(no routing artifact yet — board is placement-only)"
fi

echo "=== 6. placement/pad audit ==="
$PY 03_src/audit_board.py

echo "=== 7. rules LAST (pcbnew saves clobber .kicad_pro netclasses) ==="
python3 03_src/generate_rules.py

echo "=== 8. DRC gate ==="
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
  -o 06_build/drc/drc.rpt "$B"
$PY 03_src/drc_gate.py 06_build/drc/drc.rpt
