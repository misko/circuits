#!/bin/bash
# Full RE-ROUTE chain (placement changed -> KRT must re-route from scratch).
# generate_board -> audit -> route_prep -> route_waves -> import r2 ->
# route_bank -> rules -> stitch -> audit -> rules -> DRC.  (schematic is SEALED;
# not regenerated here — parity is re-checked by the final DRC.)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=/usr/bin/python3
SKILLS="$HOME/.claude/skills/kicad-pcb/scripts"
mkdir -p 06_build/netlists 06_build/drc 06_build/route
echo "== generate_board =="; $PY 03_src/generate_board.py 2>/dev/null | tail -1
echo "== audit(pre) ==";     $PY 03_src/audit_board.py 2>/dev/null | tail -3
echo "== route_prep =="; $PY 03_src/route_prep.py
echo "== route_waves =="
rm -f 06_build/route/r2.kicad_pcb
bash 03_src/route_waves.sh 2>&1 | tail -6
echo "== import r2 =="
$PY "$SKILLS"/import_krt.py 06_build/route/r2.kicad_pcb \
    04_kicad/cook_hub.kicad_pcb 04_kicad/cook_hub.kicad_pcb 2>/dev/null | grep imported
echo "== route_bank =="; $PY 03_src/route_bank.py 2>/dev/null | tail -2
$PY 03_src/generate_rules.py >/dev/null
echo "== stitch_and_fill =="
$PY 03_src/stitch_and_fill.py > 06_build/stitch.log 2>&1 || { echo "STITCH FAILED:"; tail -25 06_build/stitch.log; exit 1; }
grep -vE 'swig|memory leak|Debug:|assert' 06_build/stitch.log | tail -5
$PY 03_src/post_sweep.py 2>/dev/null | tail -2
echo "== audit(post) =="; $PY 03_src/audit_board.py 2>/dev/null | tail -3
$PY 03_src/generate_rules.py >/dev/null
echo "== DRC =="
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --format json \
    -o 06_build/drc/gate.json 04_kicad/cook_hub.kicad_pcb >/dev/null
$PY - <<'PYEOF'
import json
from collections import Counter
d = json.load(open('06_build/drc/gate.json'))
print('violations:', len(d['violations']), dict(Counter(v['type'] for v in d['violations'])))
print('unconnected:', len(d['unconnected_items']))
print('parity:', len(d.get('schematic_parity', [])))
PYEOF
