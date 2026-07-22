#!/bin/bash
# KRT routing waves for ble-bus-bar (west electronics zone ONLY — the
# slices/corridor are hand-routed by route_channels.py; power is pours).
# 2-layer JLC 2oz (0.16/0.16 floor).
#
# WAVE ORDER IS THE FIX (kicad-pcb golden rule 4: hardest nets first —
# escape lanes are claimed by whoever routes first): the ESP32 module's
# south/north pin rows have 0.6mm gaps that only the 0.05 fine grid can
# thread; if USB/CC/SPI route first they fence those pins in (three
# repair-loop campaigns proved it). GND is never routed (pours + vias).
set -euo pipefail
cd "$(dirname "$0")/.."
KRT=~/gits/KiCadRoutingTools
R=06_build/route
PY=~/gits/KiCadRoutingTools/.venv/bin/python

# Wave A — boxed module pins, fine grid, FIRST
$PY "$KRT"/route.py "$R"/r0.kicad_pcb --output "$R"/rA.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.16 --track-width 0.25 --grid-step 0.05 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets SDA SCL ALERT LED_ST EN BOOT9 IO8 SPI_MISO FLASH_CS

# Wave B — remaining signals, standard grid
$PY "$KRT"/route.py "$R"/rA.kicad_pcb --output "$R"/rB.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.2 --track-width 0.3 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 400000 \
  --nets USB_DP USB_DM CC1 CC2 SPI_CLK SPI_MOSI \
         LED1A LED2A TXD RXD FB SHDN

# Wave B2 — USB-C 0.5mm weave + fine-pitch stragglers (fine grid)
$PY "$KRT"/route.py "$R"/rB.kicad_pcb --output "$R"/rB2.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.16 --track-width 0.2 --grid-step 0.05 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 200000 \
  --nets USB_DM USB_DP RXD TXD

# Wave B3 — NE stragglers (J10/pullup column behind the LED col): rip
# the earlier claimants and re-route together, fine grid
$PY "$KRT"/route.py "$R"/rB2.kicad_pcb --output "$R"/rB3.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.18 --track-width 0.25 --grid-step 0.05 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 300000 \
  --nets TXD RXD IO8 USB_DM \
  --rip-existing-nets LED1A LED2A USB_DP CC1 CC2 SPI_CLK SPI_MOSI

# Wave C — electronics power (EPWR floor 0.5)
$PY "$KRT"/route.py "$R"/rB3.kicad_pcb --output "$R"/rC.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.16 --track-width 0.5 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 400000 \
  --nets TMP_3V3 VTAP VIN_E SW BOOT VLDO VUSB

# Wave C2 — 3V3 completion at the RAIL3V3 floor (0.3), fine grid
$PY "$KRT"/route.py "$R"/rC.kicad_pcb --output "$R"/r3.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.16 --track-width 0.3 --grid-step 0.05 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 200000 \
  --nets TMP_3V3

echo "waves done -> $R/r3.kicad_pcb"
