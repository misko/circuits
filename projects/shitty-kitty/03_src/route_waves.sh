#!/bin/bash
# KRT routing waves for shitty-kitty (re-route from scratch only; the
# standard rebuild imports the promoted chain file 03_src/route/r5.kicad_pcb).
# 4-layer, JLC standard tier; KRT routes F.Cu/B.Cu ONLY (In1 = GND plane,
# In2 = power pours; stitch_and_fill bonds by via). GND is NOT routed.
#
# ORDER IS LOAD-BEARING (escape geometry, kicad-pcb golden rule 4):
#  w1  fine-pitch support escapes (QFN/UQFN/LGA logic pins) — routed FIRST
#      or electrode/power tracks fence them in (seen live: INNER7 wrapped
#      U4's west side and sealed the IRQ pad; VIN/motor sealed the TMC's
#      charge-pump pins).
#  w2  3V3 (multipoint; lands on UQFN pad necks).
#  w3  the 24 electrode stubs (can detour via B.Cu; audit I8 caps length).
#  w4  USB pair + I2C bus.  w5 12V entry (0.8mm).  w6 VIN_12V + motor
#      phases (0.35 = QFN neck limit).  w7 buck 5V/SW (0.4).  w8 the rest.
# All waves: grid 0.05 (0.4mm-pitch UQFN needs it), fab-tier standard 4L.
set -euo pipefail
cd "$(dirname "$0")/.."
KRT=~/gits/KiCadRoutingTools
R=06_build/route
PY=~/gits/KiCadRoutingTools/.venv/bin/python

run() {  # run OUT IN WIDTH CLEAR ITER nets...
  local out=$1 inp=$2 w=$3 c=$4 it=$5; shift 5
  $PY "$KRT"/route.py "$R"/$inp --output "$R"/$out \
    --layers F.Cu B.Cu --grid-step 0.05 --clearance $c --track-width $w \
    --via-size 0.6 --via-drill 0.3 --fab-tier standard --fab-overrides 03_src/rules/fab_overrides.txt --no-stub-layer-swap \
    --keepout --keepout-layer User.2 --max-iterations $it --nets "$@"
}

run w1.kicad_pcb r0.kicad_pcb 0.8 0.15 300000 VIN_RAW VIN_F

# motor + VS + sense returns together (QFN top row is zero-sum)
# charge pump FIRST (serialized): the VIN/motor/BRB walls fence the CP
# pocket if they route before these four short stubs (found the hard way).
run w1b1.kicad_pcb w1.kicad_pcb 0.25 0.13 200000 VCP
run w1b2.kicad_pcb w1b1.kicad_pcb 0.25 0.13 200000 CPO
run w1b3.kicad_pcb w1b2.kicad_pcb 0.25 0.13 200000 CPI
run w1b.kicad_pcb w1b3.kicad_pcb 0.25 0.13 200000 V5OUT

run w2.kicad_pcb w1b.kicad_pcb 0.35 0.13 500000 \
    VIN_12V MOT_A1 MOT_A2 MOT_B1 MOT_B2 BRA BRB

# charge-pump + driver-support escapes get FIRST pick of the corridor west
# of the TMC2209 (they failed loudly once escalation was pinned off).
# ONE mega wave for every remaining signal: KRT's intra-wave ripup is the
# only arbiter that can trade corridors between electrode stubs, UQFN
# support pins, the TMC logic cluster and the buses. Split waves deadlock
# (whoever routes last near a fine-pitch package loses — 6 iterations of
# evidence in git history). Width 0.2 everywhere; stitch_and_fill lifts
# floored classes afterwards.
run w3.kicad_pcb w2.kicad_pcb 0.2 0.13 2000000 \
    INNER1 INNER2 INNER3 INNER4 INNER5 INNER6 INNER7 INNER8 \
    INNER9 INNER10 INNER11 INNER12 OUTER1 OUTER2 OUTER3 OUTER4 \
    OUTER5 OUTER6 OUTER7 OUTER8 OUTER9 OUTER10 OUTER11 OUTER12 \
    VREG_U3 VREG_U4 VREG_U5 VREG_U6 REXT_U3 REXT_U4 REXT_U5 REXT_U6 \
    MPR_IRQ1 MPR_IRQ2 MPR_IRQ3 MPR_IRQ4 ACC_INT SDA SCL 3V3 \
    DIR STEP ENN DIAG INDEX TMC_UART TMC_TX \
    USB_DP USB_DM CC1 CC2 USB_VBUS EN BOOT ENDSTOP_N ENDSTOP_G \
    LED_ST LED_A LED_SA HOST_TX HOST_RX GATE_Q1 EN_BUCK

run r5.kicad_pcb w3.kicad_pcb 0.4 0.15 300000 5V SW_BUCK BST

echo "waves done -> $R/r5.kicad_pcb"
