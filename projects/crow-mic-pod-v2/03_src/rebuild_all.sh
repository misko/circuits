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

echo "== route: REUSE the PROMOTED chain r3 (canon M3) -> stitch -> cleanup -> rules LAST =="
$PY    $RS prep   03_src/route.yaml
# canon M3 / route.yaml `final:` — REUSE the promoted race-winner chain r3
# verbatim for REPRODUCIBILITY. `cmd_route` re-races on every run (route.race:5)
# even when route.final is set, and the boxed-in J1.1 AUDIO_P escape fails on
# SOME stochastic race candidates (drops the escape -> 1 unconnected). Pin the
# import at the promoted r3 via the FINAL marker so `import` consumes it, exactly
# what canon 3g mandates. (To deliberately re-race from scratch, run
# `$KRTPY $RS route 03_src/route.yaml` here instead — it overwrites FINAL.)
mkdir -p 06_build/route
echo "$PWD/03_src/route/r3.kicad_pcb" > 06_build/route/FINAL
$PY    $RS import 03_src/route.yaml
$PY    $RS stitch 03_src/route.yaml
$PY 03_src/cleanup_redundant_vias.py           # drop router vias on same-net THT pads
$PY $SK/generate_rules_generic.py .            # generate_rules LAST (saves clobber netclasses)

echo "== rules gate (A-FIRE: a rule that CANNOT FIRE is a BUILD ERROR) =="
# Runs AFTER the last generate_rules and BEFORE the DRC gate, on purpose: it
# grades the rules DRC is about to be measured against. Without it, a rule
# conditioning on a netclass the project does not define — or on a rule area
# not on the board — enforces nothing, and DRC's 0/0/0 is partly vacuous for
# exactly the nets that rule names. crow-mic-pod-v2 v1.0 sealed with 2 of its
# 4 rules dead and 3 tracks 0.0002mm under the floor one of them named.
$PY $SK/rules_audit.py .

echo "== DRC gate =="
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    -o 06_build/drc_final.json --format json 04_kicad/crow_mic_pod_v2.kicad_pcb
echo "rebuild complete — check 06_build/drc_final.json = 0/0/0"
