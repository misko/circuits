#!/bin/bash
# KRT routing waves for esp32-laser-timing (re-route from scratch only; the
# standard rebuild imports the last chain file). Chain: r0 -> r1 -> r2 -> r3.
# 2-layer, JLC standard tier (0.6/0.3 vias). GND is NOT routed — it lives on
# the F/B pours + stitch vias (03_src/stitch_and_fill.py).
# Wave 1: USB differential pair + comparator block (timing path) — first pick
# Wave 2: power (PWR class; 0.6 >= the 0.5 dru floor)
# Wave 3: everything else non-GND
set -euo pipefail
cd "$(dirname "$0")/.."
KRT=~/gits/KiCadRoutingTools
R=06_build/route
PY=~/gits/KiCadRoutingTools/.venv/bin/python

# Wave 0: USB pair + CC first (hardest escape: J1's interleaved 0.5mm pad
# column). 0.45/0.3 vias = the smallest JLC-2L-standard-legal geometry so the
# router never falls back to 0.3/0.2 micro-vias (a full-size 0.6 via cannot
# turn the pair around in the escape corridor).
$PY "$KRT"/route.py "$R"/r0.kicad_pcb --output "$R"/r0b.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.2 \
  --via-size 0.45 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 400000 --via-proximity-cost 0 \
  --nets USB_DP USB_DM CC1 CC2

$PY "$KRT"/route.py "$R"/r0b.kicad_pcb --output "$R"/r1.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.25 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets COMP1 COMP2 COMP3 PD1 PD2 PD3

$PY "$KRT"/route.py "$R"/r1.kicad_pcb --output "$R"/r2.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.6 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets 5V 3V3

$PY "$KRT"/route.py "$R"/r2.kicad_pcb --output "$R"/r3.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.3 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets EN BOOT LED_A LDRV1 LDRV2 LDRV3 GATE1 GATE2 GATE3 \
  LSW1 LSW2 LSW3 VTH1 VTH2 VTH3 BTN1_N BTN2_N BTN3_N \
  BTN1_G BTN2_G BTN3_G SDA SCL

echo "waves done -> $R/r3.kicad_pcb"
