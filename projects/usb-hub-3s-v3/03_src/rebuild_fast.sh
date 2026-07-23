#!/bin/bash
# usb-hub-3s-v2 DETERMINISTIC rebuild — imports the PROMOTED KRT chain
# (03_src/route/final_chain.kicad_pcb) instead of re-running stochastic KRT.
# Valid ONLY while KRT-routed pins (PD-cell signal pins, buck signals) do NOT
# move. If placement of a signal-carrying pin changes, run the full
# rebuild_all.sh (re-routes KRT) and re-promote the chain.
set -euo pipefail
cd "$(dirname "$0")/.."                       # -> project root
BOARD=usb_hub_3s_v2
PY=/usr/bin/python3
S="$(cd "$(git rev-parse --show-toplevel 2>/dev/null || echo ../../..)" && pwd)/skills/kicad-pcb/scripts"
[ -f "$S/generate_board_generic.py" ] || S="$HOME/.claude/skills/kicad-pcb/scripts"
export PATH="$HOME/.nvm/versions/node/v22.12.0/bin:$HOME/.bun/bin:$PATH"

rm -f 06_build/route/FINAL 2>/dev/null || true   # force import to use promoted chain
$PY "$S/generate_board_generic.py" 03_src/floorplan.yaml -o "04_kicad/$BOARD.kicad_pcb"
$PY 03_src/audit_board.py
$PY "$S/generate_rules_generic.py" .
$PY "$S/route_and_stitch_generic.py" import 03_src/route.yaml
$PY "$S/route_and_stitch_generic.py" taps   03_src/route.yaml
$PY "$S/route_and_stitch_generic.py" stitch 03_src/route.yaml
$PY "$S/generate_rules_generic.py" .
$PY - <<'PYEOF'
import json
p="04_kicad/usb_hub_3s_v2.kicad_pro"
d=json.load(open(p))
r=d.setdefault("board",{}).setdefault("design_settings",{}).setdefault("rules",{})
r["min_text_height"]=0.45; r["min_text_thickness"]=0.1
json.dump(d,open(p,"w"),indent=2); print("pro silk floors: min_text_height 0.45")
PYEOF
mkdir -p 06_build/drc
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    --format json -o 06_build/drc/gate.json "04_kicad/$BOARD.kicad_pcb"
$PY -c "import json;g=json.load(open('06_build/drc/gate.json'));v,u,p=len(g['violations']),len(g['unconnected_items']),len(g.get('schematic_parity',[]));print(f'DRC {v}/{u}/{p}');exit(0 if v==u==p==0 else 1)"
