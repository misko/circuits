#!/bin/bash
# usb-hub-3s-v2 rebuild — the canonical generic pipeline (03_src/contracts.md order).
# NOTE: the schematic MUST be regenerated with `--mode grid` (layout mode merges
# buck-A BOOT_A/VCC_A — see journal/04_board.md). This script rebuilds from the
# committed .kicad_sch onward (board + route + stitch); re-run gen with grid mode
# separately if the tsx changes.
set -euo pipefail
cd "$(dirname "$0")/.."                       # -> project root

BOARD=usb_hub_3s_v2
PY=/usr/bin/python3
S="$(cd "$(git rev-parse --show-toplevel 2>/dev/null || echo ../../..)" && pwd)/skills/kicad-pcb/scripts"
[ -f "$S/generate_board_generic.py" ] || S="$HOME/.claude/skills/kicad-pcb/scripts"
export PATH="$HOME/.nvm/versions/node/v22.12.0/bin:$HOME/.bun/bin:$PATH"

# [1] board (placement + zones) from floorplan.yaml  [SHARED]
$PY "$S/generate_board_generic.py" 03_src/floorplan.yaml -o "04_kicad/$BOARD.kicad_pcb"
# [2] placement/pad invariants  [per-board gate]
$PY 03_src/audit_board.py
# [3] netclasses BEFORE route-prep (canon R1)  [SHARED]
$PY "$S/generate_rules_generic.py" .
# [4-7] route + stitch from route.yaml  [SHARED]
$PY "$S/route_and_stitch_generic.py" prep   03_src/route.yaml
$PY "$S/route_and_stitch_generic.py" route  03_src/route.yaml
$PY "$S/route_and_stitch_generic.py" import 03_src/route.yaml
$PY "$S/route_and_stitch_generic.py" taps   03_src/route.yaml
$PY "$S/route_and_stitch_generic.py" stitch 03_src/route.yaml
# [8] generate_rules LAST (pcbnew saves clobber .kicad_pro netclasses)  [SHARED]
$PY "$S/generate_rules_generic.py" .
# [8b] silk-height floor (pcbnew resets min_text_height to 0.8; advanced floor 0.45)
$PY - <<'PYEOF'
import json
p="04_kicad/usb_hub_3s_v2.kicad_pro"
d=json.load(open(p))
r=d.setdefault("board",{}).setdefault("design_settings",{}).setdefault("rules",{})
r["min_text_height"]=0.45; r["min_text_thickness"]=0.1
json.dump(d,open(p,"w"),indent=2); print("pro silk floors: min_text_height 0.45")
PYEOF
# [9] DRC gate — must be 0/0/0 at full severity
mkdir -p 06_build/drc
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    --format json -o 06_build/drc/gate.json "04_kicad/$BOARD.kicad_pcb"
$PY -c "import json;g=json.load(open('06_build/drc/gate.json'));v,u,p=len(g['violations']),len(g['unconnected_items']),len(g.get('schematic_parity',[]));print(f'DRC {v}/{u}/{p}');exit(0 if v==u==p==0 else 1)"
