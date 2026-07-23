#!/usr/bin/env bash
# rebuild_all.sh — regenerate crow-mic-pod-v2 from source to DRC 0/0/0.
# Everything downstream of 03_tscircuit/ + 03_src/ is regenerable (canon M3).
set -euo pipefail
export PATH="$HOME/.bun/bin:$PATH"
cd "$(dirname "$0")/.."                 # project root
SK=../../skills/kicad-pcb/scripts
PY=/usr/bin/python3
KRTPY=~/gits/KiCadRoutingTools/.venv/bin/python
RS=$SK/route_and_stitch_generic.py

echo "== schematic bridge (tscircuit -> converter kicad_sch, ERC + parity) =="
$PY $SK/tsx_preflight.py .
bash $SK/gen_tscircuit.sh .
$PY $SK/count_parity.py .
kicad-cli sch export netlist -o 06_build/netlists/crow_mic_pod_v2.net \
    03_tscircuit/kicad/crow_mic_pod_v2.kicad_sch

echo "== board: place -> rules -> audit =="
$PY $SK/generate_board_generic.py 03_src/floorplan.yaml
$PY $SK/generate_rules_generic.py .          # netclasses BEFORE routing (R1)
$PY 03_src/audit_board.py                     # polarity + mate/keepout (P-POL/P-KEEP)

echo "== route (reuse promoted chain) -> stitch -> cleanup -> rules LAST =="
$PY    $RS prep   03_src/route.yaml
$KRTPY $RS route  03_src/route.yaml            # reuses 03_src/route/r3.kicad_pcb
$PY    $RS import 03_src/route.yaml
$PY    $RS stitch 03_src/route.yaml
$PY 03_src/cleanup_redundant_vias.py           # drop router vias on same-net THT pads
$PY $SK/generate_rules_generic.py .            # generate_rules LAST (saves clobber netclasses)

echo "== DRC gate =="
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    -o 06_build/drc_final.json --format json 04_kicad/crow_mic_pod_v2.kicad_pcb
echo "rebuild complete — check 06_build/drc_final.json = 0/0/0"
