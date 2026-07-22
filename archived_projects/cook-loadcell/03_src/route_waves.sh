#!/bin/bash
# KRT routing waves for cook-loadcell (2-layer). GND is NOT routed (pours +
# stitch vias).
# Wave 1: bridge/excitation at 0.5 with the ANALOG-GUARD keepout (User.3 =
#         User.2 + the digital SE quadrant) so bridge nets — incl. the long
#         J5->J3.2 E- run — stay on the guarded west/north side (D5/§3.7e).
# Wave 2: 5V/3V3 at 0.5 (PWR floor 0.4), normal keepouts (User.2).
# Wave 3: signals at 0.25 (DAT/CLK take the SE corridor).
# clearance 0.21 (not 0.15): 0.6/0.3 vias at 0.15 pack drills to ~0.45 < the
# 0.5 hole-to-hole fab floor; 0.21 forces centres to 0.81 -> drill gap 0.51.
set -euo pipefail
cd "$(dirname "$0")/.."
KRT=~/gits/KiCadRoutingTools
R=06_build/route
PY=~/gits/KiCadRoutingTools/.venv/bin/python

$PY "$KRT"/route.py "$R"/r0.kicad_pcb --output "$R"/r1.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.21 --track-width 0.5 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.3 --max-iterations 400000 \
  --nets $(cat "$R"/nets_an.txt)

$PY "$KRT"/route.py "$R"/r1.kicad_pcb --output "$R"/r1b.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.21 --track-width 0.5 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 400000 \
  --nets $(cat "$R"/nets_pwr.txt)

$PY "$KRT"/route.py "$R"/r1b.kicad_pcb --output "$R"/r2.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.21 --track-width 0.25 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 800000 \
  --max-probe-iterations 60000 --max-ripup 30 \
  --nets $(cat "$R"/nets_sig.txt)

echo "waves done -> $R/r2.kicad_pcb"
