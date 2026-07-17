#!/bin/bash
# KRT routing waves for shitty-kitty (re-route from scratch only; the
# standard rebuild imports the last chain file). Chain: r0 -> r5.
# 4-layer but KRT routes F.Cu/B.Cu ONLY: In1 = GND plane, In2 = power
# pours (both must stay track-free; stitch_and_fill bonds them by via).
# GND is NOT routed — pours + stitch vias.
# Wave 1: the 24 electrode stubs (product-critical, extra clearance)
# Wave 2: USB pair + I2C bus
# Wave 3: 12V trunk at 0.8mm; Wave 4: motor/5V/SW at 0.6; 3V3 at 0.5
# Wave 5: everything else at 0.3
set -euo pipefail
cd "$(dirname "$0")/.."
KRT=~/gits/KiCadRoutingTools
R=06_build/route
PY=~/gits/KiCadRoutingTools/.venv/bin/python

$PY "$KRT"/route.py "$R"/r0.kicad_pcb --output "$R"/r1.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.3 --track-width 0.25 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets INNER1 INNER2 INNER3 INNER4 INNER5 INNER6 INNER7 INNER8 \
         INNER9 INNER10 INNER11 INNER12 OUTER1 OUTER2 OUTER3 OUTER4 \
         OUTER5 OUTER6 OUTER7 OUTER8 OUTER9 OUTER10 OUTER11 OUTER12

$PY "$KRT"/route.py "$R"/r1.kicad_pcb --output "$R"/r2.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.25 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets USB_DP USB_DM SDA SCL

$PY "$KRT"/route.py "$R"/r2.kicad_pcb --output "$R"/r3.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.2 --track-width 0.8 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets VIN_RAW VIN_F VIN_12V

$PY "$KRT"/route.py "$R"/r3.kicad_pcb --output "$R"/r4.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.2 --track-width 0.6 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets 5V MOT_A1 MOT_A2 MOT_B1 MOT_B2 BRA BRB SW_BUCK BST 3V3

$PY "$KRT"/route.py "$R"/r4.kicad_pcb --output "$R"/r5.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.3 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 400000 \
  --nets EN BOOT STEP DIR ENN DIAG INDEX TMC_TX TMC_UART \
         ENDSTOP_N ENDSTOP_G MPR_IRQ1 MPR_IRQ2 MPR_IRQ3 MPR_IRQ4 \
         ACC_INT LED_ST LED_A LED_SA HOST_TX HOST_RX CC1 CC2 USB_VBUS \
         VREG_U3 VREG_U4 VREG_U5 VREG_U6 REXT_U3 REXT_U4 REXT_U5 REXT_U6 \
         V5OUT VCP CPO CPI GATE_Q1 EN_BUCK

echo "waves done -> $R/r5.kicad_pcb"
