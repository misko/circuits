#!/bin/bash
# Full regenerate -> import -> stitch -> rules -> gate chain.
# set -e + pipefail: ANY stage failure stops the chain (a masked stitch
# failure once let DRC run on an unstitched board - 2026-07-16).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=/usr/bin/python3
$PY src/generate_schematic.py 2>/dev/null | tail -1
kicad-cli sch export netlist -o build/netlists/usb_power_3s.net kicad/usb_power_3s.kicad_sch >/dev/null
$PY src/generate_board.py 2>/dev/null | tail -1
$PY src/audit_board.py 2>/dev/null | tail -1
$PY ~/.claude/skills/kicad-pcb/scripts/import_krt.py build/route/r5.kicad_pcb \
    kicad/usb_power_3s.kicad_pcb kicad/usb_power_3s.kicad_pcb 2>/dev/null | grep imported
$PY src/route_taps.py 2>/dev/null
$PY src/route_taps_krt.py prep 2>/dev/null
/home/mouse9911/virtual-envs/spf/bin/python ~/gits/KiCadRoutingTools/route.py \
    build/route/taps_in.kicad_pcb --output build/route/taps_out.kicad_pcb \
    --nets TAPB TAPC --layers F.Cu B.Cu --track-width 0.15 --clearance 0.13 \
    --via-size 0.45 --via-drill 0.2 2>/dev/null | grep -E "Routed|failed|TAP" | tail -4
$PY src/route_taps_krt.py finish 2>/dev/null
# taps_out grew FROM the live board, so it now holds ALL tracks: rebuild the
# board fresh and import taps_out as the single source (no duplicates)
$PY src/generate_board.py 2>/dev/null | tail -1
$PY ~/.claude/skills/kicad-pcb/scripts/import_krt.py build/route/taps_out.kicad_pcb \
    kicad/usb_power_3s.kicad_pcb kicad/usb_power_3s.kicad_pcb 2>/dev/null | grep imported
$PY src/stitch_and_fill.py 2>/dev/null
python3 src/generate_rules.py
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --format json \
    -o build/drc/gate.json kicad/usb_power_3s.kicad_pcb >/dev/null
python3 - <<'PYEOF'
import json
from collections import Counter
d = json.load(open('build/drc/gate.json'))
print('violations:', len(d['violations']), dict(Counter(v['type'] for v in d['violations'])))
print('unconnected:', len(d['unconnected_items']))
PYEOF
