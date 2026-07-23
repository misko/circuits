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

# --- whole board (placement + routing) — enabled once 03_src/generate_board.py
#     + a promoted 03_src/route/ chain exist (placement/routing stages) ---
if [ -f "$PROJ/03_src/generate_board.py" ]; then
  bash "$SKILL/tsx_to_board.sh" "$PROJ"
fi
echo "rebuild_all: done"
