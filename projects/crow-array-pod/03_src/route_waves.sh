#!/bin/bash
# KRT routing waves for crow-array-pod (re-route from scratch only; the
# standard rebuild imports the promoted chain file 03_src/route/r3.kicad_pcb).
# 2-layer, JLC standard tier (0.6/0.3 vias). GND is NOT routed — it lives on
# the F/B pours + stitch vias (03_src/stitch_and_fill.py).
# HARDEST-FIRST (skill golden rule 4): the RJ45 tail-field INTERIOR pads
# (5V on 4/7, BEEP on 3/6) have one escape lane each — their nets route
# FIRST or the end-pad nets wall them in (v1.1: 5V pad 4 unroutable when
# power went last). Audio pads sit at the row ends and escape easily.
# Wave 1: power 0.5 (interior pads 4/7)
# Wave 2: beeper pair at 0.6 (interior pads 3/6; inductive 150mA bursts)
# Wave 3: audio chain + midpoint (the sensitive path; end pads at J1)
set -euo pipefail
cd "$(dirname "$0")/.."
KRT=~/gits/KiCadRoutingTools
R=06_build/route
PY=~/gits/KiCadRoutingTools/.venv/bin/python

$PY "$KRT"/route.py "$R"/r0.kicad_pcb --output "$R"/r1.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.5 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets 5V 5VF SHIELD

$PY "$KRT"/route.py "$R"/r1.kicad_pcb --output "$R"/r2.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.6 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets BEEP_5V BZ_P BEEP_RET

$PY "$KRT"/route.py "$R"/r2.kicad_pcb --output "$R"/r3.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.3 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 400000 \
  --nets MIC AIN A_OUT B_OUT FB_A FB_B VMID AUD_P_I AUD_N_I AUDIO_P AUDIO_N

echo "waves done -> $R/r3.kicad_pcb"
