#!/usr/bin/env bash
# crow-recorder-central-v2 DETERMINISTIC board rebuild (the fleet rebuild_fast
# pattern). Regenerates the whole board from COMMITTED source — 03_src/ placement
# (floorplan.yaml) + rules (nets.yaml) + the two vendored footprints in 03_src/lib
# — and IMPORTS the PROMOTED KRT chain 03_src/route/rv2_final.kicad_pcb instead of
# re-running stochastic KRT, so the routing gate is bit-for-bit reproducible.
#
# VALID ONLY while KRT-routed pins do NOT move. If a signal-carrying pad's
# placement changes, re-route KRT on a track-free board and re-promote the chain
# (there is no autorouter in this driver by design — canon M3 / golden rule 1).
#
# Assumes the netlist 06_build/netlists/<board>.net exists. It is a build output
# (throwaway) regenerated from 03_tscircuit by the schematic gate; rebuild_all.sh
# runs that gate first and then calls this driver. To reproduce fully from
# committed source in one shot, run rebuild_all.sh.
set -euo pipefail
cd "$(dirname "$0")/.."                       # -> project root (projects/<board>/)
BOARD=crow_recorder_central_v2
PY=/usr/bin/python3
S="$(git rev-parse --show-toplevel)/skills/kicad-pcb/scripts"
[ -f "$S/generate_board_generic.py" ] || S="$HOME/.claude/skills/kicad-pcb/scripts"
export PATH="$HOME/.bun/bin:$PATH"

# kicad-cli DRC and the stitch gate each drop a stray "<board>.kicad_pcb.kicad_pro"
# beside the board; generate_rules' one-board-file contract (04_kicad) then aborts.
# Purge before every rules run and before the DRC gate.
rmstray(){ rm -f "04_kicad/$BOARD.kicad_pcb.kicad_pro" "04_kicad/$BOARD.kicad_pcb.kicad_prl"; }

rm -f 06_build/route/FINAL 2>/dev/null || true   # force `import` to use route.final (the promoted chain)

# 0. netlist from the COMMITTED converter schematic (deterministic — unlike
#    `tsci build`, which regenerates a UUID-churned sch), then the NET-MERGE
#    GATE (P0 class, red-team 2026-07-23: schematic wire geometry merged
#    P5VA_4 into AUDIO4M at export and every downstream self-consistent gate
#    stayed green). check_port_nets verifies every schematic label survives
#    into the netlist AND the 8 RJ45 ports pin-for-pin per the brief.
mkdir -p 06_build/netlists
kicad-cli sch export netlist --format kicadsexpr \
    -o "06_build/netlists/$BOARD.net" "03_tscircuit/kicad/$BOARD.kicad_sch"
python3 03_src/check_port_nets.py "06_build/netlists/$BOARD.net" \
    "03_tscircuit/kicad/$BOARD.kicad_sch"

# 1. placement from floorplan.yaml (194 parts, deterministic legalize)
$PY "$S/generate_board_generic.py" 03_src/floorplan.yaml -o "04_kicad/$BOARD.kicad_pcb"
# 2. netclasses + .kicad_dru BEFORE import (canon R1: rules ride into the router)
rmstray; $PY "$S/generate_rules_generic.py" .
# 3. import the promoted KRT chain ONCE into the track-free board
$PY "$S/route_and_stitch_generic.py" import  03_src/route.yaml
# 3.5 U1 (XU316) EP thermal grid as REAL VIA OBJECTS (F1, external review
#     2026-07-24): 16x 0.30/0.15 GND vias on the 4x4 EP grid, so the drill
#     file emits them under ViaDrill (not ComponentDrill) and JLC can fill+cap
#     them. Before stitch, so every pass + the DRC gate see them.
$PY 03_src/add_u1_thermal_vias.py "04_kicad/$BOARD.kicad_pcb"
# 4. stitch: pours + stitch/thermal vias + island heal + gate
$PY "$S/route_and_stitch_generic.py" stitch  03_src/route.yaml
# 4.5 board setup via-protection -> (capping yes)(filling yes): the fab flags
#     for the filled+capped via-in-pad process ORDER_README orders (F1). Text
#     patch AFTER the last pcbnew save of the board.
$PY 03_src/add_u1_thermal_vias.py --seal-fab-flags "04_kicad/$BOARD.kicad_pcb"
# 5. generate_rules LAST (any pcbnew save in the chain clobbers netclasses)
rmstray; $PY "$S/generate_rules_generic.py" .
# 6. routing gate: classified DRC at full severity, zones refilled, sch-parity
mkdir -p 06_build/route
cp "03_tscircuit/kicad/$BOARD.kicad_sch" "04_kicad/$BOARD.kicad_sch" 2>/dev/null || true
rmstray
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    --format json -o 06_build/route/gate.json "04_kicad/$BOARD.kicad_pcb"
$PY - <<'PYEOF'
import json
g=json.load(open("06_build/route/gate.json"))
v=len(g["violations"]); u=len(g["unconnected_items"]); p=len(g.get("schematic_parity",[]) or [])
print(f"ROUTING GATE: {v} violations / {u} unconnected / {p} parity")
raise SystemExit(0 if v==u==p==0 else 1)
PYEOF
echo "rebuild_reuse: routing gate GREEN (0/0/0) from committed source"
