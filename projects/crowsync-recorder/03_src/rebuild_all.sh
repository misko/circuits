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
# ERC gate (canon S1/S4): severity-all, ZERO errors. Warnings baselined:
# endpoint_off_grid only (generator places parts on a 1mm grid vs KiCad's
# 1.27mm connection grid; connectivity is global-label-based, so geometry
# cannot change the netlist — parity gate below proves it). Any NEW warning
# type fails the gate.
mkdir -p 06_build/erc
kicad-cli sch erc --severity-all --format json \
    -o 06_build/erc/gate.json 04_kicad/crowsync_recorder.kicad_sch >/dev/null
python3 - <<'PYEOF'
import json, sys
from collections import Counter
d = json.load(open('06_build/erc/gate.json'))
viols = [v for s in d['sheets'] for v in s['violations']]
errs = [v for v in viols if v['severity'] == 'error']
warn_types = Counter(v['type'] for v in viols if v['severity'] != 'error')
BASELINE = {'endpoint_off_grid'}   # reasons above
new = set(warn_types) - BASELINE
print(f"ERC: {len(errs)} errors, warnings {dict(warn_types)}")
for v in errs[:10]:
    print('  ERR', v['type'], [i.get('description') for i in v['items']])
sys.exit(1 if (errs or new) else 0)
PYEOF
kicad-cli sch export netlist -o 06_build/netlists/crowsync_recorder.net 04_kicad/crowsync_recorder.kicad_sch >/dev/null
$PY 03_src/generate_board.py 2>/dev/null | tail -1
$PY 03_src/audit_board.py 2>/dev/null | tail -1
# canonical route artifact is PROMOTED + git-tracked (canon M3)
mkdir -p 06_build/route
[ -f 06_build/route/r3.kicad_pcb ] || cp 03_src/route/r3.kicad_pcb 06_build/route/r3.kicad_pcb 2>/dev/null || true
[ -f 06_build/route/r3.kicad_pcb ] || { echo "no route chain: run 03_src/route_prep.py + 03_src/route_waves.sh"; exit 1; }
$PY "$SKILLS"/import_krt.py 06_build/route/r3.kicad_pcb \
    04_kicad/crowsync_recorder.kicad_pcb 04_kicad/crowsync_recorder.kicad_pcb 2>/dev/null | grep imported
$PY 03_src/stitch_and_fill.py 2>/dev/null | tail -3
python3 03_src/generate_rules.py
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --format json \
    -o 06_build/drc/gate.json 04_kicad/crowsync_recorder.kicad_pcb >/dev/null
python3 - <<'PYEOF'
import json
from collections import Counter
d = json.load(open('06_build/drc/gate.json'))
print('violations:', len(d['violations']), dict(Counter(v['type'] for v in d['violations'])))
print('unconnected:', len(d['unconnected_items']))
import sys
sys.exit(1 if (d['violations'] or d['unconnected_items']) else 0)
PYEOF
