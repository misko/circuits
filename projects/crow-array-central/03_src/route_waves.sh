#!/bin/bash
# KRT routing waves for crow-array-central (6-layer, JLC standard tier —
# ADR-0008). Re-route from scratch only; the standard rebuild uses the
# PROMOTED chain file 03_src/route/final.kicad_pcb (canon M3).
#
# Stackup: F.Cu / In1.Cu GND plane / In2.Cu / In3.Cu / In4.Cu GND plane /
# B.Cu. Four SIGNAL layers (F/In2/In3/B), each over a GND plane. GND is NOT
# routed (In1+In4 planes + F/In2/In3/B pours + stitch vias). 0.6/0.3 vias.
#
# Order (D16, 6L revised): POWER FIRST. The distributed XU316 power pins
# (3V3 x10 / 0V9 x15, interleaved on every edge at 0.4mm) are the hardest
# escapes — signal-first boxes them (measured). With 4 signal layers,
# power-first still leaves room for the signal buses.
#  0 fanout XU316 (every used pin -> F.Cu escape stub, ADR-0004)
#  1 5V trunk
#  2 regulated rails 3V3/0V9/1V8/3V3A
#  3 PORTPWR (BEEP_5V/RET/5V_AUD) + buck SW nodes
#  4 USB-HS pair + MCLK clock tree + I2S/TDM + I2C bus
#  5 beeper-gate BUS (8 GPIO->gate->FET lines, jointly)
#  6 audio pairs (AUD/AIN) + injection + QSPI
#  7 signal remainder (GPIO, straps, VBUS, JTAG, ADC ins, crystal, PLL, FB)
set -euo pipefail
cd "$(dirname "$0")/.."
KRT=~/gits/KiCadRoutingTools
R=06_build/route
PY=~/gits/KiCadRoutingTools/.venv/bin/python
L="F.Cu In2.Cu In3.Cu B.Cu"   # 4 signal layers (In1/In4 = GND planes)
# --no-stub-layer-swap: escapes stay on F.Cu out of the 0.4mm pad field and
# only via once they DIVERGE into open space. Swapping at the pitch put two
# 0.6mm vias 0.4mm apart -> overlap/short (fixed). 6L gives the onward
# routing 3 more layers so escapes still converge.
V="--via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap --keepout --keepout-layer User.2"

# Wave 0: fanout ALL fine-pitch parts — the XU316 (TQFP-128 0.4mm) AND both
# PCM1865 ADCs (TSSOP-30 0.5mm). Every used pin escapes the pad field on an
# F.Cu stub, so with --no-stub-layer-swap the onward vias land in DIVERGED
# space (not at the pad pitch, where 0.6mm vias overlap -> shorts).
$PY "$KRT"/qfn_fanout.py "$R"/r0.kicad_pcb  -o "$R"/r0fa.kicad_pcb -c U1 \
  --width 0.15 --clearance 0.13 --via-size 0.45 --via-drill 0.3 \
  --fab-tier standard --grid-step 0.1
$PY "$KRT"/qfn_fanout.py "$R"/r0fa.kicad_pcb -o "$R"/r0fb.kicad_pcb -c U2 \
  --width 0.15 --clearance 0.13 --via-size 0.45 --via-drill 0.3 \
  --fab-tier standard --grid-step 0.1
$PY "$KRT"/qfn_fanout.py "$R"/r0fb.kicad_pcb -o "$R"/r0fc.kicad_pcb -c U3 \
  --width 0.15 --clearance 0.13 --via-size 0.45 --via-drill 0.3 \
  --fab-tier standard --grid-step 0.1
# USB-C receptacle (J12, 0.5mm pitch) — fan the pins out too so the USB pair
# + CC/VBUS escape the connector field instead of crowding to sub-fab gaps.
$PY "$KRT"/qfn_fanout.py "$R"/r0fc.kicad_pcb -o "$R"/r0f.kicad_pcb  -c J12 \
  --width 0.2 --clearance 0.13 --via-size 0.45 --via-drill 0.3 \
  --fab-tier standard --grid-step 0.1

$PY "$KRT"/route.py "$R"/r0f.kicad_pcb --output "$R"/r1.kicad_pcb \
  --layers $L --clearance 0.15 --track-width 0.5 $V --max-iterations 500000 \
  --nets 5V 5V_P 5V_IN

