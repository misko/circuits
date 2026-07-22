#!/bin/bash
# usb-hub-3s rebuild — the canonical generic pipeline (03_src/contracts.md order)
set -euo pipefail
cd "$(dirname "$0")/.."                       # -> project root

BOARD=usb_hub_3s
TSX=usb_hub_3s

PY=/usr/bin/python3
S="$(cd "$(git rev-parse --show-toplevel 2>/dev/null || echo ../../..)" && pwd)/skills/kicad-pcb/scripts"
[ -f "$S/generate_board_generic.py" ] || S="$HOME/.claude/skills/kicad-pcb/scripts"
export PATH="$HOME/.nvm/versions/node/v22.12.0/bin:$HOME/.bun/bin:$PATH"

# [0] tsx preflight + author-count parity base
$PY "$S/tsx_preflight.py" .

# [1] tscircuit TSX -> circuit.json -> converter .kicad_sch -> netlist
( cd 03_tscircuit && tsci build "src/$TSX.tsx" )
cp 03_tscircuit/dist/src/$TSX/circuit.json 03_tscircuit/build/circuit.json 2>/dev/null || true
# --mode grid: layout-mode wire import silently merged VIN_S into HG2 by
# wire-endpoint coincidence (2026-07-21, learnings/03_schematic.md). Grid
# label-glue is parity-safe by construction; the HUMAN schematic is
# tscircuit's own render (build/schematic.pdf), not this machine sheet.
$PY "$S/circuit_json_to_kicad_sch.py" 03_tscircuit/build/circuit.json \
    -o "04_kicad/$BOARD.kicad_sch" --parts 02_parts --mode grid
mkdir -p 06_build/netlists 06_build/drc
kicad-cli sch export netlist --output "06_build/netlists/$BOARD.net" "04_kicad/$BOARD.kicad_sch"

# [1b] S-COUNT gate
$PY "$S/count_parity.py" .

# [2] ERC gate: severity-all REPORT, gate on ERRORS = 0 (warnings baselined:
# lib_symbol/footprint_link env classes + grid-mode isolated labels - S1)
kicad-cli sch erc --severity-all "04_kicad/$BOARD.kicad_sch" -o 06_build/erc.rpt
grep -q "Errors 0 " 06_build/erc.rpt || { echo "ERC FAILED (errors != 0)"; grep "ERC messages" 06_build/erc.rpt; exit 1; }
grep "ERC messages" 06_build/erc.rpt

# [3] board (placement + zones) from floorplan.yaml  [SHARED]
$PY "$S/generate_board_generic.py" 03_src/floorplan.yaml -o "04_kicad/$BOARD.kicad_pcb"

# [4] placement/pad invariants  [per-board gate]
$PY 03_src/audit_board.py

# [5] netclasses BEFORE route-prep (canon R1)  [SHARED]
$PY "$S/generate_rules_generic.py" .

# [6-8] route + stitch from route.yaml  [SHARED]
$PY "$S/route_and_stitch_generic.py" prep   03_src/route.yaml
$PY "$S/route_and_stitch_generic.py" import 03_src/route.yaml   # replay promoted route/ chain (M3)
$PY "$S/route_and_stitch_generic.py" taps   03_src/route.yaml
# [8a] v1.1 deterministic stubs for the four pour-net chip-pin connections
$PY 03_src/add_seed_stubs.py
# [8b] v1.1 via program (X22/X23): trunk farms + thermal arrays, before fill
$PY 03_src/add_via_farms.py
$PY "$S/route_and_stitch_generic.py" stitch 03_src/route.yaml

# [9] generate_rules LAST (pcbnew saves clobber .kicad_pro netclasses)  [SHARED]
$PY "$S/generate_rules_generic.py" .
# [9b] silk-height floor: pcbnew saves reset board.design_settings.rules
# min_text_height to KiCad's 0.8 default; the fab tier's PROVEN floor is
# 0.45 (fab_tiers.yaml) and our refdes run 0.45-0.6. Backend gap: the shared
# rules emitter does not own this key yet.
$PY - <<'PYEOF'
import json
p = "04_kicad/$BOARD.kicad_pro".replace("$BOARD", "usb_hub_3s")
d = json.load(open(p))
r = d.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {})
r["min_text_height"] = 0.45
r["min_text_thickness"] = 0.1
json.dump(d, open(p, "w"), indent=2)
print("pro silk floors: min_text_height 0.45")
PYEOF

# [10] DRC gate — must be 0 / 0 / 0 at full severity
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    --format json -o 06_build/drc/gate.json "04_kicad/$BOARD.kicad_pcb"
$PY -c "import json;g=json.load(open('06_build/drc/gate.json'));v,u,p=len(g['violations']),len(g['unconnected_items']),len(g.get('schematic_parity',[]));print(f'DRC {v}/{u}/{p}');exit(0 if v==u==p==0 else 1)"
