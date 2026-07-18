#!/bin/bash
# Full regenerate -> import -> stitch -> rules -> gate chain.
# set -euo pipefail: ANY stage failure stops the chain.
# KRT re-route (03_src/route_prep.py + 03_src/route_waves.sh) is only needed
# when the netlist/placement changes; the chain imports the PROMOTED
# 03_src/route/final.kicad_pcb (canon M3).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=/usr/bin/python3
SKILLS="$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd)/skills/kicad-pcb/scripts"
[ -d "$SKILLS" ] || SKILLS="$HOME/.claude/skills/kicad-pcb/scripts"
mkdir -p 06_build/netlists 06_build/drc 06_build/route
python3 03_src/make_lib.py | tail -1
python3 03_src/generate_schematic.py | tail -1
kicad-cli sch export netlist -o 06_build/netlists/crow_array_central.net 04_kicad/crow_array_central.kicad_sch >/dev/null
# ERC gate: 0 violations at severity-all
kicad-cli sch erc --severity-all --format json -o 06_build/drc/erc.json 04_kicad/crow_array_central.kicad_sch >/dev/null
python3 - <<'PYEOF'
import json, sys
d = json.load(open('06_build/drc/erc.json'))
v = [x for s in d['sheets'] for x in s['violations']]
print(f'ERC: {len(v)} violations')
sys.exit(1 if v else 0)
PYEOF
$PY 03_src/generate_board.py 2>/dev/null | tail -1
$PY 03_src/audit_board.py 2>/dev/null | tail -1
# canonical route artifact is PROMOTED + git-tracked (canon M3)
[ -f 06_build/route/final.kicad_pcb ] || cp 03_src/route/final.kicad_pcb 06_build/route/final.kicad_pcb 2>/dev/null || true
[ -f 06_build/route/final.kicad_pcb ] || { echo "no route chain: run 03_src/route_prep.py + 03_src/route_waves.sh"; exit 1; }
$PY "$SKILLS"/import_krt.py 06_build/route/final.kicad_pcb \
    04_kicad/crow_array_central.kicad_pcb 04_kicad/crow_array_central.kicad_pcb 2>/dev/null | grep imported
# rules BEFORE stitch: the stitcher's internal checks + fill honor the floors
python3 03_src/generate_rules.py >/dev/null
$PY 03_src/stitch_and_fill.py 2>/dev/null | tail -3
# audit again post-route (I8 AIN length needs tracks)
$PY 03_src/audit_board.py 2>/dev/null | tail -2
# rules LAST: pcbnew saves clobber .kicad_pro netclasses
python3 03_src/generate_rules.py
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --format json \
    -o 06_build/drc/gate.json 04_kicad/crow_array_central.kicad_pcb >/dev/null
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
