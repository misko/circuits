#!/usr/bin/env bash
# rebuild_all.sh — crow-recorder-central-v2 full regenerate (canon M3).
# Everything downstream regenerates from 03_src/ + 03_tscircuit/. NB: the
# schematic is authored in tscircuit (03_tscircuit); the KiCad backend
# (generate_board.py, stitch_and_fill, promoted route) is added at the
# placement/routing stage. Until that backend exists this script runs the
# tscircuit BRIDGE (schematic gate) only.
set -euo pipefail
export PATH="$HOME/.bun/bin:$PATH"
SKILL="$HOME/.claude/skills/kicad-pcb/scripts"
PROJ="projects/crow-recorder-central-v2"
cd "$(git rev-parse --show-toplevel)"

# --- schematic gate (tscircuit -> converter kicad_sch -> ERC + parity) ---
# PROMOTED CONVERTER SCH (canon M3 promoted-artifact pattern, same as the
# route chain): 03_tscircuit/kicad/<board>.kicad_sch carries the two
# hand-added net-merge dogleg wires (P5VA_4, MID2P — the 2026-07-23 P0
# surgery; 695 wires vs the converter's 693) that the converter cannot yet
# emit. Regenerating it REINTRODUCES the merge class (measured 2026-07-24:
# check_port_nets LABEL-LOST P5VA_4 + MID2P on a fresh render). Save the
# promoted sch around gen_tscircuit, then refresh its ERC/netlist evidence;
# check_port_nets in rebuild_reuse PROVES the promoted sch is the one
# exported. A converter able to emit the doglegs retires this block.
BOARD=crow_recorder_central_v2
PSCH="$PROJ/03_tscircuit/kicad/$BOARD.kicad_sch"
python3 "$SKILL/tsx_preflight.py"  "$PROJ"
cp "$PSCH" "$PSCH.promoted"
bash    "$SKILL/gen_tscircuit.sh"  "$PROJ"
mv "$PSCH.promoted" "$PSCH"
kicad-cli sch erc --severity-all -o "$PROJ/03_tscircuit/verification/erc_converter.rpt" "$PSCH" >/dev/null 2>&1 || true
kicad-cli sch export netlist --format kicadsexpr \
    -o "$PROJ/03_tscircuit/verification/converter_netlist.net" "$PSCH" >/dev/null
python3 "$SKILL/count_parity.py"   "$PROJ"

# --- whole board (placement + routing) ---
# This board's KiCad backend is the GENERIC generator (generate_board_generic +
# route_and_stitch_generic) driven by 03_src/{floorplan,route,rules}.yaml, not a
# per-board 03_src/generate_board.py — so the deterministic board driver
# rebuild_reuse.sh regenerates placement + imports the PROMOTED chain
# (03_src/route/rv2_final.kicad_pcb) and runs the routing gate. The schematic gate
# above just regenerated the netlist it consumes, so this whole script reproduces
# the board 0/0/0 from committed source (03_tscircuit + 03_src). No stochastic KRT.
bash "$PROJ/03_src/rebuild_reuse.sh"

# node-for-node parity of the PROMOTED sch vs the JUST-REBUILT board
python3 "$SKILL/kicad_sch_parity.py" "$BOARD" \
    "$PROJ/03_tscircuit/verification/converter_netlist.net" \
    "$PROJ/04_kicad/$BOARD.kicad_pcb" \
    --padmap "$(cat "$PROJ/03_tscircuit/parity_padmap.txt" 2>/dev/null)" \
    | tee "$PROJ/03_tscircuit/verification/parity_converter.md"
echo "rebuild_all: done"
