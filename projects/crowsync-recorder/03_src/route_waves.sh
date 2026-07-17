#!/bin/bash
# KRT routing waves for crowsync-recorder (re-route from scratch only; the
# standard rebuild imports the last chain file). Chain: r0 -> r1 -> r2 -> r3.
# Wave 1: critical signals (USB pair + crystal) — short, direct, first pick
# Wave 2: power (PWR class; 0.5mm >= the 0.3 dru floor)
# Wave 3: everything else non-GND (GND lives on the In1 plane + pours)
set -euo pipefail
cd "$(dirname "$0")/.."
KRT=~/gits/KiCadRoutingTools
R=06_build/route
PY=~/gits/KiCadRoutingTools/.venv/bin/python

# Wave 0 (hardest-first, THIN): the J1 pad column interleaves CC/D+/D- on a
# 0.5mm pitch; only 0.15/0.13 geometry passes between pads (0.41 < 0.5),
# and whoever routes first claims the corridor (found empirically 2026-07-16)
$PY "$KRT"/route.py "$R"/r0.kicad_pcb --output "$R"/r0b.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.13 --track-width 0.15 \
  --via-size 0.45 --via-drill 0.2 --fab-tier advanced \
  --keepout --keepout-layer User.2 --max-iterations 500000 \
  --nets DM_C DP_C CC1 CC2

# Wave 1: chip-side USB pair + crystal at standard geometry
$PY "$KRT"/route.py "$R"/r0b.kicad_pcb --output "$R"/r1.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.25 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets DP DM XTI XTO

$PY "$KRT"/route.py "$R"/r1.kicad_pcb --output "$R"/r2.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.2 --track-width 0.5 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets VBUS_5V VBUS_PCM 3V3A MIC_BIAS_F

$PY "$KRT"/route.py "$R"/r2.kicad_pcb --output "$R"/r3.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.25 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets AMP_FB AMP_INP AMP_OUT LED3_A LED4_A MIC MIC_IN \
  PPS PPS_A PPS_ATT RG_X SSPND VCCCI VCCP1 VCCP2 VCCXI VCOM \
  VCOM_BUF VDDI VINL VINL_F VINR

echo "waves done -> $R/r3.kicad_pcb"
