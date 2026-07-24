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
python3 "$SKILL/tsx_preflight.py"  "$PROJ"
bash    "$SKILL/gen_tscircuit.sh"  "$PROJ"
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
echo "rebuild_all: done"
