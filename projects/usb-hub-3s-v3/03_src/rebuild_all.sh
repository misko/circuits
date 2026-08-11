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

run_stage() {
    local stage="$1"; shift
    "$PY" "$S/pcb_flow.py" run . --stage "$stage" -- "$@"
}

# One receipt for the meaningful layout stage. If the driver stops, the
# pending witness remains in 06_build/provenance instead of looking complete.
$PY "$S/artifact_provenance.py" begin . --stage pcb_layout \
    --input 03_src/floorplan.yaml --input 03_src/route.yaml \
    --input "03_tscircuit/kicad/$BOARD.kicad_sch" \
    --output "04_kicad/$BOARD.kicad_pcb" \
    --output "04_kicad/$BOARD.kicad_pro" \
    --output "04_kicad/$BOARD.kicad_dru" \
    --output 06_build/drc/gate.json

# [1] board (placement + zones) from floorplan.yaml  [SHARED]
$PY "$S/generate_board_generic.py" 03_src/floorplan.yaml -o "04_kicad/$BOARD.kicad_pcb"
# [2] placement/pad invariants  [per-board gate]
$PY 03_src/audit_board.py
# Critical connector identity/pads are independent of schematic/DRC agreement.
$PY "$S/critical_part_facts.py" .
# [3] netclasses BEFORE route-prep (canon R1)  [SHARED]
$PY "$S/generate_rules_generic.py" .
# [4-7] route + stitch from route.yaml  [SHARED]
run_stage route_prep   $PY "$S/route_and_stitch_generic.py" prep   03_src/route.yaml
run_stage route        $PY "$S/route_and_stitch_generic.py" route  03_src/route.yaml
run_stage route_import $PY "$S/route_and_stitch_generic.py" import 03_src/route.yaml --route-source build
run_stage route_taps   $PY "$S/route_and_stitch_generic.py" taps   03_src/route.yaml
run_stage stitch       $PY "$S/route_and_stitch_generic.py" stitch 03_src/route.yaml
# [7b] v1.1 post-stitch geometry fixes (EP thermal vias, VBAT_F F<->B stitch, drill/width floors, GND-island bond)
$PY 03_src/post_stitch_fixes.py
# [7c] M-SHIP READ-BACK: prove the pour SURVIVED the last board write.
#      post_stitch_fixes.py runs AFTER the stitch driver and holds the
#      LAST save, so the guard inside `stitch` guards nothing here.
#      Its section 6 (added in v1.6) unfilled to place vias and never
#      refilled -> v1.6/v1.7/v1.8 shipped 44287.91 mm2 of BARE COPPER
#      with every gate green. ADR-0004, canon M-SHIP/M-WIDTH.
#      POSITION (v1.9): this sits BETWEEN the last board write and
#      generate_rules, not after it. It only needs to follow the last
#      pcbnew SAVE, and generate_rules_generic.py never opens the
#      .kicad_pcb (it writes .kicad_pro/.kicad_dru and sweeps stray
#      droppings), so the read-back is over identical bytes either way.
#      Running it after generate_rules tripped canon A-ORDER, whose
#      read-only-checker whitelist keys on FILENAME and so cannot see
#      that `route_and_stitch_generic.py verify-fill` writes nothing.
$PY "$S/route_and_stitch_generic.py" verify-fill 03_src/route.yaml
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
# [9] DRC gate — must be 0/0/0 at full severity.
# Place the authoritative converter sch beside the board so --schematic-parity
# actually RUNS (else kicad-cli skips it and reports a hollow 0).
mkdir -p 06_build/drc
cp "03_tscircuit/kicad/$BOARD.kicad_sch" "04_kicad/$BOARD.kicad_sch" 2>/dev/null || true
run_stage layout_drc kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    --format json -o 06_build/drc/gate.json "04_kicad/$BOARD.kicad_pcb"
$PY -c "import json;g=json.load(open('06_build/drc/gate.json'));v,u,p=len(g['violations']),len(g['unconnected_items']),len(g.get('schematic_parity',[]));print(f'DRC {v}/{u}/{p}');exit(0 if v==u==p==0 else 1)"
$PY "$S/artifact_provenance.py" finish . --stage pcb_layout
$PY "$S/project_state.py" . --expect DESIGN_CLEAN