# Rails wave — the distributed XU316 3V3/0V9 pins, jointly, with high ripup
# so KRT can arbitrate the interleaved-pin escapes.
$PY "$KRT"/route.py "$R"/r1.kicad_pcb --output "$R"/r2.kicad_pcb \
  --layers $L --clearance 0.15 --track-width 0.4 $V --max-iterations 3000000 \
  --max-ripup 300 --nets 3V3 0V9 1V8 3V3A

$PY "$KRT"/route.py "$R"/r2.kicad_pcb --output "$R"/r3.kicad_pcb \
  --layers $L --clearance 0.15 --track-width 0.4 $V --max-iterations 500000 \
  --nets BEEP_5V1 BEEP_5V2 BEEP_5V3 BEEP_5V4 BEEP_5V5 BEEP_5V6 BEEP_5V7 BEEP_5V8 \
         BEEP_RET1 BEEP_RET2 BEEP_RET3 BEEP_RET4 BEEP_RET5 BEEP_RET6 BEEP_RET7 BEEP_RET8 \
         5V_AUD1 5V_AUD2 5V_AUD3 5V_AUD4 5V_AUD5 5V_AUD6 5V_AUD7 5V_AUD8 \
         BK1_SW BK2_SW

# Wave 4: USB + clock tree + I2S/TDM + I2C bus (I2C early, like the clock).
$PY "$KRT"/route.py "$R"/r3.kicad_pcb --output "$R"/r4.kicad_pcb \
  --layers $L --clearance 0.15 --track-width 0.25 $V --max-iterations 800000 \
  --nets USB_DP USB_DM MCLK_SRC MCLK_A0 MCLK_B0 MCLK_A MCLK_B \
         BCLK LRCK DATA1 DATA2 I2C_SCL I2C_SDA

# Wave 5: beeper-gate BUS (16 nets jointly).
$PY "$KRT"/route.py "$R"/r4.kicad_pcb --output "$R"/r5.kicad_pcb \
  --layers $L --clearance 0.15 --track-width 0.2 $V --max-iterations 3000000 \
  --max-ripup 300 \
  --nets BEEP_G1 BEEP_G2 BEEP_G3 BEEP_G4 BEEP_G5 BEEP_G6 BEEP_G7 BEEP_G8 \
         BG_1 BG_2 BG_3 BG_4 BG_5 BG_6 BG_7 BG_8

$PY "$KRT"/route.py "$R"/r5.kicad_pcb --output "$R"/r6.kicad_pcb \
  --layers $L --clearance 0.15 --track-width 0.2 $V --max-iterations 600000 \
  --nets AUD_P1 AUD_N1 AUD_P2 AUD_N2 AUD_P3 AUD_N3 AUD_P4 AUD_N4 \
         AUD_P5 AUD_N5 AUD_P6 AUD_N6 AUD_P7 AUD_N7 AUD_P8 AUD_N8 \
         AIN_P1 AIN_N1 AIN_P2 AIN_N2 AIN_P3 AIN_N3 AIN_P4 AIN_N4 \
         AIN_P5 AIN_N5 AIN_P6 AIN_N6 AIN_P7 AIN_N7 AIN_P8 AIN_N8 \
         INJ INJ_C QSPI_CLK QSPI_CS QSPI_D0 QSPI_D1 QSPI_D2 QSPI_D3

$PY "$KRT"/route.py "$R"/r6.kicad_pcb --output "$R"/final.kicad_pcb \
  --layers $L --clearance 0.15 --track-width 0.2 $V --max-iterations 800000 \
  --nets GATE9 \
         GP0_A GP0_B GP1_A GP1_B GP2_A GP2_B GP3_A GP3_B \
         CC1 CC2 FB1 FB2 BK1_PG BK2_PG LDO_A LDO_B VREF_A VREF_B \
         VA1M VA1P VA2M VA2P VA3M VA3P VA4M VA4P \
         VB1M VB1P VB2M VB2P VB3M VB3P VB4M VB4P \
         RST_N TCK TDI TDO TMS BCLK_X LRCK_X XIN XOUT XTAL2 \
         PLL_AVDD VBUS VBUS_DET

# ---- adaptive reconciliation: a handful of dense XU316-escape nets
# straggle (which ones varies run-to-run — KRT is nondeterministic).
# route_reconcile.py finds whatever is unrouted and rip-reroutes it on a
# FINE grid using KRT's own blocker hints (each ripped net is re-routed).
$PY 03_src/route_reconcile.py "$R"/final.kicad_pcb --passes 10

echo "waves done -> $R/final.kicad_pcb"
