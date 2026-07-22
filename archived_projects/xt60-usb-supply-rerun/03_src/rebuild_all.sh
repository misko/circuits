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

echo "=== 1b. ERC gate (canon S1/S4: severity-all, ZERO errors) ==="
# Warnings baselined: isolated_pin_label on the four deliberate NC_* nets
# only (NC_U1_PG, NC_U2_PG, NC_J5_SBU1, NC_J5_SBU2 — per-pad NC nets that
# ALSO exist on board pads; replacing the labels with no_connect flags
# would delete the nets and break netlist parity). Any error or any new
# warning type fails the gate.
mkdir -p 06_build/erc
kicad-cli sch erc --severity-all --format json \
  -o 06_build/erc/gate.json 04_kicad/xt60-usb-supply.kicad_sch >/dev/null
$PY - <<'PYEOF'
import json, sys
from collections import Counter
d = json.load(open('06_build/erc/gate.json'))
viols = [v for s in d['sheets'] for v in s['violations']]
errs = [v for v in viols if v['severity'] == 'error']
warn_types = Counter(v['type'] for v in viols if v['severity'] != 'error')
BASELINE = {'isolated_pin_label'}   # NC_* one-pin nets, reasons above
new = set(warn_types) - BASELINE
print(f"ERC: {len(errs)} errors, warnings {dict(warn_types)}")
for v in errs[:10]:
    print('  ERR', v['type'], [i.get('description') for i in v['items']])
sys.exit(1 if (errs or new) else 0)
PYEOF

echo "=== 2. netlist export ==="
kicad-cli sch export netlist -o 06_build/netlists/xt60-usb-supply.net \
  04_kicad/xt60-usb-supply.kicad_sch

echo "=== 3. netlist parity ==="
$PY 03_src/check_parity.py

echo "=== 4. board (placement + zones) ==="
$PY 03_src/generate_board.py

echo "=== 5. routing import + stitch + fill ==="
if [ -f 03_src/route/routed_final.kicad_pcb ]; then
  $PY 03_src/import_routing.py
else
  echo "(no routing artifact yet — board is placement-only)"
fi
$PY 03_src/stitch_and_fill.py

echo "=== 6. placement/pad audit ==="
$PY 03_src/audit_board.py

echo "=== 7. rules LAST (pcbnew saves clobber .kicad_pro netclasses) ==="
python3 03_src/generate_rules.py

echo "=== 8. DRC gate ==="
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
  -o 06_build/drc/drc.rpt "$B"
$PY 03_src/drc_gate.py 06_build/drc/drc.rpt
