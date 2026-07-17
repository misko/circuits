#!/bin/bash
# Full regenerate -> import -> stitch -> rules -> gate chain.
# set -euo pipefail: ANY stage failure stops the chain.
# KRT re-route (03_src/route_prep.py + 03_src/route_waves.sh) is only needed
# when the netlist/placement changes; the chain imports 06_build/route/r3.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=/usr/bin/python3
SKILLS="$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd)/skills/kicad-pcb/scripts"
[ -d "$SKILLS" ] || SKILLS="$HOME/.claude/skills/kicad-pcb/scripts"
mkdir -p 06_build/netlists 06_build/drc
python3 03_src/generate_schematic.py | tail -1
kicad-cli sch export netlist -o 06_build/netlists/esp32_laser_timing.net 04_kicad/esp32_laser_timing.kicad_sch >/dev/null
# ERC gate (P11 deliverable): 0 violations at severity-all
kicad-cli sch erc --severity-all --format json -o 06_build/drc/erc.json 04_kicad/esp32_laser_timing.kicad_sch >/dev/null
python3 - <<'PYEOF'
import json, sys
d = json.load(open('06_build/drc/erc.json'))
v = [x for s in d['sheets'] for x in s['violations']]
print(f'ERC: {len(v)} violations')
sys.exit(1 if v else 0)
PYEOF
$PY 03_src/generate_board.py 2>/dev/null | tail -1
$PY 03_src/audit_board.py 2>/dev/null | tail -1
[ -f 06_build/route/r3.kicad_pcb ] || { echo "no route chain: run 03_src/route_prep.py + 03_src/route_waves.sh"; exit 1; }
$PY "$SKILLS"/import_krt.py 06_build/route/r3.kicad_pcb \
    04_kicad/esp32_laser_timing.kicad_pcb 04_kicad/esp32_laser_timing.kicad_pcb 2>/dev/null | grep imported
$PY 03_src/fix_usb_dive.py 2>/dev/null | tail -1
$PY 03_src/stitch_and_fill.py 2>/dev/null | tail -3
# rules BEFORE repair too: repair's internal DRC needs the pro-file floors
# (hole/connection constraints live in .kicad_pro and pcbnew saves clobber it)
python3 03_src/generate_rules.py >/dev/null
# repair iterates: a nudge can shift a conflict to a neighbour (max 4 passes)
for _pass in 1 2 3 4; do
    OUT=$($PY 03_src/repair_drc.py 2>/dev/null | tail -2)
    echo "$OUT"
    echo "$OUT" | grep -q "remain" || break
done
# audit again post-route (I8 COMP length spread needs tracks)
$PY 03_src/audit_board.py 2>/dev/null | tail -2
python3 03_src/generate_rules.py
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --format json \
    -o 06_build/drc/gate.json 04_kicad/esp32_laser_timing.kicad_pcb >/dev/null
python3 - <<'PYEOF'
import json
from collections import Counter
d = json.load(open('06_build/drc/gate.json'))
print('violations:', len(d['violations']), dict(Counter(v['type'] for v in d['violations'])))
print('unconnected:', len(d['unconnected_items']))
print('parity:', len(d.get('schematic_parity', [])))
import sys
sys.exit(1 if (d['violations'] or d['unconnected_items'] or d.get('schematic_parity')) else 0)
PYEOF
