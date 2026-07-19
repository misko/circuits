#!/bin/bash
# KRT routing waves for cook-hub (re-route from scratch only; the standard
# rebuild imports the promoted chain 03_src/route/r2.kicad_pcb).
# 4-layer but KRT works F.Cu/B.Cu only (In1 = GND plane, In2 = power pours;
# plane integrity stays perfect). GND is NOT routed (planes + stitch vias);
# KEYPAD/COIL/RELAY_5V are NOT routed (route_bank.py engineered copper —
# keepouts on User.2 wall KRT out of the whole bank region).
# Wave 1: power rails at 0.5 (hardest-first: the SW entry cluster)
# Wave 2: all remaining signals at 0.25
set -euo pipefail
cd "$(dirname "$0")/.."
KRT=~/gits/KiCadRoutingTools
R=06_build/route
PY=~/gits/KiCadRoutingTools/.venv/bin/python

$PY "$KRT"/route.py "$R"/r0.kicad_pcb --output "$R"/r1.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.5 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 400000 \
  --nets $(cat "$R"/nets_pwr.txt)

$PY "$KRT"/route.py "$R"/r1.kicad_pcb --output "$R"/r1b.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.25 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 400000 \
  --nets $(cat "$R"/nets_spi.txt)

$PY "$KRT"/route.py "$R"/r1b.kicad_pcb --output "$R"/r2.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.25 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 1500000 \
  --max-probe-iterations 80000 --max-ripup 40 \
  --nets $(cat "$R"/nets_sig.txt)

echo "waves done -> $R/r2.kicad_pcb"
