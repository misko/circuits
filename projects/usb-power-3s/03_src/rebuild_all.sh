#!/bin/bash
# Full regenerate -> import -> stitch -> rules -> gate chain.
# set -e + pipefail: ANY stage failure stops the chain (a masked stitch
# failure once let DRC run on an unstitched board - 2026-07-16).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=/usr/bin/python3
# skills: repo-relative first (standalone clone), else machine-global
SKILLS="$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd)/skills/kicad-pcb/scripts"
[ -d "$SKILLS" ] || SKILLS="$HOME/.claude/skills/kicad-pcb/scripts"
$PY 03_src/generate_schematic.py 2>/dev/null | tail -1
kicad-cli sch export netlist -o 06_build/netlists/usb_power_3s.net 04_kicad/usb_power_3s.kicad_sch >/dev/null
$PY 03_src/generate_board.py 2>/dev/null | tail -1
$PY 03_src/audit_board.py 2>/dev/null | tail -1
$PY "$SKILLS"/import_krt.py 06_build/route/r5.kicad_pcb \
    04_kicad/usb_power_3s.kicad_pcb 04_kicad/usb_power_3s.kicad_pcb 2>/dev/null | grep imported
$PY 03_src/route_taps.py 2>/dev/null
$PY 03_src/stitch_and_fill.py 2>/dev/null
python3 03_src/generate_rules.py
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --format json \
    -o 06_build/drc/gate.json 04_kicad/usb_power_3s.kicad_pcb >/dev/null
python3 - <<'PYEOF'
import json
from collections import Counter
d = json.load(open('06_build/drc/gate.json'))
print('violations:', len(d['violations']), dict(Counter(v['type'] for v in d['violations'])))
print('unconnected:', len(d['unconnected_items']))
PYEOF
