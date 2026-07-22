#!/bin/bash
# TEMPLATE rebuild_all.sh — the canonical generic pipeline (skill-owned).
# Copy into a new board's 03_src/ and set BOARD + TSX below. ZERO board-specific
# generation Python: board + route + rules all run on the SHARED skill scripts.
# See 03_src/contracts.md for the authoritative step order.
set -euo pipefail
cd "$(dirname "$0")/.."                       # -> project root (03_src/..)

# --- board-specific knobs (the ONLY things to edit) -------------------------
BOARD=power3s                                  # <board> stem for 04_kicad/<board>.*
TSX=power3s                                    # 03_tscircuit/src/<TSX>.tsx basename
# ----------------------------------------------------------------------------

PY=/usr/bin/python3
# resolve the shared skill scripts (repo-relative first, ~/.claude fallback)
S="$(cd "$(git rev-parse --show-toplevel 2>/dev/null || echo ../../..)" && pwd)/skills/kicad-pcb/scripts"
[ -f "$S/generate_board_generic.py" ] || S="$HOME/.claude/skills/kicad-pcb/scripts"
export PATH="$HOME/.nvm/versions/node/v22.12.0/bin:$HOME/.bun/bin:$PATH"

# [1] tscircuit TSX -> circuit.json -> converter .kicad_sch -> netlist
( cd 03_tscircuit && tsci build "src/$TSX.tsx" )
$PY "$S/circuit_json_to_kicad_sch.py" 03_tscircuit/build/circuit.json \
    -o "04_kicad/$BOARD.kicad_sch" --parts 02_parts
kicad-cli sch export netlist --output "06_build/netlists/$BOARD.net" "04_kicad/$BOARD.kicad_sch"

# [2] ERC gate (0 errors)
kicad-cli sch erc --severity-all --exit-code-violations "04_kicad/$BOARD.kicad_sch" \
    -o 06_build/erc.rpt || { echo "ERC FAILED"; exit 1; }

# [3] board (placement + zones) from floorplan.yaml  [SHARED]
$PY "$S/generate_board_generic.py" 03_src/floorplan.yaml -o "04_kicad/$BOARD.kicad_pcb"

# [4] placement/pad invariants  [per-board gate]
$PY 03_src/audit_board.py

# [5] netclasses BEFORE route-prep (canon R1)  [SHARED]
$PY "$S/generate_rules_generic.py" .

# [6-8] route + stitch from route.yaml  [SHARED]
$PY "$S/route_and_stitch_generic.py" prep   03_src/route.yaml
$PY "$S/route_and_stitch_generic.py" import 03_src/route.yaml   # replay promoted route/ chain (M3)
$PY "$S/route_and_stitch_generic.py" stitch 03_src/route.yaml

# [9] generate_rules LAST (pcbnew saves clobber .kicad_pro netclasses)  [SHARED]
$PY "$S/generate_rules_generic.py" .

# [10] DRC gate — must be 0 / 0 / 0 at full severity
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    --format json -o 06_build/drc/gate.json "04_kicad/$BOARD.kicad_pcb"
$PY -c "import json;g=json.load(open('06_build/drc/gate.json'));v,u,p=len(g['violations']),len(g['unconnected_items']),len(g.get('schematic_parity',[]));print(f'DRC {v}/{u}/{p}');exit(0 if v==u==p==0 else 1)"
